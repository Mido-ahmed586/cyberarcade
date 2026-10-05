import { useEffect, useState } from "react";
import Navbar from "../components/layout/Navbar";
import { gamificationService } from "../services/gamification.service";
import { InlineLoader } from "../components/ui/Loader";

const RARITY_COLOR = {
  common: "var(--text-muted)",
  rare: "#4a9e7e",
  epic: "#8a5cf7",
  legendary: "#f0a020",
};

function RankBadge({ rank }) {
  if (rank === 1) return <span className="lb-rank lb-rank-1">🥇</span>;
  if (rank === 2) return <span className="lb-rank lb-rank-2">🥈</span>;
  if (rank === 3) return <span className="lb-rank lb-rank-3">🥉</span>;
  return <span className="lb-rank lb-rank-n">#{rank}</span>;
}

export default function Leaderboard({ theme, setTheme, user, nav, onLogout, currentPage, userPlan, currentStreak }) {
  const [data, setData]   = useState(null);
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    let cancelled = false;
    gamificationService.leaderboard(50)
      .then((d) => { if (!cancelled) { setData(d); setStatus("ready"); } })
      .catch(() => { if (!cancelled) setStatus("error"); });
    return () => { cancelled = true; };
  }, []);

  const myRank = data?.my_rank;

  return (
    <div className="pg">
      <Navbar theme={theme} setTheme={setTheme} user={user} nav={nav} onLogout={onLogout} currentPage={currentPage} currentStreak={currentStreak} />
      <div className="lb-page">
        <div className="lb-header">
          <button className="bkb" onClick={() => nav("dashboard")}>← Back</button>
          <h1>🏆 Global Leaderboard</h1>
          <p>Top cybersecurity practitioners ranked by XP</p>
        </div>

        {myRank && (
          <div className="lb-my-rank">
            Your rank: <strong>#{myRank}</strong>
          </div>
        )}

        {status === "loading" && (
          <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
            <InlineLoader />
          </div>
        )}

        {status === "error" && (
          <div className="lb-error">Failed to load leaderboard. Try again later.</div>
        )}

        {status === "ready" && (
          <div className="lb-table">
            <div className="lb-thead">
              <span className="lb-col-rank">Rank</span>
              <span className="lb-col-user">Player</span>
              <span className="lb-col-level">Level</span>
              <span className="lb-col-xp">XP</span>
              <span className="lb-col-labs">Labs</span>
              <span className="lb-col-streak">Streak</span>
            </div>
            {(data?.entries || []).map((entry) => {
              const isMe = entry.user_id === user?.user_id?.toString() ||
                           entry.full_name === user?.full_name;
              return (
                <div key={entry.user_id} className={`lb-row${isMe ? " lb-row-me" : ""}`}>
                  <span className="lb-col-rank">
                    <RankBadge rank={entry.rank} />
                  </span>
                  <span className="lb-col-user">
                    <div className="lb-avatar">{entry.full_name?.charAt(0)?.toUpperCase()}</div>
                    <div>
                      <div className="lb-name">{entry.full_name}{isMe && <span className="lb-you"> (you)</span>}</div>
                      <div className="lb-level-title">{entry.level_title}</div>
                    </div>
                  </span>
                  <span className="lb-col-level">
                    <span className="lb-level-badge">Lv.{entry.current_level}</span>
                  </span>
                  <span className="lb-col-xp">
                    <span className="lb-xp">{entry.total_xp.toLocaleString()}</span>
                    <span className="lb-xp-unit">XP</span>
                  </span>
                  <span className="lb-col-labs">{entry.labs_completed}</span>
                  <span className="lb-col-streak">
                    {entry.current_streak > 0 ? (
                      <span>{entry.current_streak} 🔥</span>
                    ) : (
                      <span style={{ color: "var(--text-muted)" }}>—</span>
                    )}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
