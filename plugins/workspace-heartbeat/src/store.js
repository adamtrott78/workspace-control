export class HeartbeatStore {
  constructor({ historyLimit = 50, timelineLimit = 50 } = {}) {
    this.historyLimit = historyLimit;
    this.timelineLimit = timelineLimit;
    this.tasks = new Map();
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

  _timelineIdForUpdate({ sessionId, taskId }) {
    const sessionKey = this._sessionKey(sessionId);
    let timelineId = this.timelineBySession.get(sessionKey);

    if (!timelineId) {
      timelineId = this.latestTimelineByTask.get(taskId) ?? this._newTimelineId();
      this.timelineBySession.set(sessionKey, timelineId);
    }

    return timelineId;
  }

  update({ sessionId, taskId, message, state, now = new Date() }) {
    const previous = this.tasks.get(taskId);
    const heartbeat = {
      task_id: taskId,
      message,
      state,
      sequence: (previous?.heartbeat?.sequence ?? 0) + 1,
      updated_at: now.toISOString(),
    };

    const history = [...(previous?.history ?? []), heartbeat].slice(
      -this.historyLimit,
    );
    this.tasks.set(taskId, { heartbeat, history });

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
