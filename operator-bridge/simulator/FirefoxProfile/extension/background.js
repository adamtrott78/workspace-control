"use strict";

const {
  PROTOCOL_VERSION,
  NATIVE_HOST_NAME,
  MANAGED_TAB_VALUE,
  FirefoxAdapterCore
} = globalThis.WorkspaceFirefoxAdapterCore;

const ADAPTER_VERSION = "0.1.0-sim";
const ADAPTER_INSTANCE_ID = crypto.randomUUID();
const RECONNECT_DELAY_MS = 1000;

let port = null;
let handshakeComplete = false;
let reconnectTimer = null;

function monotonicMilliseconds() {
  return performance.now();
}

function envelope(messageType, fields = {}) {
  return {
    protocol_version: PROTOCOL_VERSION,
    message_type: messageType,
    message_id: crypto.randomUUID(),
    request_id: fields.request_id ?? null,
    correlation_id: fields.correlation_id ?? null,
    sent_at_monotonic_ms: monotonicMilliseconds(),
    helper_instance_id: null,
    adapter_instance_id: ADAPTER_INSTANCE_ID,
    payload: fields.payload ?? null
  };
}

function post(message) {
  if (!port) {
    return false;
  }
  port.postMessage(message);
  return true;
}

function emitBrowserEvent(payload) {
  if (handshakeComplete) {
    post(envelope("BROWSER_EVENT", { payload }));
  }
}

async function seedSimulatorTabs(fakeWorkerUrl) {
  await browser.tabs.create({
    url: fakeWorkerUrl,
    active: false
  });

  for (let index = 1; index <= 2; index++) {
    const tab = await browser.tabs.create({
      url: fakeWorkerUrl,
      active: false
    });
    await browser.sessions.setTabValue(
      tab.id,
      MANAGED_TAB_VALUE,
      {
        managed: true,
        binding_ref: "sim-ambiguous-" + index,
        binding_generation: 1,
        worker_slot_id: "ambiguous-slot",
        session_generation: 0
      });
  }
}

async function main() {
  const fakeWorkerUrl = browser.runtime.getURL("fake-worker.html");
  await seedSimulatorTabs(fakeWorkerUrl);

  const adapter = new FirefoxAdapterCore(browser, {
    emit: emitBrowserEvent,
    workerStartUrl: fakeWorkerUrl
  });

  browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    void adapter.handleTabUpdated(tabId, changeInfo, tab);
  });
  browser.tabs.onActivated.addListener(activeInfo => {
    void adapter.handleTabActivated(activeInfo);
  });
  browser.tabs.onRemoved.addListener(tabId => {
    adapter.handleTabRemoved(tabId);
  });

  async function handleNativeMessage(message) {
    if (
      message &&
      message.message_type === "HELLO_ACK" &&
      message.protocol_version === PROTOCOL_VERSION &&
      message.payload &&
      message.payload.accepted_protocol_version === PROTOCOL_VERSION
    ) {
      handshakeComplete = true;
      await adapter.initialize();
      emitBrowserEvent({
        event_type: "ADAPTER_READY",
        worker_slot_id: null,
        session_generation: null,
        binding_ref: null,
        binding_generation: null,
        origin_classification: null
      });
      return;
    }

    if (!handshakeComplete) {
      return;
    }

    if (message && message.message_type === "BROWSER_COMMAND") {
      const result = await adapter.handleCommand(message);
      if (!result) {
        return;
      }
      post(envelope("BROWSER_RESULT", {
        request_id: message.request_id,
        correlation_id: message.correlation_id,
        payload: result
      }));
    }
  }

  function connectNative() {
    if (reconnectTimer !== null) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }

    handshakeComplete = false;
    port = browser.runtime.connectNative(NATIVE_HOST_NAME);
    port.onMessage.addListener(message => {
      void handleNativeMessage(message);
    });
    port.onDisconnect.addListener(() => {
      port = null;
      handshakeComplete = false;
      reconnectTimer = setTimeout(connectNative, RECONNECT_DELAY_MS);
    });

    post(envelope("HELLO", {
      payload: {
        adapter_kind: "FIREFOX_EXTENSION",
        adapter_version: ADAPTER_VERSION,
        supported_protocol_versions: [PROTOCOL_VERSION],
        capabilities: {
          discard: true,
          persistent_binding_metadata: true,
          origin_classification: true,
          profile_isolation: true
        }
      }
    }));
  }

  connectNative();
}

void main();
