// routes.jsx
// This file documents the available page routes used by the nav() function.
// Since this project uses a simple state-based router (no React Router),
// this file serves as a reference for all valid page keys.

export const ROUTES = {
  LANDING: "landing",
  LOGIN: "login",
  REGISTER: "register",
  DASHBOARD: "dashboard",
  AI_COACH: "ai-coach",
  COURSES: "courses",
  COURSE_DETAIL: "course-detail",
  LAB: "lab",
  ADMIN: "admin",
  INSTRUCTOR: "instructor",
  PROFILE: "profile",
  SUBSCRIPTION: "subscription",
};

// nav(ROUTES.COURSES) — navigate to courses page
// nav(ROUTES.COURSE_DETAIL, { course }) — navigate with course data
// nav(ROUTES.LAB, { lab }) — navigate with lab data
// nav(ROUTES.ADMIN) — admin panel (admin/system_admin only)
// nav(ROUTES.INSTRUCTOR) — instructor panel (instructor/admin/system_admin)
// nav(ROUTES.PROFILE) — user profile page
// nav(ROUTES.SUBSCRIPTION) — subscription plans page
