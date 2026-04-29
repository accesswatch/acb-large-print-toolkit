/**
 * Consent Gate Logic -- GLOW Accessibility Toolkit
 * 
 * Handles the "Terms of Use" checkbox/button synchronization.
 * Supports both standard page load and SPA content swaps.
 */
(function () {
    'use strict';

    function initConsent() {
        var agreeBox = document.getElementById('consent-agree-checkbox');
        var btn = document.getElementById('consent-continue-btn');
        var form = document.querySelector('form[method="post"]');
        var title = document.getElementById('consent-modal-title');

        if (title && !title.hasAttribute('data-focused')) {
            title.focus();
            title.setAttribute('data-focused', 'true');
        }

        if (agreeBox && btn) {
            // Sync initial state
            btn.disabled = !agreeBox.checked;

            // Handle changes
            var toggle = function () {
                btn.disabled = !agreeBox.checked;
            };

            agreeBox.removeEventListener('change', toggle);
            agreeBox.addEventListener('change', toggle);

            // Fallback for some browsers
            agreeBox.removeEventListener('click', toggle);
            agreeBox.addEventListener('click', toggle);
        }

        if (form && !form.hasAttribute('data-hooked')) {
            form.addEventListener('submit', function () {
                var statusEl = document.getElementById('consent-status');
                if (statusEl) statusEl.textContent = 'Saving your agreement\u2026';
                if (btn) {
                    btn.disabled = true;
                    btn.textContent = 'Continuing\u2026';
                }
            });
            form.setAttribute('data-hooked', 'true');
        }
    }

    // Bind to DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initConsent);
    } else {
        initConsent();
    }

    // Bind to SPA swaps
    document.addEventListener('glow:content-swapped', initConsent);
}());
