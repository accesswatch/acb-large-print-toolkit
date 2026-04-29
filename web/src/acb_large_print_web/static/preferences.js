(function () {
  "use strict";

  var STORAGE_KEY = "glow_user_settings";
  var LEGACY_COOKIE_NAME = "glow_user_settings";
  var STORAGE_VERSION = 2;

  var DEFAULTS = {
    version: STORAGE_VERSION,
    optIn: false,
    audit: {
      profile: "acb_2025",
      mode: "full",
      categories: ["acb", "msac"],
      customRules: [],
      suppressLinkText: false,
      suppressMissingAltText: false,
      suppressFauxHeading: false,
    },
    fix: {
      profile: "acb_2025",
      mode: "full",
      categories: ["acb", "msac"],
      customRules: [],
      bound: false,
      flushLists: true,
      flushParagraphs: true,
      preserveHeadingAlignment: false,
      detectHeadings: true,
      useAI: false,
      useListLevels: false,
      listIndent: 0.5,
      listHanging: 0.25,
      listIndentLevel1: 0.25,
      listIndentLevel2: 0.5,
      listIndentLevel3: 0.75,
      paraIndent: 0,
      firstLineIndent: 0,
      headingThreshold: 50,
      headingAccuracy: "balanced",
      allowedHeadingLevels: ["1", "2", "3", "4", "5", "6"],
      suppressLinkText: false,
      suppressMissingAltText: false,
      suppressFauxHeading: false,
    },
    template: {
      profile: "acb_2025",
      includeSample: false,
      bound: false,
      allowedHeadingLevels: ["1", "2", "3"],
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
    ui: {
      rulesReference: {
        target: "audit",
        search: "",
        severity: "",
        format: "",
        profile: "",
        category: "",
        autoFixableOnly: false,
      },
    },
  };

  function cloneDefaults() {
    return JSON.parse(JSON.stringify(DEFAULTS));
  }

  function cloneArray(value, fallback) {
    if (Array.isArray(value)) {
      return value.slice();
    }
    return Array.isArray(fallback) ? fallback.slice() : [];
  }

  function canUseLocalStorage() {
    try {
      var testKey = STORAGE_KEY + "__test";
      window.localStorage.setItem(testKey, "1");
      window.localStorage.removeItem(testKey);
      return true;
    } catch (_error) {
      return false;
    }
  }

  function getLegacyCookie(name) {
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

  function eraseLegacyCookie(name) {
    document.cookie = name + "=; Max-Age=-99999999; path=/; SameSite=Lax";
  }

  function normalizeRulesReferenceUi(ui) {
    var defaults = cloneDefaults().ui.rulesReference;
    return {
      target: ui && ui.target === "fix" ? "fix" : defaults.target,
      search: ui && typeof ui.search === "string" ? ui.search : defaults.search,
      severity: ui && typeof ui.severity === "string" ? ui.severity : defaults.severity,
      format: ui && typeof ui.format === "string" ? ui.format : defaults.format,
      profile: ui && typeof ui.profile === "string" ? ui.profile : defaults.profile,
      category: ui && typeof ui.category === "string" ? ui.category : defaults.category,
      autoFixableOnly: !!(ui && ui.autoFixableOnly),
    };
  }

  function normalizeSettings(parsed) {
    var defaults = cloneDefaults();
    if (!parsed || typeof parsed !== "object") {
      return defaults;
    }

    return {
      version: STORAGE_VERSION,
      savedAt: parsed.savedAt || null,
      optIn: !!parsed.optIn,
      audit: Object.assign({}, defaults.audit, parsed.audit || {}, {
        categories: cloneArray(parsed.audit && parsed.audit.categories, defaults.audit.categories),
        customRules: cloneArray(parsed.audit && parsed.audit.customRules, defaults.audit.customRules),
      }),
      fix: Object.assign({}, defaults.fix, parsed.fix || {}, {
        categories: cloneArray(parsed.fix && parsed.fix.categories, defaults.fix.categories),
        allowedHeadingLevels: cloneArray(
          parsed.fix && parsed.fix.allowedHeadingLevels,
          defaults.fix.allowedHeadingLevels
        ),
        customRules: cloneArray(parsed.fix && parsed.fix.customRules, defaults.fix.customRules),
      }),
      template: Object.assign({}, defaults.template, parsed.template || {}, {
        allowedHeadingLevels: cloneArray(
          parsed.template && parsed.template.allowedHeadingLevels,
          defaults.template.allowedHeadingLevels
        ),
      }),
      export: Object.assign({}, defaults.export, parsed.export || {}),
      convert: Object.assign({}, defaults.convert, parsed.convert || {}),
      ui: {
        rulesReference: normalizeRulesReferenceUi(
          parsed.ui && parsed.ui.rulesReference ? parsed.ui.rulesReference : null
        ),
      },
    };
  }

  function removeStoredSettings() {
    if (canUseLocalStorage()) {
      try {
        window.localStorage.removeItem(STORAGE_KEY);
      } catch (_error) {
        // Ignore storage removal failures.
      }
    }
    eraseLegacyCookie(LEGACY_COOKIE_NAME);
  }

  function migrateLegacyCookieIfNeeded() {
    if (!canUseLocalStorage()) {
      return;
    }
    try {
      if (window.localStorage.getItem(STORAGE_KEY)) {
        return;
      }
    } catch (_error) {
      return;
    }

    var legacyRaw = getLegacyCookie(LEGACY_COOKIE_NAME);
    if (!legacyRaw) {
      return;
    }

    try {
      var migrated = normalizeSettings(JSON.parse(legacyRaw));
      if (migrated.optIn) {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(migrated));
      }
    } catch (_error) {
      // Ignore invalid legacy preference payloads.
    }

    eraseLegacyCookie(LEGACY_COOKIE_NAME);
  }

  function loadSettings() {
    migrateLegacyCookieIfNeeded();
    if (!canUseLocalStorage()) return cloneDefaults();

    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return cloneDefaults();
      return normalizeSettings(JSON.parse(raw));
    } catch (_e) {
      return cloneDefaults();
    }
  }

  function saveSettings(settings) {
    var normalized = normalizeSettings(settings);
    if (!normalized.optIn) {
      removeStoredSettings();
      return false;
    }
    if (!canUseLocalStorage()) {
      return false;
    }
    normalized.version = STORAGE_VERSION;
    normalized.savedAt = new Date().toISOString();
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
      eraseLegacyCookie(LEGACY_COOKIE_NAME);
      return true;
    } catch (_error) {
      return false;
    }
  }

  function resetSettings() {
    removeStoredSettings();
    return cloneDefaults();
  }

  function updateSettings(mutator, options) {
    var settings = loadSettings();
    mutator(settings);
    if (options && options.forceOptIn) {
      settings.optIn = true;
    }
    saveSettings(settings);
    return normalizeSettings(settings);
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
        setRadio("standards_profile", settings.audit.profile);
        setRadio("mode", settings.audit.mode);
        setCheckboxGroup("category", settings.audit.categories);
        if (settings.audit.customRules.length) {
          setCheckboxGroup("rule", settings.audit.customRules);
        }
        setCheckbox("suppress_link_text", settings.audit.suppressLinkText);
        setCheckbox("suppress_missing_alt_text", settings.audit.suppressMissingAltText);
        setCheckbox("suppress_faux_heading", settings.audit.suppressFauxHeading);
      }

      // Fix form
      if (document.querySelector('input[name="detect_headings"]')) {
        setRadio("standards_profile", settings.fix.profile);
        setRadio("mode", settings.fix.mode);
        setCheckboxGroup("category", settings.fix.categories);
        if (settings.fix.customRules.length) {
          setCheckboxGroup("rule", settings.fix.customRules);
        }
        setCheckbox("bound", settings.fix.bound);
        setCheckbox("flush_lists", settings.fix.flushLists);
        setCheckbox("flush_paragraphs", settings.fix.flushParagraphs);
        setCheckbox("preserve_heading_alignment", settings.fix.preserveHeadingAlignment);
        setCheckbox("detect_headings", settings.fix.detectHeadings);
        setCheckbox("use_ai", settings.fix.useAI);
        setCheckbox("use_list_levels", settings.fix.useListLevels);
        setInput("list_indent", settings.fix.listIndent);
        setInput("list_hanging", settings.fix.listHanging);
        setInput("list_indent_level_1", settings.fix.listIndentLevel1);
        setInput("list_indent_level_2", settings.fix.listIndentLevel2);
        setInput("list_indent_level_3", settings.fix.listIndentLevel3);
        setInput("para_indent", settings.fix.paraIndent);
        setInput("first_line_indent", settings.fix.firstLineIndent);
        setInput("heading_threshold", settings.fix.headingThreshold);
        setInput("heading_accuracy", settings.fix.headingAccuracy);
        setCheckboxGroup("allowed_heading_levels", settings.fix.allowedHeadingLevels);
        setCheckbox("suppress_link_text", settings.fix.suppressLinkText);
        setCheckbox("suppress_missing_alt_text", settings.fix.suppressMissingAltText);
        setCheckbox("suppress_faux_heading", settings.fix.suppressFauxHeading);
      }

      // Template form
      if (document.querySelector('input[name="include_sample"]')) {
        setRadio("standards_profile", settings.template.profile);
        setCheckbox("include_sample", settings.template.includeSample);
        setCheckbox("bound", settings.template.bound);
        setCheckboxGroup("allowed_heading_levels", settings.template.allowedHeadingLevels);
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
    var existingSettings = loadSettings();

    settings.audit.customRules = cloneArray(
      existingSettings.audit.customRules,
      settings.audit.customRules
    );
    settings.fix.customRules = cloneArray(
      existingSettings.fix.customRules,
      settings.fix.customRules
    );
    settings.ui.rulesReference = normalizeRulesReferenceUi(
      existingSettings.ui && existingSettings.ui.rulesReference
        ? existingSettings.ui.rulesReference
        : null
    );

    var optIn = document.getElementById("settings-opt-in");
    settings.optIn = !!(optIn && optIn.checked);

    var auditMode = document.querySelector('input[name="settings_audit_mode"]:checked');
    var auditProfile = document.querySelector('input[name="settings_audit_profile"]:checked');
    settings.audit.profile = auditProfile ? auditProfile.value : settings.audit.profile;
    settings.audit.mode = auditMode ? auditMode.value : settings.audit.mode;
    settings.audit.categories = Array.prototype.slice
      .call(document.querySelectorAll('input[name="settings_audit_category"]:checked'))
      .map(function (el) {
        return el.value;
      });
    settings.audit.suppressLinkText = !!document.querySelector('input[name="settings_audit_suppress_link_text"]:checked');
    settings.audit.suppressMissingAltText = !!document.querySelector('input[name="settings_audit_suppress_missing_alt_text"]:checked');
    settings.audit.suppressFauxHeading = !!document.querySelector('input[name="settings_audit_suppress_faux_heading"]:checked');

    var fixMode = document.querySelector('input[name="settings_fix_mode"]:checked');
    var fixProfile = document.querySelector('input[name="settings_fix_profile"]:checked');
    settings.fix.profile = fixProfile ? fixProfile.value : settings.fix.profile;
    settings.fix.mode = fixMode ? fixMode.value : settings.fix.mode;
    settings.fix.categories = Array.prototype.slice
      .call(document.querySelectorAll('input[name="settings_fix_category"]:checked'))
      .map(function (el) {
        return el.value;
      });
    settings.fix.bound = !!document.querySelector('input[name="settings_fix_bound"]:checked');
    settings.fix.flushLists = !!document.querySelector('input[name="settings_fix_flush_lists"]:checked');
    settings.fix.flushParagraphs = !!document.querySelector('input[name="settings_fix_flush_paragraphs"]:checked');
    settings.fix.preserveHeadingAlignment = !!document.querySelector('input[name="settings_fix_preserve_heading_alignment"]:checked');
    settings.fix.detectHeadings = !!document.querySelector('input[name="settings_fix_detect_headings"]:checked');
    settings.fix.useAI = !!document.querySelector('input[name="settings_fix_use_ai"]:checked');
    settings.fix.useListLevels = !!document.querySelector('input[name="settings_fix_use_list_levels"]:checked');
    settings.fix.suppressLinkText = !!document.querySelector('input[name="settings_fix_suppress_link_text"]:checked');
    settings.fix.suppressMissingAltText = !!document.querySelector('input[name="settings_fix_suppress_missing_alt_text"]:checked');
    settings.fix.suppressFauxHeading = !!document.querySelector('input[name="settings_fix_suppress_faux_heading"]:checked');
    settings.fix.allowedHeadingLevels = Array.prototype.slice
      .call(document.querySelectorAll('input[name="settings_fix_allowed_heading_levels"]:checked'))
      .map(function (el) {
        return el.value;
      });
    if (!settings.fix.allowedHeadingLevels.length) {
      settings.fix.allowedHeadingLevels = ["1", "2", "3", "4", "5", "6"];
    }

    var listIndent = document.querySelector('input[name="settings_fix_list_indent"]');
    settings.fix.listIndent = listIndent ? parseFloat(listIndent.value || "0.5") || 0.5 : 0.5;
    var listHanging = document.querySelector('input[name="settings_fix_list_hanging"]');
    settings.fix.listHanging = listHanging ? parseFloat(listHanging.value || "0.25") || 0.25 : 0.25;
    var listIndentLevel1 = document.querySelector('input[name="settings_fix_list_indent_level_1"]');
    settings.fix.listIndentLevel1 = listIndentLevel1 ? parseFloat(listIndentLevel1.value || "0.25") || 0.25 : 0.25;
    var listIndentLevel2 = document.querySelector('input[name="settings_fix_list_indent_level_2"]');
    settings.fix.listIndentLevel2 = listIndentLevel2 ? parseFloat(listIndentLevel2.value || "0.5") || 0.5 : 0.5;
    var listIndentLevel3 = document.querySelector('input[name="settings_fix_list_indent_level_3"]');
    settings.fix.listIndentLevel3 = listIndentLevel3 ? parseFloat(listIndentLevel3.value || "0.75") || 0.75 : 0.75;
    var paraIndent = document.querySelector('input[name="settings_fix_para_indent"]');
    settings.fix.paraIndent = paraIndent ? parseFloat(paraIndent.value || "0") || 0 : 0;
    var firstLineIndent = document.querySelector('input[name="settings_fix_first_line_indent"]');
    settings.fix.firstLineIndent = firstLineIndent ? parseFloat(firstLineIndent.value || "0") || 0 : 0;

    var threshold = document.querySelector('input[name="settings_fix_heading_threshold"]');
    settings.fix.headingThreshold = threshold ? Math.max(0, Math.min(100, parseInt(threshold.value || "50", 10) || 50)) : 50;

    var accuracy = document.querySelector('select[name="settings_fix_heading_accuracy"]');
    settings.fix.headingAccuracy = accuracy ? accuracy.value : "balanced";

    var templateProfile = document.querySelector('input[name="settings_template_profile"]:checked');
    settings.template.profile = templateProfile ? templateProfile.value : settings.template.profile;
    settings.template.includeSample = !!document.querySelector('input[name="settings_template_include_sample"]:checked');
    settings.template.bound = !!document.querySelector('input[name="settings_template_bound"]:checked');
    settings.template.allowedHeadingLevels = Array.prototype.slice
      .call(document.querySelectorAll('input[name="settings_template_allowed_heading_levels"]:checked'))
      .map(function (el) {
        return el.value;
      });
    if (!settings.template.allowedHeadingLevels.length) {
      settings.template.allowedHeadingLevels = ["1", "2", "3"];
    }

    var exportMode = document.querySelector('input[name="settings_export_mode"]:checked');
    settings.export.mode = exportMode ? exportMode.value : "standalone";

    var convertDirection = document.querySelector('input[name="settings_convert_direction"]:checked');
    settings.convert.direction = convertDirection ? convertDirection.value : "to-markdown";
    settings.convert.acbFormat = !!document.querySelector('input[name="settings_convert_acb_format"]:checked');
    settings.convert.bindingMargin = !!document.querySelector('input[name="settings_convert_binding_margin"]:checked');
    settings.convert.printReady = !!document.querySelector('input[name="settings_convert_print_ready"]:checked');

    return settings;
  }

  function updateSettingsRuleSummary(target, selectedRuleIds) {
    var summaryEl = document.getElementById("settings-" + target + "-rules-summary");
    if (!summaryEl) {
      return;
    }

    var totalRules = parseInt(summaryEl.getAttribute("data-total-rules") || "0", 10) || 0;
    if (selectedRuleIds && selectedRuleIds.length) {
      summaryEl.textContent =
        selectedRuleIds.length +
        " of " +
        totalRules +
        " rules are saved for Custom " +
        (target === "fix" ? "Fix" : "Audit") +
        ".";
      return;
    }

    summaryEl.textContent =
      "All " + totalRules + " rules will be used when Custom " +
      (target === "fix" ? "Fix" : "Audit") +
      " is selected.";
  }

  function populateSettingsForm() {
    var form = document.getElementById("settings-form");
    if (!form) return;

    var settings = loadSettings();

    var optIn = document.getElementById("settings-opt-in");
    if (optIn) optIn.checked = !!settings.optIn;

    setRadio("settings_audit_profile", settings.audit.profile);
    setRadio("settings_audit_mode", settings.audit.mode);
    setCheckboxGroup("settings_audit_category", settings.audit.categories);
    setCheckbox("settings_audit_suppress_link_text", settings.audit.suppressLinkText);
    setCheckbox("settings_audit_suppress_missing_alt_text", settings.audit.suppressMissingAltText);
    setCheckbox("settings_audit_suppress_faux_heading", settings.audit.suppressFauxHeading);

    setRadio("settings_fix_profile", settings.fix.profile);
    setRadio("settings_fix_mode", settings.fix.mode);
    setCheckboxGroup("settings_fix_category", settings.fix.categories);
    setCheckbox("settings_fix_bound", settings.fix.bound);
    setCheckbox("settings_fix_flush_lists", settings.fix.flushLists);
    setCheckbox("settings_fix_flush_paragraphs", settings.fix.flushParagraphs);
    setCheckbox("settings_fix_preserve_heading_alignment", settings.fix.preserveHeadingAlignment);
    setCheckbox("settings_fix_detect_headings", settings.fix.detectHeadings);
    setCheckbox("settings_fix_use_ai", settings.fix.useAI);
    setCheckbox("settings_fix_use_list_levels", settings.fix.useListLevels);
    setCheckbox("settings_fix_suppress_link_text", settings.fix.suppressLinkText);
    setCheckbox("settings_fix_suppress_missing_alt_text", settings.fix.suppressMissingAltText);
    setCheckbox("settings_fix_suppress_faux_heading", settings.fix.suppressFauxHeading);
    setCheckboxGroup("settings_fix_allowed_heading_levels", settings.fix.allowedHeadingLevels);
    setInput("settings_fix_list_indent", settings.fix.listIndent);
    setInput("settings_fix_list_hanging", settings.fix.listHanging);
    setInput("settings_fix_list_indent_level_1", settings.fix.listIndentLevel1);
    setInput("settings_fix_list_indent_level_2", settings.fix.listIndentLevel2);
    setInput("settings_fix_list_indent_level_3", settings.fix.listIndentLevel3);
    setInput("settings_fix_para_indent", settings.fix.paraIndent);
    setInput("settings_fix_first_line_indent", settings.fix.firstLineIndent);
    setInput("settings_fix_heading_threshold", settings.fix.headingThreshold);
    setInput("settings_fix_heading_accuracy", settings.fix.headingAccuracy);

    setRadio("settings_template_profile", settings.template.profile);
    setCheckbox("settings_template_include_sample", settings.template.includeSample);
    setCheckbox("settings_template_bound", settings.template.bound);
    setCheckboxGroup("settings_template_allowed_heading_levels", settings.template.allowedHeadingLevels);

    setRadio("settings_export_mode", settings.export.mode);

    setRadio("settings_convert_direction", settings.convert.direction);
    setCheckbox("settings_convert_acb_format", settings.convert.acbFormat);
    setCheckbox("settings_convert_binding_margin", settings.convert.bindingMargin);
    setCheckbox("settings_convert_print_ready", settings.convert.printReady);

    updateSettingsRuleSummary("audit", settings.audit.customRules);
    updateSettingsRuleSummary("fix", settings.fix.customRules);

    var status = document.getElementById("settings-status");
    var saveBtn = document.getElementById("settings-save");
    var resetBtn = document.getElementById("settings-reset");
    var resetAuditRulesBtn = document.getElementById("settings-reset-audit-rules");
    var resetFixRulesBtn = document.getElementById("settings-reset-fix-rules");

    if (saveBtn && !saveBtn.dataset.glowBound) {
      saveBtn.dataset.glowBound = "true";
      saveBtn.addEventListener("click", function () {
        var newSettings = readSettingsForm();
        var saved = saveSettings(newSettings);
        if (status) {
          status.style.display = "block";
          if (newSettings.optIn && saved) {
            status.className = "flash-success";
            status.innerHTML = "<p><strong>Saved:</strong> Your settings were saved in local storage on this device and will be applied across GLOW workflows.</p>";
          } else if (newSettings.optIn) {
            status.className = "flash-warning";
            status.innerHTML = "<p><strong>Not saved:</strong> Your browser did not allow local storage for GLOW settings.</p>";
          } else {
            status.className = "flash-info";
            status.innerHTML = "<p><strong>Updated:</strong> Remember my settings is off. Saved local settings were removed and GLOW will use standard defaults.</p>";
          }
        }
      });
    }

    if (resetBtn && !resetBtn.dataset.glowBound) {
      resetBtn.dataset.glowBound = "true";
      resetBtn.addEventListener("click", function () {
        resetSettings();
        populateSettingsForm();
        if (status) {
          status.style.display = "block";
          status.className = "flash-info";
          status.innerHTML = "<p><strong>Reset:</strong> Settings returned to GLOW defaults. Local storage is now off for saved preferences.</p>";
        }
      });
    }

    function bindRuleResetButton(button, target) {
      if (!button || button.dataset.glowBound) {
        return;
      }
      button.dataset.glowBound = "true";
      button.addEventListener("click", function () {
        var settings = loadSettings();
        settings[target].customRules = [];
        if (settings.optIn) {
          saveSettings(settings);
        }
        updateSettingsRuleSummary(target, []);
        if (status) {
          status.style.display = "block";
          status.className = "flash-info";
          status.innerHTML =
            "<p><strong>Reset:</strong> The saved Custom " +
            (target === "fix" ? "Fix" : "Audit") +
            " rule set now uses all rules again.</p>";
        }
      });
    }

    bindRuleResetButton(resetAuditRulesBtn, "audit");
    bindRuleResetButton(resetFixRulesBtn, "fix");
  }

  document.addEventListener("DOMContentLoaded", function () {
    applySettingsToCurrentPage();
    populateSettingsForm();
  });

  document.addEventListener("glow:content-swapped", function () {
    applySettingsToCurrentPage();
    populateSettingsForm();
  });

  window.glowPreferences = {
    cloneDefaults: cloneDefaults,
    loadSettings: loadSettings,
    normalizeSettings: normalizeSettings,
    resetSettings: resetSettings,
    saveSettings: saveSettings,
    storageKey: STORAGE_KEY,
    updateSettings: updateSettings,
  };
})();
