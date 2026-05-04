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

  function buildFormData(includeDocument) {
    var fd = new FormData();
    var csrf = getCsrfToken();
    fd.append("csrf_token", csrf);
    fd.append("voice", getSelectedVoice());
    fd.append("text", textarea ? textarea.value : "");
    fd.append("speed", speedInput ? speedInput.value : "1.0");
    fd.append("pitch", pitchInput ? pitchInput.value : "0");
    if (documentTokenInput) {
      fd.append("token", documentTokenInput.value || "");
    }
    if (documentPrefillInput) {
      fd.append("prefill", documentPrefillInput.value || "0");
    }
    if (includeDocument && documentInput && documentInput.files && documentInput.files[0]) {
      fd.append("document", documentInput.files[0]);
    }
    return fd;
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

  function toDuration(seconds) {
    var s = Math.max(0, Math.round(seconds || 0));
    if (s < 60) {
      return s + " seconds";
    }
    var mins = Math.floor(s / 60);
    var rem = s % 60;
    if (mins < 60) {
      return rem ? (mins + "m " + rem + "s") : (mins + " minutes");
    }
    var hours = Math.floor(mins / 60);
    var minsRem = mins % 60;
    return minsRem ? (hours + "h " + minsRem + "m") : (hours + " hours");
  }

  function startTimedAnnouncements(statusFn, estimateSeconds, intervalSeconds) {
    var start = Date.now();
    var intervalMs = Math.max(5000, Math.round((intervalSeconds || 15) * 1000));
    var timer = window.setInterval(function () {
      var elapsed = Math.round((Date.now() - start) / 1000);
      statusFn("Still working... about " + toDuration(elapsed) + " elapsed (estimated " + toDuration(estimateSeconds) + ").");
    }, intervalMs);
    return function stop() {
      window.clearInterval(timer);
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
  function normalizeVoiceSelection() {
    if (!voiceInputs || !voiceInputs.length) {
      return;
    }

    var checked = [];
    for (var i = 0; i < voiceInputs.length; i += 1) {
      if (voiceInputs[i].checked) {
        checked.push(voiceInputs[i]);
      }
    }

    if (checked.length > 1) {
      for (var j = 1; j < checked.length; j += 1) {
        checked[j].checked = false;
      }
      return;
    }

    if (checked.length === 0) {
      for (var k = 0; k < voiceInputs.length; k += 1) {
        if (!voiceInputs[k].disabled) {
          voiceInputs[k].checked = true;
          return;
        }
      }
    }
  }

  function restoreVoiceSelectionFromSettings() {
    if (!window.glowPreferences || typeof window.glowPreferences.loadSettings !== "function") {
      normalizeVoiceSelection();
      return;
    }
    var settings = window.glowPreferences.loadSettings();
    var wanted = settings && settings.speech && settings.speech.voice ? settings.speech.voice : "";
    var found = false;

    if (wanted && voiceInputs && voiceInputs.length) {
      for (var i = 0; i < voiceInputs.length; i += 1) {
        if (!voiceInputs[i].disabled && voiceInputs[i].value === wanted) {
          voiceInputs[i].checked = true;
          found = true;
          break;
        }
      }
    }

    if (!found) {
      normalizeVoiceSelection();
    }
  }

  if (voiceInputs && voiceInputs.length) {
    for (var i = 0; i < voiceInputs.length; i += 1) {
      voiceInputs[i].addEventListener("change", function () {
        normalizeVoiceSelection();
        persistState();
      });
    }
    restoreVoiceSelectionFromSettings();
    normalizeVoiceSelection();
  }

  var previewBtn = byId("preview-btn");
  var downloadBtn = byId("download-btn");
  var nextDocumentBtn = byId("next-document-btn");
  var documentPreviewBtn = byId("document-preview-btn");
  var documentGoBtn = byId("document-go-btn");
  var documentAfterPrepareActions = byId("document-after-prepare-actions");
  var documentInput = byId("speech-document");
  var documentTokenInput = byId("speech-document-token");
  var documentPrefillInput = byId("speech-document-prefill");
  var documentEstimateWrap = byId("document-estimate");
  var documentEstimateText = byId("document-estimate-text");
  var documentStatus = byId("document-status");
  var documentError = byId("document-error");
  var audioPlayer = byId("audio-player");
  var playerWrap = byId("preview-player");
  var listenLivePlayer = byId("listen-live-player");
  var listenLiveStatus = byId("listen-live-status");
  var listenLiveProgressWrap = byId("listen-live-progress-wrap");
  var listenLiveProgressBar = byId("listen-live-progress-bar");
  var listenLiveStopBtn = byId("listen-live-stop-btn");
  var errorRegion = byId("preview-error");
  var statusRegion = byId("preview-status");
  var form = byId("speech-form");

  var preparedDocument = null;
  var baseNextDisabled = !!(nextDocumentBtn && nextDocumentBtn.hasAttribute("disabled"));
  var basePreviewDisabled = !!(documentPreviewBtn && documentPreviewBtn.hasAttribute("disabled"));
  var baseGoDisabled = !!(documentGoBtn && documentGoBtn.hasAttribute("disabled"));

  // Listen Live state
  var listenLiveActive = false;
  var listenLiveAbortController = null;

  function wireSpaceActivation(button) {
    if (!button) {
      return;
    }
    button.addEventListener("keydown", function (e) {
      if (e.key !== " " && e.code !== "Space") {
        return;
      }
      e.preventDefault();
      button.dataset.spacePressed = "1";
    });
    button.addEventListener("keyup", function (e) {
      if (e.key !== " " && e.code !== "Space") {
        return;
      }
      if (button.dataset.spacePressed !== "1") {
        return;
      }
      e.preventDefault();
      button.dataset.spacePressed = "";
      if (!button.disabled) {
        button.click();
      }
    });
  }

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

  function updateDocumentActionState(isBusy) {
    var canPrepare = false;
    var showPreparedActions = !!preparedDocument;
    if (documentTokenInput && documentTokenInput.value) {
      canPrepare = true;
    }
    if (documentInput && documentInput.files && documentInput.files[0]) {
      canPrepare = true;
    }

    if (nextDocumentBtn) {
      nextDocumentBtn.disabled = !!isBusy || baseNextDisabled || !canPrepare;
    }
    if (documentPreviewBtn) {
      documentPreviewBtn.disabled = !!isBusy || basePreviewDisabled || !preparedDocument;
    }
    if (documentGoBtn) {
      documentGoBtn.disabled = !!isBusy || baseGoDisabled || !preparedDocument;
    }
    if (documentAfterPrepareActions) {
      documentAfterPrepareActions.hidden = !showPreparedActions;
      documentAfterPrepareActions.setAttribute("aria-hidden", showPreparedActions ? "false" : "true");
      documentAfterPrepareActions.style.display = showPreparedActions ? "" : "none";
    }
  }

  function setBusy(isBusy) {
    if (previewBtn) {
      previewBtn.disabled = !!isBusy;
    }
    if (downloadBtn) {
      downloadBtn.disabled = !!isBusy;
    }
    updateDocumentActionState(isBusy);
    if (form) {
      form.setAttribute("aria-busy", isBusy ? "true" : "false");
    }
  }

  function showDocumentStatus(msg) {
    if (!documentStatus) {
      return;
    }
    documentStatus.textContent = msg;
    documentStatus.style.display = "";
  }

  function clearDocumentStatus() {
    if (!documentStatus) {
      return;
    }
    documentStatus.textContent = "";
    documentStatus.style.display = "none";
  }

  function showDocumentError(msg) {
    if (!documentError) {
      return;
    }
    documentError.textContent = msg;
    documentError.style.display = "";
    if (typeof documentError.scrollIntoView === "function") {
      documentError.scrollIntoView({ block: "nearest" });
    }
  }

  function clearDocumentError() {
    if (!documentError) {
      return;
    }
    documentError.textContent = "";
    documentError.style.display = "none";
  }

  function showEstimate(data) {
    if (!documentEstimateWrap || !documentEstimateText) {
      return;
    }
    documentEstimateText.textContent =
      data.word_count + " words (" + data.char_count + " chars). " +
      "Estimated audio length: " + toDuration(data.estimate_audio_seconds) + ". " +
      "Estimated processing time: " + toDuration(data.estimate_processing_seconds) + ". " +
      "Estimate source: " + (data.estimate_source || "baseline") +
      (data.estimate_samples !== undefined ? (" (" + data.estimate_samples + " samples)") : "") + ".";
    documentEstimateWrap.style.display = "";
  }

  function parseFilenameFromDisposition(value) {
    if (!value) {
      return "speech-output.wav";
    }
    var m = /filename=\"?([^\";]+)\"?/i.exec(value);
    return (m && m[1]) ? m[1] : "speech-output.wav";
  }

  function triggerDownload(blob, filename) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
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

  function ensureDocumentPrepared() {
    if (preparedDocument && preparedDocument.token) {
      return Promise.resolve(preparedDocument);
    }
    if (!form || !form.dataset.prepareUrl) {
      return Promise.reject(new Error("Document preparation endpoint is unavailable."));
    }
    if ((!documentTokenInput || !documentTokenInput.value) && (!documentInput || !documentInput.files || !documentInput.files[0])) {
      return Promise.reject(new Error("Choose a document first."));
    }

    clearDocumentError();
    showDocumentStatus("Preparing document text for speech...");
    setBusy(true);

    var fd = buildFormData(true);
    var csrfVal = getCsrfToken();
    return fetch(form.dataset.prepareUrl, {
      method: "POST",
      headers: { "X-CSRFToken": csrfVal },
      body: fd
    })
      .then(function (resp) {
        if (!resp.ok) {
          return errorFromResponse(resp);
        }
        return resp.json();
      })
      .then(function (json) {
        preparedDocument = json;
        if (documentTokenInput) {
          documentTokenInput.value = json.token || "";
        }
        if (documentPrefillInput) {
          documentPrefillInput.value = "1";
        }
        showEstimate(json);
        if (textarea && json.preview_text) {
          textarea.value = json.preview_text;
          renderCharCount();
          persistState();
        }
        showDocumentStatus("Document prepared. Review the estimate, then preview first sentences or choose Download / Listen Live.");
        updateDocumentActionState(false);
        return json;
      })
      .finally(function () {
        setBusy(false);
      });
  }

  function runDocumentPreview() {
    if (!form || !form.dataset.documentPreviewUrl) {
      showDocumentError("Document preview endpoint is unavailable.");
      return;
    }
    clearDocumentError();
    clearStatus();
    ensureDocumentPrepared()
      .then(function (doc) {
        setBusy(true);
        showDocumentStatus("Generating snippet preview...");
        var stopAnnouncements = startTimedAnnouncements(
          showDocumentStatus,
          doc.estimate_processing_seconds || 20,
          Math.min(20, doc.announcement_interval_seconds || 10)
        );

        return fetch(form.dataset.documentPreviewUrl, {
          method: "POST",
          headers: { "X-CSRFToken": getCsrfToken() },
          body: buildFormData(false)
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
            showDocumentStatus("Snippet preview is ready. Playing audio now.");
            return audioPlayer.play();
          })
          .catch(function (err) {
            if (err && err.name === "NotAllowedError") {
              showDocumentStatus("Snippet preview is ready. Press play to hear it.");
              return;
            }
            showDocumentError("Snippet preview failed: " + (err && err.message ? err.message : err));
          })
          .finally(function () {
            stopAnnouncements();
            setBusy(false);
          });
      })
      .catch(function (err) {
        setBusy(false);
        showDocumentError(err && err.message ? err.message : String(err));
      });
  }

  function runDocumentDownload() {
    if (!form || !form.dataset.documentDownloadUrl) {
      showDocumentError("Document download endpoint is unavailable.");
      return;
    }
    clearDocumentError();
    ensureDocumentPrepared()
      .then(function (doc) {
        setBusy(true);
        showDocumentStatus("Rendering full document audio. Audio will download automatically when ready. Keep this tab open.");
        var stopAnnouncements = startTimedAnnouncements(
          showDocumentStatus,
          doc.estimate_processing_seconds || 30,
          doc.announcement_interval_seconds || 20
        );

        return fetch(form.dataset.documentDownloadUrl, {
          method: "POST",
          headers: { "X-CSRFToken": getCsrfToken() },
          body: buildFormData(false)
        })
          .then(function (resp) {
            if (!resp.ok) {
              return errorFromResponse(resp);
            }
            return Promise.all([resp.blob(), Promise.resolve(resp.headers.get("Content-Disposition"))]);
          })
          .then(function (result) {
            var blob = result[0];
            var disposition = result[1];
            var filename = parseFilenameFromDisposition(disposition);
            triggerDownload(blob, filename);
            showDocumentStatus("Full document audio is ready and downloaded.");
          })
          .catch(function (err) {
            showDocumentError("Document conversion failed: " + (err && err.message ? err.message : err));
          })
          .finally(function () {
            stopAnnouncements();
            setBusy(false);
          });
      })
      .catch(function (err) {
        setBusy(false);
        showDocumentError(err && err.message ? err.message : String(err));
      });
  }

  function runDocumentListenLive() {
    if (!form || !form.dataset.documentStreamUrl) {
      showDocumentError("Listen Live streaming endpoint is unavailable.");
      return;
    }
    clearDocumentError();

    // Stop any existing live session
    if (listenLiveAbortController) {
      listenLiveAbortController.abort();
      listenLiveAbortController = null;
    }
    listenLiveActive = false;

    ensureDocumentPrepared()
      .then(function (doc) {
        var AudioContextCtor = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextCtor) {
          showDocumentError("Your browser does not support the Web Audio API required for Listen Live. Use the Download option instead.");
          return;
        }

        setBusy(true);
        listenLiveActive = true;

        // Show the Live player panel
        if (listenLivePlayer) {
          listenLivePlayer.style.display = "";
        }
        if (listenLiveProgressWrap) {
          listenLiveProgressWrap.style.display = "";
        }
        if (listenLiveStopBtn) {
          listenLiveStopBtn.style.display = "";
        }
        if (playerWrap) {
          playerWrap.style.display = "none";
        }

        function setLiveStatus(msg) {
          if (listenLiveStatus) {
            listenLiveStatus.textContent = msg;
          }
        }
        function setLiveProgress(done, total) {
          if (!listenLiveProgressBar) {
            return;
          }
          var pct = total > 0 ? Math.round((done / total) * 100) : 0;
          listenLiveProgressBar.style.width = pct + "%";
          listenLiveProgressBar.setAttribute("aria-valuenow", pct);
        }

        setLiveStatus("Connecting to speech server\u2026");
        setLiveProgress(0, 1);

        var audioCtx = new AudioContextCtor();
        var scheduledUntil = audioCtx.currentTime + 0.2;
        var totalChunks = 0;
        var chunksReceived = 0;
        var abortCtrl = new AbortController();
        listenLiveAbortController = abortCtrl;

        function stopLive(msg) {
          listenLiveActive = false;
          listenLiveAbortController = null;
          abortCtrl.abort();
          try { audioCtx.close(); } catch (e) {}
          setBusy(false);
          if (listenLiveStopBtn) {
            listenLiveStopBtn.style.display = "none";
          }
          if (listenLiveProgressWrap) {
            listenLiveProgressWrap.style.display = "none";
          }
          if (msg) {
            setLiveStatus(msg);
          }
        }

        if (listenLiveStopBtn) {
          listenLiveStopBtn.onclick = function () {
            stopLive("Playback stopped.");
          };
        }

        var stopAnnouncements = startTimedAnnouncements(
          setLiveStatus,
          doc.estimate_processing_seconds || 30,
          doc.announcement_interval_seconds || 20
        );

        // Fetch the SSE stream
        fetch(form.dataset.documentStreamUrl, {
          method: "POST",
          headers: { "X-CSRFToken": getCsrfToken() },
          body: buildFormData(false),
          signal: abortCtrl.signal
        })
          .then(function (resp) {
            if (!resp.ok) {
              return errorFromResponse(resp);
            }
            var reader = resp.body.getReader();
            var decoder = new TextDecoder();
            var sseBuffer = "";

            function parseAndHandleEvents(raw) {
              sseBuffer += raw;
              var parts = sseBuffer.split("\n\n");
              sseBuffer = parts.pop(); // keep incomplete last segment

              for (var pi = 0; pi < parts.length; pi++) {
                var block = parts[pi];
                var eventType = "";
                var dataLines = [];
                var lines = block.split("\n");
                for (var li = 0; li < lines.length; li++) {
                  var line = lines[li];
                  if (line.startsWith("event: ")) {
                    eventType = line.slice(7).trim();
                  } else if (line.startsWith("data: ")) {
                    dataLines.push(line.slice(6));
                  }
                }
                var dataStr = dataLines.join("\n");
                handleSseEvent(eventType, dataStr);
              }
            }

            function handleSseEvent(eventType, dataStr) {
              var payload;
              try {
                payload = JSON.parse(dataStr);
              } catch (e) {
                return;
              }

              if (eventType === "audio_config") {
                totalChunks = payload.totalChunks || 0;
                setLiveStatus("Synthesising audio\u2026 (0 of " + totalChunks + " segments ready)");
                setLiveProgress(0, totalChunks);

              } else if (eventType === "audio_chunk") {
                chunksReceived++;
                setLiveStatus("Playing segment " + chunksReceived + " of " + (totalChunks || "?"));
                setLiveProgress(chunksReceived, totalChunks || chunksReceived);

                // Decode base64 WAV and schedule via Web Audio API
                var wavB64 = payload.wav;
                if (wavB64) {
                  try {
                    var binaryStr = atob(wavB64);
                    var bytes = new Uint8Array(binaryStr.length);
                    for (var bi = 0; bi < binaryStr.length; bi++) {
                      bytes[bi] = binaryStr.charCodeAt(bi);
                    }
                    audioCtx.decodeAudioData(
                      bytes.buffer,
                      function (audioBuffer) {
                        var source = audioCtx.createBufferSource();
                        source.buffer = audioBuffer;
                        source.connect(audioCtx.destination);
                        var startAt = Math.max(scheduledUntil, audioCtx.currentTime + 0.05);
                        source.start(startAt);
                        scheduledUntil = startAt + audioBuffer.duration;
                      },
                      function () {
                        // Decoding failed for this chunk -- skip silently
                      }
                    );
                  } catch (e) {
                    // Skip malformed chunk
                  }
                }

              } else if (eventType === "done") {
                stopAnnouncements();
                stopLive("All " + (payload.totalChunks || chunksReceived) + " segments queued. Playback finishing\u2026");
                setLiveProgress(payload.totalChunks || chunksReceived, payload.totalChunks || chunksReceived);

              } else if (eventType === "error") {
                stopAnnouncements();
                stopLive(null);
                showDocumentError("Listen Live error: " + (payload.message || "Unknown error"));
              }
            }

            function pump() {
              return reader.read().then(function (result) {
                if (result.done) {
                  return;
                }
                var raw = decoder.decode(result.value, { stream: true });
                parseAndHandleEvents(raw);
                if (!abortCtrl.signal.aborted) {
                  return pump();
                }
              });
            }

            return pump();
          })
          .catch(function (err) {
            if (err && err.name === "AbortError") {
              return;
            }
            stopAnnouncements();
            stopLive(null);
            showDocumentError("Listen Live failed: " + (err && err.message ? err.message : err));
          });
      })
      .catch(function (err) {
        setBusy(false);
        showDocumentError(err && err.message ? err.message : String(err));
      });
  }

  function getDocMode() {
    var modeInput = document.querySelector('input[name="doc_mode"]:checked');
    return modeInput ? modeInput.value : "download";
  }

  function updateGoButtonLabel() {
    if (!documentGoBtn) {
      return;
    }
    var mode = getDocMode();
    documentGoBtn.setAttribute(
      "aria-label",
      mode === "listen" ? "Listen Live as it generates" : "Download full document audio"
    );
    documentGoBtn.textContent =
      mode === "listen" ? "Listen Live" : "Download full document audio";
  }

  // Wire mode radio buttons to update the Go button label
  var docModeInputs = document.querySelectorAll('input[name="doc_mode"]');
  for (var mi = 0; mi < docModeInputs.length; mi++) {
    docModeInputs[mi].addEventListener("change", updateGoButtonLabel);
  }
  updateGoButtonLabel();

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

  if (nextDocumentBtn) {
    nextDocumentBtn.addEventListener("click", function () {
      preparedDocument = null;
      ensureDocumentPrepared().catch(function (err) {
        showDocumentError(err && err.message ? err.message : String(err));
      });
    });
  }

  if (documentPreviewBtn) {
    documentPreviewBtn.addEventListener("click", runDocumentPreview);
  }

  if (documentGoBtn) {
    documentGoBtn.addEventListener("click", function () {
      if (getDocMode() === "listen") {
        runDocumentListenLive();
      } else {
        runDocumentDownload();
      }
    });
  }

  wireSpaceActivation(nextDocumentBtn);
  wireSpaceActivation(documentPreviewBtn);
  wireSpaceActivation(documentGoBtn);

  if (documentInput) {
    documentInput.addEventListener("change", function () {
      preparedDocument = null;
      clearDocumentError();
      clearDocumentStatus();
      if (documentTokenInput) {
        documentTokenInput.value = "";
      }
      if (documentPrefillInput) {
        documentPrefillInput.value = "0";
      }
      if (documentEstimateWrap) {
        documentEstimateWrap.style.display = "none";
      }
      if (listenLivePlayer) {
        listenLivePlayer.style.display = "none";
      }
      if (listenLiveAbortController) {
        listenLiveAbortController.abort();
        listenLiveAbortController = null;
      }
      listenLiveActive = false;
      updateDocumentActionState(false);
      showDocumentStatus("Press Next to prepare document text and show timing details.");
    });
  }

  updateDocumentActionState(false);
})();
