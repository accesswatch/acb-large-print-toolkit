(function () {
  'use strict';

  var form = document.getElementById('ai-key-form');
  var providerSelect = document.getElementById('ai-provider');
  var keyInput = document.getElementById('ai-api-key');
  var modelSelect = document.getElementById('ai-default-model');
  var validateBtn = document.getElementById('validate-key-btn');
  var saveBtn = document.getElementById('save-key-btn');
  var validateResult = document.getElementById('validate-result');
  var providerModelSummary = document.getElementById('provider-model-summary');
  var statusBox = document.getElementById('ai-key-status');
  var keyLink = document.getElementById('provider-key-link');
  var featuresForm = document.getElementById('ai-features-form');
  var providerCards = document.querySelectorAll('[data-provider-card]');
  var lastRequestId = '';
  var validatedProvider = '';
  var validatedKeyHash = '';
  var validatedModels = [];

  if (!form || !providerSelect || !keyInput || !modelSelect) {
    return;
  }

  function getCsrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') || '' : '';
  }

  function buildHeaders(extra) {
    var headers = extra ? Object.assign({}, extra) : {};
    var csrf = getCsrfToken();
    if (csrf) {
      headers['X-CSRFToken'] = csrf;
    }
    return headers;
  }

  function reportClientError(kind, message, extra) {
    if (!window.GlowClientLogger || typeof window.GlowClientLogger.report !== 'function') {
      return;
    }
    window.GlowClientLogger.report(kind, Object.assign({
      page: window.location.pathname,
      message: message
    }, extra || {}));
  }

  function parseJsonResponse(response, action) {
    var responseRequestId = response.headers.get('X-Request-ID') || '';
    if (responseRequestId) {
      lastRequestId = responseRequestId;
    }
    return response.text().then(function (text) {
      var data = null;
      if (text) {
        try {
          data = JSON.parse(text);
        } catch (parseError) {
          reportClientError('ai-response-parse', 'AI settings response was not valid JSON.', {
            action: action,
            request_id: responseRequestId,
            status: String(response.status),
            detail: text.slice(0, 500),
            source: response.url || window.location.pathname
          });
          throw new Error('The server returned an unreadable response.');
        }
      }

      if (!response.ok) {
        throw new Error(data && data.error ? data.error : ('The request failed with status ' + response.status + '.'));
      }

      return data || {};
    });
  }

  function handleRequestFailure(action, error, fallbackMessage) {
    var message = error && error.message ? error.message : fallbackMessage;
    var withRef = lastRequestId ? (message + ' (Ref: ' + lastRequestId + ')') : message;
    reportClientError('ai-fetch-failure', message, {
      action: action,
      request_id: lastRequestId,
      detail: error && error.stack ? error.stack : '',
      source: window.location.pathname
    });
    return withRef;
  }

  function updateProviderLink() {
    var option = providerSelect.options[providerSelect.selectedIndex];
    if (!option || !keyLink) {
      return;
    }
    keyLink.href = option.getAttribute('data-key-url') || '#';
    keyLink.textContent = 'Open key page for ' + option.textContent;
  }

  function setSaveEnabled(enabled) {
    saveBtn.disabled = !enabled;
    saveBtn.setAttribute('aria-disabled', enabled ? 'false' : 'true');
  }

  function invalidateValidationState() {
    validatedProvider = '';
    validatedKeyHash = '';
    validatedModels = [];
    setSaveEnabled(false);
  }

  function rebuildModelSelect(models, selectedValue) {
    while (modelSelect.options.length > 0) {
      modelSelect.remove(0);
    }
    if (!models || !models.length) {
      modelSelect.appendChild(new Option('Check a key to load models', ''));
      return;
    }
    models.forEach(function (model) {
      var label = model.name || model.id;
      if (model.capabilities && model.capabilities.vision) {
        label += ' -- vision';
      }
      if (model.capabilities && model.capabilities.audio_transcription) {
        label += ' -- audio';
      }
      if (model.input_per_million != null && model.output_per_million != null) {
        label += ' (' + model.input_per_million + '/' + model.output_per_million + ' per 1M)';
      }
      modelSelect.appendChild(new Option(label, model.id, false, model.id === selectedValue));
    });
  }

  function providerLabel() {
    return providerSelect.options[providerSelect.selectedIndex].textContent;
  }

  function validateProviderKey() {
    var provider = providerSelect.value;
    var apiKey = keyInput.value.trim();
    var fd = new FormData();

    if (!apiKey) {
      validateResult.textContent = 'Enter your key first.';
      return;
    }

    fd.append('provider', provider);
    fd.append('api_key', apiKey);
    validateBtn.disabled = true;
    validateBtn.textContent = 'Checking...';
    validateResult.textContent = '';

    fetch(form.dataset.validateUrl, {
      method: 'POST',
      body: fd,
      credentials: 'same-origin',
      headers: buildHeaders()
    })
      .then(function (response) { return parseJsonResponse(response, 'validate-key'); })
      .then(function (data) {
        if (!data.ok) {
          invalidateValidationState();
          validateResult.textContent = 'Problem: ' + (data.error || 'Unknown error.');
          return;
        }
        validatedProvider = provider;
        validatedModels = data.models || [];
        setSaveEnabled(true);
        rebuildModelSelect(validatedModels, data.suggested_model || '');
        validateResult.textContent = providerLabel() + ' key accepted.';
        providerModelSummary.textContent = (validatedModels.length ? (validatedModels.length + ' compatible model(s) found.') : 'No models returned.') + (data.suggested_model ? (' Suggested default: ' + data.suggested_model + '.') : '');
      })
      .catch(function (error) {
        invalidateValidationState();
        validateResult.textContent = handleRequestFailure('validate-key', error, 'Could not validate this provider key.');
      })
      .finally(function () {
        validateBtn.disabled = false;
        validateBtn.textContent = 'Check key';
      });
  }

  function saveProvider(event) {
    var provider = providerSelect.value;
    var apiKey = keyInput.value.trim();
    var fd = new FormData();

    event.preventDefault();
    if (!apiKey) {
      statusBox.textContent = 'Enter an API key.';
      return;
    }
    if (validatedProvider !== provider) {
      statusBox.textContent = 'Check the selected provider key before saving.';
      return;
    }

    fd.append('provider', provider);
    fd.append('api_key', apiKey);
    fd.append('default_model', modelSelect.value || '');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    fetch(form.dataset.saveUrl, {
      method: 'POST',
      body: fd,
      credentials: 'same-origin',
      headers: buildHeaders()
    })
      .then(function (response) { return parseJsonResponse(response, 'save-key'); })
      .then(function (data) {
        if (data.ok) {
          window.location.reload();
          return;
        }
        statusBox.textContent = 'Could not save: ' + (data.error || 'Unknown error.');
      })
      .catch(function (error) {
        statusBox.textContent = handleRequestFailure('save-key', error, 'Could not save this provider.');
      })
      .finally(function () {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save provider';
      });
  }

  function formatDuration(totalSeconds) {
    var seconds = Math.max(0, Number(totalSeconds || 0));
    var hours = Math.floor(seconds / 3600);
    var minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return hours + 'h ' + minutes + 'm remaining';
    }
    if (minutes > 0) {
      return minutes + 'm remaining';
    }
    return Math.max(0, seconds) + 's remaining';
  }

  function bindProviderCard(card) {
    var countdown = card.querySelector('.provider-session-countdown');
    var extendBtn = card.querySelector('.provider-session-extend-btn');
    var removeBtn = card.querySelector('.provider-remove-btn');
    var status = card.querySelector('.provider-session-status');
    var expiryMs = 0;
    var timer = null;

    function renderCountdown() {
      var secondsRemaining = Math.max(0, Math.floor((expiryMs - Date.now()) / 1000));
      if (!expiryMs || secondsRemaining <= 0) {
        countdown.textContent = 'Expired';
        if (extendBtn) {
          extendBtn.disabled = true;
        }
        return;
      }
      countdown.textContent = formatDuration(secondsRemaining);
      if (extendBtn) {
        extendBtn.disabled = false;
      }
    }

    function startTimer() {
      if (timer) {
        clearInterval(timer);
      }
      renderCountdown();
      timer = setInterval(renderCountdown, 1000);
    }

    function fetchSession() {
      var panel = card.querySelector('.provider-session-panel');
      if (!panel) {
        return;
      }
      fetch(panel.dataset.sessionUrl, {
        method: 'GET',
        credentials: 'same-origin',
        headers: buildHeaders()
      })
        .then(function (response) { return parseJsonResponse(response, 'session-status'); })
        .then(function (data) {
          expiryMs = data && data.expires_utc ? Date.parse(data.expires_utc) : 0;
          startTimer();
        })
        .catch(function () {
          countdown.textContent = 'Could not load';
        });
    }

    if (extendBtn) {
      extendBtn.addEventListener('click', function () {
        var panel = card.querySelector('.provider-session-panel');
        extendBtn.disabled = true;
        status.textContent = 'Extending key session…';
        fetch(panel.dataset.extendUrl, {
          method: 'POST',
          credentials: 'same-origin',
          headers: buildHeaders()
        })
          .then(function (response) { return parseJsonResponse(response, 'extend-session'); })
          .then(function (data) {
            expiryMs = data && data.expires_utc ? Date.parse(data.expires_utc) : 0;
            startTimer();
            status.textContent = 'Key session extended.';
          })
          .catch(function (error) {
            status.textContent = handleRequestFailure('extend-session', error, 'Could not extend the key session.');
          });
      });
    }

    if (removeBtn) {
      removeBtn.addEventListener('click', function () {
        var provider = removeBtn.getAttribute('data-provider') || '';
        var url = removeBtn.getAttribute('data-remove-url') + '?provider=' + encodeURIComponent(provider);
        removeBtn.disabled = true;
        fetch(url, {
          method: 'DELETE',
          credentials: 'same-origin',
          headers: buildHeaders()
        })
          .then(function (response) { return parseJsonResponse(response, 'remove-provider'); })
          .then(function () {
            window.location.reload();
          })
          .catch(function (error) {
            status.textContent = handleRequestFailure('remove-provider', error, 'Could not remove this provider.');
            removeBtn.disabled = false;
          });
      });
    }

    fetchSession();
  }

  function saveFeatureBindings(event) {
    var featStatus = document.getElementById('ai-features-status');
    var saveBtnFeatures = document.getElementById('save-features-btn');
    var fd = new FormData(featuresForm);

    event.preventDefault();
    saveBtnFeatures.disabled = true;
    saveBtnFeatures.textContent = 'Saving...';

    ['heading_fix', 'markitdown', 'playground', 'alt_text', 'whisperer', 'chat'].forEach(function (key) {
      if (!fd.has('feature_' + key)) {
        fd.append('feature_' + key, '0');
      }
    });

    fetch(featuresForm.dataset.saveUrl, {
      method: 'POST',
      body: fd,
      credentials: 'same-origin',
      headers: buildHeaders()
    })
      .then(function (response) { return parseJsonResponse(response, 'save-features'); })
      .then(function (data) {
        if (data.ok) {
          featStatus.textContent = 'Saved. Active: ' + ((data.enabled && data.enabled.length) ? data.enabled.join(', ') : 'none') + '.';
          return;
        }
        featStatus.textContent = 'Could not save: ' + (data.error || 'Unknown error.');
      })
      .catch(function (error) {
        featStatus.textContent = handleRequestFailure('save-features', error, 'Could not save feature choices.');
      })
      .finally(function () {
        saveBtnFeatures.disabled = false;
        saveBtnFeatures.textContent = 'Save feature choices';
      });
  }

  updateProviderLink();
  setSaveEnabled(false);
  providerSelect.addEventListener('change', function () {
    updateProviderLink();
    invalidateValidationState();
    rebuildModelSelect([], '');
    validateResult.textContent = '';
    providerModelSummary.textContent = '';
  });
  keyInput.addEventListener('input', invalidateValidationState);
  validateBtn.addEventListener('click', validateProviderKey);
  form.addEventListener('submit', saveProvider);

  Array.prototype.forEach.call(providerCards, bindProviderCard);
  if (featuresForm) {
    featuresForm.addEventListener('submit', saveFeatureBindings);
  }
}());