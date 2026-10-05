import { useEffect, useRef, useState } from "react";

const ROLE_META = {
  attacker: { dot: "#ff5f56", title: "Attacker (Kali)" },
  defender: { dot: "#27c93f", title: "Defender (Target)" },
  "df-kali": { dot: "#a78bfa", title: "Forensics Kali" },
  single:   { dot: "#27c93f", title: "Kali Terminal" },
};

export default function LabTerminal({ guacUrl, role = "single", label, onAutoSolveLive, active = true, starting = false, onScrollUp, onScrollDown, onScrollExit }) {
  const iframeRef     = useRef(null);
  const refocusGuard  = useRef(false); // debounce re-focus calls
  const [loaded,   setLoaded]   = useState(false);
  const [focused,  setFocused]  = useState(false);

  const meta        = ROLE_META[role] || ROLE_META.single;
  const headerTitle = label || meta.title;

  const refocusIframe = () => {
    if (!iframeRef.current || refocusGuard.current) return;
    refocusGuard.current = true;
    iframeRef.current.focus();
    setFocused(true);
    setTimeout(() => { refocusGuard.current = false; }, 600);
  };

  // Reset state whenever the URL changes
  useEffect(() => {
    setLoaded(false);
    setFocused(false);
  }, [guacUrl]);

  // Wire autosolve-live event
  useEffect(() => {
    if (!onAutoSolveLive) return;
    const handler = () => onAutoSolveLive();
    window.addEventListener("cyberarcade:autosolve-live", handler);
    return () => window.removeEventListener("cyberarcade:autosolve-live", handler);
  }, [onAutoSolveLive]);

  // Auto-focus when this terminal becomes the active tab
  useEffect(() => {
    if (active && guacUrl && iframeRef.current) {
      const t = setTimeout(() => iframeRef.current?.focus(), 80);
      return () => clearTimeout(t);
    }
  }, [active, guacUrl]);

  // Track focus state accurately:
  // window.blur fires when focus moves INTO the cross-origin iframe.
  // window.focus fires when focus returns FROM the iframe to the parent page.
  useEffect(() => {
    if (!guacUrl) return;
    const onBlur = () => {
      setTimeout(() => {
        if (document.activeElement === iframeRef.current) setFocused(true);
      }, 50);
    };
    const onFocus = () => {
      // Parent page regained focus — iframe lost it
      setFocused(false);
    };
    window.addEventListener("blur",  onBlur);
    window.addEventListener("focus", onFocus);
    return () => {
      window.removeEventListener("blur",  onBlur);
      window.removeEventListener("focus", onFocus);
    };
  }, [guacUrl]);

  const handleLoad = () => {
    setLoaded(true);
    setTimeout(() => iframeRef.current?.focus(), 50);
  };

  const handleHeaderClick = () => {
    refocusIframe();
  };

  return (
    <div
      style={{
        background: "#050505",
        borderRadius: "12px",
        height: "100%",
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        boxSizing: "border-box",
      }}
    >
      {/* Terminal header bar — clicking re-focuses the iframe */}
      <div
        onClick={handleHeaderClick}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          padding: "7px 14px",
          background: "#111",
          borderBottom: "1px solid #1a1a1a",
          flexShrink: 0,
          cursor: "default",
          userSelect: "none",
        }}
      >
        <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#ff5f56", display: "inline-block" }} />
        <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#ffbd2e", display: "inline-block" }} />
        <span style={{ width: 10, height: 10, borderRadius: "50%", background: meta.dot, display: "inline-block" }} />
        <span style={{ color: "#555", fontSize: "11px", marginLeft: "8px", fontFamily: "monospace" }}>
          {headerTitle}
        </span>
        {guacUrl && (onScrollUp || onScrollDown) && (
          <div style={{ marginLeft: "auto", display: "flex", gap: "4px", alignItems: "center" }}>
            {onScrollExit && (
              <button
                onMouseDown={(e) => e.preventDefault()}
                onClick={onScrollExit}
                title="Exit scroll mode (resume typing)"
                style={{
                  background: "#1a1a1a", border: "1px solid #444", color: "#f59e0b",
                  borderRadius: "4px", height: "22px", padding: "0 7px", cursor: "pointer",
                  fontSize: "10px", fontFamily: "monospace", fontWeight: 700,
                  transition: "color .2s, border-color .2s",
                }}
                onMouseEnter={(e) => { e.currentTarget.style.color = "#fbbf24"; e.currentTarget.style.borderColor = "#fbbf24"; }}
                onMouseLeave={(e) => { e.currentTarget.style.color = "#f59e0b"; e.currentTarget.style.borderColor = "#444"; }}
              >ESC</button>
            )}
            <button
              onMouseDown={(e) => e.preventDefault()}
              onClick={onScrollUp}
              title="Scroll up"
              style={{
                background: "#1a1a1a", border: "1px solid #333", color: "#888",
                borderRadius: "4px", width: "22px", height: "22px", cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "11px", lineHeight: 1, transition: "color .2s",
              }}
              onMouseEnter={(e) => e.currentTarget.style.color = "#ccc"}
              onMouseLeave={(e) => e.currentTarget.style.color = "#888"}
            >▲</button>
            <button
              onMouseDown={(e) => e.preventDefault()}
              onClick={onScrollDown}
              title="Scroll down"
              style={{
                background: "#1a1a1a", border: "1px solid #333", color: "#888",
                borderRadius: "4px", width: "22px", height: "22px", cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "11px", lineHeight: 1, transition: "color .2s",
              }}
              onMouseEnter={(e) => e.currentTarget.style.color = "#ccc"}
              onMouseLeave={(e) => e.currentTarget.style.color = "#888"}
            >▼</button>
          </div>
        )}
        {guacUrl && (
          <span style={{
            marginLeft: (onScrollUp || onScrollDown) ? "8px" : "auto",
            fontSize: "10px",
            color: focused ? "#27c93f" : loaded ? "#f59e0b" : "#666",
            fontFamily: "monospace",
            transition: "color 0.3s",
          }}>
            {focused ? "● active" : loaded ? "○ click to focus" : "○ connecting…"}
          </span>
        )}
      </div>

      {/* Guacamole iframe — fills all remaining space.
          onMouseEnter fires when the mouse enters from outside.
          onMouseMove re-focuses when the mouse was already inside (e.g. user
          submitted an answer via keyboard while hovering over the terminal). */}
      {guacUrl ? (
        <div
          style={{ flex: 1, position: "relative", minHeight: 0 }}
          onMouseEnter={refocusIframe}
          onMouseMove={() => { if (!focused) refocusIframe(); }}
        >
          <iframe
            ref={iframeRef}
            id={`guacamole-${role}`}
            src={guacUrl}
            title={headerTitle}
            tabIndex={0}
            onLoad={handleLoad}
            onFocus={() => { setFocused(true); }}
            style={{
              position: "absolute",
              inset: 0,
              border: "none",
              width: "100%",
              height: "100%",
              background: "#000",
              display: "block",
            }}
            allow="clipboard-read; clipboard-write"
          />
        </div>
      ) : (
        <div style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          color: "#444",
          fontFamily: "monospace",
          fontSize: "13px",
          gap: "12px",
        }}>
          <div style={{ fontSize: "32px" }}>⌨️</div>
          <div style={{ color: meta.dot, fontSize: "14px" }}>
            {starting ? `${headerTitle} - starting` : `${headerTitle} - not connected`}
          </div>
          <div style={{ color: "#555", textAlign: "center", lineHeight: "1.6" }}>
            {starting ? (
              <>
                Booting the container and opening your terminal.<br />
                This can take a few seconds.
              </>
            ) : (
              <>
                Press <strong style={{ color: "#aaa" }}>Launch Machine</strong> to boot the<br />
                container and open your terminal.
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
