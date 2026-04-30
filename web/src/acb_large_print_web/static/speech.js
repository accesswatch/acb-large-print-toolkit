(function () {
  "use strict";

  function byId(id) {
    return document.getElementById(id);
  }

  var textarea = byId("speech-text");
  var counter = byId("char-count-value");
  if (textarea && counter) {
    textarea.addEventListener("input", function () {
      counter.textContent = textarea.value.length;
    });
  }

  var speedInput = byId("speech-speed");
  var speedValue = byId("speed-value");
  if (speedInput && speedValue) {
    speedInput.addEventListener("input", function () {
      speedValue.textContent = parseFloat(speedInput.value).toFixed(1);
    });
  }

  var pitchInput = byId("speech-pitch");
  var pitchValue = byId("pitch-value");
  if (pitchInput && pitchValue) {
    pitchInput.addEventListener("input", function () {
      pitchValue.textContent = pitchInput.value;
    });
  }

  var previewBtn = byId("preview-btn");
  var audioPlayer = byId("audio-player");
  var playerWrap = byId("preview-player");
  var errorRegion = byId("preview-error");
  var form = byId("speech-form");

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
      previewBtn.textContent = "Generating preview...";
      previewBtn.disabled = true;

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
          return audioPlayer.play();
        })
        .catch(function (err) {
          if (err && err.name === "NotAllowedError") {
            playerWrap.style.display = "";
            return;
          }
          showError("Preview failed: " + (err && err.message ? err.message : err));
        })
        .finally(function () {
          previewBtn.textContent = "Preview audio";
          previewBtn.disabled = false;
        });
    });
  }
})();
