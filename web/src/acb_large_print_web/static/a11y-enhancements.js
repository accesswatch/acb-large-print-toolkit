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

    // --- 2b. Footer deploy + WCAG gate status -------------------------------
    function updateFooterHealthStatus() {
        var wcagEl = document.getElementById('footer-wcag-magic-status');
        var deployEl = document.getElementById('footer-deploy-phase');
        if (!wcagEl && !deployEl) return;

        function label(value) {
            var v = String(value || '').toLowerCase();
            if (!v || v === 'unknown') return 'checking';
            if (v === 'not-run') return 'not run for this revision';
            if (v === 'not-reported') return 'awaiting report';
            if (v === 'not-configured') return 'not configured (manual tracking only)';
            if (v === 'in_progress') return 'in progress';
            return String(value);
        }

        fetch('/health', { method: 'GET', credentials: 'same-origin' })
            .then(function (resp) {
                if (!resp.ok) throw new Error('health http ' + resp.status);
                return resp.json();
            })
            .then(function (payload) {
                var deployment = payload && payload.deployment ? payload.deployment : {};
                var gates = deployment.gates || {};
                var aa = label(gates.wcag22aa || 'unknown');
                var aaa = label(gates.wcag22aaa || 'unknown');
                var rawPhase = String(deployment.phase || '').toLowerCase();
                var rawState = String(deployment.state || '').toLowerCase();
                var phase = label(deployment.phase || 'unknown');
                var state = label(deployment.state || 'unknown');

                if (wcagEl) {
                    var note = '';
                    if (aa === 'failed' || aa === 'not run for this revision' || aa === 'awaiting report') {
                        note = ' See /status for full evidence and current check state.';
                    }
                    wcagEl.textContent = 'WCAG 2.2 AA gate: ' + aa + ', with selected AAA constellations tracked: ' + aaa + '.' + note;
                }
                if (deployEl) {
                    var updated = deployment.updated_at_utc ? ' Last update: ' + deployment.updated_at_utc + '.' : '';
                    if ((rawPhase === 'none' || rawPhase === '') && (rawState === 'idle' || rawState === '')) {
                        deployEl.textContent = 'Deployment: standing by. No active rollout right now.' + updated;
                    } else if (rawState === 'in_progress') {
                        deployEl.textContent = 'Deployment: in progress at phase ' + phase + '.' + updated;
                    } else if (rawState === 'completed') {
                        deployEl.textContent = 'Deployment: completed at phase ' + phase + '.' + updated;
                    } else if (rawState === 'failed') {
                        var detail = deployment.detail ? ' Details: ' + deployment.detail + '.' : '';
                        deployEl.textContent = 'Deployment: failed at phase ' + phase + '.' + detail + updated;
                    } else {
                        var fallbackDetail = deployment.detail ? ' Details: ' + deployment.detail + '.' : '';
                        deployEl.textContent = 'Deployment: phase ' + phase + ' (' + state + ').' + fallbackDetail + updated;
                    }
                }
            })
            .catch(function () {
                if (wcagEl) wcagEl.textContent = 'WCAG 2.2 AA gate: unavailable, with selected AAA constellations tracked: unavailable.';
                if (deployEl) deployEl.textContent = 'Deployment: unavailable';
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', updateFooterHealthStatus);
    } else {
        updateFooterHealthStatus();
    }
    window.setInterval(updateFooterHealthStatus, 30 * 1000);

    // --- 5. Cognitive profile helpers -------------------------------------
    function cognitiveModeEnabled() {
        try {
            return document.documentElement.getAttribute('data-cognitive') === 'on';
        } catch (_err) {
            return false;
        }
    }

    function applyCognitiveMode() {
        if (!cognitiveModeEnabled()) return;
        var details = document.querySelectorAll('details:not([data-keep-collapsed])');
        Array.prototype.forEach.call(details, function (d) {
            d.open = true;
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyCognitiveMode);
    } else {
        applyCognitiveMode();
    }

    window.GLOW = window.GLOW || {};
    window.GLOW.rewriteLocalTimes = rewriteTimes;
    window.GLOW.applyCognitiveMode = applyCognitiveMode;

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
                fetch('/health', { method: 'GET', credentials: 'same-origin' }).catch(function () { });
            } catch (_) { }
        }, 15 * 60 * 1000);
        // Cancel if the user navigates away cleanly
        window.addEventListener('beforeunload', function () { clearInterval(_keepAliveInterval); });
    }());

    // --- 6. Single-file helper upload buttons ------------------------------
    // Provide an explicit, keyboard-friendly action next to file inputs so
    // users do not depend on browser-native file dialog button behavior.
    function initUploadHelperButtons() {
        var inputs = document.querySelectorAll('input[type="file"]:not([multiple])');
        Array.prototype.forEach.call(inputs, function (input) {
            if (input.dataset.uploadHelperBound === '1') return;
            var form = input.form;
            if (!form) return;

            var container = document.createElement('div');
            container.className = 'upload-helper';

            var helperBtn = document.createElement('button');
            helperBtn.type = 'button';
            helperBtn.className = 'btn-secondary';
            helperBtn.textContent = 'Upload selected file';
            helperBtn.disabled = !(input.files && input.files.length > 0);

            helperBtn.addEventListener('click', function () {
                if (!input.files || input.files.length < 1) {
                    input.focus();
                    if (window.GLOW && window.GLOW.toast) {
                        window.GLOW.toast('Choose a file first, then select Upload selected file.', 'warning');
                    }
                    return;
                }
                if (typeof form.requestSubmit === 'function') {
                    form.requestSubmit();
                } else {
                    form.submit();
                }
            });

            container.appendChild(helperBtn);
            input.insertAdjacentElement('afterend', container);

            input.addEventListener('change', function () {
                helperBtn.disabled = !(input.files && input.files.length > 0);
            });

            input.dataset.uploadHelperBound = '1';
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initUploadHelperButtons);
    } else {
        initUploadHelperButtons();
    }

    // --- 7. File picker keyboard fallback (Enter to upload/submit) ---------
    // Some browser/file-dialog combinations return focus to the file input
    // after selecting a file, but do not reliably trigger the expected submit
    // path when users confirm with Enter/Space in the dialog.
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter' && e.keyCode !== 13) return;
        var active = document.activeElement;
        if (!active || active.tagName !== 'INPUT' || active.type !== 'file') return;
        if (!active.files || active.files.length < 1) return;
        var form = active.form;
        if (!form) return;

        // Allow explicit multi-select workflows to continue without auto-submit.
        if (active.multiple) return;

        e.preventDefault();
        if (typeof form.requestSubmit === 'function') {
            form.requestSubmit();
        } else {
            form.submit();
        }
    });
}());
