/**
 * KnowledgeHive - API Service
 *
 * Axios client and API functions for backend communication.
 */
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 120000, // 2 minutes for LLM calls
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Upload a document (PDF, DOCX, TXT)
 */
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

/**
 * Ask a question against the knowledge base
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

export default api;
