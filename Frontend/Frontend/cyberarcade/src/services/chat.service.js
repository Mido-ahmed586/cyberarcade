// src/services/chat.service.js
//
// Wraps /api/chatbot/*. Both endpoints require a logged-in user.
// Note: the backend's current chatbot is a placeholder that echoes your
// question back — real LLM integration lives in app/services/ai_service.py.

import { api } from "./api";

export const chatService = {
  /**
   * Send a message. lab_id is optional and lets the backend scope the
   * conversation to a particular lab.
   * Returns { message_id, role: "assistant", content, created_at }.
   */
  send: (message, labId = null) =>
    api.post("/api/chatbot/message", {
      message,
      lab_id: labId || null,
    }),

  /**
   * Load history. If labId is given, only messages for that lab are returned.
   * Returns { messages: [...], lab_id }.
   */
  history: (labId = null, limit = 50) =>
    api.get("/api/chatbot/history", {
      params: { lab_id: labId || undefined, limit },
    }),
};
