# Workspace Heartbeat plugin

MVP MCP plugin for operator-visible progress during long-running workspace-control tasks.

## What it does

- `heartbeat_update(task_id, message, state)` stores one rolling natural-language heartbeat for the current ChatGPT conversation.
- `heartbeat_get(task_id?)` returns the current heartbeat.
- A ChatGPT thread/conversation-panel entrypoint polls `heartbeat_get` and updates one persistent box in place.
- State is isolated by ChatGPT's anonymized `_meta["openai/session"]` conversation identifier and task ID.
- The server assigns monotonically increasing per-task sequence numbers.

The heartbeat text is intentionally normal prose. Structured fields exist only for routing/UI state.

## MVP limits

- in-memory storage only; server restart clears heartbeat state;
- no authentication yet;
- no durable history;
- no public hosting configuration;
- panel polling uses the ChatGPT `window.openai.callTool` compatibility bridge;
- the tool contract helps enforce the three-tool heartbeat lease, but cannot physically intercept unrelated tools outside this MCP server.

## Run locally

```bash
cd plugins/workspace-heartbeat
npm install
npm test
npm start
```

The MCP endpoint is:

```text
http://localhost:8787/mcp
```

Inspect it with:

```bash
npx @modelcontextprotocol/inspector@latest
```

## Connect to ChatGPT for development

ChatGPT needs an HTTPS-reachable MCP endpoint. Use a supported development tunnel or deploy the server, then add the resulting `https://.../mcp` URL in ChatGPT Developer mode.

The `heartbeat_get` tool advertises the panel as a thread entrypoint. Open the plugin beside the conversation, then keep it open while the model calls `heartbeat_update`.

## Expected model behavior

For substantial long-running work:

1. write natural-language progress with `heartbeat_update`;
2. perform at most three subsequent non-heartbeat tool operations;
3. update the heartbeat again before tool operation four;
4. update immediately when diagnosis, scope, milestone, wait state, recovery point, or closure decision changes.

Do not replace normal reasoning with rigid status-card prose. The panel is the structured presentation layer.
