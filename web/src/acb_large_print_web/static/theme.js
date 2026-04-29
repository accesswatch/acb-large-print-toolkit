/* GLOW theme controller.
 * Persists the user's preference (light / dark / auto) in localStorage,
 * resolves "auto" against prefers-color-scheme, and writes the result
 * to <html data-theme="..."> so the stylesheet can key off a single
 * attribute. The boot script in base.html applies the stored value
 * before first paint to avoid a flash; this module wires up the
 * Settings radio + Footer dropdown and keeps multiple controls in sync.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "glow_theme";
  var VALID = ["light", "dark", "auto"];
  var mql = null;
  try { mql = window.matchMedia("(prefers-color-scheme: dark)"); } catch (_) {}

  function readStored() {
    try {
      var v = window.localStorage.getItem(STORAGE_KEY);
      return VALID.indexOf(v) >= 0 ? v : "auto";
    } catch (_) { return "auto"; }
  }

  function writeStored(v) {
    try { window.localStorage.setItem(STORAGE_KEY, v); } catch (_) {}
  }

  function resolve(pref) {
    if (pref === "dark" || pref === "light") return pref;
    return mql && mql.matches ? "dark" : "light";
  }

  function apply(pref) {
    var resolved = resolve(pref);
    document.documentElement.setAttribute("data-theme", resolved);
    document.documentElement.setAttribute("data-theme-pref", pref);
  }

  function setPreference(pref) {
    if (VALID.indexOf(pref) < 0) pref = "auto";
    writeStored(pref);
    apply(pref);
    syncControls(pref);
    announce(pref);
  }

  function syncControls(pref) {
    var sel = document.querySelectorAll("[data-theme-control]");
    for (var i = 0; i < sel.length; i++) {
      var el = sel[i];
      if (el.tagName === "SELECT") {
        if (el.value !== pref) el.value = pref;
      } else if (el.type === "radio") {
        el.checked = (el.value === pref);
      }
    }
  }

  function announce(pref) {
    var live = document.getElementById("theme-status");
    if (!live) return;
    var resolved = resolve(pref);
    var msg;
    if (pref === "auto") {
      msg = "Theme set to follow system preference (currently " + resolved + ").";
    } else {
      msg = "Theme set to " + pref + ".";
    }
    live.textContent = msg;
  }

  function attach() {
    var pref = readStored();
    apply(pref);
    syncControls(pref);

    document.addEventListener("change", function (ev) {
      var t = ev.target;
      if (!t || !t.hasAttribute) return;
      if (t.hasAttribute("data-theme-control")) {
        setPreference(t.value);
      }
    });

    if (mql) {
      var handler = function () {
        if (readStored() === "auto") apply("auto");
      };
      if (typeof mql.addEventListener === "function") {
        mql.addEventListener("change", handler);
      } else if (typeof mql.addListener === "function") {
        mql.addListener(handler);
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attach);
  } else {
    attach();
  }
})();
