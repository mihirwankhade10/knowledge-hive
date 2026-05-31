/**
 * KnowledgeHive - API Service
 *
 * Axios client, REST API functions, and WebSocket helpers
 * for backend communication.
 *
 * Phase 3: Added WebSocket utilities for real-time upload progress
 * and live agent updates during queries.
 */
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 120000, // 2 minutes for LLM calls
  headers: {
    "Content-Type": "application/json",
  },
});

// ==========================================================================
// REST API Functions
// ==========================================================================

/**
 * Upload a document (PDF, DOCX, TXT)
 * Phase 3: Returns { task_id, document_id, status: "accepted" } when Celery is available
 */
export async function uploadDocument(file, { sync = false } = {}) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post(`/upload${sync ? "?sync=true" : ""}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

/**
 * Check background task status (REST polling fallback)
 */
export async function getTaskStatus(taskId) {
  const response = await api.get(`/upload/status/${taskId}`);
  return response.data;
}

/**
 * Ask a question against the knowledge base (REST — synchronous)
 */
export async function queryKnowledge(question) {
  const response = await api.post("/query", { question });
  return response.data;
}

/**
 * Check backend health
 */
export async function getHealth() {
  const response = await api.get("/health");
  return response.data;
}

/**
 * Get knowledge base statistics
 */
export async function getStats() {
  const response = await api.get("/stats");
  return response.data;
}

// ==========================================================================
// WebSocket Helpers (Phase 3)
// ==========================================================================

/**
 * Subscribe to upload task progress via WebSocket.
 *
 * @param {string} taskId - Celery task ID from the upload response
 * @param {function} onProgress - Called with progress updates: { status, step, progress, message, ... }
 * @param {function} onComplete - Called when task finishes: { status: "COMPLETED", ... }
 * @param {function} onError - Called on error: { status: "FAILED", error, ... }
 * @returns {{ ws: WebSocket, close: function }} - WebSocket handle and close function
 */
export function subscribeToTaskProgress(taskId, onProgress, onComplete, onError) {
  const ws = new WebSocket(`${WS_BASE}/ws/task/${taskId}`);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      if (data.status === "COMPLETED") {
        onComplete?.(data);
        ws.close();
      } else if (data.status === "FAILED") {
        onError?.(data);
        ws.close();
      } else {
        onProgress?.(data);
      }
    } catch (err) {
      console.error("Failed to parse WS message:", err);
    }
  };

  ws.onerror = (event) => {
    console.error("WebSocket error:", event);
    onError?.({ status: "ERROR", error: "WebSocket connection failed" });
  };

  ws.onclose = () => {
    console.log(`WebSocket closed for task: ${taskId}`);
  };

  return {
    ws,
    close: () => ws.close(),
  };
}

/**
 * Send a query via WebSocket for live agent status updates.
 *
 * @param {string} question - The question to ask
 * @param {function} onAgentUpdate - Called as each agent starts/completes: { type: "agent_update", agent, status, ... }
 * @param {function} onResult - Called with the final result: { type: "result", answer, sources, confidence, ... }
 * @param {function} onError - Called on error
 * @returns {{ ws: WebSocket, close: function }} - WebSocket handle and close function
 */
export function queryKnowledgeWS(question, onAgentUpdate, onResult, onError) {
  const ws = new WebSocket(`${WS_BASE}/ws/query`);

  ws.onopen = () => {
    ws.send(JSON.stringify({ question }));
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "agent_update":
          onAgentUpdate?.(data);
          break;
        case "cache_hit":
          onAgentUpdate?.({
            type: "agent_update",
            agent: "cache",
            status: "completed",
            message: "Returning cached result",
          });
          break;
        case "result":
          onResult?.(data);
          ws.close();
          break;
        case "error":
          onError?.(data);
          ws.close();
          break;
        default:
          console.log("Unknown WS message type:", data.type);
      }
    } catch (err) {
      console.error("Failed to parse WS message:", err);
    }
  };

  ws.onerror = (event) => {
    console.error("WebSocket error:", event);
    onError?.({ type: "error", message: "WebSocket connection failed" });
  };

  ws.onclose = () => {
    console.log("Query WebSocket closed");
  };

  return {
    ws,
    close: () => ws.close(),
  };
}

export default api;
