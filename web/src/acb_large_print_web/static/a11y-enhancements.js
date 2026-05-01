/**
 * GLOW Accessibility Enhancements
 *
 * Adds keyboard and locale niceties that are independent of any single page:
 *   1. Pressing Escape inside an open <details> accordion collapses it and
 *      restores focus to its <summary>. This matches the WAI-ARIA Authoring
 *      Practices "disclosure" pattern keyboard expectations.
 *   2. Any <time data-utc-local> element has its text content rewritten in
 *      the user's local timezone, with a short " (your time)" suffix to make
 *      it obvious the value was converted from UTC.
 */
(function () {
    'use strict';

    // --- 1. Escape collapses <details> accordions -----------------------------
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Escape' && e.keyCode !== 27) return;
        var active = document.activeElement;
        if (!active) return;
        var details = active.closest ? active.closest('details[open]') : null;
        if (!details) return;
        // Don't hijack Escape inside form controls that have their own behavior
        // (e.g. an open <select>); the closest('details[open]') guard already
        // limits us to elements within the disclosure body.
        e.preventDefault();
        details.open = false;
        var summary = details.querySelector(':scope > summary');
        if (summary && typeof summary.focus === 'function') {
            summary.focus();
        }
    });

    // --- 2. UTC -> local time rewriting --------------------------------------
    function formatLocal(d) {
        try {
            var opts = {
                weekday: undefined,
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
                timeZoneName: 'short',
            };
            return d.toLocaleString(undefined, opts);
        } catch (err) {
            return d.toString();
        }
    }

    function rewriteTimes(root) {
        var nodes = (root || document).querySelectorAll('time[data-utc-local]');
        Array.prototype.forEach.call(nodes, function (node) {
            if (node.dataset.localized === '1') return;
            var iso = node.getAttribute('datetime') || node.getAttribute('data-utc-local');
            if (!iso) return;
            var d = new Date(iso);
            if (isNaN(d.getTime())) return;
            node.textContent = formatLocal(d);
            node.title = 'Local time (converted from UTC: ' + iso + ')';
            node.dataset.localized = '1';
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () { rewriteTimes(); });
    } else {
        rewriteTimes();
    }

    window.GLOW = window.GLOW || {};
    window.GLOW.rewriteLocalTimes = rewriteTimes;

    // --- 3. Ctrl+U / Cmd+U -- focus first visible file input -----------------
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'u' && e.key !== 'U') return;
        if (!(e.ctrlKey || e.metaKey)) return;
        var input = document.querySelector('input[type="file"]:not([disabled]):not([hidden])');
        if (!input) return;
        e.preventDefault();
        input.focus();
        if (window.GLOW && window.GLOW.toast) {
            window.GLOW.toast('File picker focused. Press Space or Enter to open.', 'info');
        }
    });

    // --- 4. Session keep-alive -- ping /health every 15 minutes when a form is present ------
    (function () {
        if (!document.querySelector('form')) return;
        var _keepAliveInterval = setInterval(function () {
            try {
                fetch('/health', { method: 'GET', credentials: 'same-origin' }).catch(function () {});
            } catch (_) {}
        }, 15 * 60 * 1000);
        // Cancel if the user navigates away cleanly
        window.addEventListener('beforeunload', function () { clearInterval(_keepAliveInterval); });
    }());
}());
