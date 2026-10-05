// src/services/courses.service.js
//
// Wraps /api/courses/*. All IDs here are UUIDs (strings) — that's what the
// backend uses. The old numeric mock IDs are gone.

import { api } from "./api";

export const coursesService = {
  /**
   * List published courses with optional filters.
   * Backend query params: category, difficulty, page, per_page.
   */
  list: (params = {}) => api.get("/api/courses", { params }),

  /** Course detail, includes modules[] and lab_count. */
  detail: (courseId) => api.get(`/api/courses/${courseId}`),

  /** List labs for a course (ordered by sort_order). */
  labs: (courseId) => api.get(`/api/courses/${courseId}/labs`),

  /** Per-lab progress for the current user in a course. */
  myProgress: (courseId) => api.get(`/api/courses/${courseId}/my-progress`),
};
