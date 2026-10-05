export function CyberLoader({ text = "Initializing..." }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 28, padding: 40 }}>
      <div className="ml">
        {Array.from({ length: 5 }).map((_, c) => (
          <div key={c} className="mc" style={{ animationDelay: `${c * 0.3}s` }}>
            {Array.from({ length: 6 }).map((_, r) => (
              <div key={r} className="mx" style={{ animationDelay: `${c * 0.3 + r * 0.12}s` }} />
            ))}
          </div>
        ))}
        <div className="mg" />
      </div>
      <div className="ll">{text}</div>
    </div>
  );
}

export function InlineLoader() {
  return (
    <div className="il">
      <div className="sw">
        <div className="sf" />
      </div>
    </div>
  );
}