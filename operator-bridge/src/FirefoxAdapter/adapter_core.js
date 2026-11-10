"use strict";

(function initialize(globalObject) {
  const PROTOCOL_VERSION = "1.0";
  const NATIVE_HOST_NAME = "com.workspacecontrol.operator_bridge";
  const MANAGED_TAB_VALUE = "workspaceControlOperatorBindingV1";
  const WORKER_START_URL = "https://chatgpt.com/";
  const CHATGPT_ORIGIN = "https://chatgpt.com";
  const MAX_COMMAND_CACHE = 256;

  const OPERATIONS = new Set([
    "ENSURE_WORKER_SURFACE",
    "CREATE_WORKER_BINDING",
    "ACTIVATE_WORKER_BINDING",
    "RELOAD_OR_RESTORE_WORKER_BINDING",
    "DISCARD_WORKER_BINDING",
    "CLOSE_WORKER_BINDING",
    "INVENTORY_MANAGED_BINDINGS"
  ]);

  function classifyOrigin(rawValue) {
    if (typeof rawValue !== "string" || rawValue.length === 0) {
      return "UNKNOWN";
    }

    try {
      return new URL(rawValue).origin === CHATGPT_ORIGIN
        ? "CHATGPT_ORIGIN"
        : "OFF_CHATGPT_ORIGIN";
    } catch {
      return "UNKNOWN";
    }
  }

  function validIdentity(payload) {
    return payload &&
      typeof payload.worker_slot_id === "string" &&
      payload.worker_slot_id.length > 0 &&
      Number.isInteger(payload.session_generation) &&
      payload.session_generation >= 0;
  }

  function sanitizedMetadata(metadata) {
    if (!metadata || typeof metadata !== "object") {
      return null;
    }

    if (
      metadata.managed !== true ||
      typeof metadata.binding_ref !== "string" ||
      !Number.isInteger(metadata.binding_generation) ||
      typeof metadata.worker_slot_id !== "string" ||
      !Number.isInteger(metadata.session_generation)
    ) {
      return null;
    }

    return {
      managed: true,
      binding_ref: metadata.binding_ref,
      binding_generation: metadata.binding_generation,
      worker_slot_id: metadata.worker_slot_id,
      session_generation: metadata.session_generation
    };
  }

  function createResult(operation, outcome, extra = {}) {
    return {
      operation,
      outcome,
      normalized_error: extra.normalized_error ?? null,
      worker_slot_id: extra.worker_slot_id ?? null,
      session_generation: extra.session_generation ?? null,
      binding_ref: extra.binding_ref ?? null,
      binding_generation: extra.binding_generation ?? null,
      origin_classification: extra.origin_classification ?? null,
      discarded: extra.discarded ?? null,
      active: extra.active ?? null,
      inventory: extra.inventory ?? null
    };
  }

  class FirefoxAdapterCore {
    constructor(browserApi, options = {}) {
      this.browser = browserApi;
      this.emit = options.emit || (() => {});
      this.idFactory = options.idFactory || (() => crypto.randomUUID());
      this.commandCache = new Map();
      this.managedCache = new Map();
      this.lastOriginByTab = new Map();
    }

    async initialize() {
      await this.inventoryManagedBindings();
    }

    async handleCommand(message) {
      if (!message || message.message_type !== "BROWSER_COMMAND") {
        return null;
      }

      const requestId = message.request_id;
      const payload = message.payload || {};
      const operation = payload.operation;
      const idempotencyKey = payload.idempotency_key;

      if (
        typeof requestId !== "string" ||
        requestId.length === 0 ||
        typeof idempotencyKey !== "string" ||
        idempotencyKey.length === 0 ||
        !OPERATIONS.has(operation)
      ) {
        return createResult(operation || "UNKNOWN", "REJECTED", {
          normalized_error: "INVALID_BROWSER_COMMAND"
        });
      }

      const cached = this.commandCache.get(requestId);
      if (cached) {
        if (cached.idempotencyKey !== idempotencyKey) {
          return createResult(operation, "REJECTED", {
            normalized_error: "IDEMPOTENCY_CONFLICT"
          });
        }

        return structuredClone(cached.result);
      }

      let result;
      try {
        result = await this.execute(operation, payload);
      } catch {
        result = createResult(operation, "UNKNOWN", {
          normalized_error: "BROWSER_API_FAILURE"
        });
      }

      this.rememberCommand(requestId, idempotencyKey, result);
      return structuredClone(result);
    }

    async execute(operation, payload) {
      switch (operation) {
        case "ENSURE_WORKER_SURFACE":
          return this.ensureWorkerSurface(payload);
        case "CREATE_WORKER_BINDING":
          return this.createWorkerBinding(payload);
        case "ACTIVATE_WORKER_BINDING":
          return this.activateWorkerBinding(payload);
        case "RELOAD_OR_RESTORE_WORKER_BINDING":
          return this.reloadOrRestoreWorkerBinding(payload);
        case "DISCARD_WORKER_BINDING":
          return this.discardWorkerBinding(payload);
        case "CLOSE_WORKER_BINDING":
          return this.closeWorkerBinding(payload);
        case "INVENTORY_MANAGED_BINDINGS":
          return createResult(operation, "APPLIED", {
            inventory: await this.inventoryManagedBindings()
          });
        default:
          return createResult(operation, "REJECTED", {
            normalized_error: "UNKNOWN_BROWSER_OPERATION"
          });
      }
    }

    async ensureWorkerSurface(payload) {
      if (!validIdentity(payload)) {
        return createResult("ENSURE_WORKER_SURFACE", "REJECTED", {
          normalized_error: "INVALID_LOGICAL_TARGET"
        });
      }

      const match = await this.findManagedBinding(payload);
      if (match) {
        const tab = await this.browser.tabs.update(match.tabId, { active: true });
        return this.resultFor(
          "ENSURE_WORKER_SURFACE",
          "APPLIED",
          match.metadata,
          tab);
      }

      return this.createWorkerBinding({
        ...payload,
        operation: "CREATE_WORKER_BINDING"
      }, "ENSURE_WORKER_SURFACE");
    }

    async createWorkerBinding(payload, resultOperation = "CREATE_WORKER_BINDING") {
      if (!validIdentity(payload)) {
        return createResult(resultOperation, "REJECTED", {
          normalized_error: "INVALID_LOGICAL_TARGET"
        });
      }

      const existing = await this.findManagedBinding(payload);
      if (existing) {
        return this.resultFor(
          resultOperation,
          "REJECTED",
          existing.metadata,
          existing.tab,
          "BINDING_ALREADY_EXISTS");
      }

      const nextGeneration =
        Number.isInteger(payload.expected_binding_generation) &&
        payload.expected_binding_generation >= 0
          ? payload.expected_binding_generation + 1
          : 1;

      const tab = await this.browser.tabs.create({
        url: WORKER_START_URL,
        active: false
      });

      const metadata = {
        managed: true,
        binding_ref: this.idFactory(),
        binding_generation: nextGeneration,
        worker_slot_id: payload.worker_slot_id,
        session_generation: payload.session_generation
      };

      try {
        await this.browser.sessions.setTabValue(
          tab.id,
          MANAGED_TAB_VALUE,
          metadata);
      } catch {
        await this.browser.tabs.remove(tab.id).catch(() => {});
        return createResult(resultOperation, "UNKNOWN", {
          normalized_error: "BINDING_METADATA_WRITE_FAILED",
          worker_slot_id: payload.worker_slot_id,
          session_generation: payload.session_generation
        });
      }

      this.cacheBinding(tab.id, metadata);
      const current = await this.browser.tabs.get(tab.id);
      return this.resultFor(resultOperation, "APPLIED", metadata, current);
    }

    async activateWorkerBinding(payload) {
      const match = await this.requireManagedBinding(
        "ACTIVATE_WORKER_BINDING",
        payload);
      if (match.result) {
        return match.result;
      }

      const tab = await this.browser.tabs.update(match.tabId, { active: true });
      this.emitBindingEvent("BINDING_ACTIVATED", match.tabId, match.metadata, tab);
      return this.resultFor(
        "ACTIVATE_WORKER_BINDING",
        "APPLIED",
        match.metadata,
        tab);
    }

    async reloadOrRestoreWorkerBinding(payload) {
      const match = await this.requireManagedBinding(
        "RELOAD_OR_RESTORE_WORKER_BINDING",
        payload);
      if (match.result) {
        return match.result;
      }

      await this.browser.tabs.reload(match.tabId);
      const tab = await this.browser.tabs.get(match.tabId);
      return this.resultFor(
        "RELOAD_OR_RESTORE_WORKER_BINDING",
        "APPLIED",
        match.metadata,
        tab);
    }

    async discardWorkerBinding(payload) {
      const match = await this.requireManagedBinding(
        "DISCARD_WORKER_BINDING",
        payload);
      if (match.result) {
        return match.result;
      }

      if (match.tab.active) {
        return this.resultFor(
          "DISCARD_WORKER_BINDING",
          "NOT_APPLIED",
          match.metadata,
          match.tab,
          "ACTIVE_TAB_NOT_DISCARDABLE");
      }

      const tab = await this.browser.tabs.discard(match.tabId);
      this.emitBindingEvent("BINDING_DISCARDED", match.tabId, match.metadata, tab);
      return this.resultFor(
        "DISCARD_WORKER_BINDING",
        "APPLIED",
        match.metadata,
        tab);
    }

    async closeWorkerBinding(payload) {
      const match = await this.requireManagedBinding(
        "CLOSE_WORKER_BINDING",
        payload);
      if (match.result) {
        return match.result;
      }

      await this.browser.tabs.remove(match.tabId);
      this.managedCache.delete(match.tabId);
      this.lastOriginByTab.delete(match.tabId);
      return createResult("CLOSE_WORKER_BINDING", "APPLIED", {
        worker_slot_id: match.metadata.worker_slot_id,
        session_generation: match.metadata.session_generation,
        binding_ref: match.metadata.binding_ref,
        binding_generation: match.metadata.binding_generation,
        origin_classification: classifyOrigin(match.tab.url),
        discarded: Boolean(match.tab.discarded),
        active: Boolean(match.tab.active)
      });
    }

    async requireManagedBinding(operation, payload) {
      if (!validIdentity(payload)) {
        return {
          result: createResult(operation, "REJECTED", {
            normalized_error: "INVALID_LOGICAL_TARGET"
          })
        };
      }

      const match = await this.findManagedBinding(payload);
      if (!match) {
        return {
          result: createResult(operation, "REJECTED", {
            normalized_error: "MANAGED_BINDING_NOT_FOUND",
            worker_slot_id: payload.worker_slot_id,
            session_generation: payload.session_generation
          })
        };
      }

      if (
        Number.isInteger(payload.expected_binding_generation) &&
        payload.expected_binding_generation !== match.metadata.binding_generation
      ) {
        return {
          result: this.resultFor(
            operation,
            "REJECTED",
            match.metadata,
            match.tab,
            "BINDING_GENERATION_MISMATCH")
        };
      }

      return match;
    }

    async findManagedBinding(payload) {
      const inventory = await this.collectManagedTabs();
      return inventory.find(item =>
        item.metadata.worker_slot_id === payload.worker_slot_id &&
        item.metadata.session_generation === payload.session_generation
      ) || null;
    }

    async inventoryManagedBindings() {
      const managed = await this.collectManagedTabs();
      return managed.map(item => ({
        binding_ref: item.metadata.binding_ref,
        binding_generation: item.metadata.binding_generation,
        worker_slot_id: item.metadata.worker_slot_id,
        session_generation: item.metadata.session_generation,
        origin_classification: classifyOrigin(item.tab.url),
        discarded: Boolean(item.tab.discarded),
        active: Boolean(item.tab.active)
      }));
    }

    async collectManagedTabs() {
      const tabs = await this.browser.tabs.query({});
      const managed = [];

      for (const tab of tabs) {
        let stored;
        try {
          stored = await this.browser.sessions.getTabValue(
            tab.id,
            MANAGED_TAB_VALUE);
        } catch {
          continue;
        }

        const metadata = sanitizedMetadata(stored);
        if (!metadata) {
          continue;
        }

        this.cacheBinding(tab.id, metadata);
        managed.push({ tabId: tab.id, tab, metadata });
      }

      return managed;
    }

    async handleTabUpdated(tabId, changeInfo, tab) {
      const metadata = await this.getManagedMetadata(tabId);
      if (!metadata) {
        return;
      }

      const classification = classifyOrigin(
        typeof changeInfo.url === "string" ? changeInfo.url : tab.url);
      const previous = this.lastOriginByTab.get(tabId);
      this.lastOriginByTab.set(tabId, classification);

      if (previous !== classification) {
        this.emitBindingEvent(
          "ORIGIN_CLASS_CHANGED",
          tabId,
          metadata,
          tab,
          classification);
      }
    }

    async handleTabActivated(activeInfo) {
      const metadata = await this.getManagedMetadata(activeInfo.tabId);
      if (!metadata) {
        return;
      }

      const tab = await this.browser.tabs.get(activeInfo.tabId);
      this.emitBindingEvent(
        "BINDING_ACTIVATED",
        activeInfo.tabId,
        metadata,
        tab);
    }

    handleTabRemoved(tabId) {
      const metadata = this.managedCache.get(tabId);
      if (!metadata) {
        return;
      }

      this.emit({
        event_type: "BINDING_CLOSED",
        worker_slot_id: metadata.worker_slot_id,
        session_generation: metadata.session_generation,
        binding_ref: metadata.binding_ref,
        binding_generation: metadata.binding_generation,
        origin_classification: this.lastOriginByTab.get(tabId) || "UNKNOWN"
      });

      this.managedCache.delete(tabId);
      this.lastOriginByTab.delete(tabId);
    }

    async getManagedMetadata(tabId) {
      if (this.managedCache.has(tabId)) {
        return this.managedCache.get(tabId);
      }

      let stored;
      try {
        stored = await this.browser.sessions.getTabValue(
          tabId,
          MANAGED_TAB_VALUE);
      } catch {
        return null;
      }

      const metadata = sanitizedMetadata(stored);
      if (metadata) {
        this.cacheBinding(tabId, metadata);
      }
      return metadata;
    }

    cacheBinding(tabId, metadata) {
      this.managedCache.set(tabId, metadata);
    }

    emitBindingEvent(
      eventType,
      tabId,
      metadata,
      tab,
      forcedClassification = null) {
      const classification = forcedClassification || classifyOrigin(tab.url);
      this.lastOriginByTab.set(tabId, classification);
      this.emit({
        event_type: eventType,
        worker_slot_id: metadata.worker_slot_id,
        session_generation: metadata.session_generation,
        binding_ref: metadata.binding_ref,
        binding_generation: metadata.binding_generation,
        origin_classification: classification
      });
    }

    resultFor(
      operation,
      outcome,
      metadata,
      tab,
      normalizedError = null) {
      return createResult(operation, outcome, {
        normalized_error: normalizedError,
        worker_slot_id: metadata.worker_slot_id,
        session_generation: metadata.session_generation,
        binding_ref: metadata.binding_ref,
        binding_generation: metadata.binding_generation,
        origin_classification: classifyOrigin(tab.url),
        discarded: Boolean(tab.discarded),
        active: Boolean(tab.active)
      });
    }

    rememberCommand(requestId, idempotencyKey, result) {
      this.commandCache.set(requestId, {
        idempotencyKey,
        result: structuredClone(result)
      });

      while (this.commandCache.size > MAX_COMMAND_CACHE) {
        const firstKey = this.commandCache.keys().next().value;
        this.commandCache.delete(firstKey);
      }
    }
  }

  const exported = {
    PROTOCOL_VERSION,
    NATIVE_HOST_NAME,
    MANAGED_TAB_VALUE,
    WORKER_START_URL,
    classifyOrigin,
    FirefoxAdapterCore
  };

  globalObject.WorkspaceFirefoxAdapterCore = exported;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = exported;
  }
})(globalThis);
