export class HeartbeatStore {
  constructor() {
    this.bySession = new Map();
  }

  _session(sessionId) {
    const key = sessionId || "dev-session";
    let record = this.bySession.get(key);
    if (!record) {
      record = {
        latestTaskId: null,
        tasks: new Map(),
      };
      this.bySession.set(key, record);
    }
    return record;
  }

  update({ sessionId, taskId, message, state, now = new Date() }) {
    const session = this._session(sessionId);
    const previous = session.tasks.get(taskId);
    const heartbeat = {
      task_id: taskId,
      message,
      state,
      sequence: (previous?.sequence ?? 0) + 1,
      updated_at: now.toISOString(),
    };
    session.tasks.set(taskId, heartbeat);
    session.latestTaskId = taskId;
    return heartbeat;
  }

  get({ sessionId, taskId }) {
    const session = this._session(sessionId);
    const resolvedTaskId = taskId || session.latestTaskId;
    if (!resolvedTaskId) return null;
    return session.tasks.get(resolvedTaskId) ?? null;
  }
}
