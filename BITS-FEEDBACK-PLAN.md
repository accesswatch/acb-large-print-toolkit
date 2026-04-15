# BITS Feedback -- Development Plan

**Source:** Jeff Bishop, President, Blind Information Technology Solutions (BITS)  
**Received:** April 15, 2026  
**Document:** 100-page newsletter (16pt body, 18pt Level 2 headings, higher margins)  
**Workflow:** Full Fix with faux heading detection unchecked, AI detection off, 170 fixes applied

---

## Summary of Feedback

Jeff reported six distinct product concerns after running the fix workflow on the BITS newsletter:

1. Score remained F after 170 fixes because disabled faux heading detection still penalizes the score.
2. Raw URLs are intentional for hard-copy readers who need to type them in -- no way to suppress the link-text rule without going into Custom Fix mode.
3. Decorative images without alt text were flagged even though they are intentionally decorative.
4. The fix expanded a 100-page document to 161 pages (font size, margin changes).
5. The fix left-aligned all centered headings without asking.
6. Heading paragraphs with a soft return (Shift+Enter) combining a 20pt article title and a body-size bold author name were both normalized to 20pt bold.

He also asked about title centering for stories and poems and suggested an FAQ page.

A follow-up request was received on April 15, 2026:

7. List indentation controls were requested but not visible on the web form. The fields exist but are hidden behind the "Flush all lists to the left margin" toggle (Issue 8). Additionally, no per-nesting-level indentation control exists.

The feedback was submitted twice due to the 500 error (now fixed -- see CHANGELOG).

---

# BITS Feedback -- Development Plan

**Source:** Jeff Bishop, President, Blind Information Technology Solutions (BITS)  
**Received:** April 15, 2026  
**Document:** 100-page newsletter (16pt body, 18pt Level 2 headings, higher margins)  
**Workflow:** Full Fix with faux heading detection unchecked, AI detection off, 170 fixes applied

---

## Status Summary

**Completed & Deployed (April 15, 2026):**
- ✅ Issue 1: Faux heading score penalty when detection is disabled -- suppression mechanism and UI display implemented
- ✅ Issue 2: No easy way to disable link-text rule -- Quick Rule Exceptions panel added to Fix and Audit forms
- ✅ Issue 3: Decorative images flagged despite `alt=""` -- VML legacy shape handling for decorative content fixed
- ✅ Issue 4: Document page expansion from 100 to 161 pages -- page-growth warning implemented
- ✅ Issue 5: Fix left-aligns all centered headings without warning -- "Preserve centered headings" option added
- ✅ Issue 6: Heading run formatting normalized across soft returns -- documented as known limitation with FAQ workaround
- ✅ Issue 7: FAQ page needed -- dedicated `/faq/` route with full feature coverage and known limitations
- ✅ Issue 8B: Per-level list indentation support -- form UI and backend logic for Level 1/2/3 per-level indentation targets

**Outstanding (deferred per request):**
- Issue 9: APH guidelines support and guideline set selector (out of scope for this pass)

---

## Summary of Feedback

Jeff reported six distinct product concerns after running the fix workflow on the BITS newsletter:

1. Score remained F after 170 fixes because disabled faux heading detection still penalizes the score.
2. Raw URLs are intentional for hard-copy readers who need to type them in -- no way to suppress the link-text rule without going into Custom Fix mode.
3. Decorative images without alt text were flagged even though they are intentionally decorative.
4. The fix expanded a 100-page document to 161 pages (font size, margin changes).
5. The fix left-aligned all centered headings without asking.
6. Heading paragraphs with a soft return (Shift+Enter) combining a 20pt article title and a body-size bold author name were both normalized to 20pt bold.

He also asked about title centering for stories and poems and suggested an FAQ page.

A follow-up request was received on April 15, 2026:

7. List indentation controls were requested but not visible on the web form. The fields exist but are hidden behind the "Flush all lists to the left margin" toggle (Issue 8). Additionally, no per-nesting-level indentation control exists.

The feedback was submitted twice due to the 500 error (now fixed -- see CHANGELOG).

---

## Completed Issues (Detailed)

---

### ✅ Issue 1 -- Faux Heading Score Penalty When Detection Is Disabled

**Status:** Deployed  
**Deployment Date:** April 15, 2026

**What was implemented:**
- `_run_fix_and_render()` in `web/src/acb_large_print_web/routes/fix.py` now suppresses `ACB-FAUX-HEADING` findings when `detect_headings=False`
- Post-fix `findings` list is filtered to exclude suppressed rule IDs before scoring and display
- `fix_result.html` template renders a "Suppressed by your settings" note with the list of excluded rules and reasons
- Audit results similarly show suppressed findings in a dedicated UI section
- Test coverage added in `test_fix_routes.py` to verify suppression when heading detection is disabled

**User impact:** Users who intentionally disable heading detection are no longer penalized with a low score for a rule they chose to waive. Results clearly show which rules were suppressed and why.

---

### ✅ Issue 2 -- No Easy Way to Disable the Link-Text Rule for Intentional Raw URLs

**Status:** Deployed  
**Deployment Date:** April 15, 2026

**What was implemented:**
- New **Quick Rule Exceptions** collapsible section added to Fix and Audit forms with three pre-labeled toggles:
  - "Suppress ambiguous link text (`ACB-LINK-TEXT`)"
  - "Suppress missing alt text (`ACB-MISSING-ALT-TEXT`)"
  - "Suppress faux heading detection (`ACB-FAUX-HEADING`)"
- `_parse_form_options()` in `web/src/acb_large_print_web/routes/fix.py` extracts exception flags and adds rule IDs to the suppression set
- `_run_fix_and_render()` applies suppression before scoring (same mechanism as Issue 1)
- Audit route also supports quick exceptions parsing
- Form templates (`fix_form.html`, `audit_form.html`) render the new section with help text for each toggle
- Result templates show suppressed rules with reasons
- Test coverage added for new form parsing and suppression

**User impact:** Users no longer need to enter Custom Fix mode or expand complex panels to suppress the three most common workflow exceptions. The option is discoverable and labeled.

---

### ✅ Issue 3 -- Decorative Images Still Flagged by ACB-MISSING-ALT-TEXT

**Status:** Deployed  
**Deployment Date:** April 15, 2026 (legacy VML fix)

**What was implemented:**
- `auditor.py` now recognizes VML legacy shapes with explicit `alt=""` as decorative (same as inline drawing shapes with `a14:decorative`)
- `_check_alt_text()` changed to treat `alt=""` on VML shapes as an intentional decorative marker, not a missing-alt violation
- Combined with Issue 2's "Suppress missing alt text" exception for cases where the decorative flag is not available or applied

**User impact:** Documents using Word's "Mark as decorative" feature on VML shapes (older images or objects) no longer trigger false ACB-MISSING-ALT-TEXT findings. Users can also suppress the rule via Quick Exceptions if needed.

---

### ✅ Issue 4 -- Document Expanded from 100 to 161 Pages After Fix

**Status:** Deployed  
**Deployment Date:** April 15, 2026

**What was implemented:**
- `_run_fix_and_render()` detects if pre-fix document body text is below 18pt using pre-fix audit data
- Renders a page-growth warning in `fix_result.html` when detected: "Your source appears to use body text below 18pt. The fix increased it to meet the ACB minimum (18pt), which may expand page count. For a 100-page document, expect 10--20% more pages."
- Help text suggests binding margin and layout adjustments as options
- FAQ page includes entry "Why did my document get longer?" with explanation and mitigation strategies

**User impact:** Users are now informed before downloading that page count may increase due to font size normalization, reducing surprise and supporting informed decision-making about document preparation.

---

### ✅ Issue 5 -- Fix Left-Aligns All Centered Headings Without Warning

**Status:** Deployed  
**Deployment Date:** April 15, 2026

**What was implemented:**
- New "Heading Alignment Handling" checkbox added to Fix form: "Preserve centered headings"
- When checked, `preserve_heading_alignment=True` is passed to the fixer
- `fixer.py` `_fix_paragraph_formatting()` now accepts `preserve_heading_alignment` parameter
- Heading paragraphs (Heading 1, 2, 3 styles) skip alignment override when preserve option is enabled
- `fix.py` `_run_fix_and_render()` also suppresses `ACB-ALIGNMENT` findings for heading paragraphs when preserve option is active
- Test coverage added for suppression when preserve option is enabled
- FAQ entry explains when and why to use this option (creative publications, story/poem titles)

**User impact:** Users can now preserve intentional heading center-alignment for design-driven documents (stories, poems) while still receiving all other ACB fixes. Alignment override is no longer silent.

---

### ✅ Issue 6 -- Heading Run Formatting Normalized Across Soft Returns

**Status:** Closed as Known Limitation with Workaround  
**Deployment Date:** April 15, 2026

**What was implemented:**
- Documented as a known limitation in `/faq/` page
- FAQ answer explains the soft-return heading technique, why normalization occurs, and the workaround:
  - "Use a custom 'Heading 2 Author' style mapped to the table of contents instead of combining title and author in one heading"
  - "Or: run the fixer without heading-style fixes enabled in Custom Fix mode (advanced)"
- GitHub issue tracked for Phase 2 implementation (run-level formatting preservation by break position)

**User impact:** Users understand why mixed-format heading paragraphs are normalized and have a clear workaround for future documents. Reduces confusion and provides a path forward.

---

### ✅ Issue 7 -- FAQ Page Needed

**Status:** Deployed  
**Deployment Date:** April 15, 2026

**What was implemented:**
- New route `/faq/` in `web/src/acb_large_print_web/routes/faq.py`
- New template `web/src/acb_large_print_web/templates/faq.html` with accordion-style `<details>`/`<summary>` entries (no JS required)
- FAQ entries cover:
  - Quick Rule Exceptions usage and when to use
  - Preserve centered headings intent and use cases
  - Per-level list indentation configuration
  - Page expansion and mitigation strategies
  - VML and decorative image handling
  - Raw URLs for hard-copy readers
  - Soft-return heading workaround
  - Binding margin setup
  - Known limitations and future directions
- Route registered in `app.py`
- Link added to main navigation footer in `base.html`
- Link added to Fix result page help section

**User impact:** Common questions from users like Jeff now have a discoverable, centralized home. The FAQ reduces support friction and is easily maintained.

---

### ✅ Issue 8B -- Per-Level List Indentation Support

**Status:** Deployed  
**Deployment Date:** April 15, 2026

**What was implemented:**

**Backend (auditor & fixer):**
- `auditor.py` now includes `_list_level_from_style()` helper to extract nesting level from Word paragraph style name (e.g., "List Paragraph 2" → level 2)
- `_check_paragraph_content()` now accepts optional `list_level_indents: dict[int, float]` parameter with per-level expected indentation
- Audit findings for list indentation now reference the detected level: "Expected Level 2 indent 0.50 in, found 0.25 in"
- `audit_document()` threads `list_level_indents` through the audit pipeline
- `fixer.py` similarly implements `_list_level_from_style()` helper
- `_fix_paragraph_formatting()` now accepts `list_level_indents: dict[int, float]` and applies level-specific indent targets
- Fixer applies per-level indents when fixing list paragraphs, matching the auditor's level detection

**Frontend (web form):**
- New "Use per-level list indentation" toggle added below the standard list indent fields
- When checked, reveals Level 1 / Level 2 / Level 3 indent input fields
- "Flush all lists to the left margin" and per-level options work together (standard and per-level are mutually exclusive)
- Form JavaScript manages enable/disable state between base indents and per-level indents
- Help text explains when per-level indentation is useful (nested lists, varying depths)

**Fix route:**
- `_parse_form_options()` extracts `use_list_levels` flag and builds `list_level_indents` dict from form values
- `_fix_by_extension()` passes `list_level_indents` to the fixer's `fix_document()`
- `_audit_by_extension()` optionally accepts and forwards expected indent parameters for pre-audit with current settings

**Test coverage:**
- New test `test_parse_form_options_supports_per_level_list_indents` verifies per-level dict construction from form
- Updated existing tests to include `list_level_indents` in option dicts

**User impact:** Users with multi-level lists (e.g., nested bullets at 0.25", 0.50", 0.75") can now configure level-specific indents instead of a single uniform value. Auditor and fixer respect per-level settings, enabling more precise document formatting control.

---

## Remaining Issues (Out of Scope for This Sprint)

### Issue 9 -- APH Guidelines Support: Guideline Set Selector and Full APH Specification

**Priority:** High  
**Effort:** Large (2--3 days across all layers)  
**Status:** Deferred per request  
**Source:** APH document "Research-Based Guidelines for the Development of Documents in Large Print" (American Printing House for the Blind)

#### Problem

`detect_headings=False` skips `_convert_faux_headings()` in the fixer but has no effect on the post-fix audit. `audit_document()` always calls `_check_faux_headings()`, so `ACB-FAUX-HEADING` findings are still generated and count against the score. A user who knowingly unchecks heading detection (because their headings are already correct) gets penalized for something they deliberately waived.

#### Root Cause

`_run_fix_and_render()` in `fix.py` passes the raw `post_audit.findings` to scoring. No mechanism suppresses findings for rules the user disabled.

#### Proposed Solution

When `detect_headings` is `False`, exclude `ACB-FAUX-HEADING` from the post-fix findings before scoring and display. This is already architecturally possible -- `filter_findings()` exists for exactly this purpose.

**`web/src/acb_large_print_web/routes/fix.py`** -- `_run_fix_and_render()`:

```python
# Suppress findings for rules the user explicitly disabled
suppressed: set[str] = set()
if not opts["detect_headings"]:
suppressed.add("ACB-FAUX-HEADING")

post_audit.findings = [
f for f in post_audit.findings if f.rule_id not in suppressed
]
```

Apply this block before scoring, before `filter_findings()`, and before building `post_breakdown`. Also pass `suppressed` to the template so the Results page can display a note like "1 rule suppressed by your settings: ACB-FAUX-HEADING."

**`web/src/acb_large_print_web/templates/fix_result.html`**: Add a dismissible note if `suppressed_rules` is non-empty listing which rules were excluded and why.

#### Files Affected

- `web/src/acb_large_print_web/routes/fix.py`
- `web/src/acb_large_print_web/templates/fix_result.html`

#### Test

Add a test in `web/tests/test_fix_routes.py` that uploads a .docx, posts with `detect_headings` unchecked, and asserts `ACB-FAUX-HEADING` does not appear in the rendered result.

---

### Issue 2 -- No Easy Way to Disable the Link-Text Rule for Intentional Raw URLs

**Priority:** High  
**Effort:** Medium (4--6 hours)

#### Problem

Jeff uses raw, unlinked URLs in the newsletter body specifically so hard-copy readers can type them at a keyboard. The `ACB-LINK-TEXT` rule flags every raw URL. The only current workaround is Custom Fix mode, which requires expanding a collapsed panel and unchecking a rule buried among many others. This is not discoverable.

Note: The user said "raw links," meaning URLs typed as plain text in the body -- not hyperlinks with URL as display text. The auditor currently flags both hyperlinks with URL display text (`_check_hyperlinks`) and bare URLs in body runs (if that check exists). Confirm whether plain-text URLs (non-hyperlinked) are flagged or only hyperlinked ones. If only hyperlinked, the user may need to ensure URLs are not wrapped in Word's auto-hyperlink. Either way the discoverability problem is real.

#### Proposed Solution

Add a "Rule Exceptions" quick panel to the Fix form (and Audit form) above the existing Custom Fix details section. Show three pre-labeled exception checkboxes for the most commonly waived rules:

```
[ ] I use raw URLs for hard-copy readers -- suppress ACB-LINK-TEXT
[ ] My document contains intentional decorative images -- suppress ACB-MISSING-ALT-TEXT
[ ] My headings are already correct -- suppress ACB-FAUX-HEADING
```

When any of these checkboxes is checked, add the corresponding rule IDs to the `suppressed` set in `_run_fix_and_render()` (same mechanism as Issue 1).

Alternatively, and with less code, improve the discoverability of Custom Fix mode by expanding the custom rules panel by default when the user has already run a fix and is viewing results, with a clear "Run again with different rules" button that pre-populates the form.

**Preferred approach:** Quick exceptions panel (cleaner UX, no mode switching required).

#### Files Affected

- `web/src/acb_large_print_web/templates/fix_form.html`
- `web/src/acb_large_print_web/templates/audit_form.html`
- `web/src/acb_large_print_web/routes/fix.py` -- `_parse_form_options()`, `_run_fix_and_render()`
- `web/src/acb_large_print_web/routes/audit.py` -- similar suppression logic

#### FAQ Note

Add a FAQ entry: "Can I use bare URLs in my document?" explaining that raw URLs are acceptable in ACB hard-copy documents when screen-reader and digital-format versions use descriptive link text, and how to suppress the rule in this tool.

---

### Issue 3 -- Decorative Images Still Flagged by ACB-MISSING-ALT-TEXT

**Priority:** Medium  
**Effort:** Small (2--3 hours)

#### Problem

The auditor does check for the `a14:decorative` XML attribute on inline drawings and correctly suppresses those findings. However, two gaps exist:

1. **VML legacy shapes**: The VML path (`body.iter(_vml_qn("shape"))`) does not check for decorative intent. In Word, an image marked as decorative via the "Mark as decorative" checkbox sets `alt=""` on the `<v:shape>` element. An explicitly empty `alt` attribute is the VML signal for decorative -- but the auditor currently treats any missing or empty `alt` as a violation.

2. **Discoverability**: Even when the decorative flag is correctly parsed, users may be applying decorative images added outside Word (e.g., pasted from a browser) that lack the structured decorative marker. These will always be flagged. Without the "suppress ACB-MISSING-ALT-TEXT" exception (Issue 2), there is no escape.

#### Proposed Solution

**Gap 1 -- VML shapes:**

In `auditor.py`, `_check_alt_text()`, change the VML branch:

```python
for shape in body.iter(_vml_qn("shape")):
alt = shape.get("alt", None)  # None = attribute absent; "" = explicitly decorative
name = shape.get("id", "unknown shape")
if alt is None:  # attribute absent -- alt text missing
result.add("ACB-MISSING-ALT-TEXT", ...)
# alt == "" means explicitly marked decorative; skip
```

This is a one-line logic change with a corresponding test: create a VML shape with `alt=""` and verify no finding is generated.

**Gap 2 -- Discovery:**

Add the "suppress ACB-MISSING-ALT-TEXT" quick exception checkbox (Issue 2) with help text: "Use this if Word's 'Mark as decorative' feature does not appear in your version or if images were imported without the decorative flag."

#### Files Affected

- `desktop/src/acb_large_print/auditor.py` -- `_check_alt_text()`
- `desktop/tests/` -- new test for VML decorative shape

---

### Issue 4 -- Document Expanded from 100 to 161 Pages After Fix

**Priority:** Low  
**Effort:** Small (1--2 hours, documentation and warning only)

#### Context

This is expected behavior. The newsletter used 16pt body text (below the ACB 18pt minimum) and larger margins. The fix:

- Increases body font from 16pt to 18pt -- approximately 12.5% larger text, which expands line count significantly in a 100-page document.
- Standardizes margins to 1 inch (ACB default). If the original margins were larger, this would actually reduce page count. If smaller, it expands.
- Heading sizes may also increase (20pt Level 2 headings to the ACB 20--22pt range if not already there).

A 61% page count increase is consistent with a 16pt-to-18pt body text change across 100 pages of dense newsletter content.

#### Proposed Solution

This is not a fixable product issue but should be communicated better:

1. Add a page-count warning to the fix result when the pre-fix document font size is below the ACB minimum. Example: "Your document used 16pt body text. The fix increased it to 18pt, which will expand the page count. For a 100-page document, expect approximately 10--20% more pages. Consider adjusting margins or layout in Word after downloading."

2. Add a FAQ entry: "Why did my document get longer?" with an explanation and options (adjust binding margin, reduce heading sizes within ACB limits, review spacing settings).

3. Consider adding an optional "Compact spacing" mode for print workflows that uses 1.15x line spacing (the ACB print spec) instead of 1.5x (the WCAG digital spec), with a clear warning that this reduces digital accessibility.

#### Files Affected

- `web/src/acb_large_print_web/routes/fix.py` -- detect pre-fix body font size, add warning to `warnings` list
- `web/src/acb_large_print_web/templates/fix_result.html` -- display prominently
- Future: `/faq` route

---

### Issue 5 -- Fix Left-Aligns All Centered Headings Without Warning

**Priority:** High  
**Effort:** Medium (4--6 hours)

#### Problem

The fixer's `_fix_paragraph_formatting()` sets all non-left-aligned paragraphs to left-aligned to satisfy `ACB-ALIGNMENT`. This includes headings the user intentionally centered (article titles, story titles, poem titles). No warning is shown before or after. Jeff noted he had feared this would happen and it did.

The ACB guidelines say "flush left, ragged right" for all text. The APH large print standard reportedly permits centered titles when applied consistently and when done for visual hierarchy. An FAQ note on this distinction would be helpful. Regardless, the fix should not silently center-align headings without at least a confirmation step.

#### Proposed Solution

**Phase 1 (Quick win):** Add a "Preserve centered headings" checkbox to the fix form:

```
[ ] Preserve centered headings (do not enforce left-alignment for heading paragraphs)
```

When checked:
- `_fix_paragraph_formatting()` skips heading-styled paragraphs when resetting alignment.
- `ACB-ALIGNMENT` findings at heading paragraphs are filtered from the post-fix display (same suppression mechanism as Issue 1).

This requires detecting whether a paragraph uses a heading style before applying the alignment fix.

**Phase 2 (Better UX):** Before running a full fix, if the document contains centered heading paragraphs, show a pre-fix review step (similar to the existing heading review step) listing them and asking: "The following headings are centered. Apply left-alignment? (ACB guidelines require flush left; APH permits centered titles in creative publications.)" with options: "Align all left / Keep all centered / Choose individually."

**`desktop/src/acb_large_print/fixer.py`** -- `_fix_paragraph_formatting()`:

```python
def _fix_paragraph_formatting(doc, records, ..., preserve_heading_alignment=False):
for para in doc.paragraphs:
if preserve_heading_alignment and _is_heading_style(para.style.name):
continue  # skip alignment enforcement for headings
# ... existing alignment fix logic
```

**`web/src/acb_large_print_web/routes/fix.py`** -- add `preserve_heading_alignment` to `_parse_form_options()` and thread it through `_fix_by_extension()` → `fix_document()`.

#### Files Affected

- `desktop/src/acb_large_print/fixer.py`
- `web/src/acb_large_print_web/routes/fix.py`
- `web/src/acb_large_print_web/templates/fix_form.html`
- `office-addin/src/fixer.ts` -- sync the option

---

### Issue 6 -- Heading Run Formatting Normalized Across Soft Returns

**Priority:** Low  
**Effort:** Medium (3--4 hours; complex edge case)

#### Context

Jeff's technique: a single Heading 2 paragraph contains the article title on the first line and the author name on a second line added with Shift+Enter (a soft return / `<w:br>`). The title runs use 20pt; the author runs use body-size bold. Both the title and author appear together in the auto-generated table of contents because they are a single heading paragraph. After fix, all runs in the paragraph are normalized to 20pt bold Arial, losing the visual distinction.

This is a creative and valid publishing workflow. The ACB fixer's `_convert_faux_headings()` and `_fix_styles()` clear direct run formatting inside heading paragraphs:

```python
for run in para.runs:
run.font.size = None
run.font.bold = None
run.font.name = None
```

#### Proposed Solution

This is a nuanced case and a full solution should not be rushed. Three options:

**Option A -- Document as Known Limitation:** The soft-return heading technique is non-standard. Document in the FAQ: "If you combine a title and author name in one heading using Shift+Enter, the fixer will normalize all text in that heading to the same size. Workaround: use a 'Heading 2 Author' custom style that is mapped to the TOC." This is the lowest-effort response.

**Option B -- Detect and preserve soft-return structure:** In `_convert_faux_headings()` and `_fix_styles()`, check whether a heading paragraph contains a `<w:br>` element (soft return). If so, apply size normalization only to runs before the first break, and preserve run-level formatting after the break. This is achievable in python-docx by walking `para._element` to find `w:br` elements and grouping runs by break position.

**Option C -- User confirmation step:** Add soft-return headings to the heading review step (or a new pre-fix step) to alert the user that mixed-format heading paragraphs will be normalized, and let them choose to exclude specific paragraphs from run-level formatting changes.

**Recommendation:** Implement Option A now (FAQ entry), plan Option B for a future release after more testing with real newsletters.

#### Files Affected (Option B, future)

- `desktop/src/acb_large_print/fixer.py` -- `_convert_faux_headings()`, `_fix_styles()`
- `desktop/tests/` -- new test with a soft-return heading paragraph

---

### Issue 7 -- FAQ Page Needed

**Priority:** Medium  
**Effort:** Medium (3--5 hours)

#### Problem

Several of Jeff's questions are ones that will recur across BITS newsletter editors and other organizational publishers:

- Why is my score still an F after 170 fixes?
- Why did my document get 61% longer?
- Can I use raw URLs for hard-copy readers?
- Is title centering allowed for stories and poems?
- What should I do with decorative images?
- Can I preserve my centered headings?
- Why were my heading font sizes changed?

These are not answered on the guidelines page or in the tool UI.

#### Proposed Solution

Add a `/faq` route to the Flask app with a dedicated FAQ template. Seed it with at least the questions above. Structure as an accordion using `<details>`/`<summary>` for progressive disclosure (ACB compliant, no JS required).

Alternatively, add an "FAQ" section at the bottom of the guidelines page (`/guidelines`) since that page already exists and is linked from the nav.

Link to the FAQ from the fix result page's help box: "Have questions about your results? See the FAQ."

#### Files Affected (new route)

- `web/src/acb_large_print_web/routes/` -- new `faq.py`
- `web/src/acb_large_print_web/templates/` -- new `faq.html`
- `web/src/acb_large_print_web/app.py` -- register blueprint
- `web/src/acb_large_print_web/templates/base.html` -- add nav link

---

### Issue 8 -- List Indentation Fields Not Visible on the Web Form

**Priority:** Medium  
**Effort:** Small (1--2 hours)

#### Problem

List indentation controls (left indent and hanging indent) were requested and implemented, but they are hidden by default behind a toggle checkbox labeled "Flush all lists to the left margin (ACB default)." Because that checkbox is checked on page load, the `div#list-indent-fields` container has `display:none` applied and the fields are effectively invisible. A user who wants to set a custom indentation value has no indication the fields exist.

Additionally, the backend supports only a **single flat indentation value** applied uniformly to all list items regardless of nesting depth. Word documents with multi-level lists (Level 1 bullets at 0.25", Level 2 bullets at 0.5", Level 3 bullets at 0.75") are flattened to one value.

#### Two Gaps

**Gap A -- Discoverability:** The custom indent fields exist at lines 101--118 of `fix_form.html` but are invisible when "Flush all lists" is checked. There is no hint text below the checkbox indicating that unchecking it reveals additional controls.

**Gap B -- Per-level indentation:** The fixer applies `list_indent_in` uniformly to every list paragraph regardless of the `<w:ilvl>` (nesting level) attribute. Word uses `ilvl` values 0--8 to represent list depth. The standard Word behavior is to multiply indentation by level: Level 0 = 0.25", Level 1 = 0.50", Level 2 = 0.75", etc.

#### Proposed Solution

**Gap A -- Discoverability fix (quick win):**

Add a short hint below the "Flush all lists" checkbox pointing to the hidden fields:

```html
<p id="flush-help" class="help-text">
  When checked, bullet and numbered list items start at the left margin with no indentation.
  <strong>Uncheck to set a custom left indent and hanging indent.</strong>
</p>
```

Alternatively (and more robustly), always render the indent fields but disable them when "Flush all lists" is checked, then re-enable on uncheck. This avoids the hidden-content pattern entirely and works without JavaScript:

```html
<input type="number" id="list-indent" name="list_indent" ...
       {% if flush_lists %}disabled{% endif %}>
```

Preferred: the always-visible-but-disabled pattern, since the user requested these fields and should be able to see them at a glance.

**Gap B -- Per-level indentation (Phase 2, planned):**

Add a "Per-level indentation" sub-option that reveals a small table of indent values by level:

```
Level 1: [0.25 in]   Level 2: [0.50 in]   Level 3: [0.75 in]
```

Backend changes required:
- `desktop/src/acb_large_print/fixer.py` -- `_fix_list_indentation()` needs to accept a `level_indents: dict[int, float]` parameter and branch on `para._element.find(qn("w:numPr")) / w:ilvl @w:val`.
- `web/src/acb_large_print_web/routes/fix.py` -- parse `list_indent_level_0`, `list_indent_level_1`, `list_indent_level_2` from the form and pass as a dict.
- Sync to `office-addin/src/fixer.ts`.

**Phase 1 (this sprint):** Implement Gap A (discoverability) only.  
**Phase 2 (next sprint):** Implement Gap B after confirming the use case with Jeff.

#### Files Affected

- `web/src/acb_large_print_web/templates/fix_form.html` -- hint text or always-visible disabled fields
- `desktop/src/acb_large_print/fixer.py` (Phase 2 only)
- `web/src/acb_large_print_web/routes/fix.py` (Phase 2 only)
- `office-addin/src/fixer.ts` (Phase 2 only)

#### Test

Manually verify that unchecking "Flush all lists" reveals (or enables) the left indent and hanging indent fields and that posting the form with custom values produces the expected indentation in the downloaded document.

---

## Out of Scope / Contextual Notes

**Heading size normalization (title + author styling):** Jeff noted that after fixing, both the article title and the author name in his combined Heading 2 paragraphs are now 20pt bold, where he had the author name at body size bold. He said "I guess that's okay" -- this suggests it is tolerable as-is. Issue 6 is a low-urgency improvement.

**Centered title centering and ACB vs. APH:** Jeff asked whether the ACB or APH standard addresses centering for stories and poems. The current ACB Board of Publications guidelines (May 2025) are unambiguous: flush left for all text. The APH guidelines do not explicitly prohibit centered headings -- they are silent on alignment for headings. See Issue 9 for the full APH guidelines integration plan. We should not modify the ACB compliance rule itself without direction from ACB.

**Binding / staples / mail:** Jeff's concern about 80 copies requiring binding instead of stapling is a production constraint outside the tool's scope, but confirming that the binding margin option exists and explaining it in the FAQ is useful ("Add binding margin" adds 0.5 inch to the left margin for spiral or staple binding).

**Feedback submission bug:** Already fixed. Both Jeff's submissions are now in the database (if they went through on retry). The feedback review endpoint at `/feedback/review?key=<FEEDBACK_PASSWORD>` should show both entries.

---

### Issue 9 -- APH Guidelines Support: Guideline Set Selector and Full APH Specification

**Priority:** High  
**Effort:** Large (2--3 days across all layers)  
**Source:** APH document "Research-Based Guidelines for the Development of Documents in Large Print" (American Printing House for the Blind)

---

#### Background

The American Printing House for the Blind (APH) publishes its own research-based large print guidelines that differ in several meaningful ways from the ACB Board of Publications guidelines. Publishers serving educational, student, or consumer audiences under APH contracts or institutional mandates may need to comply with APH rather than ACB. Jeff Bishop raised this distinction directly after finding centered headings were flattened.

The APH guidelines were sourced from: `d:\code\lp\Research-Based-Large-Print-Guidelines.pdf`.

---

#### APH Specification (complete, as published)

| Property | APH Guideline |
| -------- | ------------- |
| **Fonts** | APHont (preferred), Verdana, Tahoma, Helvetica, Antique Olive, Comic Sans (for contrast). No serifs. x-height and t-height should be 1/8". |
| **Font size -- body** | 18pt minimum |
| **Font size -- subheadings** | 20pt |
| **Font size -- headings** | 22pt |
| **Italics** | Avoided. Alternatives: bold, underline, "quotation marks," or contrasting color |
| **Paragraph indentation** | No indentation. Block style. |
| **Paragraph spacing** | Double spacing between paragraphs (2.50 line spaces) |
| **Line spacing** | 1.25 between lines |
| **Line length** | 39--43 characters (shown through research to promote reading efficiency) |
| **Columns** | Discouraged. Visual shift from end of line to beginning of next line is the most difficult task for low vision readers; columns double or triple this effort. |
| **Table of contents / grids** | No leader lines (lead lines / dotted lines). Use alternating pastel row background color instead. |
| **Alignment** | Not explicitly stated (flush left implied; heading centering not prohibited) |
| **Emphasis** | Bold, underline, quotation marks, or contrasting color (all four options permitted) |
| **Color palette (approved)** | Navy blue, Royal blue, Pastel blue, CB yellow, Pastel yellow, Regulation yellow, Federal gold, Meridian gold, Dark brown, Cashew brown, Meridian tan, Regulation pastel tan, Black, White |
| **Color pairs to never place adjacent** | Green+red, dark green+black, red+black, navy+black, orange+brown, green+brown, red+brown, red+orange, green+orange, purple+blue, any color+gray, gray+gray, white+yellow |
| **Gray** | Never use gray in any document that may be read by persons with low vision |
| **Graphics / photos** | Must be enlarged without resolution loss. Must remain as clear and colorful as versions given to sighted peers. No grayscale downgrade of color images. |
| **Text over backgrounds** | Only with a 2mm halo around text (including ascenders/descenders). Discouraged whenever alternatives exist. |
| **Paper color** | White (best contrast, but may cause glare). Alternatives: ivory, antique white, eggshell, pastel yellow, pastel pink with black text; light beige with navy; yellow with navy; eggshell with dark brown. Never gray. |
| **Document size (print)** | Maximum 9" × 12" × 2.5", maximum 2.5 lbs. Reference works (atlases) may be larger. |

---

#### ACB vs. APH Specification Differences

| Property | ACB (May 2025) | APH | Notes |
| -------- | -------------- | --- | ----- |
| **Font** | Arial only | APHont (preferred), Verdana, Tahoma, Helvetica, Antique Olive, Comic Sans | ACB is more restrictive; APH allows a range of proven sans-serif fonts |
| **Line spacing** | 1.5 (digital), 1.15 (print) | 1.25 | ACB digital is more generous; APH is tighter |
| **Paragraph spacing** | 1 blank line between paragraphs | Double spacing between paragraphs (2.50 line spaces) | Conceptually similar; APH specifies it in line-space units |
| **Emphasis** | Underline only (no bold for emphasis, no italic) | Bold, underline, quotation marks, or contrasting color | APH allows bold for emphasis; ACB does not |
| **Italic** | Never | Avoid -- use alternatives | APH avoids italics but permits transitional workarounds; ACB prohibits absolutely |
| **Alignment** | Flush left, ragged right for all text (explicit) | Not stated (silent on heading alignment) | ACB explicitly prohibits centering; APH is silent, which means centered headings are not prohibited by APH |
| **Font size** | 18pt body, 20pt subheadings, 22pt headings | 18pt body, 20pt subheadings, 22pt headings | **Identical** |
| **Paragraph indentation** | No indentation | No indentation | **Identical** |
| **Columns** | Not addressed | Discouraged | APH provides explicit rationale |
| **Color guidance** | Not addressed (deferred to WCAG 4.5:1 contrast) | Extensive: approved palette, forbidden adjacent pairs, gray prohibition | APH has much richer color guidance |
| **Gray** | Not prohibited | Never permitted | APH explicitly forbids gray text and backgrounds |
| **Line length** | Not specified | 39--43 characters | APH is more specific |
| **Table of contents style** | Not addressed | No leader lines; use alternating pastel row colors | APH-specific recommendation |
| **Graphics** | Not addressed | Full color required; no grayscale downgrade | APH-specific requirement |
| **Paper** | Not addressed | Specific colors listed; gray prohibited | Print-production concern |
| **Physical document size** | Not addressed | Max 9"×12"×2.5", ≤ 2.5 lbs | Print-production concern; tool scope limited |

---

#### Proposed Solution

**Phase 1 -- Guidelines Selector UI (web + desktop)**

Add a "Guideline Set" radio group above the fix options:

```html
<fieldset>
  <legend>Guideline Set</legend>
  <label>
    <input type="radio" name="guideline_set" value="acb" checked>
    ACB Large Print Guidelines (American Council of the Blind, May 2025)
    -- Recommended for newsletters, member publications, and general consumer documents
  </label>
  <label>
    <input type="radio" name="guideline_set" value="aph">
    APH Large Print Guidelines (American Printing House for the Blind)
    -- Recommended for educational materials and student publications
  </label>
</fieldset>
```

When `guideline_set=aph` is selected:
- Show a brief summary of the key differences (link to the guidelines page for full detail)
- Adjust the fix options defaults accordingly (e.g., line spacing changes from 1.5 to 1.25; font selector expands beyond Arial)

**Phase 2 -- Backend: APH Constants and Rule Variants**

Add `GUIDELINE_SET` to `constants.py` with an `APH` variant. For each constant that differs:

```python
# ACB defaults (existing)
FONT_NAME = "Arial"
LINE_SPACING = 1.5  # digital

# APH variants
APH_FONT_NAMES = ["APHont", "Verdana", "Tahoma", "Helvetica", "Antique Olive", "Comic Sans"]
APH_LINE_SPACING = 1.25
APH_ALLOW_BOLD_EMPHASIS = True
APH_RECOMMENDED_LINE_LENGTH_MIN = 39  # characters
APH_RECOMMENDED_LINE_LENGTH_MAX = 43  # characters
```

The auditor and fixer both receive the `guideline_set` parameter and branch on it for rules that differ:

- `ACB-FONT-FACE` → under APH, flag only serif fonts and gray text; accept APHont, Verdana, Tahoma, Helvetica
- `ACB-LINE-SPACING` → under APH, target 1.25 instead of 1.5
- `ACB-EMPHASIS` → under APH, bold is permitted; underline and quotation marks also accepted
- `ACB-ALIGNMENT` → under APH, do not flag centered headings (alignment rule is silent on headings)
- New rule `APH-GRAY-TEXT` → flag any gray color text or background under APH mode

Rules that are identical in both sets (font size, no indentation, no italic body text, heading hierarchy) continue to fire regardless of guideline set.

**Phase 3 -- Guidelines Page (`/guidelines`) Update**

Add a tab or section for APH guidelines:
- Full specification table (as above)
- Side-by-side difference comparison table
- Note explaining when to use each standard
- Link to the APH guidelines source document
- Note that this tool enforces ACB by default and APH mode is opt-in

**Phase 4 -- FAQ Entries**

Add to the FAQ page (Issue 7):

- "What is the difference between ACB and APH large print guidelines?"
- "When should I use APH guidelines instead of ACB?"
- "Does APH allow centered headings?" -- Yes, APH is silent on alignment; ACB requires flush left.
- "Does APH allow bold for emphasis?" -- Yes; ACB does not.
- "Why does APH use 1.25 line spacing while ACB uses 1.5?" -- ACB's digital supplement aligns with WCAG; APH is optimized for print reading efficiency research.

**Phase 5 -- Office Add-in and Desktop App**

Sync the `guideline_set` option to:
- `office-addin/src/constants.ts` -- add `APH_CONSTANTS` block
- `office-addin/src/auditor.ts` -- branch on `guidelineSet`
- `office-addin/src/fixer.ts` -- branch on `guidelineSet`
- Desktop GUI -- add a "Guideline Set" radio group to the settings panel

---

#### Files Affected

**Web (Phase 1, 3, 4):**
- `web/src/acb_large_print_web/templates/fix_form.html` -- guideline set radio group
- `web/src/acb_large_print_web/routes/fix.py` -- parse `guideline_set`, pass to fixer/auditor
- `web/src/acb_large_print_web/templates/guidelines.html` -- APH section/tab
- `web/src/acb_large_print_web/templates/faq.html` -- APH FAQ entries

**Core (Phase 2):**
- `desktop/src/acb_large_print/constants.py` -- APH constants block
- `desktop/src/acb_large_print/auditor.py` -- guideline_set parameter and APH rule variants
- `desktop/src/acb_large_print/fixer.py` -- guideline_set parameter and APH fix variants

**Office Add-in (Phase 5):**
- `office-addin/src/constants.ts`
- `office-addin/src/auditor.ts`
- `office-addin/src/fixer.ts`

**Desktop App (Phase 5):**
- Desktop GUI settings panel (file TBD based on GUI implementation)

---

#### Test

- Add a test in `web/tests/test_fix_routes.py` that uploads a .docx, posts with `guideline_set=aph`, and asserts that the resulting audit uses 1.25 line spacing target and does not flag bold emphasis.
- Add a test that confirms a gray-color run generates `APH-GRAY-TEXT` under APH mode and no finding under ACB mode.
- Add a test that confirms a centered heading paragraph does not generate `ACB-ALIGNMENT` under APH mode.

---

#### Phasing Summary

| Phase | Scope | Effort | Priority |
| ----- | ----- | ------ | -------- |
| 1 | Guideline selector UI + form routing | Small | Implement first (unblocks user choice) |
| 2 | Backend APH constants, auditor, fixer variants | Medium | Implement with Phase 1 |
| 3 | Guidelines page APH documentation | Small | Implement with Phase 1 |
| 4 | FAQ APH entries | Small | Implement with Issue 7 FAQ page |
| 5 | Office add-in + desktop app sync | Medium | Next sprint after web is stable |

---

### Issue 10 -- AFB Style Guidelines: Scoping, Terminology, and JVIB Manuscript Standards

**Priority:** Medium  
**Effort:** Small (documentation and terminology only; no new audit rules)  
**Source:** "Style Guidelines for AFB Authors," American Foundation for the Blind  
https://afb.org/news-publications/publications/jvib/authors/afb-style-guidelines  
(Archived: https://web.archive.org/web/2025/https://www.afb.org/news-publications/publications/jvib/authors/afb-style-guidelines)

---

#### Critical Scoping Note

The AFB Style Guidelines are **not a large print document production standard**. They are the manuscript submission rules for academic authors contributing articles to the *Journal of Visual Impairment and Blindness* (JVIB). Key evidence from the document:

- Body font is **12pt Calibri** (not large print)
- Heading levels use **ALL CAPS bold, italic, and bold italic** (conventions that directly contradict large print guidelines)
- Double spacing is for **peer review and typesetting** purposes, not reading accessibility
- Rules govern file format, citation style (APA / Chicago Manual of Style), artwork DPI, figure submission, and field-specific spelling

This means the AFB guidelines **cannot and should not** be offered as a third "guideline set" radio button alongside ACB and APH in the fix/audit form. Adding an "AFB mode" would mislead users into applying JVIB journal formatting -- 12pt type, ALL CAPS headings -- to large print consumer or educational documents.

However, three categories of AFB guidance **are directly useful** to this tool:

1. **Preferred terminology and language** -- AFB maintains an authoritative and comprehensive list of preferred terms for the blindness and low vision field, person-first language rules, and a list of abbreviations. This is applicable to the FAQ, guidelines page, and all tool content.
2. **Spelling conventions** -- AFB specifies: *large print (n); large-print (adj); large type (n); large-type (adj)*. Our tool, documentation, and UI should follow this convention consistently.
3. **Em-dash formatting** -- AFB specifies em-dashes have no spaces before or after. Useful FAQ guidance.

---

#### AFB Specification (complete, per source document)

**Manuscript submission formatting** (JVIB only -- NOT for large print output):

| Property | AFB JVIB Specification |
| -------- | ---------------------- |
| File format | Microsoft Word .doc or .docx only |
| Font | Calibri, 12pt for all elements |
| Margins | 1" on all four sides |
| Line spacing | Double space all elements, including references and tables |
| Justification | Flush left, ragged right -- do not justify line endings |
| Returns | Do not insert returns at end of lines within paragraphs; let the computer determine line endings |
| Hyphenation | Do not hyphenate words at line ends; only hyphenate words when hyphens are required as part of the spelling (e.g., "merry-go-round") |
| Paragraph indent | Use automatic return at end of paragraph and a tab to start the next; do not indent or hang indent text except for extract quotations or when using the bulleted list function; never use the tab key or space bar to align elements |
| Heading 1 | Bold, ALL CAPS, flush left, same point size as body text (e.g., NUMBER ONE HEAD) |
| Heading 2 | Bold, title case, flush left, same point size as body text (e.g., Number Two Head) |
| Heading 3 | Italic, title case, flush left, same point size as body text (e.g., Number Three Head) |
| Heading 4 | Bold italic, sentence case, run into text, followed by a period (e.g., Number four head. Text follows immediately.) |
| Heading rules | Flush left -- do not center; all topics of equal importance use the same level; all headings short, clear, and parallel grammatical structure; must have at least two headings at each level under any parent (no singleton heads) |
| Permitted formatting | Bold, italic, flush left, tabs, bulleted or numbered lists, superscripts, subscripts, diacritical marks (generic Word features only -- do not use Word styles) |
| Italic | A permitted formatting feature; used for Heading 3; may be used as a general feature in other contexts |
| Lists | Use word processor's built-in bullet/numbered list function or an asterisk followed by a space |
| Quotations (in-text) | Enclose in double quotation marks; provide citation with exact page numbers |
| Quotations (block) | Quotations longer than eight lines set off as block quotations, indented from the left margin; citation required |
| Tables | Each table in a separate file; headed by a short title; all columns have concise headings; no borders; no vertical rules; use word processor's table function; do not use tabs to align columns; source must be acknowledged |
| Images (photos) | Minimum 300 dpi at print size; .eps or .tif format preferred; .jpg accepted only if no other format available; do not re-save .jpg before submitting |
| Images (line art) | Minimum 600 dpi; .tif or .eps format; created in Illustrator, CorelDRAW, or equivalent; no embedded art in text files |
| Image callout labels | 12-point Arial or Helvetica typeface; initial capital letter only (not ALL CAPS) |
| Figures | Each in a separate file; numbered by order of appearance; no figure number embedded in file |
| References | APA style (American Psychological Association) |
| Other style | Chicago Manual of Style for all points not covered by APA |
| Spelling | Merriam-Webster's Collegiate Dictionary (most recent edition) |
| Numbers | Spell out one through nine; numerals for 10 and above; same style within a paragraph for same category; use numerals before units of measurement (6 miles, 2 percent written out); use numerals for ages (a 5-year-old); avoid fractions -- use decimals (2.5 million, not 2½ million); treat ordinal numbers the same as cardinal (third, 21st); no apostrophe with decades (1970s, not 1970's); spell out the word "percent" (not %) |
| Em-dash | Use Word's Insert Symbol to insert an em-dash, or use two hyphens (--) with no spaces before or after |
| Sidebars | Separate file; generally not more than two or three double-spaced pages |

**Preferred terminology and language** (applicable to this tool's documentation and UI):

The following is the complete AFB preferred terminology list as published. First column is the term to avoid; second column is the preferred AFB term.

| Avoid | AFB Preferred |
| ----- | ------------- |
| abnormal (or atypical) | unique or unusual |
| above (to refer to something stated earlier in the text) | "earlier in this paper" or "previously" |
| assure or insure | ensure |
| below (to refer to something stated later in the text) | "later in this paper" or "subsequently" |
| the blind | "people who are blind" on first mention in a paragraph; "blind people" acceptable thereafter |
| Braille (uppercase) | braille (lowercase), unless referring to Louis Braille the person |
| doctor (generic) | specific type: physician, ophthalmologist, optometrist, low vision specialist, or eye care specialist |
| e.g. (in running text) | for example (use e.g. only in parenthetical material) |
| eyeglasses | glasses -- correction: AFB says the preferred term IS eyeglasses; avoid "glasses" |
| grade 1 braille / grade 2 braille | uncontracted braille / contracted braille |
| dog guide | guide dog |
| handicapped | disabled |
| hearing impaired | deaf and hard of hearing |
| i.e. (in running text) | that is (use i.e. only in parenthetical expressions) |
| Journal of Visual Impairment and Blindness (spelled out with "and") | Journal of Visual Impairment & Blindness (use ampersand) |
| listserv (or variations) | electronic discussion group |
| low vision aids | low vision devices |
| low vision persons (adjective) | persons with low vision (noun use only) |
| mothers | parents and other caregivers |
| normal peers | sighted peers |
| parents | families |
| partially sighted | low vision |
| residual vision | specify the visual impairment (by acuity and field loss) |
| tactual | tactile |
| teacher of the visually impaired (TVI/TSVI/TSBVI) | teacher of students with visual impairments (spell out first reference; acronym acceptable after) |
| the WHO / the AFB / the JVIB | WHO / AFB / JVIB (omit "the" before acronyms) |
| visual aids | visual devices |
| visual conditions | visual impairments |
| visual deficits | visual impairments |
| visual loss | vision loss |

**Preferred spelling for field-specific terms** (selected entries relevant to this tool and its documentation):

| Preferred spelling |
| ------------------ |
| large print (n); large-print (adj) |
| large type (n); large-type (adj) |
| braille (lowercase) |
| assistive technology (n, adj) |
| audio describe (v); audio-described (adj); audio description (n) |
| caregiver |
| closed-circuit television (CCTV) -- spell out first reference, then acronym |
| contracted braille (formerly grade 2 braille) |
| decision making (n); decision-making (adj) |
| e-book |
| email |
| handheld (adj); hands-on (adj) |
| health care (n, adj) |
| low vision (n, adj) |
| screen reader (n); screen-reading (adj) |
| setup (n); set up (v) |
| text-to-speech (adj) |
| uncontracted braille (formerly grade 1 braille) |
| URL |
| video magnifier |
| website |
| word processing (n); word-processing (adj) |

**Abbreviations acceptable after first full definition (AFB):**
ADHD, ECC, FVA, IDEA, IEP, LMA, LVT, O&M, TVI/TSVI/TSBVI, VRT

**Abbreviations that must always be spelled out in full (AFB):**
EI (early intervention), FAPE (free appropriate public education), LRE (least restrictive environment), OT (occupational therapist), PT (physical therapist), SLP (speech-language pathologist), VI (visual impairment)

**Language and inclusion rules:**

- Do not use masculine pronouns (he, him) for unspecified sex. Use "he or she" or "they" (never "he/she" or "s/he"). Switch to plural when possible. Use "the" to maintain neutrality ("The doctor gave medicine to the patient").
- Do not label groups by disability ("the blind," "the deaf," "the elderly"). Use "children who are blind" on first description; "blind children" is acceptable in later mentions within the same section.
- Avoid value-laden terms: "normal," "deficits," "of course," "unfortunately," "tragically," "sadly," "burden," "victim," "suffering."
- Avoid absolutes: "everyone," "always," "the best," "the worst."
- Avoid instructional tone: "should" (when lecturing readers).

---

#### ACB vs. APH vs. AFB (JVIB) Comparison

| Property | ACB (May 2025) | APH | AFB JVIB | Relevance to Tool |
| -------- | -------------- | --- | -------- | ----------------- |
| **Scope** | Large print consumer/member publications | Large print educational materials | Academic manuscript submission for JVIB | AFB is out of scope for fix/audit rules |
| **Font size** | 18pt body, 20pt subheadings, 22pt headings | 18pt body, 20pt subheadings, 22pt headings | 12pt Calibri | AFB cannot be a production mode |
| **Font face** | Arial only | APHont, Verdana, Tahoma, Helvetica, Antique Olive | Calibri (manuscript); Arial/Helvetica for figure callouts | AFB cannot be a production mode |
| **Heading 1 style** | Hierarchical, no ALL CAPS, no italic | Not specified in detail | Bold ALL CAPS (e.g., NUMBER ONE HEAD) | Directly contradicts large print norms |
| **Heading 3 style** | No italic | Not specified | Italic, title case | AFB uses italic; ACB and APH avoid it |
| **Flush left** | Required for all text | Implied | Required; do not center | All three agree on flush left |
| **Justification** | Flush left, ragged right | Not stated | Flush left, ragged right; do not justify | AFB and ACB explicitly agree |
| **Italic** | Never (prohibition) | Avoid; use alternatives | Permitted; used for Heading 3 | AFB is more permissive than ACB or APH |
| **Em-dash** | Not addressed | Not addressed | No spaces before or after | Useful for FAQ guidance |
| **Line spacing** | 1.5 digital / 1.15 print | 1.25 | Double space (for review) | Three different values; AFB not for production |
| **Numbers** | Not specified in detail | Not specified in detail | Detailed rules: 1--9 spelled out; numerals for 10+; spell out "percent"; no apostrophe in decades | Apply to tool documentation |
| **Terminology** | Not addressed | Not addressed | Comprehensive field-specific list | Apply across all tool documentation |
| **Spelling conventions** | Not stated | Not stated | large print (n); large-print (adj) | Apply in this tool's UI and docs |
| **Style authority** | ACB Board of Publications | APH research document | APA + Chicago Manual of Style | Different authorities; different purposes |

---

#### Proposed Actions

**Action A -- Apply AFB terminology to tool UI and documentation (Small, immediate):**

Review all existing UI strings, FAQ text, guidelines page, and README for:
- "the blind" → "people who are blind"
- "e.g." in running text → "for example"
- Uppercase "Braille" → lowercase "braille" (unless referring to Louis Braille)
- "large print" / "large-print" spelling (noun vs. adjective) -- confirm consistent usage throughout
- "visual loss" → "vision loss"
- "low vision persons" → "persons with low vision"
- "normal" (value-laden) → neutral alternatives
- "the AFB" / "the ACB" → "AFB" / "ACB" (no "the" before acronyms)

**Action B -- Add to the Guidelines page (`/guidelines`) (Small):**

Add a section "About These Guideline Sets" that:
- Explains ACB and APH are the two large print production standards supported by this tool
- Notes that AFB (JVIB) is a manuscript submission standard for academic authors, not a large print production standard, and is out of scope for this tool's fix engine
- Links to all three organizations
- Clarifies when each applies: consumer/member publications → ACB; educational/student materials → APH; academic JVIB submission → use AFB JVIB guidelines directly, outside this tool

**Action C -- Add to FAQ (Small, implement with Issue 7):**

- "Is the AFB Style Guide the same as a large print standard?" → No. It is JVIB manuscript submission formatting (12pt Calibri, ALL CAPS headings). For large print production, use ACB or APH, both of which this tool supports.
- "I've seen references to AFB large print recommendations online. Which guidelines does this tool follow?" → AFB does not publish a separate large print production standard. This tool follows ACB (default) and APH (opt-in).
- "What is the correct spelling: 'large print' or 'large-print'?" → "Large print" as a noun (e.g., "This document is in large print"); "large-print" as a modifier (e.g., "a large-print edition"). Per AFB JVIB style guidelines.

**Action D -- Em-dash and numbers guidance in FAQ (Small):**

- Em-dash: use Word's Insert Symbol or two hyphens (--) with no spaces before or after. Applies to all three guideline contexts.
- Numbers in running text: spell out one through nine; numerals for 10 and above; spell out "percent" (do not use the % symbol); no apostrophe in decades (1990s, not 1990's). Per AFB style.

---

#### Files Affected

- `web/src/acb_large_print_web/templates/guidelines.html` -- "About These Guideline Sets" section
- `web/src/acb_large_print_web/templates/faq.html` -- AFB scoping FAQ, em-dash, numbers, spelling
- `web/src/acb_large_print_web/templates/base.html` -- review "the blind," "the AFB" terminology
- All template files -- terminology audit (large print, braille, person-first language, "vision loss")
- `README.md` -- apply AFB terminology conventions
- `docs/` -- apply AFB terminology conventions across documentation files

#### No Changes Required

- `desktop/src/acb_large_print/constants.py` -- no new AFB constants; AFB is not a fix/audit mode
- `desktop/src/acb_large_print/auditor.py` -- no new rules
- `desktop/src/acb_large_print/fixer.py` -- no new fix logic
- `web/src/acb_large_print_web/templates/fix_form.html` -- no "AFB mode" radio button
- `office-addin/src/` -- no changes needed

---

## Prioritized Work Order

| Priority | Issue | Effort | Impact |
| -------- | ----- | ------ | ------ |
| 1 | Issue 5: Preserve centered headings option | Medium | High -- direct complaint, clear design |
| 2 | Issue 2: Quick exception checkboxes for common rule waivers | Medium | High -- benefits all publishers with intentional raw URLs |
| 3 | Issue 7: FAQ page | Medium | Medium -- prevents repeat questions |
| 4 | Issue 9, Phase 1--3: Guideline set selector (ACB/APH) + guidelines page + backend | Large | Medium -- directly addresses Jeff's APH question |
| 5 | Issue 10, Actions A+B+C: AFB terminology + guidelines scoping + FAQ | Small | Medium -- documentation quality (independent third source; not a replacement for ACB) |
| 6 | Issue 6: Soft-return heading formatting (Option A -- document) | Small | Low -- FAQ entry only for now |
| 7 | Issue 8: Per-level list indentation (Gap B) | Medium | Low -- confirm use case with Jeff first |
| 8 | Issue 9, Phase 5: Office add-in + desktop app APH sync | Medium | Low -- after web is stable |
