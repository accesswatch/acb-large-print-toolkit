"""Accessible step-by-step wizard GUI for ACB Large Print Tool.

Wizard flow:
  Step 1: Welcome / Open Document  (file picker)
  Step 2: Initial Audit             (scan + show results in browser)
  Step 3: Options                   (checkboxes for HTML export flavours)
  Step 4: Remediation               (auto-fix + show summary)
  Step 5: Verification              (re-audit the fixed document)
  Step 6: Save                      (save .docx + optional HTML exports)
  Step 7: Done                      (summary of everything accomplished)

Accessibility design:
  - Every control has a label or SetName()
  - Alt-key accelerators on Back / Next / Cancel
  - Read-only text areas for screen reader navigation
  - No colour-only information
  - Standard file dialogs for all file operations
  - Status bar announces current step
  - HTML reports open in the system default browser
"""

from __future__ import annotations

import shutil
import tempfile
import webbrowser
from pathlib import Path

import wx

from . import __app_name__, __version__
from .auditor import AuditResult, audit_document
from .exporter import export_cms_fragment, export_standalone_html
from .fixer import fix_document
from .reporter import generate_html_report, generate_text_report


# ── Wizard step indices ───────────────────────────────────────────────
STEP_WELCOME = 0
STEP_AUDIT = 1
STEP_OPTIONS = 2
STEP_FIX = 3
STEP_VERIFY = 4
STEP_SAVE = 5
STEP_DONE = 6

STEP_TITLES = [
    "Step 1 of 7: Open Document",
    "Step 2 of 7: Initial Audit",
    "Step 3 of 7: Output Options",
    "Step 4 of 7: Remediation",
    "Step 5 of 7: Verification",
    "Step 6 of 7: Save",
    "Step 7 of 7: Done",
]


class WizardFrame(wx.Frame):
    """Main wizard window."""

    def __init__(self) -> None:
        super().__init__(
            None,
            title=f"{__app_name__} {__version__}",
            size=(640, 520),
        )
        self.SetName(__app_name__)
        self.SetMinSize((500, 400))

        # ── State ─────────────────────────────────────────────────────
        self.src_path: Path | None = None
        self.fixed_path: Path | None = None
        self.pre_audit: AuditResult | None = None
        self.post_audit: AuditResult | None = None
        self.total_fixes: int = 0
        self.saved_files: list[str] = []
        self.current_step: int = STEP_WELCOME

        # ── UI ────────────────────────────────────────────────────────
        panel = wx.Panel(self)
        self.panel = panel
        root = wx.BoxSizer(wx.VERTICAL)

        # Step title
        self.step_label = wx.StaticText(panel, label=STEP_TITLES[0])
        font = self.step_label.GetFont()
        font.SetPointSize(12)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.step_label.SetFont(font)
        root.Add(self.step_label, flag=wx.ALL, border=10)

        # Page container (swap panels per step)
        self.page_sizer = wx.BoxSizer(wx.VERTICAL)
        root.Add(self.page_sizer, proportion=1,
                 flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # Navigation buttons
        root.Add(wx.StaticLine(panel), flag=wx.EXPAND | wx.TOP, border=5)
        nav = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_cancel = wx.Button(panel, wx.ID_CANCEL, "&Cancel")
        nav.Add(self.btn_cancel, flag=wx.ALL, border=8)
        nav.AddStretchSpacer()
        self.btn_back = wx.Button(panel, label="< &Back")
        self.btn_back.SetName("Back to previous step")
        nav.Add(self.btn_back, flag=wx.ALL, border=8)
        self.btn_next = wx.Button(panel, label="&Next >")
        self.btn_next.SetName("Proceed to next step")
        self.btn_next.SetDefault()
        nav.Add(self.btn_next, flag=wx.ALL, border=8)
        root.Add(nav, flag=wx.EXPAND)

        panel.SetSizer(root)

        # Status bar
        self.status_bar = self.CreateStatusBar()

        # ── Events ────────────────────────────────────────────────────
        self.btn_next.Bind(wx.EVT_BUTTON, self._on_next)
        self.btn_back.Bind(wx.EVT_BUTTON, self._on_back)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self._on_cancel)
        self.Bind(wx.EVT_CLOSE, self._on_close)

        # ── Build each page ───────────────────────────────────────────
        self.pages: list[wx.Panel] = []
        self._build_step_welcome()
        self._build_step_audit()
        self._build_step_options()
        self._build_step_fix()
        self._build_step_verify()
        self._build_step_save()
        self._build_step_done()

        self._show_step(STEP_WELCOME)

    # ==================================================================
    # Step builders
    # ==================================================================

    def _make_page(self) -> wx.Panel:
        page = wx.Panel(self.panel)
        page.Hide()
        self.pages.append(page)
        return page

    # ── Step 1: Welcome / Open ────────────────────────────────────────

    def _build_step_welcome(self) -> None:
        page = self._make_page()
        sizer = wx.BoxSizer(wx.VERTICAL)

        intro = wx.StaticText(page, label=(
            "Welcome to the ACB Large Print Compliance Wizard.\n\n"
            "This wizard will:\n"
            "  1. Audit your Word document for ACB guideline violations\n"
            "  2. Attempt to automatically fix issues found\n"
            "  3. Verify the fixes were applied correctly\n"
            "  4. Save the corrected document and optional HTML exports\n\n"
            "Select a Word document to begin."
        ))
        intro.Wrap(560)
        sizer.Add(intro, flag=wx.BOTTOM, border=15)

        lbl = wx.StaticText(page, label="&Document file:")
        sizer.Add(lbl)
        self.file_picker = wx.FilePickerCtrl(
            page,
            message="Open a Word document",
            wildcard="Word Documents (*.docx)|*.docx",
            style=wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST | wx.FLP_USE_TEXTCTRL,
        )
        self.file_picker.SetName("Document file path")
        sizer.Add(self.file_picker, flag=wx.EXPAND | wx.TOP, border=4)

        page.SetSizer(sizer)

    # ── Step 2: Initial Audit ─────────────────────────────────────────

    def _build_step_audit(self) -> None:
        page = self._make_page()
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.audit_status = wx.StaticText(page, label="Auditing document...")
        sizer.Add(self.audit_status, flag=wx.BOTTOM, border=8)

        self.audit_text = wx.TextCtrl(
            page, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP,
        )
        self.audit_text.SetName("Initial audit results")
        mono = wx.Font(10, wx.FONTFAMILY_TELETYPE,
                       wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.audit_text.SetFont(mono)
        sizer.Add(self.audit_text, proportion=1, flag=wx.EXPAND)

        self.btn_view_audit = wx.Button(
            page, label="&View report in browser",
        )
        self.btn_view_audit.SetName("Open audit report in default web browser")
        self.btn_view_audit.Bind(wx.EVT_BUTTON, self._on_view_audit_report)
        self.btn_view_audit.Disable()
        sizer.Add(self.btn_view_audit, flag=wx.TOP, border=8)

        page.SetSizer(sizer)

    # ── Step 3: Options ───────────────────────────────────────────────

    def _build_step_options(self) -> None:
        page = self._make_page()
        sizer = wx.BoxSizer(wx.VERTICAL)

        intro = wx.StaticText(page, label=(
            "Choose which outputs to create in addition to the "
            "fixed Word document."
        ))
        intro.Wrap(560)
        sizer.Add(intro, flag=wx.BOTTOM, border=12)

        self.chk_cms = wx.CheckBox(
            page,
            label="&CMS fragment (WordPress / Drupal copy-paste with embedded CSS)",
        )
        self.chk_cms.SetName(
            "Create CMS HTML fragment with embedded CSS for WordPress or Drupal"
        )
        self.chk_cms.SetValue(True)
        sizer.Add(self.chk_cms, flag=wx.BOTTOM, border=6)

        self.chk_standalone = wx.CheckBox(
            page,
            label="&Standalone HTML file with separate CSS stylesheet",
        )
        self.chk_standalone.SetName(
            "Create standalone HTML file with external CSS stylesheet"
        )
        self.chk_standalone.SetValue(True)
        sizer.Add(self.chk_standalone, flag=wx.BOTTOM, border=12)

        note = wx.StaticText(page, label=(
            "The CMS fragment is a single file you can paste directly into "
            "a WordPress or Drupal HTML block. The standalone version is a "
            "complete web page with a separate CSS file for hosting or email."
        ))
        note.Wrap(560)
        sizer.Add(note)

        page.SetSizer(sizer)

    # ── Step 4: Remediation ───────────────────────────────────────────

    def _build_step_fix(self) -> None:
        page = self._make_page()
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.fix_status = wx.StaticText(page, label="Applying fixes...")
        sizer.Add(self.fix_status, flag=wx.BOTTOM, border=8)

        self.fix_text = wx.TextCtrl(
            page, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP,
        )
        self.fix_text.SetName("Remediation results")
        mono = wx.Font(10, wx.FONTFAMILY_TELETYPE,
                       wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.fix_text.SetFont(mono)
        sizer.Add(self.fix_text, proportion=1, flag=wx.EXPAND)

        page.SetSizer(sizer)

    # ── Step 5: Verification ──────────────────────────────────────────

    def _build_step_verify(self) -> None:
        page = self._make_page()
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.verify_status = wx.StaticText(
            page, label="Re-auditing fixed document...",
        )
        sizer.Add(self.verify_status, flag=wx.BOTTOM, border=8)

        self.verify_text = wx.TextCtrl(
            page, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP,
        )
        self.verify_text.SetName("Verification audit results")
        mono = wx.Font(10, wx.FONTFAMILY_TELETYPE,
                       wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.verify_text.SetFont(mono)
        sizer.Add(self.verify_text, proportion=1, flag=wx.EXPAND)

        self.btn_view_verify = wx.Button(
            page, label="View &verification report in browser",
        )
        self.btn_view_verify.SetName(
            "Open verification report in default web browser"
        )
        self.btn_view_verify.Bind(wx.EVT_BUTTON, self._on_view_verify_report)
        self.btn_view_verify.Disable()
        sizer.Add(self.btn_view_verify, flag=wx.TOP, border=8)

        page.SetSizer(sizer)

    # ── Step 6: Save ──────────────────────────────────────────────────

    def _build_step_save(self) -> None:
        page = self._make_page()
        sizer = wx.BoxSizer(wx.VERTICAL)

        intro = wx.StaticText(page, label=(
            "Choose where to save the fixed document and any HTML exports."
        ))
        intro.Wrap(560)
        sizer.Add(intro, flag=wx.BOTTOM, border=12)

        lbl_docx = wx.StaticText(page, label="Fixed &Word document:")
        sizer.Add(lbl_docx)
        self.save_docx_picker = wx.FilePickerCtrl(
            page,
            message="Save fixed Word document as",
            wildcard="Word Documents (*.docx)|*.docx",
            style=wx.FLP_SAVE | wx.FLP_OVERWRITE_PROMPT | wx.FLP_USE_TEXTCTRL,
        )
        self.save_docx_picker.SetName("Save fixed Word document location")
        sizer.Add(self.save_docx_picker, flag=wx.EXPAND | wx.BOTTOM, border=10)

        lbl_html = wx.StaticText(page, label="HTML &output folder:")
        sizer.Add(lbl_html)
        self.html_dir_picker = wx.DirPickerCtrl(
            page,
            message="Choose folder for HTML output files",
            style=wx.DIRP_USE_TEXTCTRL,
        )
        self.html_dir_picker.SetName("HTML output folder location")
        sizer.Add(self.html_dir_picker, flag=wx.EXPAND | wx.BOTTOM, border=10)

        page.SetSizer(sizer)

    # ── Step 7: Done ──────────────────────────────────────────────────

    def _build_step_done(self) -> None:
        page = self._make_page()
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.done_text = wx.TextCtrl(
            page, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP,
        )
        self.done_text.SetName("Summary of all actions completed")
        mono = wx.Font(10, wx.FONTFAMILY_TELETYPE,
                       wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.done_text.SetFont(mono)
        sizer.Add(self.done_text, proportion=1, flag=wx.EXPAND)

        page.SetSizer(sizer)

    # ==================================================================
    # Navigation
    # ==================================================================

    def _show_step(self, step: int) -> None:
        """Switch visible page and update navigation buttons."""
        if 0 <= self.current_step < len(self.pages):
            old = self.pages[self.current_step]
            self.page_sizer.Detach(old)
            old.Hide()

        self.current_step = step
        page = self.pages[step]
        self.page_sizer.Add(page, proportion=1, flag=wx.EXPAND)
        page.Show()

        self.step_label.SetLabel(STEP_TITLES[step])

        self.btn_back.Enable(step > STEP_WELCOME)
        if step == STEP_DONE:
            self.btn_next.SetLabel("&Finish")
            self.btn_next.SetName("Close the wizard")
        else:
            self.btn_next.SetLabel("&Next >")
            self.btn_next.SetName("Proceed to next step")

        self.status_bar.SetStatusText(STEP_TITLES[step])
        self.panel.Layout()
        wx.CallAfter(self._focus_page, step)

    def _focus_page(self, step: int) -> None:
        targets = {
            STEP_WELCOME: self.file_picker,
            STEP_AUDIT: self.audit_text,
            STEP_OPTIONS: self.chk_cms,
            STEP_FIX: self.fix_text,
            STEP_VERIFY: self.verify_text,
            STEP_SAVE: self.save_docx_picker,
            STEP_DONE: self.done_text,
        }
        ctrl = targets.get(step)
        if ctrl:
            ctrl.SetFocus()

    # ==================================================================
    # Navigation handlers
    # ==================================================================

    def _on_next(self, _evt: wx.CommandEvent) -> None:
        step = self.current_step

        if step == STEP_WELCOME:
            if not self._validate_welcome():
                return
            self._show_step(STEP_AUDIT)
            wx.CallAfter(self._run_initial_audit)

        elif step == STEP_AUDIT:
            self._show_step(STEP_OPTIONS)

        elif step == STEP_OPTIONS:
            self._show_step(STEP_FIX)
            wx.CallAfter(self._run_fix)

        elif step == STEP_FIX:
            self._show_step(STEP_VERIFY)
            wx.CallAfter(self._run_verify)

        elif step == STEP_VERIFY:
            self._prepare_save_defaults()
            self._show_step(STEP_SAVE)

        elif step == STEP_SAVE:
            if not self._do_save():
                return
            self._show_step(STEP_DONE)
            wx.CallAfter(self._build_done_summary)

        elif step == STEP_DONE:
            self._cleanup()
            self.Close()

    def _on_back(self, _evt: wx.CommandEvent) -> None:
        if self.current_step > STEP_WELCOME:
            self._show_step(self.current_step - 1)

    def _on_cancel(self, _evt: wx.CommandEvent) -> None:
        if self.current_step == STEP_DONE:
            self._cleanup()
            self.Close()
            return
        dlg = wx.MessageDialog(
            self,
            "Are you sure you want to cancel the wizard?",
            "Cancel",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        if dlg.ShowModal() == wx.ID_YES:
            self._cleanup()
            self.Close()
        dlg.Destroy()

    def _on_close(self, evt: wx.CloseEvent) -> None:
        self._cleanup()
        evt.Skip()

    def _cleanup(self) -> None:
        if self.fixed_path and self.fixed_path.exists():
            try:
                if self.fixed_path.stem.startswith("_acb_tmp_"):
                    self.fixed_path.unlink(missing_ok=True)
            except OSError:
                pass

    # ==================================================================
    # Step logic
    # ==================================================================

    def _validate_welcome(self) -> bool:
        path_str = self.file_picker.GetPath()
        if not path_str:
            wx.MessageBox(
                "Please select a Word document to continue.",
                "No file selected",
                wx.OK | wx.ICON_INFORMATION,
            )
            self.file_picker.SetFocus()
            return False
        p = Path(path_str)
        if not p.exists():
            wx.MessageBox(
                f"File not found:\n{p}",
                "File not found",
                wx.OK | wx.ICON_ERROR,
            )
            self.file_picker.SetFocus()
            return False
        if p.suffix.lower() != ".docx":
            wx.MessageBox(
                "Please select a .docx file.",
                "Wrong file type",
                wx.OK | wx.ICON_INFORMATION,
            )
            self.file_picker.SetFocus()
            return False
        self.src_path = p
        return True

    # ── Audit ─────────────────────────────────────────────────────────

    def _run_initial_audit(self) -> None:
        self.btn_next.Disable()
        self.btn_back.Disable()
        self.audit_status.SetLabel("Auditing document, please wait...")
        wx.BeginBusyCursor()
        try:
            self.pre_audit = audit_document(self.src_path)
            report = generate_text_report(self.pre_audit)
            self.audit_text.SetValue(report)
            self.audit_text.SetInsertionPoint(0)

            score = self.pre_audit.score
            grade = self.pre_audit.grade
            n = len(self.pre_audit.findings)
            self.audit_status.SetLabel(
                f"Audit complete: score {score}/100 "
                f"(grade {grade}), {n} findings."
            )
            self.btn_view_audit.Enable()
            self.status_bar.SetStatusText(
                f"Audit: {score}/100 grade {grade}, {n} findings"
            )
        except Exception as exc:
            self.audit_status.SetLabel(f"Audit failed: {exc}")
            self.audit_text.SetValue(str(exc))
        finally:
            wx.EndBusyCursor()
            self.btn_next.Enable()
            self.btn_back.Enable()

    def _on_view_audit_report(self, _evt: wx.CommandEvent) -> None:
        if self.pre_audit:
            self._open_report_in_browser(self.pre_audit, "Initial Audit")

    # ── Fix ───────────────────────────────────────────────────────────

    def _run_fix(self) -> None:
        self.btn_next.Disable()
        self.btn_back.Disable()
        self.fix_status.SetLabel("Applying automatic fixes, please wait...")
        wx.BeginBusyCursor()
        try:
            tmp = Path(tempfile.mkdtemp()) / f"_acb_tmp_{self.src_path.name}"
            self.fixed_path, self.total_fixes, self.post_audit = fix_document(
                self.src_path, tmp,
            )

            lines: list[str] = []
            lines.append(f"Fixes applied: {self.total_fixes}")
            lines.append(
                f"Post-fix score: {self.post_audit.score}/100 "
                f"(grade {self.post_audit.grade})"
            )
            lines.append("")

            if self.pre_audit:
                delta = self.post_audit.score - self.pre_audit.score
                sign = "+" if delta >= 0 else ""
                lines.append(
                    f"Score change: {self.pre_audit.score} -> "
                    f"{self.post_audit.score} ({sign}{delta})"
                )
                lines.append(
                    f"Findings: {len(self.pre_audit.findings)} -> "
                    f"{len(self.post_audit.findings)}"
                )
            lines.append("")

            if self.post_audit.findings:
                lines.append("Remaining issues (may require manual review):")
                for i, f in enumerate(self.post_audit.findings, 1):
                    lines.append(
                        f"  {i}. [{f.severity.value}] "
                        f"{f.rule_id}: {f.message}"
                    )
            else:
                lines.append(
                    "All issues resolved. Document is fully compliant."
                )

            self.fix_text.SetValue("\n".join(lines))
            self.fix_text.SetInsertionPoint(0)
            self.fix_status.SetLabel(
                f"Remediation complete: {self.total_fixes} fixes applied."
            )
            self.status_bar.SetStatusText(
                f"Fixed: {self.total_fixes} fixes, "
                f"score {self.post_audit.score}/100"
            )
        except Exception as exc:
            self.fix_status.SetLabel(f"Fix failed: {exc}")
            self.fix_text.SetValue(str(exc))
        finally:
            wx.EndBusyCursor()
            self.btn_next.Enable()
            self.btn_back.Enable()

    # ── Verify ────────────────────────────────────────────────────────

    def _run_verify(self) -> None:
        self.btn_next.Disable()
        self.btn_back.Disable()
        self.verify_status.SetLabel(
            "Re-auditing fixed document, please wait..."
        )
        wx.BeginBusyCursor()
        try:
            target = self.fixed_path if self.fixed_path else self.src_path
            self.post_audit = audit_document(target)
            report = generate_text_report(self.post_audit)
            self.verify_text.SetValue(report)
            self.verify_text.SetInsertionPoint(0)

            score = self.post_audit.score
            grade = self.post_audit.grade
            n = len(self.post_audit.findings)
            if self.post_audit.passed:
                self.verify_status.SetLabel(
                    f"Verification passed: score {score}/100 "
                    f"(grade {grade}). Document is fully compliant."
                )
            else:
                self.verify_status.SetLabel(
                    f"Verification: score {score}/100 "
                    f"(grade {grade}), {n} issues remaining."
                )
            self.btn_view_verify.Enable()
            self.status_bar.SetStatusText(
                f"Verify: {score}/100 grade {grade}, {n} remaining"
            )
        except Exception as exc:
            self.verify_status.SetLabel(f"Verification failed: {exc}")
            self.verify_text.SetValue(str(exc))
        finally:
            wx.EndBusyCursor()
            self.btn_next.Enable()
            self.btn_back.Enable()

    def _on_view_verify_report(self, _evt: wx.CommandEvent) -> None:
        if self.post_audit:
            self._open_report_in_browser(self.post_audit, "Verification")

    # ── Save ──────────────────────────────────────────────────────────

    def _prepare_save_defaults(self) -> None:
        if self.src_path:
            default_name = f"{self.src_path.stem}-acb-compliant.docx"
            default_path = self.src_path.parent / default_name
            self.save_docx_picker.SetPath(str(default_path))
            self.html_dir_picker.SetPath(str(self.src_path.parent))

    def _do_save(self) -> bool:
        docx_dest = self.save_docx_picker.GetPath()
        if not docx_dest:
            wx.MessageBox(
                "Please choose a save location for the Word document.",
                "No save location",
                wx.OK | wx.ICON_INFORMATION,
            )
            self.save_docx_picker.SetFocus()
            return False

        docx_dest = Path(docx_dest)
        self.saved_files.clear()

        wx.BeginBusyCursor()
        try:
            # 1. Copy fixed .docx to chosen location
            src = self.fixed_path if self.fixed_path else self.src_path
            docx_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(docx_dest))
            self.saved_files.append(f"Word document: {docx_dest}")

            # 2. Optional HTML exports
            html_dir = self.html_dir_picker.GetPath()
            if not html_dir:
                html_dir = str(docx_dest.parent)
            html_dir = Path(html_dir)

            title = docx_dest.stem.replace("-", " ").replace("_", " ")

            if self.chk_cms.GetValue():
                cms_path = html_dir / f"{docx_dest.stem}-cms.html"
                export_cms_fragment(src, cms_path, title=title)
                self.saved_files.append(f"CMS fragment: {cms_path}")

            if self.chk_standalone.GetValue():
                html_path = html_dir / f"{docx_dest.stem}.html"
                css_path = html_dir / "acb-large-print.css"
                export_standalone_html(
                    src, html_path, title=title, css_path=css_path,
                )
                self.saved_files.append(f"Standalone HTML: {html_path}")
                self.saved_files.append(f"CSS stylesheet: {css_path}")

            self.status_bar.SetStatusText(
                f"Saved {len(self.saved_files)} files"
            )
            return True

        except Exception as exc:
            wx.MessageBox(
                f"Save failed:\n{exc}",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return False
        finally:
            wx.EndBusyCursor()

    # ── Done ──────────────────────────────────────────────────────────

    def _build_done_summary(self) -> None:
        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("ACB Large Print Wizard -- Complete")
        lines.append("=" * 60)
        lines.append("")

        if self.pre_audit:
            lines.append(
                f"Original score:    {self.pre_audit.score}/100 "
                f"(grade {self.pre_audit.grade})"
            )
            lines.append(
                f"Original findings: {len(self.pre_audit.findings)}"
            )
        lines.append(f"Fixes applied:     {self.total_fixes}")
        if self.post_audit:
            lines.append(
                f"Final score:       {self.post_audit.score}/100 "
                f"(grade {self.post_audit.grade})"
            )
            lines.append(
                f"Remaining issues:  {len(self.post_audit.findings)}"
            )
        lines.append("")

        lines.append("-" * 60)
        lines.append("Files saved:")
        lines.append("-" * 60)
        for f in self.saved_files:
            lines.append(f"  {f}")
        lines.append("")

        if self.post_audit and self.post_audit.passed:
            lines.append(
                "Document is fully compliant with ACB "
                "Large Print Guidelines."
            )
        elif self.post_audit:
            lines.append(
                f"{len(self.post_audit.findings)} issues remain and "
                "may require manual review in Microsoft Word."
            )
        lines.append("")
        lines.append("Press Finish to close the wizard.")

        self.done_text.SetValue("\n".join(lines))
        self.done_text.SetInsertionPoint(0)
        self.done_text.SetFocus()

    # ==================================================================
    # Shared helpers
    # ==================================================================

    def _open_report_in_browser(
        self, result: AuditResult, label: str,
    ) -> None:
        """Write an HTML report to a temp file and open in the browser."""
        html = generate_html_report(result, title=f"ACB {label} Report")
        tmp = (
            Path(tempfile.mkdtemp())
            / f"acb-{label.lower().replace(' ', '-')}-report.html"
        )
        tmp.write_text(html, encoding="utf-8")
        webbrowser.open(tmp.as_uri())


def launch_gui() -> None:
    """Create and run the wizard application."""
    app = wx.App()
    frame = WizardFrame()
    frame.Show()
    app.MainLoop()
