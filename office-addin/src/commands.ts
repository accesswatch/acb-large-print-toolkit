/**
 * Command handlers for ribbon buttons (Fix, Template).
 *
 * These run when the user clicks a ribbon button that uses ExecuteFunction.
 * The Audit button opens the task pane instead (ShowTaskpane action).
 */

import { fixDocument } from "./fixer";
import { applyTemplate } from "./template";

Office.onReady(() => {
    // Register global functions for ribbon commands
    Office.actions.associate("fixDocument", fixDocumentCommand);
    Office.actions.associate("applyTemplate", applyTemplateCommand);
});

async function fixDocumentCommand(event: Office.AddinCommands.Event): Promise<void> {
    try {
        const result = await fixDocument();
        const msg = result.totalFixes === 0
            ? "No fixable issues found."
            : `Applied ${result.totalFixes} fix${result.totalFixes === 1 ? "" : "es"}. Open the task pane to see details.`;

        Office.context.ui.displayDialogAsync(
            `data:text/html,<html lang="en"><head><title>ACB Fix Complete</title></head><body><p>${encodeURIComponent(msg)}</p></body></html>`,
            { height: 20, width: 30 },
        );
    } catch (err) {
        // Silently fail -- user can open task pane for details
    }
    event.completed();
}

async function applyTemplateCommand(event: Office.AddinCommands.Event): Promise<void> {
    try {
        const result = await applyTemplate();
        const msg = `Template applied: ${result.applied.length} settings configured. Open the task pane to see details.`;

        Office.context.ui.displayDialogAsync(
            `data:text/html,<html lang="en"><head><title>ACB Template Applied</title></head><body><p>${encodeURIComponent(msg)}</p></body></html>`,
            { height: 20, width: 30 },
        );
    } catch (err) {
        // Silently fail
    }
    event.completed();
}
