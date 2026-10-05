import React from "react";
import I from "./icons/Icons";
import { formatCountdown } from "../utils/helpers";

export default function TaskHints({
  hints = [],
  totalHints = 0,
  hintsUsed = 0,
  countdown = 0,
  hintBusy = false,
  locked = false,
  onRevealHint = () => {},
  meta = {},
}) {
  const allRevealed = totalHints > 0 && hintsUsed >= totalHints;
  const onCooldown  = countdown > 0;

  return (
    <div className="task-hint-zone">
      {/* Already-revealed hints */}
      {hints.map((h, i) => (
        <div
          key={h.hint_id}
          className="task-hint-revealed"
          style={{ animationDelay: `${i * 0.05}s` }}
        >
          <div className="task-hint-revealed-tag">
            <I.Bulb /> Hint {h.hint_order}
          </div>
          <pre>{h.hint_text}</pre>
        </div>
      ))}

      {totalHints === 0 && (
        <div className="task-hint-empty">No hints for this task</div>
      )}

      {/* Global cooldown slot — locks ALL hint buttons across every task in the lab */}
      {totalHints > 0 && onCooldown && (
        <div className="task-hint-locked-slot">
          <div className="task-hint-locked-icon">
            <I.Lock />
          </div>
          <div className="task-hint-locked-body">
            <span className="task-hint-locked-label">
              {allRevealed ? "Hint cooldown active" : `Hint ${hintsUsed + 1} of ${totalHints}`}
            </span>
            <div className="hint-timer-bar">
              <I.Clock />
              <span>Next hint available in</span>
              <strong className="hint-timer-value">{formatCountdown(countdown)}</strong>
              <div className="hint-timer-track">
                <div className="hint-timer-fill" style={{ animationDuration: "30s" }} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Hint button — shown only when more hints are available */}
      {totalHints > 0 && !allRevealed && (
        <div className="task-hint-controls">
          <button
            key={`hb-${hintsUsed}`}
            className={`task-hint-btn${onCooldown ? " waiting" : ""}${hintBusy ? " busy" : ""}`}
            disabled={onCooldown || hintBusy || locked}
            onClick={onRevealHint}
            title={onCooldown ? `Next hint available in ${countdown}s` : ""}
          >
            {onCooldown ? <I.Lock /> : <I.Bulb />}
            <span>
              {hintBusy
                ? "Requesting..."
                : onCooldown
                ? `Locked (${formatCountdown(countdown)})`
                : hintsUsed > 0
                ? `Hint ${hintsUsed + 1} of ${totalHints}`
                : "Hint"}
            </span>
            {totalHints > 0 && (
              <span className="hint-count-badge">{hintsUsed}/{totalHints}</span>
            )}
          </button>
        </div>
      )}

      {meta?.error && (
        <div className="afb no" style={{ marginTop: 8 }}>
          {meta.error}
        </div>
      )}
    </div>
  );
}
