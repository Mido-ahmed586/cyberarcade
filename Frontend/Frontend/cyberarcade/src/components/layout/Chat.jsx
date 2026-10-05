import { useState, useEffect, useRef } from "react";
import I from "../icons/Icons";
import { chatService } from "../../services/chat.service";

export default function Chat({ onClose, labId = null, ctx }) {
  const [msgs, setMsgs] = useState([
    {
      r: "a",
      c: labId || ctx
        ? "Welcome! I can help with concepts and guide you through tasks."
        : "Hi! I'm the CyberArcade AI. How can I help?",
    },
  ]);
  const [inp, setInp] = useState("");
  const [typ, setTyp] = useState(false);
  const [err, setErr] = useState("");
  const end = useRef(null);

  useEffect(() => {
    if (!labId) return;
    let cancelled = false;
    chatService
      .history(labId, 30)
      .then((res) => {
        if (cancelled) return;
        const mapped = (res.messages || []).map((m) => ({
          r: m.role === "user" ? "u" : "a",
          c: m.content,
          id: m.message_id,
        }));
        if (mapped.length > 0) setMsgs(mapped);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [labId]);

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, typ]);

  const send = async () => {
    const text = inp.trim();
    if (!text || typ) return;

    setMsgs((p) => [...p, { r: "u", c: text }]);
    setInp("");
    setErr("");
    setTyp(true);

    try {
      const res = await chatService.send(text, labId || null);
      setMsgs((p) => [...p, { r: "a", c: res.content, id: res.message_id }]);
    } catch (e) {
      setErr(e?.message || "Failed to reach the AI. Please try again.");
    } finally {
      setTyp(false);
    }
  };

  return (
    <div className="chp chat-popup">
      <div className="chh">
        <div className="chl">
          {/* Bigger bot icon */}
          <div className="chat-bot-icon">
            <I.Bot />
          </div>
          <span>AI Assistant</span>
        </div>
        <button onClick={onClose}>
          <I.X />
        </button>
      </div>
      <div className="chm">
        {msgs.map((m, i) => (
          <div key={m.id || i} className={`cm ${m.r}`}>
            {m.r === "a" && (
              <div className="cav">
                <I.Bot />
              </div>
            )}
            <div className="cbb">{m.c}</div>
          </div>
        ))}
        {typ && (
          <div className="cm a">
            <div className="cav">
              <I.Bot />
            </div>
            <div className="cbb ty">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}
        {err && (
          <div className="cm a">
            <div className="cav">
              <I.Bot />
            </div>
            <div className="cbb" style={{ color: "var(--error, #ff6b6b)" }}>
              {err}
            </div>
          </div>
        )}
        <div ref={end} />
      </div>
      <div className="chi">
        <input
          placeholder="Ask a question..."
          value={inp}
          onChange={(e) => setInp(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          disabled={typ}
        />
        <button onClick={send} disabled={!inp.trim() || typ}>
          <I.Send />
        </button>
      </div>
    </div>
  );
}