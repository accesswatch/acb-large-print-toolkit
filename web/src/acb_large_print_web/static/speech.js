(function () {
  "use strict";

  function byId(id) {
    return document.getElementById(id);
  }

  function getSelectedVoice() {
    var selected = document.querySelector('input[name="voice"]:checked');
    return selected ? selected.value : "";
  }

  function getFormState() {
    return {
      voice: getSelectedVoice(),
      text: textarea ? textarea.value : "",
      speed: speedInput ? parseFloat(speedInput.value || "1.0") : 1.0,
      pitch: pitchInput ? parseInt(pitchInput.value || "0", 10) : 0
    };
  }

  function persistState() {
    if (!window.glowPreferences || typeof window.glowPreferences.updateSettings !== "function") {
      return;
    }
    var state = getFormState();
    window.glowPreferences.updateSettings(function (settings) {
      settings.speech.voice = state.voice;
      settings.speech.text = state.text;
      settings.speech.speed = state.speed;
      settings.speech.pitch = state.pitch;
    });
  }

  function debounce(fn, waitMs) {
    var timer = null;
    return function () {
      var args = arguments;
      if (timer) {
        clearTimeout(timer);
      }
      timer = setTimeout(function () {
        fn.apply(null, args);
      }, waitMs);
    };
  }

  var textarea = byId("speech-text");
  var counter = byId("char-count-value");
  var debouncedPersist = debounce(persistState, 300);

  function renderCharCount() {
    if (textarea && counter) {
      counter.textContent = textarea.value.length;
    }
  }

  if (textarea && counter) {
    renderCharCount();
    textarea.addEventListener("input", function () {
      renderCharCount();
      debouncedPersist();
    });
    textarea.addEventListener("change", persistState);
  }

  var speedInput = byId("speech-speed");
  var speedValue = byId("speed-value");
  function renderSpeed() {
    if (speedInput && speedValue) {
      speedValue.textContent = parseFloat(speedInput.value).toFixed(1);
    }
  }

  if (speedInput && speedValue) {
    renderSpeed();
    speedInput.addEventListener("input", function () {
      renderSpeed();
      persistState();
    });
    speedInput.addEventListener("change", function () {
      renderSpeed();
      persistState();
    });
  }

  var pitchInput = byId("speech-pitch");
  var pitchValue = byId("pitch-value");
  function renderPitch() {
    if (pitchInput && pitchValue) {
      pitchValue.textContent = pitchInput.value;
    }
  }

  if (pitchInput && pitchValue) {
    renderPitch();
    pitchInput.addEventListener("input", function () {
      renderPitch();
      persistState();
    });
    pitchInput.addEventListener("change", function () {
      renderPitch();
      persistState();
    });
  }

  var voiceInputs = document.querySelectorAll('input[name="voice"]');
  if (voiceInputs && voiceInputs.length) {
    for (var i = 0; i < voiceInputs.length; i += 1) {
      voiceInputs[i].addEventListener("change", persistState);
    }
  }

  var previewBtn = byId("preview-btn");
  var downloadBtn = byId("download-btn");
  var audioPlayer = byId("audio-player");
  var playerWrap = byId("preview-player");
  var errorRegion = byId("preview-error");
  var statusRegion = byId("preview-status");
  var form = byId("speech-form");

  function showStatus(msg) {
    if (!statusRegion) {
      return;
    }
    statusRegion.textContent = msg;
    statusRegion.style.display = "";
  }

  function clearStatus() {
    if (!statusRegion) {
      return;
    }
    statusRegion.textContent = "";
    statusRegion.style.display = "none";
  }

  function setBusy(isBusy) {
    if (previewBtn) {
      previewBtn.disabled = !!isBusy;
    }
    if (downloadBtn) {
      downloadBtn.disabled = !!isBusy;
    }
    if (form) {
      form.setAttribute("aria-busy", isBusy ? "true" : "false");
    }
  }

  function showError(msg) {
    if (errorRegion) {
      errorRegion.textContent = msg;
      errorRegion.style.display = "";
    }
    if (playerWrap) {
      playerWrap.style.display = "none";
    }
  }

  function clearError() {
    if (errorRegion) {
      errorRegion.style.display = "none";
      errorRegion.textContent = "";
    }
  }

  function getCsrfToken() {
    var field = document.querySelector("input[name=csrf_token]");
    var meta = document.querySelector("meta[name=csrf-token]");
    return (field && field.value) || (meta && meta.content) || "";
  }

  function errorFromResponse(resp) {
    return resp.json()
      .then(function (json) {
        throw new Error(json.error || ("Server error " + resp.status));
      })
      .catch(function (err) {
        if (err instanceof SyntaxError) {
          throw new Error("Server error " + resp.status);
        }
        throw err;
      });
  }

  if (previewBtn && form && audioPlayer && playerWrap) {
    previewBtn.addEventListener("click", function () {
      clearError();
      clearStatus();
      previewBtn.textContent = "Generating preview...";
      setBusy(true);
      showStatus("Generating preview audio. This can take up to 20 seconds.");

      var slowHintTimer = setTimeout(function () {
        showStatus("Still generating preview audio. Please wait...");
      }, 5000);

      var fd = new FormData(form);
      var csrfVal = getCsrfToken();
      var previewFd = new FormData();
      previewFd.append("csrf_token", csrfVal);
      previewFd.append("voice", fd.get("voice") || "");
      previewFd.append("text", fd.get("text") || "");
      previewFd.append("speed", fd.get("speed") || "1.0");
      previewFd.append("pitch", fd.get("pitch") || "0");

      fetch(form.dataset.previewUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfVal },
        body: previewFd
      })
        .then(function (resp) {
          if (!resp.ok) {
            return errorFromResponse(resp);
          }
          return resp.blob();
        })
        .then(function (blob) {
          var url = URL.createObjectURL(blob);
          if (audioPlayer.dataset.prevObjectUrl) {
            URL.revokeObjectURL(audioPlayer.dataset.prevObjectUrl);
          }
          audioPlayer.dataset.prevObjectUrl = url;
          audioPlayer.src = url;
          playerWrap.style.display = "";
          audioPlayer.load();
          showStatus("Preview is ready. Playing audio now.");
          return audioPlayer.play();
        })
        .catch(function (err) {
          if (err && err.name === "NotAllowedError") {
            playerWrap.style.display = "";
            showStatus("Preview is ready. Press play to hear it.");
            return;
          }
          clearStatus();
          showError("Preview failed: " + (err && err.message ? err.message : err));
        })
        .finally(function () {
          clearTimeout(slowHintTimer);
          previewBtn.textContent = "Preview audio";
          setBusy(false);
        });
    });
  }
})();
