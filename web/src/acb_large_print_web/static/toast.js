/**
 * GLOW Toast Notification System
 *
 * Exposes window.GLOW.toast(message, type) where type is one of:
 *   'success' | 'error' | 'info' (default)
 *
 * Also wires up [data-copy-target] buttons globally for clipboard copy.
 */
(function () {
  'use strict';

  function createToast(msg, type) {
    var container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.setAttribute('aria-live', 'polite');
      container.setAttribute('aria-atomic', 'false');
      document.body.appendChild(container);
    }
    var toast = document.createElement('div');
    toast.className = 'toast toast--' + (type || 'info');
    toast.setAttribute('role', 'status');
    toast.textContent = msg;
    container.appendChild(toast);
    // Force reflow so transition plays
    void toast.offsetWidth;
    toast.classList.add('toast--visible');
    setTimeout(function () {
      toast.classList.remove('toast--visible');
      toast.addEventListener('transitionend', function () {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, { once: true });
    }, 3500);
  }

  // Expose globally
  window.GLOW = window.GLOW || {};
  window.GLOW.toast = createToast;

  // Global clipboard-copy handler for [data-copy-target] buttons
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-copy-target]');
    if (!btn) return;
    var targetId = btn.getAttribute('data-copy-target');
    var target = document.getElementById(targetId);
    if (!target) return;
    var text = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA'
      ? target.value
      : target.textContent;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        createToast('Copied to clipboard.', 'success');
        var orig = btn.textContent;
        btn.textContent = 'Copied!';
        btn.setAttribute('aria-label', 'Copied to clipboard');
        setTimeout(function () {
          btn.textContent = orig;
          btn.removeAttribute('aria-label');
        }, 2000);
      }).catch(function () {
        createToast('Copy failed. Please select and copy manually.', 'error');
      });
    } else {
      // Fallback for older browsers
      try {
        if (target.select) { target.select(); }
        document.execCommand('copy');
        createToast('Copied to clipboard.', 'success');
      } catch (err) {
        createToast('Copy failed. Please select and copy manually.', 'error');
      }
    }
  });
}());
