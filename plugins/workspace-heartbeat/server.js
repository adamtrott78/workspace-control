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
const SUMMARY_URI = "ui://workspace-heartbeat/summary-v1.html";
const panelHtml = readFileSync(
  new URL("./public/heartbeat-panel.html", import.meta.url),
  "utf8",
);
const summaryHtml = readFileSync(
  new URL("./public/heartbeat-summary-card.html", import.meta.url),
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

const heartbeatUpdateOutputSchema = {
  heartbeat: heartbeatSchema,
};

const heartbeatSummaryOutputSchema = {
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

function createHeartbeatServer() {
  const server = new McpServer(
    {
      name: "workspace-heartbeat",
      version: "0.4.2",
    },
    {
      instructions:
        "For substantial long-running work, keep the operator informed through heartbeat_update. Heartbeat prose should sound like your normal conversational progress commentary: one or two natural sentences about what materially changed, what you learned, or what you are doing next. Prefer findings and decisions over narration of tool mechanics. Do not write status-report boilerplate, sequence numbers, task IDs, stage labels, or phrases like 'tool call completed' unless genuinely useful. Call heartbeat_update on meaningful state changes and before a fourth non-heartbeat tool operation occurs. Do not attach UI to routine heartbeat_update calls. Near the end of a substantial assistant turn, call heartbeat_render exactly once for the owning task so ChatGPT renders one compact task-scoped card containing only the three most recent updates. Use heartbeat_get only when the user explicitly requests full history/sidebar inspection or recovery genuinely requires it."
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
    "workspace-heartbeat-summary",
    SUMMARY_URI,
    {},
    async () => ({
      contents: [
        {
          uri: SUMMARY_URI,
          mimeType: RESOURCE_MIME_TYPE,
          text: summaryHtml,
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
        "Record a concise natural-language progress update for the owning task. Write it like normal ChatGPT commentary: one or two conversational sentences focused on a meaningful finding, decision, state change, or next action. Prefer 'The runner reached checkout, but dependency setup failed, so I am isolating that path next' over 'GitHub read completed'. Avoid headings, task IDs, sequence numbers, stage labels, and telemetry-style boilerplate. This tool is state-only and intentionally has no UI. Call heartbeat_render once near the end of the substantial turn to show the latest three updates in one compact card.",
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
    },
  );

  registerAppTool(
    server,
    "heartbeat_render",
    {
      title: "Show recent task progress",
      description:
        "Render one compact end-of-turn heartbeat card for exactly one task. Call this at most once near the end of a substantial assistant turn, after the final heartbeat_update. It shows only the three most recent heartbeats for the supplied task_id; it never mixes tasks and does not expose full history.",
      inputSchema: {
        task_id: z.string().min(1).max(160),
      },
      outputSchema: heartbeatSummaryOutputSchema,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: true,
      },
      _meta: {
        ui: {
          resourceUri: SUMMARY_URI,
          visibility: ["model", "app"],
        },
        "openai/toolInvocation/invoking": "Preparing progress summary…",
        "openai/toolInvocation/invoked": "Progress summary ready",
      },
    },
    async ({ task_id }, { _meta } = {}) => {
      const snapshot = store.getSnapshot({
        sessionId: sessionIdFromMeta(_meta),
        taskId: task_id.trim(),
      });
      const recent = snapshot.history.slice(-3);
      return {
        structuredContent: {
          heartbeat: snapshot.heartbeat,
          recent,
        },
        content: [
          {
            type: "text",
            text: snapshot.heartbeat
              ? `Recent progress for ${snapshot.heartbeat.task_id}: ${recent.map((item) => item.message).join(" | ")}`
              : `No heartbeat has been recorded for ${task_id.trim()} yet.`,
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
        "Full task-history inspection only. Use this when the user explicitly asks to open/read heartbeat history or when recovery genuinely requires historical state. Pass task_id whenever it is known. Routine progress delivery should use heartbeat_update during work and heartbeat_render once near the end of the turn.",
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
