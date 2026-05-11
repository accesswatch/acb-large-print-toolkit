(function () {
  'use strict';

  var tokenEl = document.getElementById('alt-text-token');
  var statusEl = document.getElementById('alt-text-status');
  var extraInstructionEl = document.getElementById('extra-instruction');
  var generateButtons = document.querySelectorAll('.alt-text-generate-btn');
  var copyButtons = document.querySelectorAll('.alt-text-copy-btn');

  if (!tokenEl || !generateButtons.length) {
    return;
  }

  function getCsrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') || '' : '';
  }

  function setStatus(message) {
    if (statusEl) {
      statusEl.textContent = message;
    }
  }

  function requestSuggestion(button) {
    var fd = new FormData();
    var itemIndex = button.getAttribute('data-item-index') || '0';
    var target = document.getElementById('suggestion-' + itemIndex);

    fd.append('token', tokenEl.value);
    fd.append('item_index', itemIndex);
    fd.append('extra_instruction', extraInstructionEl ? extraInstructionEl.value : '');

    button.disabled = true;
    button.textContent = 'Generating...';
    setStatus('Generating alt text suggestion...');

    fetch(window.location.pathname.replace(/\/$/, '') + '/suggest', {
      method: 'POST',
      body: fd,
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': getCsrfToken() }
    })
      .then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, data: data };
        });
      })
      .then(function (payload) {
        if (!payload.ok || !payload.data || !payload.data.ok) {
          throw new Error((payload.data && payload.data.error) || 'Could not generate alt text.');
        }
        if (target) {
          target.value = payload.data.suggestion || '';
        }
        setStatus('Suggestion ready for ' + (payload.data.label || ('item ' + itemIndex)) + '.');
        document.dispatchEvent(new CustomEvent('ai:request-complete'));
      })
      .catch(function (error) {
        setStatus(error && error.message ? error.message : 'Could not generate alt text.');
      })
      .finally(function () {
        button.disabled = false;
        button.textContent = 'Generate suggestion';
      });
  }

  Array.prototype.forEach.call(generateButtons, function (button) {
    button.addEventListener('click', function () {
      requestSuggestion(button);
    });
  });

  Array.prototype.forEach.call(copyButtons, function (button) {
    button.addEventListener('click', function () {
      var targetId = button.getAttribute('data-target') || '';
      var target = document.getElementById(targetId);
      if (!target || !target.value) {
        setStatus('Nothing to copy yet for this item.');
        return;
      }
      target.select();
      target.setSelectionRange(0, target.value.length);
      navigator.clipboard.writeText(target.value)
        .then(function () {
          setStatus('Suggestion copied to clipboard.');
        })
        .catch(function () {
          setStatus('Could not copy automatically. The text is selected for manual copy.');
        });
    });
  });
}());