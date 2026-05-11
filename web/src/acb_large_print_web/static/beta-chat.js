(function () {
  'use strict';

  var form = document.getElementById('playground-form');
  var textarea = document.getElementById('playground-message');
  var sendBtn = document.getElementById('send-btn');
  var clearBtn = document.getElementById('clear-btn');
  var regenBtn = document.getElementById('regen-btn');
  var stopBtn = document.getElementById('stop-btn');
  var modelSelect = document.getElementById('playground-model-select');
  var quotaBox = document.getElementById('playground-quota');
  var templateBtns = document.querySelectorAll('.template-btn');
  var log = document.getElementById('conversation-log');
  var status = document.getElementById('playground-status');
  var progressAlert = document.getElementById('playground-progress-alert');
  var completionAlert = document.getElementById('playground-complete-alert');
  var typing = document.getElementById('typing-indicator');
  var charCount = document.getElementById('playground-char-count');
  var emptyMsg = document.getElementById('empty-log-msg');
  var activeModel = document.getElementById('active-model');
  var model = activeModel && activeModel.textContent ? activeModel.textContent : '';
  var maxLen = 3000;
  var activeStreamController = null;
  var progressAnnouncementTimer = null;
  var longProgressThresholdMs = 5000;
  var longResponseThresholdMs = 8000;

  if (!form || !textarea || !log) {
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

  function setStatus(message, kind) {
    status.textContent = message;
    status.className = 'playground-status' + (kind ? ' playground-status--' + kind : '');
  }

  function clearStatus() {
    status.textContent = '';
    status.className = 'playground-status';
  }

  function announceCompletionIfDelayed(startedAt) {
    if (!completionAlert || !startedAt) {
      return;
    }
    if ((Date.now() - startedAt) < longResponseThresholdMs) {
      return;
    }
    completionAlert.textContent = '';
    window.setTimeout(function () {
      completionAlert.textContent = 'AI response received.';
      window.setTimeout(function () {
        completionAlert.textContent = '';
      }, 1500);
    }, 50);
  }

  function clearProgressAnnouncement() {
    if (progressAnnouncementTimer) {
      window.clearTimeout(progressAnnouncementTimer);
      progressAnnouncementTimer = null;
    }
    if (progressAlert) {
      progressAlert.textContent = '';
    }
  }

  function scheduleProgressAnnouncement() {
    clearProgressAnnouncement();
    if (!progressAlert) {
      return;
    }
    progressAnnouncementTimer = window.setTimeout(function () {
      progressAlert.textContent = '';
      window.setTimeout(function () {
        progressAlert.textContent = 'AI response still in progress.';
      }, 50);
    }, longProgressThresholdMs);
  }

  function setStopVisible(visible) {
    if (!stopBtn) {
      return;
    }
    stopBtn.hidden = !visible;
    stopBtn.disabled = !visible;
  }

  function escapeHtml(text) {
    return String(text || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function notifyAiRequestComplete() {
    document.dispatchEvent(new CustomEvent('ai:request-complete'));
  }

  function ensureAssistantMeta(article, modelName) {
    var meta = article.querySelector('.message__meta');
    var modelEl;
    var copyBtn;
    if (!meta) {
      meta = document.createElement('div');
      meta.className = 'message__meta';
      modelEl = document.createElement('span');
      modelEl.className = 'message__model';
      copyBtn = document.createElement('button');
      copyBtn.type = 'button';
      copyBtn.className = 'copy-btn';
      copyBtn.setAttribute('aria-label', 'Copy this response to clipboard');
      copyBtn.setAttribute('title', 'Copy response');
      copyBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><rect x="4" y="4" width="9" height="11" rx="1" stroke="currentColor" stroke-width="1.5" fill="none"></rect><path d="M3 3V2a1 1 0 011-1h7a1 1 0 011 1v9a1 1 0 01-1 1h-1" stroke="currentColor" stroke-width="1.5" fill="none"></path></svg> Copy response';
      meta.appendChild(modelEl);
      meta.appendChild(copyBtn);
      article.appendChild(meta);
    }
    modelEl = meta.querySelector('.message__model');
    if (modelEl) {
      modelEl.textContent = 'Model: ' + (modelName || model || '');
    }
    return meta;
  }

  function appendMessage(role, text, modelName) {
    var article = document.createElement('article');
    var heading = document.createElement(role === 'user' ? 'h3' : 'h4');
    var body = document.createElement('div');

    if (emptyMsg) {
      emptyMsg.remove();
      emptyMsg = null;
    }

    article.className = 'message message--' + role;
    heading.className = 'message__heading';
    body.className = 'message__body';
    body.textContent = text;

    if (role === 'user') {
      heading.textContent = 'You asked';
    } else {
      heading.textContent = 'AI response';
    }

    article.appendChild(heading);
    article.appendChild(body);
    if (role !== 'user') {
      ensureAssistantMeta(article, modelName);
    }
    log.appendChild(article);
    log.scrollTop = log.scrollHeight;
    log.focus();
    return article;
  }

  function appendThinkingMessage(modelName) {
    var article = appendMessage('assistant', 'Thinking…', modelName);
    article.classList.add('message--thinking');
    log.setAttribute('aria-busy', 'true');
    return article;
  }

  function setAssistantContent(article, text, modelName) {
    var body;
    if (!article) {
      return;
    }
    article.classList.remove('message--thinking');
    body = article.querySelector('.message__body');
    if (body) {
      body.textContent = text;
    }
    ensureAssistantMeta(article, modelName || model || '');
  }

  function parseSseEvents(buffer, onEvent) {
    var parts = buffer.split('\n\n');
    var remainder = parts.pop() || '';
    parts.forEach(function (block) {
      var dataLines = [];
      block.split('\n').forEach(function (line) {
        if (line.indexOf('data:') === 0) {
          dataLines.push(line.slice(5).trim());
        }
      });
      if (!dataLines.length) {
        return;
      }
      try {
        onEvent(JSON.parse(dataLines.join('\n')));
      } catch (error) {
        // Ignore malformed event blocks.
      }
    });
    return remainder;
  }

  function setTyping(visible) {
    if (typing) {
      typing.hidden = !visible;
      typing.setAttribute('aria-hidden', visible ? 'false' : 'true');
    }
    if (log) {
      log.setAttribute('aria-busy', visible ? 'true' : 'false');
    }
    if (sendBtn) {
      sendBtn.disabled = visible;
    }
    textarea.disabled = visible;
  }

  function renderQuota(quota) {
    var used = Number(quota.chat_turns_today || 0);
    var limit = Number(quota.chat_daily_limit || 0);
    var pct = limit > 0 ? Math.round((used / limit) * 100) : 0;
    if (!quotaBox) {
      return;
    }
    quotaBox.className = 'playground-quota';
    if (pct >= 80) {
      quotaBox.classList.add('playground-quota--warn');
    }
    quotaBox.textContent = 'Session usage: ' + used + '/' + limit + ' chat turns today' + (pct >= 80 ? ' (near limit)' : '');
  }

  function fetchQuota() {
    fetch(form.dataset.quotaUrl, { credentials: 'same-origin' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (data && data.ok && data.quota) {
          renderQuota(data.quota);
        }
      })
      .catch(function () {});
  }

  function refreshCharCounter() {
    var remaining = maxLen - textarea.value.length;
    if (!charCount) {
      return;
    }
    charCount.textContent = remaining + ' characters remaining';
    charCount.classList.toggle('char-count--warn', remaining < 100);
  }

  function streamReply(message, pendingAssistant, startedAt) {
    activeStreamController = new AbortController();
    return fetch(form.dataset.streamUrl, {
      method: 'POST',
      headers: buildHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'same-origin',
      body: JSON.stringify({ message: message }),
      signal: activeStreamController.signal
    }).then(function (response) {
      if (!response.ok) {
        return response.json().then(function (data) {
          throw new Error(data.error || ('Server error ' + response.status));
        });
      }
      if (!response.body || typeof response.body.getReader !== 'function') {
        throw new Error('Streaming is not supported in this browser session.');
      }
      var reader = response.body.getReader();
      var decoder = new TextDecoder('utf-8');
      var buffer = '';
      var assembled = '';
      var streamedModel = model;

      function handleEvent(evt) {
        if (!evt || !evt.type) {
          return;
        }
        if (evt.model) {
          streamedModel = evt.model;
        }
        if (evt.type === 'token') {
          assembled += evt.token || '';
          setAssistantContent(pendingAssistant, assembled, streamedModel);
          return;
        }
        if (evt.type === 'done') {
          assembled = evt.reply || assembled;
          setAssistantContent(pendingAssistant, assembled, streamedModel);
          if (activeModel && streamedModel) {
            activeModel.textContent = streamedModel;
          }
          clearProgressAnnouncement();
          notifyAiRequestComplete();
          announceCompletionIfDelayed(startedAt);
          setStatus('Response received.', 'success');
          window.setTimeout(clearStatus, 3000);
          return;
        }
        if (evt.type === 'error') {
          throw new Error(evt.error || 'Streaming failed.');
        }
      }

      function pump() {
        return reader.read().then(function (result) {
          if (result.done) {
            return;
          }
          buffer += decoder.decode(result.value, { stream: true });
          buffer = parseSseEvents(buffer, handleEvent);
          return pump();
        });
      }

      return pump();
    }).finally(function () {
      activeStreamController = null;
    });
  }

  function legacyReply(message, pendingAssistant, startedAt) {
    return fetch(form.dataset.sendUrl, {
      method: 'POST',
      headers: buildHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'same-origin',
      body: JSON.stringify({ message: message })
    })
      .then(function (response) {
        return response.json().then(function (data) {
          if (!response.ok || !data.ok) {
            throw new Error(data.error || ('Server error ' + response.status));
          }
          return data;
        });
      })
      .then(function (data) {
        setAssistantContent(pendingAssistant, data.reply || '', data.model || model);
        if (data.model) {
          model = data.model;
          if (activeModel) {
            activeModel.textContent = data.model;
          }
          if (modelSelect) {
            modelSelect.value = data.model;
          }
        }
        notifyAiRequestComplete();
        clearProgressAnnouncement();
        announceCompletionIfDelayed(startedAt);
        setStatus('Response received.', 'success');
        window.setTimeout(clearStatus, 3000);
      });
  }

  function flashCopied(btn) {
    var original = btn.innerHTML;
    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M2 8l4 4 8-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"></path></svg> Copied!';
    btn.classList.add('copy-btn--copied');
    btn.setAttribute('aria-label', 'Copied to clipboard');
    window.setTimeout(function () {
      btn.innerHTML = original;
      btn.classList.remove('copy-btn--copied');
      btn.setAttribute('aria-label', 'Copy this response to clipboard');
    }, 2000);
  }

  function clearConversation() {
    fetch(form.dataset.clearUrl, {
      method: 'POST',
      credentials: 'same-origin',
      headers: buildHeaders()
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        var placeholder;
        if (!data.ok) {
          throw new Error('Could not clear conversation.');
        }
        while (log.firstChild) {
          log.removeChild(log.firstChild);
        }
        placeholder = document.createElement('p');
        placeholder.id = 'empty-log-msg';
        placeholder.className = 'conversation-log__empty';
        placeholder.textContent = 'Conversation cleared. Start a new one below.';
        log.appendChild(placeholder);
        emptyMsg = placeholder;
        log.removeAttribute('aria-busy');
        setStatus('Conversation cleared.', 'info');
        window.setTimeout(clearStatus, 3000);
        textarea.focus();
        fetchQuota();
      })
      .catch(function () {
        setStatus('Could not clear conversation. Please try again.', 'error');
      });
  }

  textarea.addEventListener('input', refreshCharCounter);
  textarea.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    }
  });

  form.addEventListener('submit', function (event) {
    var message = textarea.value.trim();
    var pendingAssistant;
    var startedAt;

    event.preventDefault();
    if (!message) {
      setStatus('Please type a message before sending.', 'error');
      textarea.focus();
      return;
    }
    if (message.length > maxLen) {
      setStatus('Message is too long. Please shorten it to ' + maxLen + ' characters.', 'error');
      return;
    }

    clearStatus();
    appendMessage('user', message, null);
    textarea.value = '';
    refreshCharCounter();
    setTyping(true);
    setStopVisible(true);
    pendingAssistant = appendThinkingMessage(model);
    startedAt = Date.now();
    scheduleProgressAnnouncement();

    streamReply(message, pendingAssistant, startedAt)
      .catch(function (error) {
        if (error && error.name === 'AbortError') {
          clearProgressAnnouncement();
          setStatus('Generation stopped.', 'info');
          return;
        }
        setStatus('Streaming unavailable, using standard response...', 'info');
        return legacyReply(message, pendingAssistant, startedAt);
      })
      .catch(function (error) {
        var msg = error && error.message ? error.message : 'Something went wrong. Please try again.';
        clearProgressAnnouncement();
        setStatus('⚠ ' + msg, 'error');
        log.scrollTop = log.scrollHeight;
      })
      .finally(function () {
        clearProgressAnnouncement();
        setTyping(false);
        setStopVisible(false);
        log.removeAttribute('aria-busy');
        textarea.focus();
        fetchQuota();
      });
  });

  if (stopBtn) {
    stopBtn.addEventListener('click', function () {
      if (activeStreamController) {
        activeStreamController.abort();
      }
    });
  }

  if (regenBtn) {
    regenBtn.addEventListener('click', function () {
      var startedAt = Date.now();
      scheduleProgressAnnouncement();
      regenBtn.disabled = true;
      fetch(form.dataset.regenUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers: buildHeaders()
      })
        .then(function (response) { return response.json(); })
        .then(function (data) {
          if (!data.ok) {
            throw new Error(data.error || 'Could not regenerate response.');
          }
          appendMessage('assistant', data.reply || '', data.model || model);
          if (data.model) {
            model = data.model;
            if (activeModel) {
              activeModel.textContent = data.model;
            }
            if (modelSelect) {
              modelSelect.value = data.model;
            }
          }
            notifyAiRequestComplete();
          clearProgressAnnouncement();
          announceCompletionIfDelayed(startedAt);
          setStatus('Response regenerated.', 'success');
          window.setTimeout(clearStatus, 3000);
          fetchQuota();
        })
        .catch(function (error) {
          var msg = error && error.message ? error.message : 'Could not regenerate response.';
          clearProgressAnnouncement();
          setStatus('⚠ ' + msg, 'error');
        })
        .finally(function () {
          clearProgressAnnouncement();
          regenBtn.disabled = false;
        });
    });
  }

  if (modelSelect) {
    modelSelect.addEventListener('change', function () {
      var selected = modelSelect.value;
      fetch(modelSelect.dataset.modelUrl, {
        method: 'POST',
        headers: buildHeaders({ 'Content-Type': 'application/json' }),
        credentials: 'same-origin',
        body: JSON.stringify({ model: selected })
      })
        .then(function (response) { return response.json(); })
        .then(function (data) {
          if (!data.ok) {
            throw new Error(data.error || 'Could not change model.');
          }
          model = data.model || selected;
          if (activeModel) {
            activeModel.textContent = model;
          }
          setStatus('Model updated for playground.', 'info');
          window.setTimeout(clearStatus, 2000);
        })
        .catch(function (error) {
          var msg = error && error.message ? error.message : 'Could not change model.';
          setStatus('⚠ ' + msg, 'error');
        });
    });
  }

  Array.prototype.forEach.call(templateBtns, function (btn) {
    btn.addEventListener('click', function () {
      var snippet = btn.getAttribute('data-template') || '';
      var current = textarea.value.trim();
      textarea.value = current ? (current + '\n\n' + snippet) : snippet;
      textarea.focus();
      refreshCharCounter();
    });
  });

  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      if (window.confirm('Clear the entire conversation? This cannot be undone.')) {
        clearConversation();
      }
    });
  }

  log.addEventListener('click', function (event) {
    var btn = event.target.closest('.copy-btn');
    var article;
    var bodyEl;
    var text;
    if (!btn) {
      return;
    }
    article = btn.closest('article.message--assistant');
    if (!article) {
      return;
    }
    bodyEl = article.querySelector('.message__body');
    if (!bodyEl) {
      return;
    }
    text = bodyEl.textContent || '';
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        flashCopied(btn);
      }).catch(function () {
        setStatus('Could not copy to clipboard.', 'error');
      });
      return;
    }
    setStatus('Copy not supported in this browser.', 'error');
  });

  log.scrollTop = log.scrollHeight;
  fetchQuota();
  refreshCharCounter();
}());