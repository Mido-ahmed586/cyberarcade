const RARITY_COLOR = {
  common:    "#5eafff",
  rare:      "#4a9e7e",
  epic:      "#8a5cf7",
  legendary: "#f0a020",
};

const STREAK_UNIT = {
  streak_3:   { num: "3",  unit: "Days",   type: "Streak" },
  streak_7:   { num: "7",  unit: "Days",   type: "Streak" },
  streak_30:  { num: "1",  unit: "Month",  type: "Streak" },
  streak_90:  { num: "3",  unit: "Months", type: "Streak" },
  streak_180: { num: "6",  unit: "Months", type: "Streak" },
  streak_365: { num: "12", unit: "Months", type: "Streak" },
  streak_545: { num: "18", unit: "Months", type: "Streak" },
  streak_730: { num: "24", unit: "Months", type: "Streak" },
};

function BadgeEmblem({ badge, size = 80 }) {
  const color = RARITY_COLOR[badge.rarity] || RARITY_COLOR.common;
  const streakData = STREAK_UNIT[badge.slug];

  if (streakData) {
    return (
      <div
        className="bdg-emblem bdg-emblem-streak"
        style={{ "--ec": color, width: size, height: size, minWidth: size }}
      >
        <div className="bdg-emblem-ring" />
        <div className="bdg-emblem-content">
          <span className="bdg-emblem-num">{streakData.num}</span>
          <span className="bdg-emblem-unit">{streakData.unit}</span>
          <span className="bdg-emblem-type">{streakData.type}</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className="bdg-emblem"
      style={{ "--ec": color, width: size, height: size, minWidth: size }}
    >
      <div className="bdg-emblem-ring" />
      <span className="bdg-emblem-icon">{badge.icon}</span>
    </div>
  );
}

export default function BadgeCard({ badge, locked = false, small = false }) {
  if (!badge) return null;
  const color = RARITY_COLOR[badge.rarity] || RARITY_COLOR.common;
  const size  = small ? 48 : 72;

  return (
    <div
      className={`badge-card${small ? " badge-card-sm" : ""}${locked ? " badge-locked" : ""}`}
      title={`${badge.name}: ${badge.description}`}
      style={{ "--badge-color": color }}
    >
      <BadgeEmblem badge={badge} size={size} />
      {!small && (
        <>
          <div className="badge-name">{badge.name}</div>
          <div className="badge-rarity" style={{ color }}>{badge.rarity}</div>
          {badge.xp_reward > 0 && (
            <div className="badge-xp">+{badge.xp_reward} XP</div>
          )}
        </>
      )}
    </div>
  );
}

export { BadgeEmblem, RARITY_COLOR };
