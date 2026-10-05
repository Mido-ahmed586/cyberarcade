import { useState } from "react";
import Navbar from "../components/layout/Navbar";
import I from "../components/icons/Icons";
import { PLANS, subscriptionService } from "../services/subscription.service";
import { capitalize } from "../utils/helpers";

export default function Subscription({ theme, setTheme, user, nav, onLogout, currentPage, userPlan, onPlanChange, currentStreak }) {
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState("");
  const [toastType, setToastType] = useState("info");

  const showToast = (m, type = "info") => {
    setToast(m);
    setToastType(type);
    setTimeout(() => setToast(""), 6000);
  };

  const subscribe = async (planId) => {
    if (planId === userPlan || busy) return;
    setBusy(true);

    try {
      if (planId === "free") {
        await subscriptionService.subscribeFree();
        if (onPlanChange) onPlanChange("free");
        showToast("Switched to Free plan.", "info");
        setBusy(false);
        return;
      }

      // Premium — create checkout session then redirect
      showToast("Creating checkout session...", "info");

      let checkout;
      try {
        checkout = await subscriptionService.createCheckout(planId);
      } catch (e) {
        // Log full error details to console so we can see exactly what's wrong
        console.error("[Subscription] createCheckout failed:", {
          status: e?.status,
          message: e?.message,
          original: e?.original,
          response: e?.original?.response?.data,
        });
        throw e;
      }

      if (!checkout?.checkout_url) {
        throw new Error("No checkout URL returned from server.");
      }

      showToast("Redirecting to payment page...", "success");
      setTimeout(() => {
        window.location.href = checkout.checkout_url;
      }, 600);

    } catch (e) {
      setBusy(false);

      const status = e?.status;
      const msg    = e?.message || "";

      console.error("[Subscription] error status:", status, "message:", msg);

      if (!status) {
        // No HTTP status = true network failure OR axios threw before getting a response
        showToast(`Server unreachable (${msg}). Open DevTools Console for details.`, "error");
      } else if (status === 401 || status === 403) {
        showToast("Session expired — please sign in again.", "error");
      } else if (status === 400) {
        showToast("Bad request: " + msg, "error");
      } else if (status === 404) {
        showToast("Checkout endpoint not found (404).", "error");
      } else if (status >= 500) {
        showToast(`Server error ${status}: ${msg}`, "error");
      } else {
        showToast(`Error ${status}: ${msg}`, "error");
      }
    }
  };

  return (
    <div className="pg">
      <Navbar theme={theme} setTheme={setTheme} user={user} nav={nav} onLogout={onLogout} currentPage={currentPage} currentStreak={currentStreak} />
      <div className="sub-page">
        <div className="sub-header">
          <h1>Choose Your <span className="he">Plan</span></h1>
          <p>Unlock unlimited access to all cybersecurity labs, courses, and premium features</p>
        </div>

        <div className="sub-grid">
          {PLANS.map((plan) => {
            const isCurrent = plan.id === userPlan;
            const isPremium = plan.id === "premium";
            const isLoading = busy && !isCurrent && isPremium;

            return (
              <div key={plan.id} className={`sub-card ${isPremium ? "sub-premium" : ""} ${isCurrent ? "sub-current" : ""}`}>
                {isCurrent && <div className="sub-current-badge">Current Plan</div>}
                {isPremium && !isCurrent && <div className="sub-recommended">Recommended</div>}

                <div className="sub-card-header">
                  <div className="sub-icon">{isPremium ? <I.Crown /> : <I.Shield />}</div>
                  <h2>{plan.name}</h2>
                  <div className="sub-price">
                    <span className="sub-amount">{plan.price}</span>
                    <span className="sub-period">{plan.period}</span>
                  </div>
                </div>

                <div className="sub-features">
                  {plan.features.map((f, i) => (
                    <div key={i} className="sub-feature">
                      <I.Check /> <span>{f}</span>
                    </div>
                  ))}
                  {plan.limitations.map((l, i) => (
                    <div key={`l-${i}`} className="sub-limitation">
                      <I.X /> <span>{l}</span>
                    </div>
                  ))}
                </div>

                <button
                  className={`btn ${isCurrent ? "bg" : "ba2"} bf`}
                  onClick={() => subscribe(plan.id)}
                  disabled={isCurrent || busy}
                >
                  {isLoading ? (
                    <span style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "center" }}>
                      <span className="sub-spinner" /> Processing...
                    </span>
                  ) : isCurrent ? "Current Plan"
                    : isPremium ? "Upgrade to Premium"
                    : "Switch to Free"}
                </button>
              </div>
            );
          })}
        </div>

        <div className="sub-faq">
          <h2>Frequently Asked Questions</h2>
          <div className="sub-faq-grid">
            {[
              { q: "Can I cancel anytime?", a: "Yes! You can downgrade to the Free plan at any time. Your premium access will remain until the end of the billing period." },
              { q: "What happens to my progress?", a: "Your progress, completed labs, and certificates are never lost — even if you downgrade." },
              { q: "Do I need premium for all labs?", a: "Free users can access the first 2 labs in every course. Premium unlocks all labs across the entire platform." },
              { q: "Is there a student discount?", a: "Contact your institution's instructor — they can provide class access that includes premium features." },
            ].map((faq, i) => (
              <div key={i} className="sub-faq-item">
                <h4>{faq.q}</h4>
                <p>{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {toast && (
        <div className={`toast-msg toast-${toastType}`}>
          {toastType === "error"   && <I.X />}
          {toastType === "success" && <I.Check />}
          <span>{toast}</span>
        </div>
      )}
    </div>
  );
}