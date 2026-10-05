// src/services/classes.service.js
//
// Wraps /api/classes/*. Instructors create and manage classes;
// students join via class codes and view enrolled classes.

import { api } from "./api";

export const classesService = {
  /** Create a class (instructor/admin only). */
  create: (data) => api.post("/api/classes", data),

  /** List classes created by the current instructor. */
  myClasses: () => api.get("/api/classes/my-classes"),

  /** Get student progress report for a class. */
  classProgress: (classId) => api.get(`/api/classes/${classId}/progress`),

  /** Join a class using a class code (any authenticated user). */
  join: (classCode) => api.post("/api/classes/join", { class_code: classCode }),

  /** List all classes the current student is enrolled in. */
  enrolled: () => api.get("/api/classes/enrolled"),
};
