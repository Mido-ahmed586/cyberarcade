// src/services/subscription.service.js
//
// Wraps /api/subscriptions/*. Premium upgrades go through a real checkout
// redirect (currently a sandbox page on the backend, swappable for a real
// provider — see app/routers/subscription.py).

import { api } from "./api";

/** Static plan definitions shown in the subscription UI. */
export const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    period: "forever",
    features: [
      "Access to first 2 labs per course",
      "Community forum support",
      "Basic AI assistant",
      "Progress tracking",
    ],
    limitations: [
      "Limited lab access",
      "No instructor classes",
      "Standard AI responses",
    ],
  },
  {
    id: "premium",
    name: "Premium",
    price: "$19",
    period: "/month",
    features: [
      "Unlimited access to ALL labs",
      "All courses & advanced modules",
      "Priority AI assistant",
      "Join instructor-led classes",
      "Auto-solve on all labs",
      "Priority support",
      "Certificate of completion",
    ],
    limitations: [],
  },
];

export const subscriptionService = {
  /** Get the current user's active subscription (404 if none → free). */
  getMySubscription: () => api.get("/api/subscriptions/me"),

  /**
   * Free-tier downgrade. Premium MUST go through createCheckout — the backend
   * rejects premium here on purpose so the payment step can't be bypassed.
   */
  subscribeFree: () => api.post("/api/subscriptions", { plan: "free" }),

  /**
   * Start a premium checkout session.
   * Returns { session_id, checkout_url, ... }. Caller should:
   *   window.location.href = result.checkout_url
   */
  createCheckout: (plan = "premium") =>
    api.post("/api/subscriptions/checkout", { plan }),

  /**
   * Backwards-compat wrapper used by older code paths. Free is instant;
   * premium triggers a redirect to the provider's checkout page.
   */
  subscribe: async (plan) => {
    if (plan === "free") return subscriptionService.subscribeFree();
    const checkout = await subscriptionService.createCheckout(plan);
    window.location.href = checkout.checkout_url;
    // Resolve so callers don't see a hanging promise; navigation will
    // unmount the page anyway.
    return checkout;
  },

  /** Helper: determine user plan from subscription, fallback to free. */
  getUserPlan: async () => {
    try {
      const sub = await subscriptionService.getMySubscription();
      return sub?.status === "active" ? sub.plan : "free";
    } catch {
      return "free";
    }
  },
};
