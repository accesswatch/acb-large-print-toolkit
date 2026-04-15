(function () {
  "use strict";

  var COOKIE_NAME = "glow_user_settings";
  var COOKIE_DAYS = 365;

  var DEFAULTS = {
    version: 1,
    optIn: false,
    audit: {
      mode: "full",
      categories: ["acb", "msac"],
    },
    fix: {
      mode: "full",
      bound: false,
      flushLists: true,
      flushParagraphs: true,
      detectHeadings: true,
      useAI: false,
      headingThreshold: 50,
      headingAccuracy: "balanced",
    },
    template: {
      includeSample: false,
      bound: false,
    },
    export: {
      mode: "standalone",
    },
    convert: {
      direction: "to-markdown",
      acbFormat: true,
      bindingMargin: false,
      printReady: false,
    },
  };

  function cloneDefaults() {
    return JSON.parse(JSON.stringify(DEFAULTS));
  }

  function setCookie(name, value, days) {
    var expires = "";
    if (days) {
      var date = new Date();
      date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
      expires = "; expires=" + date.toUTCString();
    }
    document.cookie =
      name +
      "=" +
      encodeURIComponent(value) +
      expires +
      "; path=/; SameSite=Lax";
  }

  function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(";");
    for (var i = 0; i < ca.length; i += 1) {
      var c = ca[i];
      while (c.charAt(0) === " ") c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) {
        return decodeURIComponent(c.substring(nameEQ.length, c.length));
      }
    }
    return null;
  }

  function eraseCookie(name) {
    document.cookie = name + "=; Max-Age=-99999999; path=/; SameSite=Lax";
  }

  function loadSettings() {
    var raw = getCookie(COOKIE_NAME);
    if (!raw) return cloneDefaults();
    try {
      var parsed = JSON.parse(raw);
      var defaults = cloneDefaults();
      return {
        version: 1,
        optIn: !!parsed.optIn,
        audit: Object.assign(defaults.audit, parsed.audit || {}),
        fix: Object.assign(defaults.fix, parsed.fix || {}),
        template: Object.assign(defaults.template, parsed.template || {}),
        export: Object.assign(defaults.export, parsed.export || {}),
        convert: Object.assign(defaults.convert, parsed.convert || {}),
      };
    } catch (_e) {
      return cloneDefaults();
    }
  }

  function saveSettings(settings) {
    if (!settings.optIn) {
      eraseCookie(COOKIE_NAME);
      return;
    }
    settings.version = 1;
    settings.savedAt = new Date().toISOString();
    setCookie(COOKIE_NAME, JSON.stringify(settings), COOKIE_DAYS);
  }

  function setRadio(name, value) {
    var selector = 'input[name="' + name + '"]';
    var radios = document.querySelectorAll(selector);
    for (var i = 0; i < radios.length; i += 1) {
      if (radios[i].value === value && !radios[i].disabled) {
        radios[i].checked = true;
        radios[i].dispatchEvent(new Event("change", { bubbles: true }));
        break;
      }
    }
  }

  function setCheckbox(name, checked) {
    var el = document.querySelector('input[name="' + name + '"]');
    if (!el || el.disabled) return;
    el.checked = !!checked;
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function setCheckboxGroup(name, values) {
    var selector = 'input[name="' + name + '"]';
    var checkboxes = document.querySelectorAll(selector);
    for (var i = 0; i < checkboxes.length; i += 1) {
      if (checkboxes[i].disabled) continue;
      checkboxes[i].checked = values.indexOf(checkboxes[i].value) >= 0;
      checkboxes[i].dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  function setInput(name, value) {
    var el = document.querySelector('[name="' + name + '"]');
    if (!el || el.disabled) return;
    el.value = value;
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function applySettingsToCurrentPage() {
    var settings = loadSettings();
    if (!settings.optIn) return;

    if (document.querySelector('form[action], form[method="post"]')) {
      // Audit form
      if (document.querySelector('input[name="mode"][value="full"]') && document.querySelector('input[name="category"][value="acb"]')) {
        setRadio("mode", settings.audit.mode);
        setCheckboxGroup("category", settings.audit.categories);
      }

      // Fix form
      if (document.querySelector('input[name="detect_headings"]')) {
        setRadio("mode", settings.fix.mode);
        setCheckbox("bound", settings.fix.bound);
        setCheckbox("flush_lists", settings.fix.flushLists);
        setCheckbox("flush_paragraphs", settings.fix.flushParagraphs);
        setCheckbox("detect_headings", settings.fix.detectHeadings);
        setCheckbox("use_ai", settings.fix.useAI);
        setInput("heading_threshold", settings.fix.headingThreshold);
        setInput("heading_accuracy", settings.fix.headingAccuracy);
      }

      // Template form
      if (document.querySelector('input[name="include_sample"]')) {
        setCheckbox("include_sample", settings.template.includeSample);
        setCheckbox("bound", settings.template.bound);
      }

      // Export form
      if (document.querySelector('input[name="mode"][value="standalone"]') && document.querySelector('input[name="mode"][value="cms"]') && document.querySelector('input[name="document"][accept=".docx"]')) {
        setRadio("mode", settings.export.mode);
      }

      // Convert form
      if (document.querySelector('input[name="direction"]')) {
        setRadio("direction", settings.convert.direction);
        setCheckbox("acb_format", settings.convert.acbFormat);
        setCheckbox("binding_margin", settings.convert.bindingMargin);
        setCheckbox("print_ready", settings.convert.printReady);
      }
    }
  }

  function readSettingsForm() {
    var settings = cloneDefaults();

    var optIn = document.getElementById("settings-opt-in");
    settings.optIn = !!(optIn && optIn.checked);

    var auditMode = document.querySelector('input[name="settings_audit_mode"]:checked');
    settings.audit.mode = auditMode ? auditMode.value : settings.audit.mode;
    settings.audit.categories = Array.prototype.slice
      .call(document.querySelectorAll('input[name="settings_audit_category"]:checked'))
      .map(function (el) {
        return el.value;
      });

    var fixMode = document.querySelector('input[name="settings_fix_mode"]:checked');
    settings.fix.mode = fixMode ? fixMode.value : settings.fix.mode;
    settings.fix.bound = !!document.querySelector('input[name="settings_fix_bound"]:checked');
    settings.fix.flushLists = !!document.querySelector('input[name="settings_fix_flush_lists"]:checked');
    settings.fix.flushParagraphs = !!document.querySelector('input[name="settings_fix_flush_paragraphs"]:checked');
    settings.fix.detectHeadings = !!document.querySelector('input[name="settings_fix_detect_headings"]:checked');
    settings.fix.useAI = !!document.querySelector('input[name="settings_fix_use_ai"]:checked');

    var threshold = document.querySelector('input[name="settings_fix_heading_threshold"]');
    settings.fix.headingThreshold = threshold ? Math.max(0, Math.min(100, parseInt(threshold.value || "50", 10) || 50)) : 50;

    var accuracy = document.querySelector('select[name="settings_fix_heading_accuracy"]');
    settings.fix.headingAccuracy = accuracy ? accuracy.value : "balanced";

    settings.template.includeSample = !!document.querySelector('input[name="settings_template_include_sample"]:checked');
    settings.template.bound = !!document.querySelector('input[name="settings_template_bound"]:checked');

    var exportMode = document.querySelector('input[name="settings_export_mode"]:checked');
    settings.export.mode = exportMode ? exportMode.value : "standalone";

    var convertDirection = document.querySelector('input[name="settings_convert_direction"]:checked');
    settings.convert.direction = convertDirection ? convertDirection.value : "to-markdown";
    settings.convert.acbFormat = !!document.querySelector('input[name="settings_convert_acb_format"]:checked');
    settings.convert.bindingMargin = !!document.querySelector('input[name="settings_convert_binding_margin"]:checked');
    settings.convert.printReady = !!document.querySelector('input[name="settings_convert_print_ready"]:checked');

    return settings;
  }

  function populateSettingsForm() {
    var form = document.getElementById("settings-form");
    if (!form) return;

    var settings = loadSettings();

    var optIn = document.getElementById("settings-opt-in");
    if (optIn) optIn.checked = !!settings.optIn;

    setRadio("settings_audit_mode", settings.audit.mode);
    setCheckboxGroup("settings_audit_category", settings.audit.categories);

    setRadio("settings_fix_mode", settings.fix.mode);
    setCheckbox("settings_fix_bound", settings.fix.bound);
    setCheckbox("settings_fix_flush_lists", settings.fix.flushLists);
    setCheckbox("settings_fix_flush_paragraphs", settings.fix.flushParagraphs);
    setCheckbox("settings_fix_detect_headings", settings.fix.detectHeadings);
    setCheckbox("settings_fix_use_ai", settings.fix.useAI);
    setInput("settings_fix_heading_threshold", settings.fix.headingThreshold);
    setInput("settings_fix_heading_accuracy", settings.fix.headingAccuracy);

    setCheckbox("settings_template_include_sample", settings.template.includeSample);
    setCheckbox("settings_template_bound", settings.template.bound);

    setRadio("settings_export_mode", settings.export.mode);

    setRadio("settings_convert_direction", settings.convert.direction);
    setCheckbox("settings_convert_acb_format", settings.convert.acbFormat);
    setCheckbox("settings_convert_binding_margin", settings.convert.bindingMargin);
    setCheckbox("settings_convert_print_ready", settings.convert.printReady);

    var status = document.getElementById("settings-status");
    var saveBtn = document.getElementById("settings-save");
    var resetBtn = document.getElementById("settings-reset");

    if (saveBtn) {
      saveBtn.addEventListener("click", function () {
        var newSettings = readSettingsForm();
        saveSettings(newSettings);
        if (status) {
          status.style.display = "block";
          if (newSettings.optIn) {
            status.className = "flash-success";
            status.innerHTML = "<p><strong>Saved:</strong> Your settings were saved in a cookie on this device and will be applied across GLOW workflows.</p>";
          } else {
            status.className = "flash-info";
            status.innerHTML = "<p><strong>Updated:</strong> Cookie opt-in is off. Saved settings were removed and GLOW will use standard defaults.</p>";
          }
        }
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        eraseCookie(COOKIE_NAME);
        populateSettingsForm();
        if (status) {
          status.style.display = "block";
          status.className = "flash-info";
          status.innerHTML = "<p><strong>Reset:</strong> Settings returned to GLOW defaults. Cookie storage is now off.</p>";
        }
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    applySettingsToCurrentPage();
    populateSettingsForm();
  });

  document.addEventListener("glow:content-swapped", function () {
    applySettingsToCurrentPage();
    populateSettingsForm();
  });
})();
