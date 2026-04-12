/* Expand All / Collapse All toggle for <details> accordions on the guidelines page. */
(function () {
  "use strict";
  var btn = document.querySelector(".toggle-all-btn");
  if (!btn) return;

  var details = document.querySelectorAll("details.guideline-accordion");

  function updateButton() {
    var allOpen = Array.prototype.every.call(details, function (d) {
      return d.open;
    });
    btn.textContent = allOpen ? "Collapse All" : "Expand All";
    btn.setAttribute(
      "aria-label",
      allOpen
        ? "Collapse all guideline sections"
        : "Expand all guideline sections"
    );
  }

  btn.addEventListener("click", function () {
    var allOpen = Array.prototype.every.call(details, function (d) {
      return d.open;
    });
    Array.prototype.forEach.call(details, function (d) {
      d.open = !allOpen;
    });
    updateButton();
  });

  /* Sync button text when a user manually opens/closes individual sections. */
  Array.prototype.forEach.call(details, function (d) {
    d.addEventListener("toggle", updateButton);
  });

  /* Force all details open before printing so nothing is hidden on paper. */
  var savedStates = [];
  window.addEventListener("beforeprint", function () {
    savedStates = [];
    Array.prototype.forEach.call(details, function (d) {
      savedStates.push(d.open);
      d.open = true;
    });
  });
  window.addEventListener("afterprint", function () {
    Array.prototype.forEach.call(details, function (d, i) {
      if (i < savedStates.length) d.open = savedStates[i];
    });
    updateButton();
  });
})();
