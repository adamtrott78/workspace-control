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

const PANEL_URI = "ui://workspace-heartbeat/panel-v1.html";
const panelHtml = readFileSync(
  new URL("./public/heartbeat-panel.html", import.meta.url),
  "utf8",
);
const store = new HeartbeatStore();

const heartbeatSchema = z.object({
  task_id: z.string(),
  message: z.string(),
  state: z.enum(["working", "waiting", "blocked", "done"]),
  sequence: z.number().int().nonnegative(),
  updated_at: z.string(),
});

const heartbeatOutputSchema = {
  heartbeat: heartbeatSchema.nullable(),
};

function sessionIdFromMeta(meta) {
  return meta?.["openai/session"] ?? "dev-session";
}

function resultFor(heartbeat, text) {
  return {
    structuredContent: { heartbeat },
    content: [{ type: "text", text }],
  };
}

function createHeartbeatServer() {
  const server = new McpServer(
    {
      name: "workspace-heartbeat",
      version: "0.1.0",
    },
    {
      instructions:
        "For substantial long-running work, keep the operator informed through heartbeat_update. Use natural conversational prose, not rigid status headings. Call heartbeat_update on meaningful state changes and before a fourth non-heartbeat tool operation occurs.",
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

  registerAppTool(
    server,
    "heartbeat_update",
    {
      title: "Update operator heartbeat",
      description:
        "Use this during substantial long-running work to replace the operator's current progress heartbeat with a concise natural-language update. Call on meaningful state changes and before a fourth non-heartbeat tool operation.",
      inputSchema: {
        task_id: z.string().min(1).max(160),
        message: z.string().min(1).max(4000),
        state: z.enum(["working", "waiting", "blocked", "done"]).default("working"),
      },
      outputSchema: heartbeatOutputSchema,
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: false,
      },
      _meta: {
        ui: { visibility: ["model"] },
        "openai/toolInvocation/invoking": "Updating progress…",
        "openai/toolInvocation/invoked": "Progress updated",
      },
    },
    async ({ task_id, message, state }, { _meta } = {}) => {
      const heartbeat = store.update({
        sessionId: sessionIdFromMeta(_meta),
        taskId: task_id.trim(),
        message: message.trim(),
        state,
      });
      return resultFor(
        heartbeat,
        `Heartbeat updated for ${heartbeat.task_id} (sequence ${heartbeat.sequence}).`,
      );
    },
  );

  registerAppTool(
    server,
    "heartbeat_get",
    {
      title: "Read operator heartbeat",
      description:
        "Read the latest operator heartbeat for this ChatGPT conversation. Omit task_id to read the most recently updated task.",
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
      const heartbeat = store.get({
        sessionId: sessionIdFromMeta(_meta),
        taskId: task_id?.trim(),
      });
      if (!heartbeat) {
        return resultFor(null, "No heartbeat has been recorded in this conversation yet.");
      }
      return resultFor(
        heartbeat,
        `Latest heartbeat for ${heartbeat.task_id}: ${heartbeat.message}`,
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
