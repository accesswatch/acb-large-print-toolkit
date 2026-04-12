/* Expand All / Collapse All toggle for <details> accordions on the guidelines page. */
(function () {
  "use strict";
  var btn = document.querySelector(".toggle-all-btn");
  if (!btn) return;

  btn.addEventListener("click", function () {
    var details = document.querySelectorAll("details.guideline-accordion");
    var allOpen = Array.prototype.every.call(details, function (d) {
      return d.open;
    });
    Array.prototype.forEach.call(details, function (d) {
      d.open = !allOpen;
    });
    btn.textContent = allOpen ? "Expand All" : "Collapse All";
    btn.setAttribute(
      "aria-label",
      allOpen
        ? "Expand all guideline sections"
        : "Collapse all guideline sections"
    );
  });
})();
