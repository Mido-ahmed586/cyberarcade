import { useMemo } from "react";

function getIntensity(count) {
  if (!count) return 0;
  if (count >= 8) return 4;
  if (count >= 5) return 3;
  if (count >= 3) return 2;
  return 1;
}

export default function ActivityHeatmap({ activity = [] }) {
  const actMap = useMemo(() => {
    const m = {};
    activity.forEach(({ date, count }) => { m[date] = count; });
    return m;
  }, [activity]);

  // Build last 13 weeks (91 days) of dates
  const today = new Date();
  const days = useMemo(() => {
    const d = [];
    for (let i = 90; i >= 0; i--) {
      const dt = new Date(today);
      dt.setDate(dt.getDate() - i);
      const iso = dt.toISOString().split("T")[0];
      d.push({ iso, count: actMap[iso] || 0, dow: dt.getDay() });
    }
    return d;
  }, [actMap]);

  // Group by week
  const weeks = useMemo(() => {
    const ws = [];
    let week = [];
    days.forEach((d, i) => {
      if (i === 0) {
        // pad leading days
        for (let p = 0; p < d.dow; p++) week.push(null);
      }
      week.push(d);
      if (d.dow === 6 || i === days.length - 1) {
        ws.push(week);
        week = [];
      }
    });
    return ws;
  }, [days]);

  const DAY_LABELS = ["S", "M", "T", "W", "T", "F", "S"];

  return (
    <div className="heatmap">
      <div className="heatmap-day-labels">
        {DAY_LABELS.map((l, i) => (
          <span key={i} className="heatmap-day-lbl">{l}</span>
        ))}
      </div>
      <div className="heatmap-grid">
        {weeks.map((week, wi) => (
          <div key={wi} className="heatmap-week">
            {week.map((d, di) =>
              d === null ? (
                <div key={di} className="heatmap-cell heatmap-empty" />
              ) : (
                <div
                  key={di}
                  className={`heatmap-cell heatmap-level-${getIntensity(d.count)}`}
                  title={`${d.iso}: ${d.count} activities`}
                />
              )
            )}
          </div>
        ))}
      </div>
      <div className="heatmap-legend">
        <span className="hm-lbl">Less</span>
        {[0, 1, 2, 3, 4].map((l) => (
          <div key={l} className={`heatmap-cell heatmap-level-${l}`} />
        ))}
        <span className="hm-lbl">More</span>
      </div>
    </div>
  );
}
