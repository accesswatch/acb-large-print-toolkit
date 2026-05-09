/**
 * ai-meter.js -- live AI usage sidebar meter.
 *
 * Polls /ai/usage/ every 30 seconds and after each page AI action (signalled
 * via a CustomEvent "ai:request-complete" dispatched by feature scripts).
 * Updates the sidebar meter in place without a page reload.
 */
(function () {
  "use strict";

  var POLL_INTERVAL_MS = 30000;
  var USAGE_URL = "/ai/usage/";
  var _timer = null;

  function el(id) { return document.getElementById(id); }

  function updateMeter(data) {
    var meterEl = el("ai-meter");
    if (!meterEl) return;

    if (data.provider === "ollama") {
      var reqEl    = el("ai-meter-requests");
      var modelEl  = el("ai-meter-model");
      if (reqEl)   reqEl.textContent   = data.session_requests_today;
      if (modelEl) modelEl.textContent = data.ollama_model || "unknown";

    } else if (data.provider === "openrouter") {
      var reqEl2   = el("ai-meter-requests");
      var limitEl  = el("ai-meter-limit");
      var barEl    = el("ai-meter-bar");
      var fillEl   = el("ai-meter-bar-fill");

      if (reqEl2)  reqEl2.textContent  = data.session_requests_today;
      if (limitEl) {
        var limit = data.chat_remaining_today != null
          ? (data.session_requests_today + data.chat_remaining_today)
          : 50;
        limitEl.textContent = limit;
      }
      if (barEl && data.budget_pct_remaining != null) {
        barEl.setAttribute("aria-valuenow", data.budget_pct_remaining);
        if (fillEl) fillEl.style.width = data.budget_pct_remaining + "%";
      }
    }
  }

  function fetchUsage() {
    fetch(USAGE_URL, { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) { if (data) updateMeter(data); })
      .catch(function () { /* silent -- meter stays at last value */ });
  }

  function resetTimer() {
    if (_timer) clearTimeout(_timer);
    _timer = setTimeout(function () {
      fetchUsage();
      resetTimer();
    }, POLL_INTERVAL_MS);
  }

  // Initial fetch shortly after page load (gives Flask time to settle)
  if (el("ai-meter")) {
    setTimeout(fetchUsage, 1500);
    resetTimer();

    // Also refresh immediately after any AI feature fires its completion event
    document.addEventListener("ai:request-complete", function () {
      fetchUsage();
      resetTimer();
    });
  }
}());
