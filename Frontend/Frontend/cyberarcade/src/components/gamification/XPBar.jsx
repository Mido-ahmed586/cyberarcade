export default function XPBar({ xp }) {
  if (!xp) return null;
  const { total_xp = 0, current_level = 1, level_title = "Recruit", xp_to_next_level = 0, progress_pct = 0 } = xp;

  return (
    <div className="xpbar-card">
      <div className="xpbar-top">
        <div className="xpbar-level">
          <span className="xpbar-lvl-num">Lv.{current_level}</span>
          <span className="xpbar-lvl-title">{level_title}</span>
        </div>
        <div className="xpbar-xp">
          <span className="xpbar-total">{total_xp.toLocaleString()} XP</span>
          {xp_to_next_level > 0 && (
            <span className="xpbar-next">{xp_to_next_level.toLocaleString()} to next level</span>
          )}
        </div>
      </div>
      <div className="xpbar-track">
        <div className="xpbar-fill" style={{ width: `${progress_pct}%` }} />
      </div>
      <div className="xpbar-pct">{progress_pct}%</div>
    </div>
  );
}
