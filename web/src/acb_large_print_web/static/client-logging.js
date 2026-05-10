(function () {
  'use strict';

  var ENDPOINT = '/ai/client-log';

  function trim(value, limit) {
    var text = String(value || '').trim();
    if (text.length <= limit) {
      return text;
    }
    return text.slice(0, limit - 1) + '...';
  }

  function send(payload) {
    var body = JSON.stringify(payload);

    if (navigator.sendBeacon) {
      try {
        navigator.sendBeacon(ENDPOINT, new Blob([body], { type: 'application/json' }));
        return;
      } catch (error) {
        // Fall through to fetch.
      }
    }

    if (window.fetch) {
      fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        keepalive: true,
        body: body
      }).catch(function () {});
    }
  }

  function normalizePayload(kind, details) {
    var payload = details || {};
    return {
      kind: trim(kind || 'client-error', 80),
      request_id: trim(payload.request_id || payload.requestId, 80),
      action: trim(payload.action, 120),
      message: trim(payload.message || payload.detail || 'Unknown browser error', 600),
      detail: trim(payload.detail, 1200),
      source: trim(payload.source, 120),
      status: trim(payload.status, 40),
      url: trim(payload.url || window.location.href, 200),
      page: trim(payload.page || window.location.pathname, 200),
      line: trim(payload.line, 20),
      column: trim(payload.column, 20),
      stack: trim(payload.stack, 1500)
    };
  }

  window.GlowClientLogger = {
    report: function (kind, details) {
      send(normalizePayload(kind, details));
    }
  };

  window.addEventListener('error', function (event) {
    window.GlowClientLogger.report('window-error', {
      message: event.message || 'Unhandled browser error',
      source: event.filename,
      line: event.lineno,
      column: event.colno,
      stack: event.error && event.error.stack ? event.error.stack : ''
    });
  });

  window.addEventListener('unhandledrejection', function (event) {
    var reason = event.reason || {};
    window.GlowClientLogger.report('unhandled-rejection', {
      message: reason.message || String(reason || 'Unhandled promise rejection'),
      detail: typeof reason === 'string' ? reason : '',
      stack: reason.stack || ''
    });
  });
}());