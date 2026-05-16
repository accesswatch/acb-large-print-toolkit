# PDF Form Round-Trip Plan

## Purpose

This document lays out a practical plan for GLOW to inspect PDF forms, render an accessible web form, let a helper enrich missing structure, and write the data back into the PDF when the source document supports it.

The plan aims to be useful in the real world, not just technically impressive in a demo. The product should feel magical where it can, but it must stay explicit about uncertainty, unsupported inputs, and when human review is required.

## Product Vision

The target workflow is:

1. A user uploads a PDF.
2. GLOW determines whether the PDF is a real interactive form, a partially structured form, or only a visual form.
3. GLOW extracts every field it can find.
4. GLOW builds an accessible HTML form from that extraction.
5. A helper can review and enrich anything missing: labels, help text, option names, grouping, expected data type, required state, and reading order.
6. GLOW saves that enriched definition as a reusable template profile for the same form in the future.
7. A user or helper fills the accessible web form.
8. GLOW writes the values back into the source PDF when the PDF is a supported round-trip candidate.
9. GLOW also returns structured JSON so the data is never trapped inside the PDF.

That workflow supports two kinds of users:

1. A person filling out a form directly.
2. A person assisting someone else and building a better accessible representation of the form over time.

## Core Principle

PDF form handling must be treated as a confidence-based system with human correction, not as a perfect parser.

GLOW should always distinguish between:

1. What the PDF explicitly says.
2. What GLOW inferred from geometry, names, or heuristics.
3. What a human helper confirmed.

That distinction is the foundation of trust.

## What We Are Building

The feature is not just "fill a PDF." It is a layered system with four major capabilities:

1. PDF form inspection and eligibility classification.
2. Accessible form reconstruction.
3. Human-assisted metadata enrichment.
4. PDF write-back and export.

The enrichment layer is the part that makes this more than a thin wrapper over a PDF library.

## Supported Input Classes

The following table defines the product support model for input PDFs.

| Input class | Description | Round-trip support | Notes |
| --- | --- | --- | --- |
| AcroForm with widgets | Standard interactive PDF form with page widgets | Yes | Primary v1 target |
| AcroForm with weak metadata | Real fields exist, but labels or tooltips are poor | Yes, with warnings | Strong candidate for helper enrichment |
| AcroForm with incomplete widgets | Field tree exists but widget data is partial or odd | Limited | Allow if field identity is stable |
| Hybrid form | Mixed AcroForm and unusual viewer behavior | Limited | Case-by-case support |
| XFA form | Adobe XML Forms Architecture | No in v1 | Reject clearly |
| Flattened PDF | Former fields burned into page content | No round-trip | Offer assistive transcription path |
| Static visual form | Looks like a form but has no real fields | No round-trip | Requires template capture and overlay mode |
| Scanned form | Image-only or mostly image-based PDF | No round-trip in v1 | Route to OCR workflow |
| Signed form | Digital signature present | Read-only or reject | Any write-back may invalidate signature |

## Product Modes

The system should expose three product modes rather than one.

### 1. Native Round-Trip Mode

Use this when the PDF is a supported AcroForm.

Behavior:

1. Extract fields.
2. Render accessible HTML.
3. Let a helper enrich missing metadata.
4. Write values back to the original PDF.

### 2. Assisted Template Mode

Use this when the PDF has some useful structure but is incomplete.

Behavior:

1. Extract what can be trusted.
2. Ask the helper to supply missing labels, options, group semantics, and ordering.
3. Save the enriched template.
4. Attempt write-back only for fields mapped to real PDF form objects.

### 3. Accessible Surrogate Mode

Use this when the PDF is not really fillable.

Behavior:

1. Build an accessible surrogate form from OCR, visual detection, or manual helper input.
2. Export JSON and an accessible HTML record.
3. Optionally produce an overlay PDF or companion packet.
4. Do not pretend the original PDF is truly interactive.

This mode still has value for assisted completion, even when round-trip write-back is impossible.

## User Journeys

### Journey A: Direct fill of a good PDF

1. Upload PDF.
2. GLOW classifies it as a supported AcroForm.
3. GLOW extracts fields and renders a usable web form.
4. User fills it out.
5. GLOW returns a filled PDF and JSON.

### Journey B: Helper builds a better version of the form

1. Upload PDF.
2. GLOW extracts fields but some labels and options are weak.
3. Helper opens a form-definition review screen.
4. Helper corrects labels, adds help text, groups radios, fixes option names, marks required fields, and reorders controls.
5. GLOW saves those corrections as a template profile.
6. Future uploads of the same form start from the enriched profile.

### Journey C: Static visual form that is not truly interactive

1. Upload PDF.
2. GLOW classifies it as non-round-trip.
3. GLOW offers a helper workflow to create an accessible surrogate form.
4. User completes the surrogate form.
5. GLOW exports JSON, an accessible HTML summary, and optionally an overlay or companion output.

## What "Magical" Means in Practice

The system should feel magical in four ways:

1. It finds more structure than a naive parser would.
2. It makes useful guesses without hiding that they are guesses.
3. It learns from helper corrections for future uploads.
4. It always leaves the user with structured data, even if the PDF itself cannot be rewritten cleanly.

The system should not be magical in the dishonest sense. It must never silently invent certainty.

## Heuristic Inference System

The heuristic engine is how GLOW can recover missing meaning from imperfect PDFs.

Every inferred property should store:

1. `value`
2. `confidence`
3. `evidence_sources`
4. `human_confirmed`

### Signals to use

#### 1. Explicit field metadata

Highest-trust sources:

1. field name
2. alternate name or tooltip
3. mapping name
4. field type
5. choice list values
6. export values
7. default value
8. required or readonly flags

#### 2. Field name parsing

Transform names like:

1. `firstName` to `First Name`
2. `applicant.address.city` to `Applicant Address City`
3. `q12_yes` to `Question 12 - Yes`
4. `dependent_3_dob` to `Dependent 3 Date of Birth`

This requires:

1. camelCase splitting
2. underscore splitting
3. dot-path grouping
4. abbreviation expansion
5. ordinal and row parsing
6. noise-token removal such as `fld`, `txt`, `cb`, `rb`, `grp`

#### 3. Geometry-based nearby text

For widgets that have page coordinates, inspect nearby visible text blocks:

1. immediately left of the field
2. immediately above the field
3. on the same baseline
4. adjacent to a checkbox or radio circle
5. within the local section heading region

This is a major source of label recovery for poorly-authored forms.

#### 4. Option semantics

Infer likely meaning from option sets:

1. state abbreviations suggest a state selector
2. `Yes`, `No` suggests boolean confirmation
3. `Mr`, `Ms`, `Dr` suggests honorific
4. month names suggest date-related semantics

#### 5. Shape and size

Use widget geometry to infer probable field purpose:

1. very short field may be ZIP, month, day, or state
2. multiline rectangle may be comments or address
3. repeated short fields in a row may be phone or date segments

#### 6. Repetition patterns

Infer repeated groups from naming and layout:

1. `child1_name`, `child1_dob`
2. `child2_name`, `child2_dob`
3. `employer_1_name`, `employer_2_name`

That can drive sectioning and fieldset generation.

#### 7. Section context

Nearby headings and instructional text should influence interpretation.

Examples:

1. `city` inside `Mailing Address` should become `Mailing Address City`
2. `phone` inside `Emergency Contact` should become `Emergency Contact Phone`

#### 8. Existing values

Prefilled values can improve classification:

1. date-like content
2. phone-number patterns
3. email patterns
4. ZIP patterns

### Confidence Model

The following table summarizes the scoring model. The exact numbers can be tuned during implementation.

| Signal | Example contribution |
| --- | --- |
| Explicit tooltip or alternate label | +40 |
| Exact nearby left or above label | +30 |
| Strong parsed field-name match | +20 |
| Known option-set semantic match | +15 |
| Section heading context | +10 |
| Size and shape agreement | +10 |
| Repetition template match | +10 |
| Conflicting nearby text candidates | -20 |
| Ambiguous internal field name | -15 |
| Missing widget geometry | -25 |

Suggested bands:

1. `0.85` and above: high confidence
2. `0.60` to `0.84`: medium confidence
3. below `0.60`: low confidence and helper review required

## Human-Assisted Enrichment Workflow

This is the heart of the plan.

The helper review screen should let someone richly define what the PDF is missing.

For each extracted field, the helper must be able to edit:

1. display label
2. help text or instructions
3. control type
4. required state
5. readonly state
6. placeholder text for the web form
7. group membership
8. section membership
9. display order
10. validation type such as email, phone, date, numeric, ZIP
11. normalization rules such as uppercase state abbreviation
12. field options for dropdowns, radios, and checkboxes
13. human-friendly option labels separate from PDF export values
14. mapping to PDF object or widget identifier
15. whether the field is safe for write-back

The helper should also be able to create missing structure:

1. add a label where the PDF only has a cryptic field name
2. split a bad radio group into meaningful options
3. merge multiple widgets into one logical field
4. add section headings and fieldsets
5. mark ambiguous fields as "needs confirmation"
6. suppress junk fields that exist in the PDF but should not be shown

### Helper actions at the form level

The helper should also be able to define:

1. form title
2. form description
3. page descriptions
4. section headings
5. reading order overrides
6. repeated row templates
7. completion notes for the assisted user
8. export behavior: editable PDF, flattened PDF, JSON only, surrogate only

## Template Memory

GLOW should store corrected form definitions as reusable template profiles.

Each profile should include:

1. a PDF fingerprint
2. document title if available
3. page count
4. stable field signatures
5. helper-supplied labels and help text
6. corrected option lists
7. ordering overrides
8. grouping rules
9. validation rules
10. known write-back-safe mappings

The system should try to reapply the profile on future uploads of the same or nearly identical form.

### Fingerprint strategy

Use a layered fingerprint:

1. file-level hash for exact match
2. normalized field-tree signature
3. page-count and widget-count signature
4. relaxed similarity score for minor version changes of the same form

This allows the system to reuse helper knowledge even when the PDF changes slightly.

## Standards and Authoritative Constraints

The implementation needs to respect the fact that three different concerns are in play.

### 1. PDF form mechanics

This is the raw PDF question:

1. does the PDF contain an AcroForm field tree
2. do the pages contain widget annotations
3. can values be written back without corrupting the file
4. can appearance streams be made reliable across viewers

This is not the same thing as accessibility.

### 2. PDF accessibility semantics

This is the tagged-PDF and PDF/UA question:

1. does the PDF expose structure and relationships to assistive technology
2. are labels, instructions, and grouping expressed semantically
3. does the PDF remain usable in assistive reading workflows

This matters greatly, but many real PDFs with fillable fields are weak here.

### 3. Accessible web form reconstruction

This is the HTML and WCAG 2.2 AA question:

1. can GLOW represent the form in a screen-reader-friendly, keyboard-friendly web UI
2. can labels, grouping, errors, and instructions be made explicit
3. can the interaction model be made better than the source PDF

This is where DAISY guidance is especially relevant.

### What the standards imply for GLOW

The standards landscape implies several non-negotiable truths:

1. a fillable PDF is not automatically an accessible PDF
2. a tagged PDF is not automatically a well-labeled or assistive-friendly form
3. WCAG-quality HTML reconstruction is often more achievable than direct remediation of the original PDF
4. writing values back into a PDF does not make the PDF/UA problem solved

## ISO Technical Inspection Framework

This section defines the complete standards-inspection model for PDF form work in GLOW.

The goal is to make standards coverage explicit, testable, and auditable across machine checks and human review.

### Inspection scope

The ISO inspection should treat each uploaded document as an evidence package evaluated across these standards domains:

1. PDF core and form mechanics (ISO 32000 family)
2. Accessible PDF semantics (ISO 14289 family, PDF/UA)
3. Workflow profile expectations when relevant (for example WTPDF profile checks used by validator ecosystems)
4. HTML reconstruction conformance for user interaction (WCAG 2.2 AA baseline)

### Clause-family inspection map

Inspection should be organized by requirement families rather than by tool output order.

#### Family A: Identification and metadata

Verify:

1. metadata stream presence and type
2. document title availability
3. display title preference state
4. PDF/UA identification schema presence and expected part/revision values for target conformance mode

Evidence sources:

1. metadata dictionary and XMP package extraction
2. validator rule hits for identification and metadata requirements

#### Family B: Tagged structure integrity

Verify:

1. MarkInfo tagged state
2. StructTreeRoot presence
3. structure parent linkage integrity
4. role-map validity and no circular mapping
5. real-content versus Artifact separation

Evidence sources:

1. raw object inspection
2. validator failures for structure-tree and role-map rule families

#### Family C: Structural semantics and reading model

Verify:

1. heading strategy consistency
2. list and table structural constraints
3. language tagging at catalog and local levels
4. caption and referencing semantics where applicable

Evidence sources:

1. validator rules for heading/list/table/lang families
2. helper review for semantic intent in ambiguous regions

#### Family D: Form and annotation semantics

Verify:

1. widget and form structure tagging expectations
2. annotation containment and allowed subtype behavior
3. tab-order keys for annotated pages
4. XFA exclusion requirements for conformance modes that disallow XFA

Evidence sources:

1. AcroForm and annotation object inspection
2. validator rule outcomes for form and annotation families

#### Family E: Text and font mapping reliability

Verify:

1. embedded font coverage where required
2. Unicode mapping availability
3. .notdef prohibition checks
4. private-use-area handling constraints

Evidence sources:

1. font dictionary and mapping inspection
2. validator rule outcomes for text and font families

#### Family F: Navigation and destination semantics

Verify:

1. destination strategy suitability for profile target
2. TOC or TOCI reference integrity where present
3. internal link target consistency

Evidence sources:

1. destination object extraction
2. validator rule outcomes for destination and TOC families

### Machine validator stack

Use a multi-validator posture because no single engine is authoritative for every practical edge case.

Primary automated evidence should include:

1. a ruleset-based validator pass for PDF/UA-1, PDF/UA-2, and relevant profile checks
2. a secondary validator pass for cross-tool disagreement detection
3. local heuristic diagnostics from GLOW extraction for field mapping and geometry context

Automated output should be normalized into a single internal finding format:

1. requirement family
2. rule identifier
3. severity
4. affected object references
5. machine confidence
6. remediation hint

### Human verification gates

Certain checkpoints should never be considered closed from machine output alone.

Mandatory helper-review gates:

1. ambiguous label and instruction recovery
2. radio or checkbox grouping semantics when layout is unclear
3. section and reading order correctness for assistive interaction
4. error-message clarity and required-state communication in HTML reconstruction

Each gate should produce a review outcome:

1. accepted
2. accepted with caveat
3. unresolved and blocked for conformance claim

### Conformance claim policy

GLOW should separate operational outcomes from formal conformance claims.

Operational outcomes:

1. write-back eligible
2. write-back limited
3. surrogate-only

Conformance outcomes:

1. no claim
2. partial claim with listed unresolved checkpoints
3. claim candidate pending licensed-text legal review

### Licensed-text verification gate

Clause-level legal conformance statements require direct review against licensed ISO publications.

Therefore:

1. validator mappings and public technical summaries can drive engineering behavior
2. formal external conformance assertions must pass a documented licensed-text verification checkpoint
3. if licensed-text verification is not completed, output must be labeled as engineering assessment only

### Acceptance checklist for implementation

A document-level ISO inspection is complete only when all items below are satisfied:

1. document classified into the correct support mode
2. machine validator passes executed and normalized
3. all high-severity findings triaged to disposition
4. helper-review gates completed for ambiguous semantics
5. write-back safety decision recorded with evidence
6. reconstruction accessibility checks completed against WCAG 2.2 AA requirements
7. conformance claim status explicitly set to no claim, partial, or claim candidate

### Traceability artifacts

Store the following artifacts for each inspected document:

1. normalized validator findings
2. helper review decisions and rationale
3. template version used or produced
4. submission and write-back diagnostics
5. final inspection summary with requirement-family status matrix

### DAISY guidance that should shape the web form

The system therefore needs to treat PDF write-back and accessible interaction as related but separate deliverables.

### DAISY guidance that should shape the web form

The DAISY Accessible Publishing Knowledge Base is directly relevant to the surrogate and reconstructed HTML form layer.

Its form guidance reinforces that accessible forms must:

1. use explicit labels
2. group related controls such as checkbox and radio sets
3. identify required fields
4. identify and explain input errors
5. use `aria-describedby` for supporting instructions when the label alone is not enough
6. avoid relying on visual layout alone for understanding

That should become a hard requirement for the GLOW review and fill flows.

### PDF/UA reality for this project

For this project, PDF/UA should be treated as a validation and aspiration layer, not as something the open-source Python stack can guarantee for arbitrary existing forms.

The accurate product stance is:

1. GLOW can inspect and fill many AcroForm PDFs
2. GLOW can reconstruct an accessible HTML form that follows WCAG 2.2 AA patterns
3. GLOW cannot claim that rewriting field values alone makes an arbitrary source PDF PDF/UA conformant
4. if PDF/UA remediation becomes a formal requirement, it will likely require a narrower source profile, dedicated remediation logic, or commercial tooling

## Field Definition Studio

The helper workflow should be formalized as a Field Definition Studio rather than treated as a simple edit screen.

This studio is where GLOW turns raw PDF extraction into a durable, accessible form model.

### Studio goals

The studio should let a helper:

1. understand what the PDF contains
2. correct or enrich what the PDF is missing
3. organize the form into meaningful sections and groups
4. preview the accessible web experience before the end user sees it
5. preserve exact write-back mappings separately from human-friendly labels

### Studio information architecture

The studio should be organized into five regions.

#### 1. Form overview panel

This panel should show:

1. document title
2. form classification
3. support status
4. page count
5. number of extracted fields
6. number of unresolved low-confidence fields
7. number of unsupported or suppressed fields

#### 2. Field inventory panel

This panel should show every extracted logical field as a keyboard-navigable list or table.

Each row should include:

1. visible label or fallback label
2. raw PDF field name
3. field type
4. section membership
5. confidence badge
6. write-back status
7. unresolved warnings

This inventory should support keyboard filtering and sorting.

#### 3. Field editor panel

This panel should allow detailed editing of the selected field.

Editable properties should include:

1. display label
2. short label for compact views
3. help text
4. required state
5. readonly state
6. field type override when safe
7. validation type
8. placeholder text for HTML only
9. autocomplete hint when appropriate
10. visible option labels
11. export value mapping
12. write-back-safe flag

#### 4. Form organization panel

This panel should let a helper define:

1. sections
2. section descriptions
3. subsection order
4. fieldset membership
5. repeatable row groups
6. page-to-section mapping where helpful

#### 5. Preview panel

This panel should render the accessible HTML version of the form using the current reviewed definition.

The preview should make it easy to test:

1. heading structure
2. label clarity
3. radio and checkbox grouping
4. required-field announcements
5. error messaging
6. tab order

### Field definition richness

The field definition model should be richer than the PDF model.

Each reviewed field should be able to carry:

1. a human-facing label
2. a human-facing description
3. a machine write-back mapping
4. visible options and machine export values
5. a section and subgroup placement
6. a preferred control presentation in HTML
7. a confidence state
8. a provenance record showing whether the value came from the PDF, heuristics, AI suggestion, or a human review

### Why rich field definitions matter

This richness is what lets GLOW avoid two common failures:

1. a technically correct but unusable web form
2. a nice web form that can no longer write back to the source PDF

The model must preserve both human meaning and machine mapping.

## Accessible Web Form Requirements

The generated web form must be better than the original PDF from an accessibility standpoint.

Requirements:

1. semantic labels for every control
2. `fieldset` and `legend` for grouped radios and related controls
3. explicit error summary plus inline errors
4. keyboard-only full operability
5. high-contrast and zoom-safe layout
6. visible page and section context where useful
7. no dependence on spatial PDF layout for comprehension
8. helper notes and descriptions exposed as normal text, not only as tooltips
9. support for screen readers, magnification, and switch control workflows

## Keyboard and WCAG 2.2 AA Design Requirements

The review and fill experiences should be designed as first-class accessible applications, not as PDF utilities with accessibility added later.

### Review studio keyboard model

The Field Definition Studio should support:

1. full tab access to every actionable control
2. visible focus indicators at all times
3. keyboard-operable filter, sort, and navigation controls
4. arrow-key navigation only where it matches established widget patterns
5. no keyboard traps in side panels, dialogs, or preview regions
6. a skip link or equivalent jump controls for large review screens

If a grid or listbox pattern is used, it must follow the established ARIA interaction model consistently. If the team cannot maintain that fidelity, use simpler native HTML patterns.

### Fill form keyboard model

The end-user fill page should support:

1. linear tab order that follows the reviewed logical order, not the PDF geometry
2. `fieldset` and `legend` for every radio group and related set of controls
3. Enter and Space behavior consistent with native HTML controls
4. reliable submission and error recovery without moving keyboard users unpredictably
5. no drag-and-drop-only interactions

### Error handling model

The fill page should include:

1. a top-level error summary on failed submission
2. inline field errors adjacent to each failing field
3. `aria-invalid` only after a validation failure is known
4. `aria-describedby` wiring from each field to help and error text
5. clear required-state exposure in both visual and programmatic form

### WCAG 2.2 AA topics that matter most here

For this feature, the most important success criteria to explicitly design for are:

1. Info and Relationships
2. Labels or Instructions
3. Error Identification
4. Focus Visible
5. Dragging Movements, by ensuring no drag-only requirement exists
6. Target Size, for pointer users on review controls and dense form editors
7. Consistent Help, so helper guidance appears in stable locations

### Safe UI pattern preference

Use native HTML whenever possible:

1. `input`
2. `select`
3. `textarea`
4. `fieldset`
5. `legend`
6. `details` and `summary` only where their behavior helps, not where they hide critical instructions

Avoid custom composite widgets unless they materially improve the workflow and can be implemented accessibly.

The goal is not to reproduce the page visually. The goal is to produce an accessible interaction model.

## Architecture for GLOW

The implementation should follow GLOW's current pattern of shared core logic in `desktop/src/acb_large_print/` and web routes in `web/src/acb_large_print_web/`.

### Proposed core modules

1. `desktop/src/acb_large_print/pdf_form_classifier.py`
2. `desktop/src/acb_large_print/pdf_form_extract.py`
3. `desktop/src/acb_large_print/pdf_form_infer.py`
4. `desktop/src/acb_large_print/pdf_form_template.py`
5. `desktop/src/acb_large_print/pdf_form_fill.py`
6. `desktop/src/acb_large_print/pdf_form_models.py`

### Proposed web modules

1. `web/src/acb_large_print_web/routes/pdf_forms.py`
2. `web/src/acb_large_print_web/templates/pdf_forms_upload.html`
3. `web/src/acb_large_print_web/templates/pdf_forms_review.html`
4. `web/src/acb_large_print_web/templates/pdf_forms_fill.html`
5. `web/src/acb_large_print_web/templates/pdf_forms_result.html`

### Proposed feature flags

1. `GLOW_ENABLE_PDF_FORM_ROUNDTRIP`
2. `GLOW_ENABLE_PDF_FORM_TEMPLATE_MEMORY`
3. `GLOW_ENABLE_PDF_FORM_SURROGATE_MODE`
4. `GLOW_ENABLE_PDF_FORM_AI_ASSIST`

## Data Model

The following entities should exist in the implementation.

### 1. Extracted form document

Stores raw machine extraction.

Key properties:

1. document id
2. classification
3. eligibility
4. warnings
5. pages
6. fields
7. widgets

### 2. Enriched form template

Stores helper-confirmed structure.

Key properties:

1. template id
2. document fingerprint
3. version
4. human-edited labels
5. field groups
6. ordering
7. validation rules
8. write-back rules
9. display rules

### 3. Submission payload

Stores end-user answers.

Key properties:

1. submission id
2. template id
3. field values
4. validation state
5. write-back result
6. generated files

## Storage Strategy

The first implementation can use SQLite in the instance directory, consistent with existing lightweight persistence patterns in the web app.

Suggested tables:

1. `pdf_form_templates`
2. `pdf_form_fields`
3. `pdf_form_options`
4. `pdf_form_submissions`
5. `pdf_form_reviews`
6. `pdf_form_fingerprints`

Binary outputs should stay in the existing temp-file model, not in the database.

## Data Storage Architecture

This section defines the concrete storage architecture for implementation.

### Storage layers

The feature should use three storage layers with clear responsibilities.

#### 1. Ephemeral upload and output storage

Purpose:

1. hold uploaded source PDFs
2. hold intermediate extraction artifacts
3. hold generated filled PDF outputs

Implementation:

1. reuse the existing tokenized temp directory model from the web upload system
2. keep files under request-scoped or session-scoped token directories
3. clean up by TTL and explicit completion cleanup

Retention:

1. short-lived only
2. no long-term persistence by default

#### 2. Persistent metadata and template storage

Purpose:

1. store extracted field metadata
2. store helper-reviewed field definitions
3. store reusable template mappings and fingerprints
4. store diagnostic events and outcomes

Implementation:

1. SQLite database in `instance/` for v1 and early v2
2. schema versioning with forward-only migrations
3. JSON columns for flexible metadata where relational shape would be too rigid

Retention:

1. template metadata is long-lived
2. reviewed definitions are versioned, not overwritten in place

#### 3. Submission record storage

Purpose:

1. record fill submissions and write-back results
2. support auditing and troubleshooting
3. preserve structured JSON payloads when allowed by policy

Implementation:

1. SQLite records keyed to template version and submission id
2. optional payload minimization mode for privacy-sensitive deployments

Retention:

1. configurable via policy
2. default to short retention unless explicit persistence is enabled

### Database location and naming

Use `Path(current_app.instance_path)` to align with existing GLOW persistence patterns.

Suggested database path:

1. `instance/pdf_forms.db`

This keeps PDF-form persistence isolated from unrelated feature databases.

### Logical data model

The following logical entities should exist in the storage model.

#### 1. Source documents

Tracks uploaded documents at the metadata level.

Key fields:

1. document id (UUID)
2. upload token
3. original filename
4. sha256 digest
5. page count
6. detected form class
7. eligibility status
8. created at
9. expires at

#### 2. Extraction snapshots

Stores machine extraction results from a specific run.

Key fields:

1. extraction id (UUID)
2. document id
3. extractor version
4. extraction json
5. confidence summary
6. warning summary
7. created at

#### 3. Template fingerprints

Maps form signatures to reusable reviewed templates.

Key fields:

1. fingerprint id (UUID)
2. exact hash
3. normalized signature hash
4. page count
5. widget count
6. similarity profile json
7. created at

#### 4. Reviewed templates

Represents helper-reviewed form definitions.

Key fields:

1. template id (UUID)
2. fingerprint id
3. template version
4. title
5. description
6. status (draft, active, retired)
7. created by
8. created at
9. supersedes template id

#### 5. Reviewed fields

Stores the reviewed field definitions used to render accessible HTML and map write-back.

Key fields:

1. reviewed field id (UUID)
2. template id
3. raw pdf field name
4. widget refs json
5. display label
6. help text
7. control type
8. required flag
9. readonly flag
10. section key
11. display order
12. write-back policy
13. confidence
14. provenance json

#### 6. Reviewed options

Stores option label and export mappings for discrete-choice fields.

Key fields:

1. option id (UUID)
2. reviewed field id
3. display label
4. export value
5. order index
6. selected by default flag

#### 7. Submissions

Stores form completion events.

Key fields:

1. submission id (UUID)
2. template id
3. template version
4. status (draft, submitted, written, failed)
5. submitted by
6. submitted at
7. write-back outcome
8. diagnostic json

#### 8. Submission values

Stores field-level answers for a submission.

Key fields:

1. submission value id (UUID)
2. submission id
3. reviewed field id
4. submitted value text
5. submitted value json for multi-select cases
6. normalized value
7. validation state

#### 9. Output artifacts

Tracks generated files and download metadata.

Key fields:

1. artifact id (UUID)
2. submission id
3. artifact type (pdf_editable, pdf_flattened, json, report)
4. token
5. relative path
6. mime type
7. file size
8. created at
9. expires at

### Physical SQLite schema design

Use normalized core tables plus JSON columns for flexible metadata.

Recommended table set:

1. `pdf_form_documents`
2. `pdf_form_extractions`
3. `pdf_form_fingerprints`
4. `pdf_form_templates`
5. `pdf_form_template_fields`
6. `pdf_form_template_options`
7. `pdf_form_submissions`
8. `pdf_form_submission_values`
9. `pdf_form_artifacts`
10. `pdf_form_events`

### Index strategy

Create explicit indexes for expected access paths.

Required indexes:

1. `pdf_form_documents(sha256)`
2. `pdf_form_fingerprints(exact_hash)`
3. `pdf_form_fingerprints(normalized_hash)`
4. `pdf_form_templates(fingerprint_id, status, template_version)`
5. `pdf_form_template_fields(template_id, section_key, display_order)`
6. `pdf_form_submissions(template_id, submitted_at)`
7. `pdf_form_artifacts(submission_id, artifact_type)`

Optional full-text indexes can be added later for helper search across field labels and help text.

### Event and audit log model

Store lifecycle events as append-only rows in `pdf_form_events`.

Event examples:

1. document_uploaded
2. extraction_completed
3. template_created
4. template_published
5. submission_validated
6. writeback_started
7. writeback_succeeded
8. writeback_failed
9. artifact_downloaded

Each event should include:

1. actor type
2. actor id where available
3. correlation id
4. payload json
5. timestamp

This is critical for debugging difficult PDF edge cases.

### Versioning strategy

Template and schema versioning should be explicit.

Template versioning:

1. immutable template versions
2. editable drafts branch from a prior version
3. publication creates a new active version
4. old versions remain queryable for historical submissions

Schema versioning:

1. one migration ledger table such as `pdf_form_schema_migrations`
2. forward-only migrations
3. startup migration check in app initialization

### Data retention and cleanup

Retention needs to separate temporary artifacts from durable metadata.

Recommended defaults:

1. uploaded source files: short TTL (for example 1 to 24 hours)
2. generated artifacts: short TTL unless user explicitly saves
3. submission value records: policy-driven TTL
4. templates and reviewed definitions: durable
5. event logs: longer retention but bounded by size policy

Cleanup jobs:

1. file cleanup for expired token directories
2. DB cleanup for expired artifacts and old submission payloads
3. periodic compaction and vacuum scheduling

### Privacy and sensitive-data controls

Because forms may contain personal data, storage controls must be explicit.

Controls:

1. configurable submission payload persistence mode:
2. mode A: full payload retention
3. mode B: metadata-only retention with payload hash
4. mode C: no persistence beyond generated output window
5. explicit redaction hooks before persistence
6. separation of template metadata from user-submitted values

The policy should be deployment-configurable through environment flags.

### Concurrency and integrity

SQLite is appropriate for v1 if writes are disciplined.

Approach:

1. short transactions
2. WAL mode enabled
3. explicit retry for transient lock contention
4. idempotency keys for inspect and fill operations
5. unique constraints on template version tuples

### Failure recovery model

The storage architecture should support safe partial failure recovery.

Requirements:

1. extraction can fail without leaving half-created templates
2. submission failure preserves diagnostics and user-safe recovery guidance
3. write-back failure does not delete the validated JSON payload
4. artifact generation failure does not corrupt submission status transitions

Recommended status machine for submissions:

1. draft
2. validated
3. writeback_in_progress
4. writeback_failed
5. writeback_succeeded
6. artifact_ready

### Example storage lifecycle

A typical successful flow should look like:

1. upload creates token directory and document metadata row
2. extraction creates extraction snapshot row
3. helper review creates template version rows
4. submission creates submission and submission value rows
5. write-back updates submission status and diagnostic fields
6. artifact rows are created with expiry timestamps
7. cleanup removes expired files and artifact metadata

## Library Strategy

Start with the libraries already in the repo.

### Primary open-source stack

1. PyMuPDF for widget inspection, geometry, text extraction, and page-local analysis
2. pypdf for AcroForm reads, field-tree access, write-back, and flattening
3. pikepdf as an optional low-level support library for repair-oriented PDF handling, metadata work, and appearance-stream support when the higher-level libraries hit malformed files

This is the correct default because both are already present in the project dependencies.

### Open-source library roles

The current best-fit division of labor is:

| Library | Best role in GLOW | Strengths | Important limitations |
| --- | --- | --- | --- |
| PyMuPDF | extraction and inspection | widgets, field labels, field values, choice values, coordinates, script metadata, fast page-local inspection | not a turnkey PDF/UA remediation stack |
| pypdf | write-back and export | `get_fields()`, `update_page_form_field_values()`, flattening flow, AcroForm tree access | appearance fidelity and viewer behavior still require testing; not a complete XFA or PDF/UA solution |
| pikepdf | low-level support | AcroForm helper, appearance stream generation, metadata editing, PDF repair-friendly object model | higher-level form helper has real limitations, including duplicate-name problems and no signature support |
| PyPDFForm | optional abstraction layer | simple high-level fill API for text, checkbox, radio, dropdown, image, and signature-image style workflows | less transparent than using the core stack directly; should be treated as optional, not foundational |
| pypdfium2 | optional preview and rendering support | strong rendering and flattening support, useful for preview fidelity and form rendering checks | not needed for a first implementation unless rendering validation becomes a pain point |

### Recommended stack decision

The best technical starting point is:

1. PyMuPDF for extraction
2. pypdf for write-back
3. pikepdf held in reserve as a support library when malformed PDFs or appearance regeneration become blockers

That gives GLOW a clean architecture without prematurely depending on a heavier rendering stack.

### What the open-source stack can do accurately

The current open-source Python stack can accurately support:

1. AcroForm presence detection
2. widget enumeration
3. field name and basic label extraction
4. option extraction for common choice controls
5. page-local geometry inspection
6. text-near-widget heuristics
7. write-back for common field types
8. flattening for distribution copies

### What the open-source stack cannot honestly promise by itself

The current open-source Python stack should not be described as automatically providing:

1. full XFA support
2. signature-preserving workflows
3. full PDF/UA remediation for arbitrary source PDFs
4. universal viewer-consistent appearance regeneration for every malformed or exotic form
5. turnkey assistive semantics for forms whose source PDF lacks trustworthy structure

### Optional commercial upgrade path

If open-source behavior proves too inconsistent for production quality, evaluate a commercial SDK.

Evaluation criteria:

1. accurate AcroForm and XFA coverage
2. robust appearance regeneration
3. stable write-back across Acrobat, Edge, and Chrome viewers
4. Python or service-friendly integration
5. permissive deployment model for a web application
6. reasonable annual cost relative to user value

Possible categories to evaluate:

1. full PDF SDKs with strong form APIs
2. server-side PDF rendering and write-back services
3. hybrid browser plus server SDKs if they materially improve accessibility review workflows

Commercial evaluation should happen only after the open-source spike produces clear failure cases.

## Role of AI

AI is the force multiplier that makes this feature workable at real-world quality, but it must run inside a deterministic safety envelope.

Core rule:

1. deterministic extraction remains the system of record
2. AI generates ranked suggestions, never silent overrides
3. every AI output carries confidence, evidence, and provenance
4. high-impact decisions require helper confirmation

### AI capability lanes

Implement AI in clear capability lanes so behavior is predictable and testable.

#### Lane A: Label recovery and normalization

Purpose:

1. recover user-friendly labels from weak field names and nearby text
2. normalize style to consistent form language

Input:

1. raw field name
2. nearby text windows from geometry extraction
3. section context
4. known label dictionary from prior reviewed templates

Output:

1. top 3 label candidates
2. confidence score
3. evidence snippets used to generate each candidate

Hard constraints:

1. never delete a deterministic label when one is already high-confidence
2. never auto-accept low-confidence labels

#### Lane B: Option semantics and group repair

Purpose:

1. propose human-friendly option labels for radios, checkboxes, and dropdowns
2. suggest radio grouping where widgets are fragmented

Input:

1. option export values
2. widget geometry clusters
3. nearby heading and instruction text

Output:

1. proposed option label map
2. proposed group key and group title
3. confidence and ambiguity flags

Hard constraints:

1. export values are immutable unless helper explicitly remaps
2. write-back map changes require helper approval

#### Lane C: Help text and instruction drafting

Purpose:

1. draft concise assistive help text for fields with missing instructions
2. improve plain-language clarity

Output requirements:

1. short help variant
2. detailed help variant
3. reason code showing what gap is being addressed

Hard constraints:

1. no legal or compliance interpretation claims
2. no invented mandatory requirements

#### Lane D: Data-type and validation hinting

Purpose:

1. suggest likely validation type when deterministic signals are mixed
2. detect probable formatting intent such as phone, ZIP, date, currency

Hard constraints:

1. validation suggestions are advisory until confirmed
2. any suggestion that changes rejection behavior must be reviewed

#### Lane E: Sectioning and ordering assistance

Purpose:

1. propose logical section headings
2. propose display order for accessibility-first interaction

Hard constraints:

1. final order used in fill UI must be helper-confirmed for medium or low confidence

### AI model strategy

Use role-specific model selection rather than one model for everything.

Recommended strategy:

1. small, low-latency model for classification and normalization tasks
2. stronger reasoning model for ambiguous label, grouping, and sectioning tasks
3. optional vision-capable model only when image-derived text context is required

Model routing should be capability-driven by feature, with per-lane defaults and override support in admin configuration.

### Prompt architecture

Store prompts as versioned assets and not hard-coded strings.

Required prompt sets:

1. label recovery prompt
2. option and grouping prompt
3. help text drafting prompt
4. validation hint prompt
5. sectioning and ordering prompt

Each prompt should include:

1. strict output schema
2. disallowed behaviors
3. uncertainty handling instructions
4. explanation field for helper transparency

### Confidence and acceptance policy

Use deterministic plus AI fusion scoring.

Suggested final decision bands:

1. high confidence: auto-apply but visibly marked as AI-assisted
2. medium confidence: pre-fill suggestion, helper review required
3. low confidence: do not pre-fill, helper action required

Suggested thresholds:

1. high at 0.85 and above
2. medium at 0.60 to 0.84
3. low below 0.60

The threshold values should be deployment-configurable for beta tuning.

### Human-in-the-loop UX requirements

For each AI suggestion, the review UI should support:

1. accept
2. edit then accept
3. reject
4. compare alternatives
5. show evidence source

The UI should also capture rejection reason tags to improve future prompt tuning.

### Evaluation and quality gates

AI should ship with explicit evaluation, not anecdotal quality checks.

Create a labeled evaluation corpus with expected outputs for:

1. label recovery
2. option mapping
3. grouping
4. help text usefulness
5. validation type suggestion

Track per-lane metrics:

1. top-1 and top-3 label accuracy
2. helper acceptance rate
3. helper edit distance after accept
4. false-confidence rate
5. p95 latency
6. estimated cost per document

Beta release gate recommendation:

1. no lane should default on if helper acceptance is below 80 percent
2. false-confidence rate should stay below 5 percent for high-confidence auto-apply

### Safety and policy controls

AI output handling must include:

1. prompt and output sanitization
2. schema validation before UI display
3. redaction pass for sensitive text where policy requires it
4. full audit trail of model, prompt version, and response id

Never use AI output to:

1. infer legal commitments
2. infer identity attributes beyond explicit document context
3. silently alter write-back mappings

### Cost and performance controls

To keep the feature practical in beta:

1. run deterministic heuristics first, AI only on unresolved fields
2. batch fields by section to reduce call overhead
3. cache AI suggestions by fingerprint and prompt version
4. enforce request budgets per document and per session
5. provide a hard timeout with safe fallback to deterministic behavior

### Beta rollout wiring

This feature should be beta by design.

Add AI beta controls:

1. `GLOW_ENABLE_PDF_FORM_AI_ASSIST` master switch
2. per-lane switches for labels, options, help text, validation, and ordering
3. percentage rollout by session or tenant
4. kill switch that instantly reverts to deterministic-only mode

### Planned AI endpoint shape

Suggested internal endpoints for clean separation:

1. `POST /api/pdf-forms/ai/labels/suggest`
2. `POST /api/pdf-forms/ai/options/suggest`
3. `POST /api/pdf-forms/ai/help/suggest`
4. `POST /api/pdf-forms/ai/validation/suggest`
5. `POST /api/pdf-forms/ai/sections/suggest`

Every endpoint should return:

1. `suggestions`
2. `confidence`
3. `evidence`
4. `model`
5. `prompt_version`
6. `trace_id`

### Definition of amazing in practice

The AI layer is successful when:

1. helpers spend less time fixing label and option noise
2. confidence is honest and predictable
3. write-back mappings remain stable and safe
4. accessibility quality improves without hiding uncertainty
5. costs remain low enough for routine use

## Fill and Write-Back Rules

Write-back should be governed by conservative rules.

### Safe write-back cases

1. standard text fields
2. checkboxes with stable export values
3. radio groups with confirmed mappings
4. dropdowns with known option mappings
5. list boxes where option values are explicit

### High-risk cases

1. XFA forms
2. digitally signed forms
3. JavaScript-heavy calculated forms
4. forms requiring viewer-specific behavior
5. fields with unstable appearance streams

For high-risk cases, the UI should explain why the PDF cannot be trusted for direct rewrite.

## Result Outputs

Every successful workflow should produce at least one structured output beyond the PDF.

Supported outputs:

1. editable filled PDF
2. flattened PDF
3. JSON submission payload
4. accessible HTML review record
5. helper-reviewed template profile

This ensures the data remains portable.

## Proposed Web Flow

### Step 1: Upload and classify

The user uploads a PDF and receives:

1. support classification
2. warnings
3. confidence summary
4. recommended path: round-trip, assisted template, or surrogate

### Step 2: Inspect extracted fields

Show:

1. raw field names
2. inferred labels
3. current values
4. page references
5. confidence indicators
6. fields missing labels or options

### Step 3: Helper review and enrichment

Allow a helper to:

1. rename fields
2. define help text
3. fix options
4. create sections and groups
5. reorder fields
6. suppress broken fields
7. mark write-back eligibility

### Step 4: Fill form

Render the enriched accessible form.

### Step 5: Export

Return the requested outputs and a write-back status report.

## Proposed API Shape

The route structure should make the stages explicit.

Suggested endpoints:

1. `GET /pdf-forms/`
2. `POST /pdf-forms/inspect`
3. `POST /pdf-forms/review`
4. `POST /pdf-forms/template/save`
5. `POST /pdf-forms/fill`
6. `GET /pdf-forms/download/<token>/<filename>`

Optional JSON endpoints for future integrations:

1. `POST /api/pdf-forms/inspect`
2. `POST /api/pdf-forms/template/save`
3. `POST /api/pdf-forms/fill`

## Validation Model

Validation should exist at two layers.

### 1. Form-definition validation

Checks whether the helper-defined structure is internally coherent.

Examples:

1. every visible field has a label
2. radio groups have options
3. dropdown values map to write-back values
4. display order is unique within a section

### 2. Submission validation

Checks whether user answers meet the template rules.

Examples:

1. required field completion
2. email format
3. date format
4. numeric range
5. ZIP or phone normalization

## Testing Strategy

This feature needs a strong corpus, not just unit tests.

### Test corpus categories

1. clean AcroForm with text fields
2. checkbox-heavy government-style form
3. radio-heavy application form
4. dropdown and list-box form
5. repeated row form with duplicate naming patterns
6. form with weak internal names but visible labels
7. form with tooltips only
8. hybrid or strange viewer-dependent form
9. signed form
10. XFA form
11. flattened form
12. scanned pseudo-form

### Required verification targets

Every write-back-capable output should be checked in:

1. Adobe Acrobat Reader
2. Microsoft Edge PDF viewer
3. Chrome PDF viewer

### Required automated test layers

1. classifier tests
2. field extraction tests
3. heuristic scoring tests
4. template persistence tests
5. write-back tests
6. route tests
7. accessibility tests for rendered HTML

## Security and Privacy

PDF forms often contain sensitive data. The implementation must assume that personal data may appear in uploads and submissions.

Requirements:

1. keep uploads in request-scoped temp storage unless the user explicitly saves a template
2. never store raw submission data longer than necessary
3. separate template metadata from end-user answers
4. allow deployments to disable template memory if privacy policy requires it
5. preserve existing filename sanitization and path traversal protections

## Metrics for Success

The following table defines the quality targets for the first useful release.

| Metric | Initial target |
| --- | --- |
| Correct field-type extraction on supported AcroForms | 95 percent |
| Correct label recovery without helper edits | 80 percent |
| Correct label recovery after helper review | 98 percent |
| Successful write-back on supported corpus | 95 percent |
| Forms requiring surrogate mode correctly classified | 95 percent |
| Repeat uploads benefiting from saved template memory | 90 percent of matching templates |

## V1 Execution Plan

The rest of this document defines the full long-term system. This section defines the first production-worthy version.

V1 should be built to solve one narrow problem well:

1. inspect a supported AcroForm PDF
2. reconstruct an accessible web form
3. let a helper fix missing labels and option names
4. collect answers through the web form
5. write those answers back into the original PDF
6. export the same answers as JSON

### V1 product promise

The user-facing promise for v1 should be:

"Upload a supported interactive PDF form, review or correct missing field details, fill it out accessibly in the browser, and download a filled PDF plus structured JSON."

That promise is narrow enough to be testable and strong enough to be useful.

### V1 goals

V1 goals:

1. support real AcroForm PDFs reliably
2. avoid silent corruption or misleading output
3. let helpers enrich weak field definitions before use
4. produce an accessible HTML interaction model that is better than the original PDF
5. preserve structured data outside the PDF itself

### V1 non-goals

V1 should explicitly avoid:

1. XFA support
2. scanned-form round-trip editing
3. arbitrary overlay generation for visually drawn fake forms
4. full PDF JavaScript emulation
5. signature-preserving rewrite
6. AI-first extraction that bypasses deterministic parsing

### V1 target inputs

V1 should accept only:

1. AcroForm PDFs with stable widget annotations
2. text fields
3. multiline text fields
4. checkboxes
5. radio groups
6. dropdowns and simple list boxes

V1 should reject or downgrade:

1. XFA forms
2. digitally signed forms
3. forms with missing field-tree stability
4. forms with no reliable write-back mapping

### V1 helper workflow

The helper workflow is part of v1, not a future nice-to-have.

V1 helper review must support:

1. editing display labels
2. editing help text
3. changing visible option labels
4. mapping visible option labels to PDF export values
5. grouping radio buttons into a single logical question
6. setting section headings
7. setting display order
8. suppressing broken or junk fields
9. marking a field as view-only or not safe for write-back

The helper review should not require perfect PDF structure to be useful.

### V1 end-user workflow

The end-user workflow for v1 should be:

1. upload PDF
2. inspect support classification
3. if needed, helper reviews and enriches the form
4. user fills accessible HTML form
5. submit answers
6. download editable PDF, optionally flattened PDF, and JSON

### V1 implementation slices

V1 should be built in vertical slices rather than by building every backend piece first.

#### Slice 1: classification and extraction

Deliverables:

1. AcroForm classifier
2. field extraction JSON
3. confidence and warning model
4. unsupported-state messages

#### Slice 2: review UI

Deliverables:

1. extracted field list page
2. editable labels and help text
3. option editor for radios and dropdowns
4. ordering and grouping controls

#### Slice 3: fill UI and validation

Deliverables:

1. accessible HTML form rendering
2. required-field validation
3. basic type validation for email, date, numeric, phone, ZIP
4. result summary page

#### Slice 4: write-back and export

Deliverables:

1. editable filled PDF
2. flattened PDF option
3. JSON export
4. write-back diagnostics report

### V1 architecture decisions

V1 should lock in these decisions early:

1. PyMuPDF is the primary extraction and geometry engine
2. pypdf is the primary write-back engine
3. helper-reviewed template data lives in SQLite in the instance directory
4. temporary uploads and outputs stay in the existing temp-file model
5. every inferred field property carries a confidence score

### V1 data model

V1 only needs a minimal but explicit data model.

#### Extracted field

Required properties:

1. raw PDF field name
2. widget id or xref
3. page number
4. field type
5. current value
6. option values if present
7. inferred label
8. confidence
9. warnings

#### Reviewed field definition

Required properties:

1. display label
2. help text
3. visible options
4. PDF export value mapping
5. required state
6. readonly state
7. display order
8. section id
9. write-back eligibility

#### Submission record

Required properties:

1. reviewed template id
2. submitted values
3. validation outcome
4. write-back outcome
5. generated file names

### V1 acceptance criteria

V1 should not ship until the following are true:

1. supported AcroForm PDFs are correctly classified with a clear supported or unsupported reason
2. field types are extracted accurately for the v1 corpus
3. radio groups can be reviewed and written back correctly
4. helpers can rename labels and option text without touching raw PDF export values
5. the rendered HTML form is keyboard-operable and screen-reader-usable
6. editable and flattened PDF downloads both work on the supported corpus
7. JSON output matches the submitted form values exactly
8. unsupported files fail safely with clear user guidance

### V1 test corpus

V1 needs a test set that reflects the actual promise.

Required examples:

1. clean text-field AcroForm
2. checkbox-heavy form
3. radio-heavy form
4. dropdown form
5. duplicate-name repeated-row form
6. form with poor field names but usable nearby text
7. form with broken labels needing helper fixes
8. unsupported XFA form
9. signed form

### V1 operational risks

The main risks for v1 are:

1. appearance streams render inconsistently across PDF viewers
2. duplicate field names produce ambiguous write-back behavior
3. helper edits drift away from the real PDF mapping if the review model is too loose
4. low-confidence label guesses create user trust problems if uncertainty is not visible

### V1 launch recommendation

V1 should launch behind a feature flag and should initially be described as a guided beta.

Recommended rollout:

1. internal spike corpus first
2. maintainer-only or admin-enabled beta
3. limited real-form pilot with saved templates
4. broader release after viewer compatibility and write-back diagnostics are stable

## Delivery Plan

### Phase 0: Research spike

Goal: prove the real boundaries of the open-source stack.

Deliverables:

1. classification script
2. write-back proof of concept
3. corpus of representative PDFs
4. failure taxonomy
5. recommendation on whether commercial SDK evaluation is necessary

### Phase 1: Core extraction and classification

Goal: identify support level reliably.

Deliverables:

1. classifier module
2. extracted field model
3. raw JSON inspection output
4. confidence and warning model

### Phase 2: Accessible inspection UI

Goal: let users inspect what GLOW found.

Deliverables:

1. upload route
2. inspection page
3. confidence presentation
4. unsupported-state messaging

### Phase 3: Helper enrichment UI

Goal: allow rich human correction.

Deliverables:

1. field editing interface
2. option editor
3. grouping and ordering controls
4. template save flow

### Phase 4: Fill and export

Goal: make the system genuinely useful.

Deliverables:

1. accessible fill page
2. editable PDF output
3. flattened PDF output
4. JSON export
5. result summary report

### Phase 5: Template memory and reuse

Goal: make the system better with repeated forms.

Deliverables:

1. fingerprint matching
2. template auto-apply
3. helper correction reuse
4. versioning controls

### Phase 6: AI assist and surrogate mode

Goal: improve difficult forms without overstating certainty.

Deliverables:

1. optional AI suggestion layer
2. static visual form assistant mode
3. helper review for surrogate mappings

## V1 Scope Summary

The first production release should support only:

1. AcroForm PDFs with stable widgets
2. text fields
3. checkboxes
4. radio groups
5. dropdowns
6. helper label and option enrichment
7. JSON plus PDF output

The first production release should not support:

1. XFA
2. signatures
3. heavy JavaScript calculations
4. scanned visual-form round-trip
5. universal overlay generation for arbitrary static forms

## Why This Is Worth Doing

This feature fits GLOW's existing mission well.

GLOW already:

1. inspects documents for accessibility issues
2. reconstructs usable outputs from difficult formats
3. provides accessible web workflows around complex document processing

PDF form round-trip extends that model from document accessibility into form accessibility and assisted completion.

## Open Questions

These decisions should be made before implementation starts:

1. Should helper-created templates be private by default, or shareable within an organization?
2. Should saved templates persist only metadata, or optionally also keep a sanitized source PDF fingerprint sample?
3. Should surrogate mode generate overlay PDFs in v1, or stop at JSON plus accessible HTML?
4. Should AI suggestions be enabled by default when available, or only on explicit request?
5. What minimum viewer-compatibility bar is required for claiming write-back support?

## Recommendation

Proceed with a spike and then build the feature in phases.

The most defensible product promise is:

"GLOW can inspect supported PDF forms, generate an accessible web form, let a helper enrich missing structure, and write answers back into the PDF when the source document supports reliable round-trip editing."

That promise is ambitious, useful, and technically credible.