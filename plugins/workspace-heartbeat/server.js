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
import { HeartbeatLeaseError, HeartbeatStore } from "./src/store.js";

const PANEL_URI = "ui://workspace-heartbeat/panel-v8.html";
const LIVE_URI = "ui://workspace-heartbeat/live-v1.html";
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
  message: z.string(),
  state: z.enum(["working", "waiting", "blocked", "done"]),
  sequence: z.number().int().nonnegative(),
  updated_at: z.string(),
});

const heartbeatLeaseErrorSchema = z.object({
  code: z.string(),
  task_id: z.string().nullable(),
  sequence: z.number().int().nonnegative(),
  expected_sequence: z.number().int().nonnegative().optional(),
});

const heartbeatLeaseSchema = z.object({
  task_id: z.string(),
  sequence: z.number().int().nonnegative(),
  status: z.enum(["handoff_ready", "owned", "recovered"]),
});

const heartbeatUpdateOutputSchema = {
  heartbeat: heartbeatSchema.optional(),
  error: heartbeatLeaseErrorSchema.optional(),
};

const heartbeatWriterOutputSchema = {
  lease: heartbeatLeaseSchema.optional(),
  error: heartbeatLeaseErrorSchema.optional(),
};

const heartbeatLiveOutputSchema = {
  heartbeat: heartbeatSchema.nullable(),
  recent: z.array(heartbeatSchema).max(3),
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

function leaseErrorResult(error) {
  if (!(error instanceof HeartbeatLeaseError)) {
    throw error;
  }
  const publicError = error.toPublic();
  return {
    isError: true,
    structuredContent: { error: publicError },
    content: [
      {
        type: "text",
        text: `Heartbeat writer operation rejected: ${publicError.code}. ${error.message}`,
      },
    ],
  };
}

function createHeartbeatServer() {
  const server = new McpServer(
    {
      name: "workspace-heartbeat",
      version: "0.4.3",
    },
    {
      instructions:
        "For substantial work, call heartbeat_update with natural concise progress about real findings, decisions, and next actions—not tool-operation telemetry. The first hidden ChatGPT session that successfully writes a task_id claims that task's writer lease; another session's heartbeat_update for the same task fails closed and does not mutate task state. Normal chat handoff is explicit: the current writer calls heartbeat_writer with action=handoff and the exact current sequence, then the receiving session calls heartbeat_writer with action=claim and the same sequence before writing. Recovery takeover is allowed only through heartbeat_writer action=recover with the exact current sequence; stale evidence is rejected. heartbeat_open, heartbeat_snapshot, and heartbeat_get are read-only and never claim or transfer writer ownership. Call heartbeat_update on meaningful state changes and before the fourth non-heartbeat tool operation. After the first update, call heartbeat_open(task_id) once early for the owning task, then continue working and writing data-only updates. The mounted live card calls its own app-only heartbeat_snapshot tool via the MCP Apps bridge, updating the rolling last-three history without further model renders. Do not reopen a healthy card merely to refresh it. If the card is demonstrably absent, unmounted, failed, or lost after a chat/plugin reload, one recovery heartbeat_open(task_id) is allowed to restore the live surface. Do not call heartbeat_render (removed). Initial mounting is controlled by the host; the app controls refresh only after it mounts. Use heartbeat_get(task_id) only for explicitly requested full history or necessary recovery.",
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
          _meta: {
            ui: {
              prefersBorder: false,
            },
          },
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
          _meta: {
            ui: {
              prefersBorder: false,
            },
          },
        },
      ],
    }),
  );

  registerAppTool(
    server,
    "heartbeat_update",
    {
      title: "Update operator heartbeat",
      description:
        "Record natural, conversational operator progress focused on what materially changed, what you learned, or what you are doing next. The first session to write a task claims its writer lease. A different session writing the same leased task is rejected without mutating heartbeat state. Prefer findings and decisions over tool mechanics, avoid generic heartbeat numbering and boilerplate. Keep this call data-only. After the first update of a substantial turn, call heartbeat_open once early for this task; the mounted app handles its own later refreshes.",
      inputSchema: {
        task_id: z.string().min(1).max(160),
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
    async ({ task_id, message, state }, { _meta } = {}) => {
      const sessionId = sessionIdFromMeta(_meta);
      try {
        const heartbeat = store.update({
          sessionId,
          taskId: task_id.trim(),
          message: message.trim(),
          state,
        });
        return {
          structuredContent: { heartbeat },
          content: [
            {
              type: "text",
              text: `${heartbeat.message}\n\n${heartbeat.task_id} · update ${heartbeat.sequence} · ${heartbeat.state}`,
            },
          ],
        };
      } catch (error) {
        return leaseErrorResult(error);
      }
    },
  );

  registerAppTool(
    server,
    "heartbeat_writer",
    {
      title: "Control heartbeat writer lease",
      description:
        "Explicit writer-lease control for chat handoff and recovery. action=handoff may be called only by the current writer and releases the task at expected_sequence; action=claim explicitly binds a released handoff to the calling session; action=recover is the dedicated fail-closed takeover path and succeeds only when expected_sequence exactly matches the current task sequence. These operations do not append heartbeat history or increment sequence. Raw hidden session identifiers are never returned.",
      inputSchema: {
        task_id: z.string().min(1).max(160),
        action: z.enum(["handoff", "claim", "recover"]),
        expected_sequence: z.number().int().nonnegative(),
      },
      outputSchema: heartbeatWriterOutputSchema,
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: false,
      },
      _meta: {
        "openai/toolInvocation/invoking": "Updating heartbeat writer lease…",
        "openai/toolInvocation/invoked": "Heartbeat writer lease updated",
      },
    },
    async ({ task_id, action, expected_sequence }, { _meta } = {}) => {
      const sessionId = sessionIdFromMeta(_meta);
      const args = {
        sessionId,
        taskId: task_id.trim(),
        expectedSequence: expected_sequence,
      };
      try {
        const lease =
          action === "handoff"
            ? store.handoff(args)
            : action === "claim"
              ? store.claim(args)
              : store.recover(args);
        return {
          structuredContent: { lease },
          content: [
            {
              type: "text",
              text: `Heartbeat writer ${action} accepted for ${lease.task_id} at sequence ${lease.sequence}.`,
            },
          ],
        };
      } catch (error) {
        return leaseErrorResult(error);
      }
    },
  );

  registerAppTool(
    server,
    "heartbeat_open",
    {
      title: "Open live task heartbeat",
      description:
        "Mount one live, task-scoped heartbeat card early in a substantial turn, after the first heartbeat_update. This is read-only and never claims or transfers writer ownership. Do not call it again merely to refresh a healthy card: the mounted card independently fetches fresh state through heartbeat_snapshot. If the card is demonstrably absent, unmounted, failed, or lost after a chat/plugin reload, one recovery call is allowed to restore the surface. It shows only the latest three updates for this task; full history is available separately through heartbeat_get. Host-controlled iframe mounting may be delayed.",
      inputSchema: {
        task_id: z.string().min(1).max(160),
      },
      outputSchema: heartbeatLiveOutputSchema,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: true,
      },
      _meta: {
        ui: {
          resourceUri: LIVE_URI,
          visibility: ["model", "app"],
        },
        "openai/toolInvocation/invoking": "Opening live progress…",
        "openai/toolInvocation/invoked": "Live progress opened",
      },
    },
    async ({ task_id }, { _meta } = {}) => {
      const scoped = task_id.trim();
      const snapshot = store.getSnapshot({
        sessionId: sessionIdFromMeta(_meta),
        taskId: scoped,
      });
      const recent = snapshot.history.slice(-3);
      return {
        structuredContent: { task_id: scoped, heartbeat: snapshot.heartbeat, recent },
        content: [
          {
            type: "text",
            text: "Live heartbeat card opened for " + scoped + ". It will fetch subsequent task-local updates itself.",
          },
        ],
      };
    },
  );

  registerAppTool(
    server,
    "heartbeat_snapshot",
    {
      title: "Read live task heartbeat snapshot",
      description:
        "App-only read-only helper: return the latest three updates for the explicit task_id. The mounted heartbeat card calls this through tools/call. This tool never claims or transfers writer ownership and must not mount another UI resource.",
      inputSchema: {
        task_id: z.string().min(1).max(160),
      },
      outputSchema: heartbeatLiveOutputSchema,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: true,
      },
      _meta: {
        ui: {
          visibility: ["app"],
        },
        "openai/widgetAccessible": true,
      },
    },
    async ({ task_id }, { _meta } = {}) => {
      const scoped = task_id.trim();
      const snapshot = store.getSnapshot({
        sessionId: sessionIdFromMeta(_meta),
        taskId: scoped,
      });
      const recent = snapshot.history.slice(-3);
      return {
        structuredContent: { task_id: scoped, heartbeat: snapshot.heartbeat, recent },
        content: [
          {
            type: "text",
            text: "Task-local heartbeat snapshot for " + scoped + ".",
          },
        ],
      };
    },
  );

  registerAppTool(
    server,
    "heartbeat_get",
    {
      title: "Read operator heartbeat",
      description:
        "Full task-history inspection only. This is read-only and never claims or transfers writer ownership. Use this when the user explicitly asks to open/read heartbeat history or when recovery genuinely requires historical state. Pass task_id whenever it is known. Routine progress delivery uses heartbeat_update and a single early heartbeat_open, whose app refreshes itself through heartbeat_snapshot.",
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
        return resultFor(
          snapshot,
          "No heartbeat has been recorded for this task yet.",
        );
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
