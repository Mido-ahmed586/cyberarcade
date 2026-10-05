import Navbar from "../components/layout/Navbar";
import I from "../components/icons/Icons";

export default function Landing({ theme, setTheme, nav, user, onLogout, currentPage, currentStreak }) {
  return (
    <div className="pg ld">
      <Navbar theme={theme} setTheme={setTheme} nav={nav} user={user} onLogout={onLogout} currentPage={currentPage} clear currentStreak={currentStreak} />

      <div className="hero">
        <div className="hn" />
        <div className="hi">
          <div className="ht">
            <div className="hp">
              <span className="pd" />
              Cybersecurity Training Platform
            </div>
            <h1 className="hh">
              Master the Art of <span className="he">Cyber Offense.</span>
              <br />
              Build Your <span className="he2">Defense.</span>
            </h1>
            <p className="hsp">
              Industry-grade labs with real attacker &amp; victim environments in your browser. AI-powered guidance. Zero configuration required.
            </p>
            <div className="hb">
              <button
                className="btn ba2 bl"
                onClick={() => nav(user ? "courses" : "register")}
              >
                <I.Terminal /> {user ? "Continue Training" : "Start Your Mission"}
              </button>
              <button className="btn bg bl" onClick={() => nav("courses")}>
                Explore Modules <I.Right />
              </button>
            </div>
            <div className="hns">
              <div className="hn2"><span>45+</span><small>Training Modules</small></div>
              <div className="hnd" />
              <div className="hn2"><span>14</span><small>Live Lab Environments</small></div>
              <div className="hnd" />
              <div className="hn2"><span>24/7</span><small>AI Lab Assistant</small></div>
            </div>
          </div>

          <div className="ha">
            <div className="tc2">
              <div className="tb2">
                <div className="td r" /><div className="td y" /><div className="td g" />
                <span>kali@cyberarcade:~</span>
              </div>
              <div className="tby">
                <p><b className="tcc">$</b> nmap -sV -A 10.10.14.5</p>
                <p className="tmm">Starting Nmap 7.94 ...</p>
                <p className="tmm">PORT   STATE SERVICE  VERSION</p>
                <p><b className="tgg">22</b>/tcp  open  ssh      OpenSSH 8.9</p>
                <p><b className="trr">80</b>/tcp  open  http     Apache 2.4.52</p>
                <p><b className="tww">443</b>/tcp open  ssl      nginx 1.18</p>
                <p className="tmm">Nmap done: 1 host up</p>
                <p><b className="tcc">$</b> <span className="cr">▊</span></p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Stats strip ─────────────────────────────────────────────── */}
      <div className="ld-stats">
        <div className="ld-stat"><span className="ld-stat-n">500+</span><span className="ld-stat-l">Active Students</span></div>
        <div className="ld-stat-sep" />
        <div className="ld-stat"><span className="ld-stat-n">45+</span><span className="ld-stat-l">Training Labs</span></div>
        <div className="ld-stat-sep" />
        <div className="ld-stat"><span className="ld-stat-n">10+</span><span className="ld-stat-l">Course Paths</span></div>
        <div className="ld-stat-sep" />
        <div className="ld-stat"><span className="ld-stat-n">54</span><span className="ld-stat-l">Badges to Earn</span></div>
        <div className="ld-stat-sep" />
        <div className="ld-stat"><span className="ld-stat-n">24/7</span><span className="ld-stat-l">AI Lab Assistant</span></div>
      </div>

      <section className="fs">
        <h2 className="sh">Why CyberArcade</h2>
        <div className="fg2">
          {[
            { i: <I.Monitor />, t: "Browser-Based Labs", d: "Access attacker & victim machines directly in your browser. No local setup or VMs required." },
            { i: <I.Bot />, t: "AI-Powered Assistant", d: "Context-aware guidance that helps you develop critical thinking — without giving away the answer." },
            { i: <I.Bulb />, t: "Time-Gated Hints", d: "Strategically paced hints encourage independent problem-solving before revealing guidance." },
            { i: <I.Zap />, t: "Auto-Solve Engine", d: "Stuck after all hints? Watch the automated solver demonstrate the correct attack methodology." },
            { i: <I.Split />, t: "Split-Screen Interface", d: "Tasks on one side, live terminal on the other. Designed for complete operational immersion." },
            { i: <I.Layers />, t: "Kill Chain Curriculum", d: "Modules aligned with real-world attack frameworks — from reconnaissance through exfiltration." },
          ].map((f, i) => (
            <div key={i} className="fc" style={{ animationDelay: `${i * 0.08}s` }}>
              <div className="fi">{f.i}</div>
              <h3>{f.t}</h3>
              <p>{f.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How It Works ────────────────────────────────────────────── */}
      <section className="fs">
        <h2 className="sh">How It Works</h2>
        <p className="ld-sub">Three steps to becoming a cybersecurity professional</p>
        <div className="ld-hiw">
          <div className="ld-hiw-step">
            <div className="ld-hiw-num">01</div>
            <h3>Create Your Account</h3>
            <p>Sign up for free in seconds. No credit card, no configuration — just create an account and you're ready.</p>
          </div>
          <div className="ld-hiw-arrow"><I.Right /></div>
          <div className="ld-hiw-step">
            <div className="ld-hiw-num">02</div>
            <h3>Choose a Learning Path</h3>
            <p>Pick from Web Security, Network Penetration, Digital Forensics, Linux Privilege Escalation, and more.</p>
          </div>
          <div className="ld-hiw-arrow"><I.Right /></div>
          <div className="ld-hiw-step">
            <div className="ld-hiw-num">03</div>
            <h3>Hack, Learn & Level Up</h3>
            <p>Complete real labs in your browser, earn XP and badges, climb the leaderboard, and get certified.</p>
          </div>
        </div>
      </section>

      {/* ── Learning Paths ───────────────────────────────────────────── */}
      <section className="fs">
        <h2 className="sh">Learning Paths</h2>
        <p className="ld-sub">Structured curricula aligned with real-world attack and defense frameworks</p>
        <div className="ld-paths">
          {[
            { icon: "🌐", title: "Web Application Security", level: "Beginner → Advanced", tags: ["OWASP", "XSS", "SQLi", "CSRF"] },
            { icon: "📡", title: "Network Penetration Testing", level: "Intermediate", tags: ["Nmap", "Metasploit", "Pivoting", "MITM"] },
            { icon: "🐧", title: "Linux Privilege Escalation", level: "Intermediate → Advanced", tags: ["SUID", "Cron", "Kernel", "sudo"] },
            { icon: "🔍", title: "Digital Forensics & IR", level: "Intermediate", tags: ["Volatility", "Autopsy", "Memory", "Logs"] },
          ].map((p, i) => (
            <div key={i} className="ld-path-card" onClick={() => nav("courses")}>
              <div className="ld-path-icon">{p.icon}</div>
              <div className="ld-path-body">
                <div className="ld-path-title">{p.title}</div>
                <div className="ld-path-level">{p.level}</div>
                <div className="ld-path-tags">
                  {p.tags.map((t) => <span key={t} className="ld-path-tag">{t}</span>)}
                </div>
              </div>
              <I.Right />
            </div>
          ))}
        </div>
      </section>

      {/* Pricing preview */}
      <section className="fs">
        <h2 className="sh">Simple, Transparent Pricing</h2>
        <p style={{ textAlign: "center", color: "var(--text-muted)", marginBottom: 40, marginTop: -28 }}>Start free, upgrade when you're ready for more</p>
        <div className="landing-pricing">
          <div className="landing-plan">
            <h3>Free</h3>
            <div className="landing-price">$0<span>/forever</span></div>
            <ul>
              <li><I.Check /> First 2 labs per course</li>
              <li><I.Check /> Basic AI assistant</li>
              <li><I.Check /> Progress tracking</li>
              <li className="landing-limit"><I.X /> Limited lab access</li>
            </ul>
            <button
              className="btn bg bf"
              onClick={() => nav(user ? "courses" : "register")}
            >
              {user ? "Browse Courses" : "Get Started"}
            </button>
          </div>
          <div className="landing-plan landing-plan-premium">
            <div className="sub-recommended">Most Popular</div>
            <h3><I.Crown /> Premium</h3>
            <div className="landing-price">$19<span>/month</span></div>
            <ul>
              <li><I.Check /> Unlimited lab access</li>
              <li><I.Check /> All courses & modules</li>
              <li><I.Check /> Priority AI assistant</li>
              <li><I.Check /> Instructor classes</li>
              <li><I.Check /> Certificates</li>
            </ul>
            <button
              className="btn ba2 bf"
              onClick={() => nav(user ? "subscription" : "register")}
            >
              {user ? "Upgrade Now" : "Start Premium"}
            </button>
          </div>
        </div>
      </section>
      {/* ── CTA Banner ──────────────────────────────────────────────── */}
      <section className="ld-cta">
        <div className="ld-cta-glow" />
        <h2 className="ld-cta-h">Ready to Start Your Cyber Journey?</h2>
        <p className="ld-cta-p">Join hundreds of students mastering offensive and defensive security in real, hands-on environments.</p>
        <div className="ld-cta-btns">
          <button className="btn ba2 bl" onClick={() => nav(user ? "courses" : "register")}>
            <I.Terminal /> {user ? "Continue Training" : "Get Started Free"}
          </button>
          <button className="btn bg bl" onClick={() => nav("courses")}>
            Browse Courses <I.Right />
          </button>
        </div>
      </section>
    </div>
  );
}