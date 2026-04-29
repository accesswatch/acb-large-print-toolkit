/* dropzone.js -- Drag-and-drop enhancement for file inputs.
 *
 * Adds a visual drop zone adjacent to every <input type="file"> found in the
 * page.  The original <input> remains fully accessible and functional; the
 * drop zone is decorative (aria-hidden="true") so keyboard and screen-reader
 * users are unaffected.
 *
 * On drop the file is assigned to the real input and a synthetic "change" event
 * is dispatched so other scripts (e.g. the convert-form extension filter) react
 * correctly.
 */
(function () {
  'use strict';

  function initDropZones() {
    document.querySelectorAll('input[type="file"]').forEach(function (input) {
      // Use the nearest .form-group ancestor as the drag target (so the whole
      // label area is droppable, not just the tiny drop-zone div itself).
      var group = input.closest('.form-group, fieldset') || input.parentNode;

      // Build the visual zone
      var zone = document.createElement('div');
      zone.className = 'drop-zone';
      zone.setAttribute('aria-hidden', 'true');

      var hint = document.createElement('p');
      hint.className = 'drop-zone-hint';
      hint.textContent = 'or drag and drop a file here';
      zone.appendChild(hint);

      // Insert immediately after the <input>
      input.insertAdjacentElement('afterend', zone);

      // Detect whether the dragged item contains files (vs. other data)
      function isFileDrag(e) {
        if (!e.dataTransfer || !e.dataTransfer.types) return false;
        var types = Array.from(e.dataTransfer.types);
        return types.indexOf('Files') !== -1 ||
               types.indexOf('application/x-moz-file') !== -1;
      }

      group.addEventListener('dragenter', function (e) {
        if (isFileDrag(e)) { e.preventDefault(); zone.classList.add('drop-zone--active'); }
      });
      group.addEventListener('dragover', function (e) {
        if (isFileDrag(e)) { e.preventDefault(); }
      });
      group.addEventListener('dragleave', function (e) {
        // Only deactivate when focus actually leaves the group
        if (!group.contains(e.relatedTarget)) {
          zone.classList.remove('drop-zone--active');
        }
      });
      group.addEventListener('drop', function (e) {
        e.preventDefault();
        zone.classList.remove('drop-zone--active');
        var files = e.dataTransfer && e.dataTransfer.files;
        if (!files || !files.length) return;

        // Assign file to the real input via DataTransfer (works in all modern browsers)
        try {
          var dt = new DataTransfer();
          dt.items.add(files[0]);
          input.files = dt.files;
        } catch (_err) {
          /* Older browsers can't programmatically set input.files; the hint still
             shows the filename but the input will be empty on form submit. */
        }
        hint.textContent = '\u2714 ' + files[0].name;

        // Notify other scripts (e.g. convert form extension filter)
        input.dispatchEvent(new Event('change', { bubbles: true }));
      });

      // Keep hint in sync when user picks a file through the normal file dialog
      input.addEventListener('change', function () {
        hint.textContent = (input.files && input.files.length)
          ? '\u2714 ' + input.files[0].name
          : 'or drag and drop a file here';
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDropZones);
  } else {
    initDropZones();
  }
}());
