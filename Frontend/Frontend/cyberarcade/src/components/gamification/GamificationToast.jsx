import { useEffect, useState } from "react";

export default function GamificationToast({ rewards, onDone }) {
  const [visible, setVisible] = useState(false);
  const [index, setIndex] = useState(0);
  const items = buildItems(rewards);

  useEffect(() => {
    if (!items.length) { onDone?.(); return; }
    setIndex(0);
    setVisible(true);
    const advance = () => {
      setIndex((i) => {
        if (i + 1 >= items.length) {
          setVisible(false);
          setTimeout(() => onDone?.(), 300);
          return i;
        }
        return i + 1;
      });
    };
    const t = setInterval(advance, 2200);
    return () => clearInterval(t);
  }, [rewards]);

  if (!visible || !items.length) return null;
  const item = items[index] || items[0];

  return (
    <div className={`gtoast gtoast-${item.type}`}>
      <span className="gtoast-icon">{item.icon}</span>
      <div className="gtoast-body">
        <div className="gtoast-title">{item.title}</div>
        <div className="gtoast-sub">{item.sub}</div>
      </div>
    </div>
  );
}

function buildItems(rewards) {
  if (!rewards) return [];
  const items = [];

  if (rewards.xp_gained > 0) {
    items.push({ type: "xp", icon: "⚡", title: `+${rewards.xp_gained} XP`, sub: "earned" });
  }
  if (rewards.level_up) {
    items.push({
      type: "levelup",
      icon: "🆙",
      title: `Level Up!`,
      sub: `You reached Level ${rewards.new_level} — ${rewards.new_level_title}`,
    });
  }
  (rewards.new_badges || []).forEach((b) => {
    items.push({ type: "badge", icon: b.icon || "🏆", title: `Badge Unlocked`, sub: b.name });
  });
  return items;
}
