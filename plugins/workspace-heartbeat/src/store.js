import { randomUUID } from "node:crypto";

function fail(code, message) {
  const error = new Error(`${code}: ${message}`);
  error.code = code;
  throw error;
}

export class HeartbeatStore {
  constructor({
    historyLimit = 50,
    timelineLimit = 50,
    turnHistoryLimit = 50,
    turnIdFactory = () => randomUUID(),
  } = {}) {
    this.historyLimit = historyLimit;
    this.timelineLimit = timelineLimit;
    this.turnHistoryLimit = turnHistoryLimit;
    this.turnIdFactory = turnIdFactory;
    this.tasks = new Map();
    this.turns = new Map();
    this.latestTaskBySession = new Map();
    this.timelineBySession = new Map();
    this.latestTimelineByTask = new Map();
    this.timelines = new Map();
    this.timelineCounter = 0;
  }

  _sessionKey(sessionId) {
    return sessionId || "dev-session";
  }

  _newTimelineId() {
    this.timelineCounter += 1;
    return `timeline-${this.timelineCounter}`;
  }

  _newTurnId() {
    let id = this.turnIdFactory();
    while (this.turns.has(id)) id = this.turnIdFactory();
    return id;
  }

  _taskRecord(taskId) {
    let record = this.tasks.get(taskId);
    if (!record) {
      record = {
        heartbeat: null,
        history: [],
        activeTurnId: null,
        ownerSessionId: null,
      };
      this.tasks.set(taskId, record);
    }
    return record;
  }

  _timelineIdForUpdate({ sessionId, taskId }) {
    const sessionKey = this._sessionKey(sessionId);
    let timelineId = this.timelineBySession.get(sessionKey);

    if (!timelineId) {
      timelineId = this.latestTimelineByTask.get(taskId) ?? this._newTimelineId();
      this.timelineBySession.set(sessionKey, timelineId);
    }

    return timelineId;
  }

  _appendHeartbeat({ sessionId, taskId, turn, message, state, now }) {
    const task = this._taskRecord(taskId);
    const heartbeat = {
      task_id: taskId,
      turn_id: turn.turnId,
      message,
      state,
      sequence: (task.heartbeat?.sequence ?? 0) + 1,
      updated_at: now.toISOString(),
    };

    task.heartbeat = heartbeat;
    task.history = [...task.history, heartbeat].slice(-this.historyLimit);
    turn.heartbeat = heartbeat;
    turn.history = [...turn.history, heartbeat].slice(-this.turnHistoryLimit);

    const sessionKey = this._sessionKey(sessionId);
    this.latestTaskBySession.set(sessionKey, taskId);

    const timelineId = this._timelineIdForUpdate({ sessionId, taskId });
    const timeline = [...(this.timelines.get(timelineId) ?? []), heartbeat].slice(
      -this.timelineLimit,
    );
    this.timelines.set(timelineId, timeline);
    this.latestTimelineByTask.set(taskId, timelineId);

    return heartbeat;
  }

  beginTurn({
    sessionId,
    taskId,
    message,
    state = "working",
    now = new Date(),
  }) {
    const sessionKey = this._sessionKey(sessionId);
    const task = this._taskRecord(taskId);

    if (task.ownerSessionId && task.ownerSessionId !== sessionKey) {
      fail(
        "HEARTBEAT_TASK_OWNED_BY_ANOTHER_CONVERSATION",
        "This task already has an active heartbeat writer in another conversation.",
      );
    }

    if (task.activeTurnId) {
      const previous = this.turns.get(task.activeTurnId);
      if (previous?.active) {
        if (previous.sessionId !== sessionKey) {
          fail(
            "HEARTBEAT_TASK_OWNED_BY_ANOTHER_CONVERSATION",
            "This task already has an active heartbeat writer in another conversation.",
          );
        }
        previous.active = false;
        previous.superseded = true;
        previous.superseded_at = now.toISOString();
      }
    }

    const turnId = this._newTurnId();
    const turn = {
      turnId,
      taskId,
      sessionId: sessionKey,
      active: true,
      superseded: false,
      completed: false,
      heartbeat: null,
      history: [],
      started_at: now.toISOString(),
    };
    this.turns.set(turnId, turn);
    task.activeTurnId = turnId;
    task.ownerSessionId = sessionKey;

    this._appendHeartbeat({
      sessionId: sessionKey,
      taskId,
      turn,
      message,
      state,
      now,
    });
    turn.last_executor_touch_at = now.toISOString();

    if (state === "done") {
      this._completeTurn({ task, turn, now });
    }

    return this.getTurnSnapshot({ taskId, turnId });
  }

  _completeTurn({ task, turn, now }) {
    turn.active = false;
    turn.completed = true;
    turn.completed_at = now.toISOString();
    if (task.activeTurnId === turn.turnId) {
      task.activeTurnId = null;
      task.ownerSessionId = null;
    }
  }

  updateTurn({
    sessionId,
    taskId,
    turnId,
    message,
    state = "working",
    now = new Date(),
  }) {
    const sessionKey = this._sessionKey(sessionId);
    const turn = this.turns.get(turnId);

    if (!turn) {
      fail(
        "HEARTBEAT_TURN_NOT_FOUND",
        "This heartbeat turn does not exist. Start the current assistant response with heartbeat_begin_turn.",
      );
    }
    if (turn.taskId !== taskId) {
      fail(
        "HEARTBEAT_TURN_TASK_MISMATCH",
        "The supplied turn_id does not belong to this task_id.",
      );
    }
    if (turn.sessionId !== sessionKey) {
      fail(
        "HEARTBEAT_TURN_CONVERSATION_MISMATCH",
        "The supplied turn_id belongs to another ChatGPT conversation.",
      );
    }
    if (!turn.active) {
      const reason = turn.superseded ? "superseded" : "completed";
      fail(
        "HEARTBEAT_TURN_STALE",
        `This heartbeat turn is ${reason}. Start a new assistant turn with heartbeat_begin_turn.`,
      );
    }

    const task = this._taskRecord(taskId);
    if (task.activeTurnId !== turnId || task.ownerSessionId !== sessionKey) {
      fail(
        "HEARTBEAT_TURN_STALE",
        "This is no longer the active heartbeat turn for the task.",
      );
    }

    const heartbeat = this._appendHeartbeat({
      sessionId: sessionKey,
      taskId,
      turn,
      message,
      state,
      now,
    });
    turn.last_executor_touch_at = now.toISOString();

    if (state === "done") {
      this._completeTurn({ task, turn, now });
    }

    return heartbeat;
  }

  touchTurn({ sessionId, taskId, turnId, now = new Date() }) {
    const sessionKey = this._sessionKey(sessionId);
    const turn = this.turns.get(turnId);
    if (!turn) fail("HEARTBEAT_TURN_NOT_FOUND", "Unknown turn.");
    if (turn.taskId !== taskId) fail("HEARTBEAT_TURN_TASK_MISMATCH", "Wrong task.");
    if (turn.sessionId !== sessionKey) fail("HEARTBEAT_TURN_CONVERSATION_MISMATCH", "Wrong conversation.");
    const task = this._taskRecord(taskId);
    if (!turn.active || task.activeTurnId !== turnId || task.ownerSessionId !== sessionKey) {
      fail("HEARTBEAT_TURN_STALE", "Turn no longer owns this task.");
    }
    turn.last_executor_touch_at = now.toISOString();
    return { acknowledged: true };
  }

  observeUi({ taskId, turnId, now = new Date() }) {
    const turn = this.turns.get(turnId);
    if (!turn || turn.taskId !== taskId) return null;
    turn.last_ui_seen_at = now.toISOString();
    return this.getTurnSnapshot({ taskId, turnId });
  }

  observeUiDelta({ taskId, turnId, afterSequence = 0, now = new Date() }) {
    const turn = this.turns.get(turnId);
    if (!turn || turn.taskId !== taskId) return null;

    turn.last_ui_seen_at = now.toISOString();
    const history = [...turn.history];
    const oldestSequence = history[0]?.sequence ?? null;
    const latestSequence = turn.heartbeat?.sequence ?? 0;
    const resync =
      (oldestSequence !== null && afterSequence < oldestSequence - 1) ||
      afterSequence > latestSequence;
    const updates = resync
      ? history
      : history.filter((heartbeat) => heartbeat.sequence > afterSequence);
    const turnStatus = turn.superseded
      ? "superseded"
      : turn.completed
        ? "completed"
        : "active";

    return {
      task_id: taskId,
      turn_id: turnId,
      turn_status: turnStatus,
      updates,
      resync,
      last_executor_touch_at: turn.last_executor_touch_at ?? null,
      last_ui_seen_at: turn.last_ui_seen_at ?? null,
    };
  }

  getTurnSnapshot({ taskId, turnId }) {
    const turn = this.turns.get(turnId);
    if (!turn || turn.taskId !== taskId) return null;

    return {
      task_id: taskId,
      turn_id: turnId,
      heartbeat: turn.heartbeat,
      recent: [...turn.history].slice(-3),
      turn_history: [...turn.history],
      active: turn.active,
      superseded: turn.superseded,
      completed: turn.completed,
      last_executor_touch_at: turn.last_executor_touch_at ?? null,
      last_ui_seen_at: turn.last_ui_seen_at ?? null,
      executor_touch_age_seconds: turn.last_executor_touch_at ? Math.max(0, (Date.now() - Date.parse(turn.last_executor_touch_at)) / 1000) : null,
      ui_seen_age_seconds: turn.last_ui_seen_at ? Math.max(0, (Date.now() - Date.parse(turn.last_ui_seen_at)) / 1000) : null,
    };
  }

  _resolveTaskId({ sessionId, taskId }) {
    if (taskId) return taskId;
    return this.latestTaskBySession.get(this._sessionKey(sessionId)) ?? null;
  }

  _resolveTimeline({ sessionId, taskId }) {
    if (taskId) {
      const timelineId = this.latestTimelineByTask.get(taskId);
      return timelineId ? [...(this.timelines.get(timelineId) ?? [])] : [];
    }

    const timelineId = this.timelineBySession.get(this._sessionKey(sessionId));
    return timelineId ? [...(this.timelines.get(timelineId) ?? [])] : [];
  }

  get({ sessionId, taskId }) {
    const resolvedTaskId = this._resolveTaskId({ sessionId, taskId });
    if (!resolvedTaskId) return null;
    return this.tasks.get(resolvedTaskId)?.heartbeat ?? null;
  }

  getSnapshot({ sessionId, taskId }) {
    const resolvedTaskId = this._resolveTaskId({ sessionId, taskId });
    const timeline = this._resolveTimeline({
      sessionId,
      taskId: resolvedTaskId ?? taskId,
    });

    if (!resolvedTaskId) {
      return { heartbeat: null, history: [], timeline };
    }

    const record = this.tasks.get(resolvedTaskId);
    if (!record) {
      return { heartbeat: null, history: [], timeline };
    }

    return {
      heartbeat: record.heartbeat,
      history: [...record.history],
      timeline,
    };
  }
}
