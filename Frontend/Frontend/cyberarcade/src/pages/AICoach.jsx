import { useEffect, useMemo, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Line, LineChart, PolarAngleAxis, PolarGrid,
  PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import Navbar from "../components/layout/Navbar";
import I from "../components/icons/Icons";
import { InlineLoader } from "../components/ui/Loader";
import { aiCoachService } from "../services/aiCoach.service";

const emptyOverview = {
  metrics: {},
  insight: { strengths: [], weaknesses: [], improvement_plan: [], recommended_labs: [], summary: "" },
  progress_over_time: [],
  category_performance: [],
};

export default function AICoach({ theme, setTheme, user, nav, onLogout, currentPage, currentStreak }) {
  const [data, setData] = useState(emptyOverview);
  const [status, setStatus] = useState("loading");
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    aiCoachService.overview()
      .then((res) => { if (!cancelled) setData({ ...emptyOverview, ...res }); })
      .catch((e) => { if (!cancelled) setError(e.message || "Failed to load AI Coach."); })
      .finally(() => { if (!cancelled) setStatus("ready"); });
    return () => { cancelled = true; };
  }, []);

  const metrics = data.metrics || {};
  const insight = data.insight || emptyOverview.insight;

  // Recharts expects compact data rows, so the backend's skill names are shortened
  // only for chart labels while the full names remain available in cards/tooltips.
  const skillRows = useMemo(() => {
    const rows = data.category_performance?.length ? data.category_performance : [];
    return rows.map((s) => ({
      skill: s.skill_category.replace("Digital ", "D. ").replace("Vulnerability ", "Vuln. "),
      fullSkill: s.skill_category,
      score: s.score || 0,
      completed: s.completed || 0,
      attempted: s.attempted || 0,
    }));
  }, [data]);

  const lineRows = data.progress_over_time?.length
    ? data.progress_over_time
    : [{ week: "Start", progress: metrics.course_progress_percent || 0 }];

  const strongest = [...skillRows].sort((a, b) => b.score - a.score)[0];
  const weakest = [...skillRows].sort((a, b) => a.score - b.score)[0];

  const regenerate = async () => {
    setRefreshing(true);
    setError("");
    try {
      await aiCoachService.generateInsight();
      const fresh = await aiCoachService.overview();
      setData({ ...emptyOverview, ...fresh });
    } catch (e) {
      setError(e.message || "Could not generate insight.");
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="pg">
      <Navbar theme={theme} setTheme={setTheme} user={user} nav={nav} onLogout={onLogout} currentPage={currentPage} currentStreak={currentStreak} />
      <div className="coach-page">
        <div className="coach-header">
          <div>
            <div className="coach-kicker"><I.Bot /> AI Learning Coach</div>
            <h1>Personalized Performance Insights</h1>
            <p>Tracks lab behavior, skill growth, hints, retries, time spent, and chatbot usage.</p>
          </div>
          <button className="btn ba2 bs" onClick={regenerate} disabled={refreshing}>
            <I.Zap /> {refreshing ? "Analyzing..." : "Generate Insight"}
          </button>
        </div>

        {status === "loading" && <div className="adm-center"><InlineLoader /></div>}
        {error && <div className="ae" style={{ marginBottom: 16 }}>{error}</div>}

        {status === "ready" && (
          <>
            <div className="coach-stat-grid">
              <CoachStat label="Overall Progress" value={`${metrics.course_progress_percent || 0}%`} />
              <CoachStat label="Strongest Skill" value={strongest?.fullSkill || "Not enough data"} />
              <CoachStat label="Weakest Skill" value={weakest?.fullSkill || "Not enough data"} />
              <CoachStat label="Hints Used" value={metrics.hints_used || 0} />
              <CoachStat label="Labs Completed" value={metrics.labs_completed || 0} />
              <CoachStat label="Average Score" value={`${metrics.average_score || 0}%`} />
            </div>

            <div className="coach-insight-card">
              <div className="coach-insight-top">
                <h2>AI Review</h2>
                <span>{metrics.started_labs || 0} started labs · {metrics.chatbot_questions || 0} chatbot questions</span>
              </div>
              <p className="coach-summary">{insight.summary || "Complete labs to generate a personalized review."}</p>
              <div className="coach-review-grid">
                <InsightList title="Strengths" icon={<I.Check />} items={insight.strengths} />
                <InsightList title="Weaknesses" icon={<I.AlertTriangle />} items={insight.weaknesses} />
                <InsightList title="Improvement Plan" icon={<I.Bulb />} items={insight.improvement_plan} />
              </div>
            </div>

            {/* Visual analytics: radar = skill balance, line = weekly growth, bar = category performance. */}
            <div className="coach-chart-grid">
              <ChartPanel title="Skill Radar">
                <ResponsiveContainer width="100%" height={330}>
                  <RadarChart data={skillRows}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="skill" tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: "var(--text-muted)", fontSize: 10 }} />
                    <Radar dataKey="score" stroke="var(--accent-bright)" fill="var(--accent-bright)" fillOpacity={0.28} />
                    <Tooltip contentStyle={{ background: "var(--bg-card-solid)", border: "1px solid var(--border)" }} />
                  </RadarChart>
                </ResponsiveContainer>
              </ChartPanel>

              <ChartPanel title="Progress Over Time">
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={lineRows}>
                    <CartesianGrid stroke="rgba(255,255,255,.08)" />
                    <XAxis dataKey="week" tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: "var(--bg-card-solid)", border: "1px solid var(--border)" }} />
                    <Line type="monotone" dataKey="progress" stroke="var(--accent-bright)" strokeWidth={3} dot />
                  </LineChart>
                </ResponsiveContainer>
              </ChartPanel>

              <ChartPanel title="Lab Performance By Category">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={skillRows}>
                    <CartesianGrid stroke="rgba(255,255,255,.08)" />
                    <XAxis dataKey="skill" tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: "var(--bg-card-solid)", border: "1px solid var(--border)" }} />
                    <Bar dataKey="score" fill="var(--accent-bright)" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartPanel>
            </div>

            <div className="coach-recommendations">
              <h2>Recommended Next Labs</h2>
              {insight.recommended_labs?.length ? insight.recommended_labs.map((lab) => (
                <div className="coach-rec-row" key={lab.lab_id}>
                  <div>
                    <strong>{lab.title}</strong>
                    <span>{lab.course_title} · {lab.skill_category}</span>
                  </div>
                </div>
              )) : (
                <div className="adm-empty">No specific recommendation yet. Complete or attempt more labs for better guidance.</div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function CoachStat({ label, value }) {
  return (
    <div className="coach-stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function InsightList({ title, icon, items = [] }) {
  return (
    <div className="coach-review-card">
      <h3>{icon} {title}</h3>
      {(items.length ? items : ["More lab activity is needed for this section."]).map((item) => (
        <p key={item}>{item}</p>
      ))}
    </div>
  );
}

function ChartPanel({ title, children }) {
  return (
    <div className="coach-chart-card">
      <h2>{title}</h2>
      {children}
    </div>
  );
}
