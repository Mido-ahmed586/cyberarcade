// src/services/labs.service.js

import { api } from "./api";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");

export const labsService = {
  /** Lab detail with tasks[] (tasks include hint_count and has_autosolve). */
  detail: (labId) => api.get(`/api/labs/${labId}`),

  /** Start a lab instance. Backend may 409 if one is already active. */
  start: (labId) => api.post(`/api/labs/${labId}/start`),

  /** Terminate the user's active instance for this lab. */
  stop: (labId) => api.post(`/api/labs/${labId}/stop`),

  /** Get the live instance status (404 when nothing is active). */
  status: (labId) => api.get(`/api/labs/${labId}/status`),

  /**
   * Per-task progress for the current user in a lab.
   * Returns { lab_id, tasks: [{task_id, status, submitted_answer, is_correct, hints_used}], completed_count, total_count, percent }
   */
  myProgress: (labId) => api.get(`/api/labs/${labId}/my-progress`),

  /**
   * Submit an answer for a task.
   * Returns { is_correct: bool, status: string, message: string }
   */
  submitAnswer: (taskId, answer) =>
    api.post(`/api/labs/tasks/${taskId}/submit`, { answer }),

  /**
   * Request the next hint (time-gated by server, 30s global cooldown).
   * Returns { is_available, hint?, seconds_remaining, total_hints, hints_used, next_hint_cooldown_ends_at }
   */
  requestHint: (taskId) => api.get(`/api/labs/tasks/${taskId}/hint`),

  /**
   * Get all hints the user has already revealed for a task (no cooldown info).
   * Returns { hints, hints_used, total_hints }
   */
  getRevealedHints: (taskId) => api.get(`/api/labs/tasks/${taskId}/hints`),

  /**
   * Get the GLOBAL hint cooldown state for a lab (shared across all tasks).
   * Returns { seconds_remaining, global_cooldown_ends_at }
   * Call once per lab load to restore the shared timer.
   */
  getLabHintCooldown: (labId) => api.get(`/api/labs/${labId}/hint-cooldown`),

  /** Mark task as auto-solved in DB (called after WS autosolve). */
  autoSolve: (taskId) => api.post(`/api/labs/tasks/${taskId}/auto-solve`),

  /**
   * Open a WebSocket for streaming autosolve.
   * Returns the WebSocket instance.
   * token: JWT access token string
   * onLine(type, data): callback for each message
   *   type = "cmd" | "line" | "answer" | "done" | "error" | "info"
   */
  openAutosolveWS(taskId, token, onMessage) {
    const url = `${WS_BASE}/api/labs/ws/autosolve/${taskId}?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    ws.onmessage = (event) => {
      try { onMessage(JSON.parse(event.data)); } catch { onMessage({ type: "line", data: event.data }); }
    };
    ws.onerror = () => { onMessage({ type: "error", data: "WebSocket connection error" }); };
    return ws;
  },

  /** Lab-level autosolve: runs ALL tasks' commands and injects them into the tmux terminal. */
  openLabAutosolveWS(labId, token, onMessage) {
    const url = `${WS_BASE}/api/labs/ws/autosolve-lab/${labId}?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    ws.onmessage = (event) => {
      try { onMessage(JSON.parse(event.data)); } catch { onMessage({ type: "line", data: event.data }); }
    };
    ws.onerror = () => { onMessage({ type: "error", data: "WebSocket connection error" }); };
    return ws;
  },
};
