// src/services/admin.service.js
//
// Wraps /api/admin/* and admin-only course/lab CRUD endpoints.
// All endpoints require admin or system_admin role — the backend
// enforces this via require_role().

import { api } from "./api";

export const adminService = {
  /* ── Platform stats ─────────────────────────────────────────── */
  getStats: () => api.get("/api/admin/stats"),

  /* ── User management ────────────────────────────────────────── */
  listUsers: (params = {}) => api.get("/api/admin/users", { params }),

  getUser: (userId) => api.get(`/api/admin/users/${userId}`),

  updateUserRole: (userId, role) =>
    api.put(`/api/admin/users/${userId}/role`, { role }),

  updateUserStatus: (userId, isActive) =>
    api.put(`/api/admin/users/${userId}/status`, { is_active: isActive }),

  /* ── Audit log ──────────────────────────────────────────────── */
  getAuditLog: (params = {}) => api.get("/api/admin/audit-log", { params }),

  /* ── Course CRUD (admin only on backend) ────────────────────── */
  createCourse: (data) => api.post("/api/courses", data),

  updateCourse: (courseId, data) => api.put(`/api/courses/${courseId}`, data),

  deleteCourse: (courseId) => api.delete(`/api/courses/${courseId}`),

  /* ── Lab CRUD (admin only on backend) ───────────────────────── */
  createLab: (data) => api.post("/api/labs", data),

  updateLab: (labId, data) => api.put(`/api/labs/${labId}`, data),

  createTask: (labId, data) => api.post(`/api/labs/${labId}/tasks`, data),

  createHint: (labId, taskId, data) =>
    api.post(`/api/labs/${labId}/tasks/${taskId}/hints`, data),
};
