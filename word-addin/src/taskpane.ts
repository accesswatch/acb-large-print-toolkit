/**
 * Task pane entry point -- wires up UI controls to audit/fix/template logic.
 */

import "./taskpane.css";
import { auditDocument, AuditResult, Finding } from "./auditor";
import { fixDocument } from "./fixer";
import { applyTemplate } from "./template";

Office.onReady((info) => {
    if (info.host === Office.HostType.Word) {
        initTaskPane();
    }
});

function $(id: string): HTMLElement {
    const el = document.getElementById(id);
    if (!el) throw new Error(`Element #${id} not found`);
    return el;
}

function initTaskPane(): void {
    $("btn-audit").addEventListener("click", handleAudit);
    $("btn-fix").addEventListener("click", handleFix);
    $("btn-template").addEventListener("click", handleTemplate);

    // Filter checkboxes
    document.querySelectorAll<HTMLInputElement>(".filter-checkbox").forEach((cb) => {
        cb.addEventListener("change", applyFilters);
    });
}

// ---------------------------------------------------------------------------
// Audit
// ---------------------------------------------------------------------------

let lastAuditResult: AuditResult | null = null;

async function handleAudit(): Promise<void> {
    setStatus("Scanning document for ACB compliance...");
    showProgress(true);
    disableActions(true);

    try {
        const result = await auditDocument();
        lastAuditResult = result;

        hideAllResults();
        showScore(result);
        showFindings(result.findings);

        const msg = result.findings.length === 0
            ? "Document is fully ACB compliant!"
            : `Found ${result.findings.length} issue${result.findings.length === 1 ? "" : "s"}. Score: ${result.score}/100 (${result.grade})`;
        setStatus(msg);
    } catch (err) {
        setStatus(`Audit failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
        showProgress(false);
        disableActions(false);
    }
}

// ---------------------------------------------------------------------------
// Fix
// ---------------------------------------------------------------------------

async function handleFix(): Promise<void> {
    setStatus("Fixing ACB compliance issues...");
    disableActions(true);

    try {
        const result = await fixDocument();

        hideAllResults();
        const section = $("fix-section");
        section.hidden = false;

        $("fix-summary").textContent = result.totalFixes === 0
            ? "No fixable issues found."
            : `Applied ${result.totalFixes} fix${result.totalFixes === 1 ? "" : "es"}.`;

        const list = $("fix-details") as HTMLUListElement;
        list.innerHTML = "";
        for (const detail of result.details) {
            const li = document.createElement("li");
            li.textContent = detail;
            list.appendChild(li);
        }

        setStatus(`Fix complete: ${result.totalFixes} fixes applied. Run Audit to verify.`);
    } catch (err) {
        setStatus(`Fix failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
        disableActions(false);
    }
}

// ---------------------------------------------------------------------------
// Template
// ---------------------------------------------------------------------------

async function handleTemplate(): Promise<void> {
    setStatus("Applying ACB Large Print template...");
    disableActions(true);

    try {
        const result = await applyTemplate();

        hideAllResults();
        const section = $("template-section");
        section.hidden = false;

        const list = $("template-details") as HTMLUListElement;
        list.innerHTML = "";
        for (const item of result.applied) {
            const li = document.createElement("li");
            li.textContent = item;
            list.appendChild(li);
        }

        setStatus(`Template applied: ${result.applied.length} settings configured.`);
    } catch (err) {
        setStatus(`Template failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
        disableActions(false);
    }
}

// ---------------------------------------------------------------------------
// UI helpers
// ---------------------------------------------------------------------------

function setStatus(msg: string): void {
    $("status").textContent = msg;
}

function showProgress(visible: boolean): void {
    const el = $("progress");
    el.hidden = !visible;
    if (visible) {
        const fill = $("progress-fill") as HTMLDivElement;
        // Indeterminate: animate width
        fill.style.width = "100%";
    }
}

function disableActions(disabled: boolean): void {
    ($("btn-audit") as HTMLButtonElement).disabled = disabled;
    ($("btn-fix") as HTMLButtonElement).disabled = disabled;
    ($("btn-template") as HTMLButtonElement).disabled = disabled;
}

function hideAllResults(): void {
    $("score-section").hidden = true;
    $("findings-section").hidden = true;
    $("fix-section").hidden = true;
    $("template-section").hidden = true;
}

function showScore(result: AuditResult): void {
    const section = $("score-section");
    section.hidden = false;

    const grade = $("score-grade");
    grade.textContent = result.grade;
    grade.setAttribute("aria-label", `Grade: ${result.grade}`);

    const value = $("score-value");
    value.textContent = `${result.score}/100`;
    value.setAttribute("aria-label", `Score: ${result.score} out of 100`);

    $("score-summary").textContent =
        `${result.totalParagraphs} paragraphs scanned, ${result.findings.length} finding${result.findings.length === 1 ? "" : "s"}`;
}

function showFindings(findings: Finding[]): void {
    if (findings.length === 0) return;

    const section = $("findings-section");
    section.hidden = false;

    renderFindingsTable(findings);
    updateFindingsCount(findings.length, findings.length);
}

function renderFindingsTable(findings: Finding[]): void {
    const tbody = $("findings-body") as HTMLTableSectionElement;
    tbody.innerHTML = "";

    const activeFilters = getActiveFilters();

    let visibleCount = 0;
    for (const finding of findings) {
        const row = document.createElement("tr");
        row.dataset.severity = finding.severity;

        const visible = activeFilters.has(finding.severity);
        row.hidden = !visible;
        if (visible) visibleCount++;

        // Severity cell
        const sevTd = document.createElement("td");
        const badge = document.createElement("span");
        badge.className = `severity-badge severity-${finding.severity.toLowerCase()}`;
        badge.textContent = finding.severity;
        sevTd.appendChild(badge);
        row.appendChild(sevTd);

        // Rule cell
        const ruleTd = document.createElement("td");
        ruleTd.textContent = finding.ruleId;
        row.appendChild(ruleTd);

        // Message cell
        const msgTd = document.createElement("td");
        msgTd.textContent = finding.message;
        row.appendChild(msgTd);

        // Location cell
        const locTd = document.createElement("td");
        locTd.textContent = finding.location;
        row.appendChild(locTd);

        // Auto-fixable cell
        const fixTd = document.createElement("td");
        if (finding.autoFixable) {
            fixTd.innerHTML = '<span class="fixable-yes">Auto</span>';
        } else {
            fixTd.innerHTML = '<span class="fixable-no">Manual</span>';
        }
        row.appendChild(fixTd);

        tbody.appendChild(row);
    }

    updateFindingsCount(visibleCount, findings.length);
}

function applyFilters(): void {
    if (!lastAuditResult) return;
    const activeFilters = getActiveFilters();
    const tbody = $("findings-body") as HTMLTableSectionElement;
    let visibleCount = 0;

    for (const row of Array.from(tbody.rows)) {
        const severity = row.dataset.severity || "";
        const visible = activeFilters.has(severity);
        row.hidden = !visible;
        if (visible) visibleCount++;
    }

    updateFindingsCount(visibleCount, lastAuditResult.findings.length);
}

function getActiveFilters(): Set<string> {
    const set = new Set<string>();
    document.querySelectorAll<HTMLInputElement>(".filter-checkbox").forEach((cb) => {
        if (cb.checked) {
            set.add(cb.dataset.severity || "");
        }
    });
    return set;
}

function updateFindingsCount(visible: number, total: number): void {
    $("findings-count").textContent =
        visible === total
            ? `Showing all ${total} finding${total === 1 ? "" : "s"}`
            : `Showing ${visible} of ${total} finding${total === 1 ? "" : "s"}`;
}
