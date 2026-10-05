export default function StreakWidget({ streak }) {
  if (!streak) return null;
  const { current_streak = 0, longest_streak = 0, total_active_days = 0 } = streak;

  const flame = (n) => {
    if (n >= 30) return "🔥🔥🔥";
    if (n >= 7) return "🔥🔥";
    if (n >= 3) return "🔥";
    return "❄️";
  };

  return (
    <div className="streak-widget">
      <div className="streak-header">
        <span className="streak-label">Daily Streak</span>
        <span className="streak-fire">{flame(current_streak)}</span>
      </div>
      <div className="streak-main">
        <span className="streak-num">{current_streak}</span>
        <span className="streak-unit">{current_streak === 1 ? "day" : "days"}</span>
      </div>
      <div className="streak-stats">
        <div className="streak-stat">
          <span className="streak-stat-val">{longest_streak}</span>
          <span className="streak-stat-lbl">Best</span>
        </div>
        <div className="streak-divider" />
        <div className="streak-stat">
          <span className="streak-stat-val">{total_active_days}</span>
          <span className="streak-stat-lbl">Total Days</span>
        </div>
      </div>
    </div>
  );
}
