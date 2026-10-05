export class HeartbeatStore {
  constructor({ historyLimit = 50 } = {}) {
    this.historyLimit = historyLimit;
    this.tasks = new Map();
    this.latestTaskBySession = new Map();
  }

  _sessionKey(sessionId) {
    return sessionId || "dev-session";
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
    this.latestTaskBySession.set(this._sessionKey(sessionId), taskId);

    return heartbeat;
  }

  _resolveTaskId({ sessionId, taskId }) {
    if (taskId) return taskId;
    return this.latestTaskBySession.get(this._sessionKey(sessionId)) ?? null;
  }

  get({ sessionId, taskId }) {
    const resolvedTaskId = this._resolveTaskId({ sessionId, taskId });
    if (!resolvedTaskId) return null;
    return this.tasks.get(resolvedTaskId)?.heartbeat ?? null;
  }

  getSnapshot({ sessionId, taskId }) {
    const resolvedTaskId = this._resolveTaskId({ sessionId, taskId });
    if (!resolvedTaskId) {
      return { heartbeat: null, history: [] };
    }

    const record = this.tasks.get(resolvedTaskId);
    if (!record) {
      return { heartbeat: null, history: [] };
    }

    return {
      heartbeat: record.heartbeat,
      history: [...record.history],
    };
  }
}
