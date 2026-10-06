const LEASE_MESSAGES = {
  TASK_NOT_FOUND: "No heartbeat exists for this task.",
  SEQUENCE_MISMATCH: "The supplied task sequence does not match the current heartbeat sequence.",
  WRITER_OWNERSHIP_CONFLICT: "Another ChatGPT session currently owns the writer lease for this task.",
  WRITER_HANDOFF_PENDING: "This task is awaiting an explicit writer claim before another heartbeat update.",
  WRITER_NOT_OWNER: "Only the current writer session may release this task for handoff.",
  WRITER_HANDOFF_NOT_READY: "This task has not been released for a normal writer handoff.",
};

export class HeartbeatLeaseError extends Error {
  constructor(code, { taskId, sequence = 0, expectedSequence } = {}) {
    super(LEASE_MESSAGES[code] ?? "Heartbeat writer lease operation rejected.");
    this.name = "HeartbeatLeaseError";
    this.code = code;
    this.taskId = taskId ?? null;
    this.sequence = sequence;
    this.expectedSequence = expectedSequence;
  }

  toPublic() {
    const result = {
      code: this.code,
      task_id: this.taskId,
      sequence: this.sequence,
    };
    if (this.expectedSequence !== undefined) {
      result.expected_sequence = this.expectedSequence;
    }
    return result;
  }
}

export class HeartbeatStore {
  constructor({ historyLimit = 50, timelineLimit = 50 } = {}) {
    this.historyLimit = historyLimit;
    this.timelineLimit = timelineLimit;
    this.tasks = new Map();
    this.latestTaskBySession = new Map();
    this.timelineBySession = new Map();
    this.latestTimelineByTask = new Map();
    this.timelines = new Map();
    this.writerLeaseByTask = new Map();
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

  _sequenceForTask(taskId) {
    return this.tasks.get(taskId)?.heartbeat?.sequence ?? 0;
  }

  _requireTaskSequence(taskId, expectedSequence) {
    const sequence = this._sequenceForTask(taskId);
    if (!this.tasks.has(taskId)) {
      throw new HeartbeatLeaseError("TASK_NOT_FOUND", { taskId, sequence });
    }
    if (sequence !== expectedSequence) {
      throw new HeartbeatLeaseError("SEQUENCE_MISMATCH", {
        taskId,
        sequence,
        expectedSequence,
      });
    }
    return sequence;
  }

  _leaseResult(taskId, status) {
    return {
      task_id: taskId,
      sequence: this._sequenceForTask(taskId),
      status,
    };
  }

  _assertWriterForUpdate({ sessionId, taskId }) {
    const sessionKey = this._sessionKey(sessionId);
    const lease = this.writerLeaseByTask.get(taskId);

    if (!lease) {
      this.writerLeaseByTask.set(taskId, {
        status: "owned",
        sessionKey,
      });
      return;
    }

    if (lease.status === "released") {
      throw new HeartbeatLeaseError("WRITER_HANDOFF_PENDING", {
        taskId,
        sequence: this._sequenceForTask(taskId),
      });
    }

    if (lease.sessionKey !== sessionKey) {
      throw new HeartbeatLeaseError("WRITER_OWNERSHIP_CONFLICT", {
        taskId,
        sequence: this._sequenceForTask(taskId),
      });
    }
  }

  update({ sessionId, taskId, message, state, now = new Date() }) {
    this._assertWriterForUpdate({ sessionId, taskId });

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

  handoff({ sessionId, taskId, expectedSequence }) {
    const sequence = this._requireTaskSequence(taskId, expectedSequence);
    const sessionKey = this._sessionKey(sessionId);
    const lease = this.writerLeaseByTask.get(taskId);

    if (
      !lease ||
      lease.status !== "owned" ||
      lease.sessionKey !== sessionKey
    ) {
      throw new HeartbeatLeaseError("WRITER_NOT_OWNER", {
        taskId,
        sequence,
      });
    }

    this.writerLeaseByTask.set(taskId, {
      status: "released",
      releasedSequence: sequence,
    });
    return this._leaseResult(taskId, "handoff_ready");
  }

  claim({ sessionId, taskId, expectedSequence }) {
    const sequence = this._requireTaskSequence(taskId, expectedSequence);
    const lease = this.writerLeaseByTask.get(taskId);

    if (
      !lease ||
      lease.status !== "released" ||
      lease.releasedSequence !== sequence
    ) {
      throw new HeartbeatLeaseError("WRITER_HANDOFF_NOT_READY", {
        taskId,
        sequence,
      });
    }

    this.writerLeaseByTask.set(taskId, {
      status: "owned",
      sessionKey: this._sessionKey(sessionId),
    });
    return this._leaseResult(taskId, "owned");
  }

  recover({ sessionId, taskId, expectedSequence }) {
    this._requireTaskSequence(taskId, expectedSequence);
    this.writerLeaseByTask.set(taskId, {
      status: "owned",
      sessionKey: this._sessionKey(sessionId),
    });
    return this._leaseResult(taskId, "recovered");
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
