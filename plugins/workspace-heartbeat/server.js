import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import {
  registerAppResource,
  registerAppTool,
  RESOURCE_MIME_TYPE,
} from "@modelcontextprotocol/ext-apps/server";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";
import { HeartbeatStore } from "./src/store.js";

const PANEL_URI = "ui://workspace-heartbeat/panel-v8.html";
const LIVE_URI = "ui://workspace-heartbeat/live-v2.html";
const panelHtml = readFileSync(
  new URL("./public/heartbeat-panel.html", import.meta.url),
  "utf8",
);
const liveHtml = readFileSync(
  new URL("./public/heartbeat-live-card.html", import.meta.url),
  "utf8",
);
const store = new HeartbeatStore({ historyLimit: 50 });

const heartbeatSchema = z.object({
  task_id: z.string(),
  turn_id: z.string(),
  message: z.string(),
  state: z.enum(["working", "waiting", "blocked", "done"]),
  sequence: z.number().int().nonnegative(),
  updated_at: z.string(),
});

const heartbeatUpdateOutputSchema = {
  heartbeat: heartbeatSchema,
};

const heartbeatTurnOutputSchema = {
  task_id: z.string(),
  turn_id: z.string(),
  heartbeat: heartbeatSchema.nullable(),
  recent: z.array(heartbeatSchema).max(3),
  active: z.boolean(),
  superseded: z.boolean(),
  completed: z.boolean(),
};

const heartbeatOutputSchema = {
  heartbeat: heartbeatSchema.nullable(),
  history: z.array(heartbeatSchema),
  timeline: z.array(heartbeatSchema),
};

function sessionIdFromMeta(meta) {
  return meta?.["openai/session"] ?? "dev-session";
}

function resultFor(snapshot, text) {
  return {
    structuredContent: snapshot,
    content: [{ type: "text", text }],
  };
}

function createHeartbeatServer() {
  const server = new McpServer(
    {
      name: "workspace-heartbeat",
      version: "0.4.4",
    },
    {
      instructions:
        "For every substantial assistant response, FIRST call heartbeat_begin_turn(task_id, message, state). That single operation supersedes the prior heartbeat turn for this conversation/task, creates a new opaque turn_id, writes the first natural progress update, and mounts the current rolling-three card. Carry the returned turn_id explicitly on every later heartbeat_update for that assistant response. Call heartbeat_update on meaningful findings/decisions and before the fourth non-heartbeat tool operation. Never call heartbeat_snapshot directly; it is app-only. heartbeat_get is explicit task-history/debugging only. A stale/missing turn_id must fail closed. If this conversation does not expose heartbeat_begin_turn or heartbeat_update does not accept turn_id, its plugin contract is stale: do not use Heartbeat here; refresh the plugin and start a new conversation.",
    },
  );

  registerAppResource(
    server,
    "workspace-heartbeat-panel",
    PANEL_URI,
    {},
    async () => ({
      contents: [
        {
          uri: PANEL_URI,
          mimeType: RESOURCE_MIME_TYPE,
          text: panelHtml,
          _meta: { ui: { prefersBorder: false } },
        },
      ],
    }),
  );

  registerAppResource(
    server,
    "workspace-heartbeat-live",
    LIVE_URI,
    {},
    async () => ({
      contents: [
        {
          uri: LIVE_URI,
          mimeType: RESOURCE_MIME_TYPE,
          text: liveHtml,
          _meta: { ui: { prefersBorder: false } },
        },
      ],
    }),
  );

  registerAppTool(
    server,
    "heartbeat_begin_turn",
    {
      title: "Begin live heartbeat turn",
      description:
        "FIRST heartbeat operation for every substantial assistant response. Atomically supersedes the previous heartbeat turn for this task in the same ChatGPT conversation, creates a fresh server-generated turn_id, records this first natural progress message, and mounts one live rolling-three card for the new turn. Carry the returned turn_id on every heartbeat_update in this response.",
      inputSchema: {
        task_id: z.string().min(1).max(160),
        message: z.string().min(1).max(4000),
        state: z.enum(["working", "waiting", "blocked", "done"]).default("working"),
      },
      outputSchema: heartbeatTurnOutputSchema,
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: false,
      },
      _meta: {
        ui: {
          resourceUri: LIVE_URI,
          visibility: ["model", "app"],
        },
        "openai/toolInvocation/invoking": "Starting live progress…",
        "openai/toolInvocation/invoked": "Live progress started",
      },
    },
    async ({ task_id, message, state }, { _meta } = {}) => {
      const snapshot = store.beginTurn({
        sessionId: sessionIdFromMeta(_meta),
        taskId: task_id.trim(),
        message: message.trim(),
        state,
      });
      return {
        structuredContent: snapshot,
        content: [
          {
            type: "text",
            text:
              snapshot.heartbeat.message +
              "\n\n" +
              snapshot.task_id +
              " · turn " +
              snapshot.turn_id +
              " · update " +
              snapshot.heartbeat.sequence +
              " · " +
              snapshot.heartbeat.state,
          },
        ],
      };
    },
  );

  registerAppTool(
    server,
    "heartbeat_update",
    {
      title: "Update current heartbeat turn",
      description:
        "Record a later natural progress update for the assistant response that was started by heartbeat_begin_turn. task_id and the exact returned turn_id are both required. Stale, superseded, missing, wrong-task, or cross-conversation turn IDs fail closed instead of writing history.",
      inputSchema: {
        task_id: z.string().min(1).max(160),
        turn_id: z.string().min(1).max(160),
        message: z.string().min(1).max(4000),
        state: z.enum(["working", "waiting", "blocked", "done"]).default("working"),
      },
      outputSchema: heartbeatUpdateOutputSchema,
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: false,
      },
      _meta: {
        "openai/toolInvocation/invoking": "Updating progress…",
        "openai/toolInvocation/invoked": "Progress updated",
      },
    },
    async ({ task_id, turn_id, message, state }, { _meta } = {}) => {
      const heartbeat = store.updateTurn({
        sessionId: sessionIdFromMeta(_meta),
        taskId: task_id.trim(),
        turnId: turn_id.trim(),
        message: message.trim(),
        state,
      });
      return {
        structuredContent: { heartbeat },
        content: [
          {
            type: "text",
            text:
              heartbeat.message +
              "\n\n" +
              heartbeat.task_id +
              " · turn " +
              heartbeat.turn_id +
              " · update " +
              heartbeat.sequence +
              " · " +
              heartbeat.state,
          },
        ],
      };
    },
  );

  registerAppTool(
    server,
    "heartbeat_snapshot",
    {
      title: "Read one heartbeat turn snapshot",
      description:
        "App-only read-only helper for the live card. Returns only the rolling last three updates for the explicit task_id + turn_id and whether that turn is still active, superseded, or completed.",
      inputSchema: {
        task_id: z.string().min(1).max(160),
        turn_id: z.string().min(1).max(160),
      },
      outputSchema: heartbeatTurnOutputSchema,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: true,
      },
      _meta: {
        ui: { visibility: ["app"] },
        "openai/widgetAccessible": true,
      },
    },
    async ({ task_id, turn_id }) => {
      const snapshot = store.getTurnSnapshot({
        taskId: task_id.trim(),
        turnId: turn_id.trim(),
      });
      if (!snapshot) {
        throw new Error(
          "HEARTBEAT_TURN_NOT_FOUND: This live card refers to an unknown heartbeat turn.",
        );
      }
      return {
        structuredContent: snapshot,
        content: [],
      };
    },
  );

  registerAppTool(
    server,
    "heartbeat_get",
    {
      title: "Read heartbeat task history",
      description:
        "Explicit task-history/sidebar inspection only. Returns bounded task-level history across heartbeat turns. It is not the routine live-progress path.",
      inputSchema: {
        task_id: z.string().min(1).max(160).optional(),
      },
      outputSchema: heartbeatOutputSchema,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: true,
      },
      _meta: {
        ui: {
          resourceUri: PANEL_URI,
          visibility: ["model", "app"],
        },
        "openai/ui": {
          entrypoints: [{ type: "thread" }],
        },
        "openai/toolInvocation/invoking": "Reading progress…",
        "openai/toolInvocation/invoked": "Progress ready",
      },
    },
    async ({ task_id }, { _meta } = {}) => {
      const snapshot = store.getSnapshot({
        sessionId: sessionIdFromMeta(_meta),
        taskId: task_id?.trim(),
      });
      if (!snapshot.heartbeat) {
        return resultFor(snapshot, "No heartbeat has been recorded for this task yet.");
      }
      return resultFor(
        snapshot,
        `Latest heartbeat for ${snapshot.heartbeat.task_id}: ${snapshot.heartbeat.message}`,
      );
    },
  );

  return server;
}

const port = Number(process.env.PORT ?? 8787);
const MCP_PATH = "/mcp";

const httpServer = createServer(async (req, res) => {
  if (!req.url) {
    res.writeHead(400).end("Missing URL");
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host ?? "localhost"}`);

  if (req.method === "OPTIONS" && url.pathname === MCP_PATH) {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, GET, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "content-type, mcp-session-id",
      "Access-Control-Expose-Headers": "Mcp-Session-Id",
    });
    res.end();
    return;
  }

  if (req.method === "GET" && url.pathname === "/") {
    res.writeHead(200, { "content-type": "text/plain; charset=utf-8" });
    res.end("workspace-heartbeat MCP server");
    return;
  }

  const methods = new Set(["POST", "GET", "DELETE"]);
  if (url.pathname === MCP_PATH && req.method && methods.has(req.method)) {
    const startedAt = Date.now();
    res.on("finish", () => {
      console.log(
        `[mcp] ${req.method} ${url.pathname} -> ${res.statusCode} (${Date.now() - startedAt} ms)`,
      );
    });

    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Expose-Headers", "Mcp-Session-Id");

    const server = createHeartbeatServer();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
      enableJsonResponse: true,
    });

    res.on("close", () => {
      transport.close();
      server.close();
    });

    try {
      await server.connect(transport);
      await transport.handleRequest(req, res);
    } catch (error) {
      console.error("MCP request failed:", error);
      if (!res.headersSent) {
        res.writeHead(500).end("Internal server error");
      }
    }
    return;
  }

  res.writeHead(404).end("Not Found");
});

httpServer.listen(port, () => {
  console.log(`workspace-heartbeat listening on http://localhost:${port}${MCP_PATH}`);
});
