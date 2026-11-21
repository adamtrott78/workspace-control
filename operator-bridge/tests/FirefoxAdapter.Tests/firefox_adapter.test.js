"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const {
  MANAGED_TAB_VALUE,
  WORKER_START_URL,
  classifyOrigin,
  FirefoxAdapterCore
} = require("../../src/FirefoxAdapter/adapter_core.js");

class MockBrowser {
  constructor(initialTabs = []) {
    this.nextTabId = 100;
    this.tabsById = new Map();
    this.tabValues = new Map();
    this.calls = [];

    for (const tab of initialTabs) {
      this.tabsById.set(tab.id, { discarded: false, active: false, windowId: 1, ...tab });
      this.nextTabId = Math.max(this.nextTabId, tab.id + 1);
    }

    this.tabs = {
      query: async () => Array.from(this.tabsById.values()).map(tab => ({ ...tab })),
      create: async createProperties => {
        this.calls.push(["tabs.create", structuredClone(createProperties)]);
        const tab = {
          id: this.nextTabId++,
          url: createProperties.url,
          active: Boolean(createProperties.active),
          discarded: false,
          windowId: 1
        };
        this.tabsById.set(tab.id, tab);
        return { ...tab };
      },
      get: async tabId => {
        const tab = this.requireTab(tabId);
        return { ...tab };
      },
      update: async (tabId, updateProperties) => {
        this.calls.push(["tabs.update", tabId, structuredClone(updateProperties)]);
        const tab = this.requireTab(tabId);
        Object.assign(tab, updateProperties);
        return { ...tab };
      },
      reload: async tabId => {
        this.calls.push(["tabs.reload", tabId]);
        const tab = this.requireTab(tabId);
        tab.discarded = false;
      },
      discard: async tabId => {
        this.calls.push(["tabs.discard", tabId]);
        const tab = this.requireTab(tabId);
        tab.discarded = true;
        return { ...tab };
      },
      remove: async tabId => {
        this.calls.push(["tabs.remove", tabId]);
        this.requireTab(tabId);
        this.tabsById.delete(tabId);
        this.tabValues.delete(tabId);
      }
    };

    this.windows = {
      update: async (windowId, updateInfo) => {
        this.calls.push(["windows.update", windowId, structuredClone(updateInfo)]);
        return { id: windowId, ...updateInfo };
      }
    };

    this.sessions = {
      setTabValue: async (tabId, key, value) => {
        this.calls.push(["sessions.setTabValue", tabId, key, structuredClone(value)]);
        this.requireTab(tabId);
        if (!this.tabValues.has(tabId)) {
          this.tabValues.set(tabId, new Map());
        }
        this.tabValues.get(tabId).set(key, structuredClone(value));
      },
      getTabValue: async (tabId, key) => {
        this.requireTab(tabId);
        return structuredClone(this.tabValues.get(tabId)?.get(key) ?? null);
      }
    };
  }

  seedManaged(tabId, metadata) {
    if (!this.tabValues.has(tabId)) {
      this.tabValues.set(tabId, new Map());
    }
    this.tabValues.get(tabId).set(MANAGED_TAB_VALUE, structuredClone(metadata));
  }

  requireTab(tabId) {
    const tab = this.tabsById.get(tabId);
    if (!tab) {
      throw new Error("tab not found");
    }
    return tab;
  }
}

function command(requestId, operation, extra = {}, idempotencyKey = "idem-1") {
  return {
    protocol_version: "1.0",
    message_type: "BROWSER_COMMAND",
    message_id: "m-" + requestId,
    request_id: requestId,
    correlation_id: "c-" + requestId,
    sent_at_monotonic_ms: 1,
    payload: {
      operation,
      idempotency_key: idempotencyKey,
      ...extra
    }
  };
}

function managedMetadata(bindingRef = "binding-1") {
  return {
    managed: true,
    binding_ref: bindingRef,
    binding_generation: 1,
    worker_slot_id: "slot-1",
    session_generation: 7
  };
}

test("origin reduction never returns raw URL text", () => {
  assert.equal(classifyOrigin("https://chatgpt.com/c/abc?x=1"), "CHATGPT_ORIGIN");
  assert.equal(classifyOrigin("https://example.com/private"), "OFF_CHATGPT_ORIGIN");
  assert.equal(classifyOrigin("not a url"), "UNKNOWN");
});

test("unmanaged non-bootstrap ChatGPT tab is never adopted", async () => {
  const browser = new MockBrowser([
    { id: 1, url: "https://chatgpt.com/c/unmanaged", active: true }
  ]);
  const adapter = new FirefoxAdapterCore(browser, {
    idFactory: () => "binding-new"
  });

  const result = await adapter.handleCommand(command(
    "req-1",
    "ENSURE_WORKER_SURFACE",
    { worker_slot_id: "slot-1", session_generation: 7 }
  ));

  assert.equal(result.outcome, "APPLIED");
  assert.equal(result.binding_ref, "binding-new");
  assert.equal(browser.tabsById.size, 2);
  assert.equal(browser.tabValues.get(1), undefined);

  const createCall = browser.calls.find(call => call[0] === "tabs.create");
  assert.deepEqual(createCall[1], {
    url: WORKER_START_URL,
    active: false
  });
});

test("initialize navigates exactly one active blank startup tab to temporary chat", async () => {
  const browser = new MockBrowser([
    { id: 20, url: "about:newtab", active: true }
  ]);
  const adapter = new FirefoxAdapterCore(browser);

  await adapter.initialize();

  assert.equal(browser.tabsById.get(20).url, WORKER_START_URL);
  assert.deepEqual(
    browser.calls.find(call =>
      call[0] === "tabs.update" &&
      call[1] === 20 &&
      call[2]?.url === WORKER_START_URL),
    ["tabs.update", 20, { url: WORKER_START_URL }]
  );
  assert.equal(browser.tabValues.get(20), undefined);
});

test("initialize repairs exact legacy fake-worker residue without leaving the stale blank tab", async () => {
  const browser = new MockBrowser([
    { id: 22, url: "http://127.0.0.1:8765/fake-worker.html", active: true },
    { id: 23, url: "about:newtab", active: false }
  ]);
  const adapter = new FirefoxAdapterCore(browser);

  await adapter.initialize();

  assert.equal(browser.tabsById.size, 1);
  assert.equal(browser.tabsById.get(22).url, WORKER_START_URL);
  assert.equal(browser.tabsById.has(23), false);
  assert.deepEqual(
    browser.calls.find(call =>
      call[0] === "tabs.update" &&
      call[1] === 22 &&
      call[2]?.url === WORKER_START_URL),
    ["tabs.update", 22, { url: WORKER_START_URL }]
  );
  assert.deepEqual(
    browser.calls.find(call =>
      call[0] === "tabs.remove" &&
      call[1] === 23),
    ["tabs.remove", 23]
  );
});

test("initialize does not repair arbitrary localhost pages", async () => {
  const browser = new MockBrowser([
    { id: 24, url: "http://127.0.0.1:8765/not-the-legacy-worker.html", active: true },
    { id: 25, url: "about:newtab", active: false }
  ]);
  const adapter = new FirefoxAdapterCore(browser);

  await adapter.initialize();

  assert.equal(
    browser.tabsById.get(24).url,
    "http://127.0.0.1:8765/not-the-legacy-worker.html"
  );
  assert.equal(browser.tabsById.has(25), true);
  assert.equal(
    browser.calls.filter(call => call[0] === "tabs.update").length,
    0
  );
  assert.equal(
    browser.calls.filter(call => call[0] === "tabs.remove").length,
    0
  );
});

test("initialize does not navigate arbitrary unmanaged tabs", async () => {
  const browser = new MockBrowser([
    { id: 21, url: "https://example.com/", active: true }
  ]);
  const adapter = new FirefoxAdapterCore(browser);

  await adapter.initialize();

  assert.equal(browser.tabsById.get(21).url, "https://example.com/");
  assert.equal(
    browser.calls.filter(call => call[0] === "tabs.update").length,
    0
  );
});

test("exact active temporary-chat bootstrap tab is adopted instead of duplicated", async () => {
  const browser = new MockBrowser([
    { id: 2, url: WORKER_START_URL, active: true }
  ]);
  const adapter = new FirefoxAdapterCore(browser, {
    idFactory: () => "binding-bootstrap"
  });

  const result = await adapter.handleCommand(command(
    "req-bootstrap",
    "ENSURE_WORKER_SURFACE",
    { worker_slot_id: "slot-bootstrap", session_generation: 1 }
  ));

  assert.equal(result.outcome, "APPLIED");
  assert.equal(result.binding_ref, "binding-bootstrap");
  assert.equal(browser.tabsById.size, 1);
  assert.equal(
    browser.calls.filter(call => call[0] === "tabs.create").length,
    0
  );
  assert.deepEqual(
    browser.tabValues.get(2).get(MANAGED_TAB_VALUE),
    {
      managed: true,
      binding_ref: "binding-bootstrap",
      binding_generation: 1,
      worker_slot_id: "slot-bootstrap",
      session_generation: 1
    }
  );
});

test("worker start URL is the requested temporary-chat route", () => {
  assert.equal(
    WORKER_START_URL,
    "https://chatgpt.com/?temporary-chat=true"
  );
});

test("binding metadata contains only non-authoritative local identity", async () => {
  const browser = new MockBrowser();
  const adapter = new FirefoxAdapterCore(browser, {
    idFactory: () => "binding-safe"
  });

  await adapter.handleCommand(command(
    "req-2",
    "CREATE_WORKER_BINDING",
    { worker_slot_id: "slot-2", session_generation: 9 }
  ));

  const stored = browser.calls
    .filter(call => call[0] === "sessions.setTabValue")
    .at(-1)[3];

  assert.deepEqual(Object.keys(stored).sort(), [
    "binding_generation",
    "binding_ref",
    "managed",
    "session_generation",
    "worker_slot_id"
  ]);
  const serialized = JSON.stringify(stored).toLowerCase();
  for (const forbidden of [
    "packet", "clipboard", "url", "cookie", "token", "credential", "password"
  ]) {
    assert.equal(serialized.includes(forbidden), false);
  }
});

test("duplicate same request and idempotency key does not duplicate create effect", async () => {
  const browser = new MockBrowser();
  let counter = 0;
  const adapter = new FirefoxAdapterCore(browser, {
    idFactory: () => "binding-" + (++counter)
  });

  const firstCommand = command(
    "req-3",
    "CREATE_WORKER_BINDING",
    { worker_slot_id: "slot-3", session_generation: 1 },
    "idem-same"
  );

  const first = await adapter.handleCommand(firstCommand);
  const second = await adapter.handleCommand(structuredClone(firstCommand));

  assert.deepEqual(second, first);
  assert.equal(
    browser.calls.filter(call => call[0] === "tabs.create").length,
    1);
});

test("same request with different idempotency key fails closed", async () => {
  const browser = new MockBrowser();
  const adapter = new FirefoxAdapterCore(browser, {
    idFactory: () => "binding-conflict"
  });

  await adapter.handleCommand(command(
    "req-4",
    "CREATE_WORKER_BINDING",
    { worker_slot_id: "slot-4", session_generation: 1 },
    "idem-a"
  ));

  const conflict = await adapter.handleCommand(command(
    "req-4",
    "CREATE_WORKER_BINDING",
    { worker_slot_id: "slot-4", session_generation: 1 },
    "idem-b"
  ));

  assert.equal(conflict.outcome, "REJECTED");
  assert.equal(conflict.normalized_error, "IDEMPOTENCY_CONFLICT");
  assert.equal(
    browser.calls.filter(call => call[0] === "tabs.create").length,
    1);
});

test("inventory returns only managed tabs and only origin enum", async () => {
  const browser = new MockBrowser([
    { id: 5, url: "https://chatgpt.com/c/managed", active: false },
    { id: 6, url: "https://example.com/unmanaged", active: true }
  ]);
  browser.seedManaged(5, managedMetadata());
  const adapter = new FirefoxAdapterCore(browser);

  const result = await adapter.handleCommand(command(
    "req-5",
    "INVENTORY_MANAGED_BINDINGS"
  ));

  assert.equal(result.outcome, "APPLIED");
  assert.equal(result.inventory.length, 1);
  assert.equal(result.inventory[0].binding_ref, "binding-1");
  assert.equal(result.inventory[0].origin_classification, "CHATGPT_ORIGIN");
  const serialized = JSON.stringify(result);
  assert.equal(serialized.includes("https://"), false);
  assert.equal(serialized.includes("/c/managed"), false);
});

test("active managed tab is not discarded", async () => {
  const browser = new MockBrowser([
    { id: 7, url: "https://chatgpt.com/", active: true }
  ]);
  browser.seedManaged(7, managedMetadata("binding-active"));
  const adapter = new FirefoxAdapterCore(browser);

  const result = await adapter.handleCommand(command(
    "req-6",
    "DISCARD_WORKER_BINDING",
    { worker_slot_id: "slot-1", session_generation: 7 }
  ));

  assert.equal(result.outcome, "NOT_APPLIED");
  assert.equal(result.normalized_error, "ACTIVE_TAB_NOT_DISCARDABLE");
  assert.equal(
    browser.calls.filter(call => call[0] === "tabs.discard").length,
    0);
});

test("activating managed worker also focuses its Firefox window", async () => {
  const browser = new MockBrowser([
    { id: 8, url: "https://chatgpt.com/", active: false, windowId: 42 }
  ]);
  browser.seedManaged(8, managedMetadata("binding-focus"));
  const adapter = new FirefoxAdapterCore(browser);

  const result = await adapter.handleCommand(command(
    "req-focus",
    "ACTIVATE_WORKER_BINDING",
    { worker_slot_id: "slot-1", session_generation: 7 }
  ));

  assert.equal(result.outcome, "APPLIED");
  assert.deepEqual(
    browser.calls.find(call => call[0] === "tabs.update"),
    ["tabs.update", 8, { active: true }]
  );
  assert.deepEqual(
    browser.calls.find(call => call[0] === "windows.update"),
    ["windows.update", 42, { focused: true }]
  );
});

test("worker activation fails closed when Firefox window focus fails", async () => {
  const browser = new MockBrowser([
    { id: 18, url: "https://chatgpt.com/", active: false, windowId: 77 }
  ]);
  browser.seedManaged(18, managedMetadata("binding-focus-fail"));
  browser.windows.update = async () => { throw new Error("focus denied"); };
  const adapter = new FirefoxAdapterCore(browser);

  const result = await adapter.handleCommand(command(
    "req-focus-fail",
    "ACTIVATE_WORKER_BINDING",
    { worker_slot_id: "slot-1", session_generation: 7 }
  ));

  assert.equal(result.outcome, "NOT_APPLIED");
  assert.equal(result.normalized_error, "WINDOW_FOCUS_FAILED");
});

test("binding generation mismatch rejects lifecycle mutation", async () => {
  const browser = new MockBrowser([
    { id: 8, url: "https://chatgpt.com/", active: false }
  ]);
  browser.seedManaged(8, managedMetadata("binding-generation"));
  const adapter = new FirefoxAdapterCore(browser);

  const result = await adapter.handleCommand(command(
    "req-7",
    "ACTIVATE_WORKER_BINDING",
    {
      worker_slot_id: "slot-1",
      session_generation: 7,
      expected_binding_generation: 99
    }
  ));

  assert.equal(result.outcome, "REJECTED");
  assert.equal(result.normalized_error, "BINDING_GENERATION_MISMATCH");
  assert.equal(
    browser.calls.filter(call => call[0] === "tabs.update").length,
    0);
});

test("tab URL changes emit only reduced origin classification", async () => {
  const browser = new MockBrowser([
    { id: 9, url: "https://chatgpt.com/", active: false }
  ]);
  browser.seedManaged(9, managedMetadata("binding-event"));
  const events = [];
  const adapter = new FirefoxAdapterCore(browser, {
    emit: event => events.push(structuredClone(event))
  });

  await adapter.handleTabUpdated(
    9,
    { url: "https://login.example.invalid/private?secret=x" },
    { id: 9, url: "https://login.example.invalid/private?secret=x", active: false }
  );

  assert.equal(events.length, 1);
  assert.equal(events[0].event_type, "ORIGIN_CLASS_CHANGED");
  assert.equal(events[0].origin_classification, "OFF_CHATGPT_ORIGIN");
  const serialized = JSON.stringify(events[0]);
  assert.equal(serialized.includes("login.example.invalid"), false);
  assert.equal(serialized.includes("secret=x"), false);
});

test("close operation can only close a managed matching binding", async () => {
  const browser = new MockBrowser([
    { id: 10, url: "https://chatgpt.com/c/unmanaged", active: false },
    { id: 11, url: "https://chatgpt.com/c/managed", active: false }
  ]);
  browser.seedManaged(11, managedMetadata("binding-close"));
  const adapter = new FirefoxAdapterCore(browser);

  const missing = await adapter.handleCommand(command(
    "req-8",
    "CLOSE_WORKER_BINDING",
    { worker_slot_id: "different", session_generation: 7 }
  ));
  assert.equal(missing.outcome, "REJECTED");
  assert.equal(browser.tabsById.has(10), true);
  assert.equal(browser.tabsById.has(11), true);

  const closed = await adapter.handleCommand(command(
    "req-9",
    "CLOSE_WORKER_BINDING",
    { worker_slot_id: "slot-1", session_generation: 7 }
  ));
  assert.equal(closed.outcome, "APPLIED");
  assert.equal(browser.tabsById.has(10), true);
  assert.equal(browser.tabsById.has(11), false);
});


test("ensure existing binding does not activate before explicit focus", async () => {
  const browser = new MockBrowser([
    { id: 12, url: "https://chatgpt.com/", active: false }
  ]);
  browser.seedManaged(12, managedMetadata("binding-ensure"));
  const adapter = new FirefoxAdapterCore(browser);

  const result = await adapter.handleCommand(command(
    "req-10",
    "ENSURE_WORKER_SURFACE",
    { worker_slot_id: "slot-1", session_generation: 7 }
  ));

  assert.equal(result.outcome, "APPLIED");
  assert.equal(
    browser.calls.filter(call => call[0] === "tabs.update").length,
    0);
});

test("ambiguous managed bindings fail closed", async () => {
  const browser = new MockBrowser([
    { id: 13, url: "https://chatgpt.com/", active: false },
    { id: 14, url: "https://chatgpt.com/", active: false }
  ]);
  browser.seedManaged(13, managedMetadata("binding-a"));
  browser.seedManaged(14, managedMetadata("binding-b"));
  const adapter = new FirefoxAdapterCore(browser);

  const result = await adapter.handleCommand(command(
    "req-11",
    "ENSURE_WORKER_SURFACE",
    { worker_slot_id: "slot-1", session_generation: 7 }
  ));

  assert.equal(result.outcome, "REJECTED");
  assert.equal(result.normalized_error, "BINDING_AMBIGUOUS");
  assert.equal(
    browser.calls.filter(call => call[0] === "tabs.update").length,
    0);
  assert.equal(
    browser.calls.filter(call => call[0] === "tabs.create").length,
    0);
});

test("simulator-only constructor override can target local fake worker", async () => {
  const browser = new MockBrowser();
  const adapter = new FirefoxAdapterCore(browser, {
    idFactory: () => "binding-sim",
    workerStartUrl: "moz-extension://simulator/fake-worker.html"
  });

  const result = await adapter.handleCommand(command(
    "req-12",
    "CREATE_WORKER_BINDING",
    { worker_slot_id: "slot-sim", session_generation: 1 }
  ));

  assert.equal(result.outcome, "APPLIED");
  const createCall = browser.calls.find(call => call[0] === "tabs.create");
  assert.equal(
    createCall[1].url,
    "moz-extension://simulator/fake-worker.html");
});


test("discard re-reads tab because Firefox discard resolves without a Tab", async () => {
  const browser = new MockBrowser([
    { id: 15, url: "https://chatgpt.com/", active: false }
  ]);
  browser.seedManaged(15, managedMetadata("binding-discard"));

  browser.tabs.discard = async tabId => {
    browser.calls.push(["tabs.discard", tabId]);
    const tab = browser.requireTab(tabId);
    tab.discarded = true;
    return undefined;
  };

  const adapter = new FirefoxAdapterCore(browser);
  const result = await adapter.handleCommand(command(
    "req-13",
    "DISCARD_WORKER_BINDING",
    { worker_slot_id: "slot-1", session_generation: 7 }
  ));

  assert.equal(result.outcome, "APPLIED");
  assert.equal(result.discarded, true);
  assert.equal(
    browser.calls.filter(call => call[0] === "tabs.discard").length,
    1);
});
