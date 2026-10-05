import { api } from "./api";

export const gamificationService = {
  profile: () => api.get("/api/gamification/profile"),
  dashboard: () => api.get("/api/gamification/dashboard"),
  badges: () => api.get("/api/gamification/badges"),
  markBadgesSeen: () => api.post("/api/gamification/badges/seen"),
  streak: () => api.get("/api/gamification/streak"),
  xpHistory: (limit = 20) => api.get(`/api/gamification/xp-history?limit=${limit}`),
  activity: (days = 90) => api.get(`/api/gamification/activity?days=${days}`),
  leaderboard: (limit = 50) => api.get(`/api/gamification/leaderboard?limit=${limit}`),
};
