import { api } from "./api";

export const aiCoachService = {
  overview: () => api.get("/api/ai-coach/overview"),
  skills: () => api.get("/api/ai-coach/skills"),
  recommendations: () => api.get("/api/ai-coach/recommendations"),
  generateInsight: () => api.post("/api/ai-coach/generate-insight"),
};
