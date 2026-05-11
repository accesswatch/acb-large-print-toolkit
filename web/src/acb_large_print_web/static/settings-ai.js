(function () {
  'use strict';

  var keyInput = document.getElementById('ollama-api-key');
  var modelSel = document.getElementById('ollama-model');
  var customGrp = document.getElementById('custom-model-group');
  var customIn = document.getElementById('ollama-custom-model');
  var validateBtn = document.getElementById('validate-key-btn');
  var saveBtn = document.getElementById('save-key-btn');
  var form = document.getElementById('ai-key-form');
  var valResult = document.getElementById('validate-result');
  var statusBox = document.getElementById('ai-key-status');
  var forgetBtn = document.getElementById('forget-key-btn');
  var featuresForm = document.getElementById('ai-features-form');
  var keyValidated = false;
  var lastRequestId = '';
  var knownModels = {};
  var preferredModels = ['gemma3:4b', 'gemma3:12b', 'gpt-oss:120b', 'mistral', 'qwen3:8b', 'llama3.2'];

  if (!form || !modelSel) {
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

  function setSaveEnabled(enabled) {
    if (!saveBtn) {
      return;
    }
    saveBtn.disabled = !enabled;
    saveBtn.setAttribute('aria-disabled', enabled ? 'false' : 'true');
  }

  function invalidateValidationState() {
    keyValidated = false;
    setSaveEnabled(false);
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
        var errorMessage = data && data.error ? data.error : ('The request failed with status ' + response.status + '.');
        reportClientError('ai-http-error', errorMessage, {
          action: action,
          request_id: responseRequestId,
          status: String(response.status),
          detail: text.slice(0, 500),
          source: response.url || window.location.pathname
        });
        throw new Error(errorMessage);
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

  function resolvedModel() {
    return modelSel.value === 'other' ? customIn.value.trim() : modelSel.value;
  }

  function normalizeModel(raw) {
    return String(raw || '').trim().replace(/:latest$/, '');
  }

  function collectKnownModels() {
    Array.prototype.forEach.call(modelSel.options, function (option) {
      var value = normalizeModel(option.value);
      if (!value || value === 'other') {
        return;
      }
      knownModels[value] = {
        label: option.textContent.replace(/\s+\(recommended\)$/, ''),
        plan: option.getAttribute('data-plan') || '',
        recommended: /\(recommended\)$/.test(option.textContent)
      };
    });
  }

  function planBadge(plan) {
    if (plan === 'free') {
      return ' — Free';
    }
    if (plan === 'pro') {
      return ' — Pro plan (paid)';
    }
    if (plan === 'max') {
      return ' — Max plan (paid)';
    }
    return '';
  }

  function preferredAvailableModel(liveModels, fallback) {
    var available = {};
    liveModels.forEach(function (model) {
      available[normalizeModel(model)] = true;
    });
    for (var index = 0; index < preferredModels.length; index += 1) {
      if (available[preferredModels[index]]) {
        return preferredModels[index];
      }
    }
    return liveModels.length ? normalizeModel(liveModels[0]) : fallback;
  }

  function buildOptions(liveModels, selectedValue) {
    var available = {};
    var options = [];
    liveModels.forEach(function (raw) {
      var id = normalizeModel(raw);
      if (!id || available[id]) {
        return;
      }
      available[id] = true;
      if (knownModels[id]) {
        options.push({
          value: id,
          label: knownModels[id].label,
          plan: knownModels[id].plan,
          recommended: knownModels[id].recommended,
          unavailable: false
        });
      } else {
        options.push({
          value: id,
          label: id + ' — (from your account)',
          plan: '',
          recommended: false,
          unavailable: false
        });
      }
    });

    Object.keys(knownModels).forEach(function (id) {
      if (available[id]) {
        return;
      }
      options.push({
        value: id,
        label: knownModels[id].label + ' — not on your account',
        plan: knownModels[id].plan,
        recommended: false,
        unavailable: true
      });
    });

    options.sort(function (left, right) {
      if (left.unavailable !== right.unavailable) {
        return left.unavailable ? 1 : -1;
      }
      if (left.recommended !== right.recommended) {
        return left.recommended ? -1 : 1;
      }
      return left.label.localeCompare(right.label);
    });

    return options.map(function (item) {
      var option = document.createElement('option');
      option.value = item.value;
      option.textContent = item.label + planBadge(item.plan) + (item.recommended && !item.unavailable ? ' (recommended)' : '');
      option.selected = item.value === selectedValue;
      if (item.unavailable) {
        option.dataset.unavailable = 'true';
      }
      return option;
    });
  }

  function rebuildSelect(select, liveModels, selectedValue) {
    while (select.options.length > 0) {
      select.remove(0);
    }
    buildOptions(liveModels, selectedValue).forEach(function (option) {
      select.appendChild(option);
    });
    var otherOpt = document.createElement('option');
    otherOpt.value = 'other';
    otherOpt.textContent = 'Other / use model from your account';
    otherOpt.selected = selectedValue === 'other';
    select.appendChild(otherOpt);
  }

  function mergeModelsIntoSelects(liveModels, suggestedModel) {
    var normalized = liveModels.map(normalizeModel).filter(Boolean);
    if (!normalized.length) {
      return;
    }

    var desired = suggestedModel || preferredAvailableModel(normalized, resolvedModel());
    var currentValue = resolvedModel();
    var currentAvailable = normalized.indexOf(normalizeModel(currentValue)) !== -1;
    var selectedValue = currentAvailable ? normalizeModel(currentValue) : desired;

    rebuildSelect(modelSel, normalized, selectedValue);
    if (selectedValue && selectedValue !== 'other') {
      modelSel.value = selectedValue;
    }

    var selects = document.querySelectorAll('.feature-model-select');
    Array.prototype.forEach.call(selects, function (select) {
      var featureCurrent = normalizeModel(select.value);
      var featureSelected = normalized.indexOf(featureCurrent) !== -1 ? featureCurrent : desired;
      rebuildSelect(select, normalized, featureSelected);
      select.value = featureSelected;
    });
  }

  function updateCustomModelVisibility() {
    customGrp.hidden = modelSel.value !== 'other';
    if (!customGrp.hidden) {
      customIn.focus();
    }
  }

  collectKnownModels();
  setSaveEnabled(false);
  updateCustomModelVisibility();

  modelSel.addEventListener('change', updateCustomModelVisibility);
  keyInput.addEventListener('input', invalidateValidationState);

  validateBtn.addEventListener('click', function () {
    var key = keyInput.value.trim();
    var validateUrl = form.dataset.validateUrl;
    if (!key) {
      valResult.textContent = 'Enter your key first.';
      return;
    }

    validateBtn.disabled = true;
    validateBtn.textContent = 'Checking...';
    valResult.textContent = '';

    var fd = new FormData();
    fd.append('ollama_api_key', key);

    fetch(validateUrl, {
      method: 'POST',
      body: fd,
      credentials: 'same-origin',
      headers: buildHeaders()
    })
      .then(function (response) {
        return parseJsonResponse(response, 'validate-key');
      })
      .then(function (data) {
        if (!data.ok) {
          invalidateValidationState();
          valResult.textContent = 'Problem: ' + (data.error || 'Unknown error.');
          return;
        }
        keyValidated = true;
        setSaveEnabled(true);
        mergeModelsIntoSelects(data.models || [], normalizeModel(data.suggested_model || ''));
        valResult.textContent = 'Key accepted — ' + (data.models && data.models.length ? data.models.length + ' model(s) found on your account.' : 'no models listed yet.') + (data.suggested_model ? ' Suggested model: ' + normalizeModel(data.suggested_model) + '.' : '');
      })
      .catch(function (error) {
        invalidateValidationState();
        valResult.textContent = handleRequestFailure('validate-key', error, 'Could not reach Ollama. Check your connection.');
      })
      .finally(function () {
        validateBtn.disabled = false;
        validateBtn.textContent = 'Check key';
      });
  });

  form.addEventListener('submit', function (event) {
    var key = keyInput.value.trim();
    var model = resolvedModel();
    var saveUrl = form.dataset.saveUrl;

    event.preventDefault();
    if (!key) {
      statusBox.textContent = 'Enter your Ollama API key.';
      return;
    }
    if (!model) {
      statusBox.textContent = 'Choose or enter a model name.';
      return;
    }
    if (!keyValidated) {
      statusBox.textContent = 'Check your key before saving.';
      return;
    }

    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    var fd = new FormData();
    fd.append('ollama_api_key', key);
    fd.append('ollama_model', model);

    fetch(saveUrl, {
      method: 'POST',
      body: fd,
      credentials: 'same-origin',
      headers: buildHeaders()
    })
      .then(function (response) {
        return parseJsonResponse(response, 'save-key');
      })
      .then(function (data) {
        if (data.ok) {
          window.location.reload();
          return;
        }
        statusBox.textContent = 'Could not save: ' + (data.error || 'Unknown error.');
      })
      .catch(function (error) {
        statusBox.textContent = handleRequestFailure('save-key', error, 'Request failed. Try again.');
      })
      .finally(function () {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save and enable AI';
      });
  });

  if (forgetBtn) {
    forgetBtn.addEventListener('click', function () {
      var saveUrl = form.dataset.saveUrl;
      forgetBtn.disabled = true;
      fetch(saveUrl, {
        method: 'DELETE',
        credentials: 'same-origin',
        headers: buildHeaders()
      })
        .then(function (response) {
          return parseJsonResponse(response, 'forget-key');
        })
        .then(function () {
          window.location.reload();
        })
        .catch(function (error) {
          statusBox.textContent = handleRequestFailure('forget-key', error, 'Could not remove key. Try again.');
          forgetBtn.disabled = false;
        });
    });
  }

  if (featuresForm) {
    featuresForm.addEventListener('submit', function (event) {
      var featStatus = document.getElementById('ai-features-status');
      var saveFeatsBtn = document.getElementById('save-features-btn');
      var saveUrl = featuresForm.dataset.saveUrl;
      var fd;

      event.preventDefault();
      saveFeatsBtn.disabled = true;
      saveFeatsBtn.textContent = 'Saving...';

      fd = new FormData(featuresForm);
      ['heading_fix', 'markitdown', 'chat', 'playground'].forEach(function (key) {
        if (!fd.has('feature_' + key)) {
          fd.append('feature_' + key, '0');
        }
      });

      fetch(saveUrl, {
        method: 'POST',
        body: fd,
        credentials: 'same-origin',
        headers: buildHeaders()
      })
        .then(function (response) {
          return parseJsonResponse(response, 'save-features');
        })
        .then(function (data) {
          if (data.ok) {
            var on = data.enabled && data.enabled.length ? data.enabled.join(', ') : 'none';
            featStatus.textContent = 'Saved. Active: ' + on + '.';
            return;
          }
          featStatus.textContent = 'Could not save: ' + (data.error || 'Unknown error.');
        })
        .catch(function (error) {
          featStatus.textContent = handleRequestFailure('save-features', error, 'Request failed. Try again.');
        })
        .finally(function () {
          saveFeatsBtn.disabled = false;
          saveFeatsBtn.textContent = 'Save feature choices';
        });
    });
  }
}());
