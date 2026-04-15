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
from . import constants as C
from .auditor import AuditResult, audit_document
from .exporter import export_cms_fragment, export_standalone_html
from .fixer import fix_document
from .reporter import generate_html_report, generate_text_report

# Supported file extensions for the GUI
_SUPPORTED_EXTENSIONS = {".docx", ".xlsx", ".pptx"}
_DOCX_ONLY_EXTENSIONS = {".docx"}

# Extensions MarkItDown can convert to Markdown
try:
    from .converter import CONVERTIBLE_EXTENSIONS as _CONVERT_EXTENSIONS
except ImportError:
    _CONVERT_EXTENSIONS: set[str] = set()

# Extensions Pandoc can convert to ACB HTML
try:
    from .pandoc_converter import PANDOC_INPUT_EXTENSIONS as _PANDOC_EXTENSIONS
    from .pandoc_converter import pandoc_available as _pandoc_available
except ImportError:
    _PANDOC_EXTENSIONS: set[str] = set()

    def _pandoc_available() -> bool:
        return False


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
        root.Add(
            self.page_sizer,
            proportion=1,
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=10,
        )

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

        # Menu bar
        self._build_menu_bar()

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

        intro = wx.StaticText(
            page,
            label=(
                "Welcome to the GLOW Accessibility Wizard.\n\n"
                "This wizard will:\n"
                "  1. Audit your document for ACB guideline violations\n"
                "  2. Attempt to automatically fix issues found (Word only)\n"
                "  3. Verify the fixes were applied correctly\n"
                "  4. Save the corrected document and optional HTML exports\n\n"
                "Select a Word, Excel, or PowerPoint document to begin."
            ),
        )
        intro.Wrap(560)
        sizer.Add(intro, flag=wx.BOTTOM, border=15)

        lbl = wx.StaticText(page, label="&Document file:")
        sizer.Add(lbl)
        self.file_picker = wx.FilePickerCtrl(
            page,
            message="Open a document",
            wildcard=(
                "Office Documents (*.docx;*.xlsx;*.pptx)|*.docx;*.xlsx;*.pptx|"
                "Word Documents (*.docx)|*.docx|"
                "Excel Workbooks (*.xlsx)|*.xlsx|"
                "PowerPoint Presentations (*.pptx)|*.pptx"
            ),
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
            page,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP,
        )
        self.audit_text.SetName("Initial audit results")
        mono = wx.Font(
            10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )
        self.audit_text.SetFont(mono)
        sizer.Add(self.audit_text, proportion=1, flag=wx.EXPAND)

        self.btn_view_audit = wx.Button(
            page,
            label="&View report in browser",
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

        intro = wx.StaticText(
            page,
            label=(
                "Choose which outputs to create in addition to the "
                "fixed document. HTML exports are available for Word "
                "documents only. Markdown conversion works for all formats."
            ),
        )
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
        sizer.Add(self.chk_standalone, flag=wx.BOTTOM, border=6)

        self.chk_convert_md = wx.CheckBox(
            page,
            label="&Markdown file (convert document to Markdown via MarkItDown)",
        )
        self.chk_convert_md.SetName("Convert document to Markdown using MarkItDown")
        self.chk_convert_md.SetValue(False)
        if not _CONVERT_EXTENSIONS:
            self.chk_convert_md.Disable()
            self.chk_convert_md.SetLabel("Markdown file (MarkItDown not installed)")
        sizer.Add(self.chk_convert_md, flag=wx.BOTTOM, border=6)

        self.chk_convert_html = wx.CheckBox(
            page,
            label="ACB &HTML file (convert document to HTML via Pandoc)",
        )
        self.chk_convert_html.SetName(
            "Convert document to ACB-compliant HTML using Pandoc"
        )
        self.chk_convert_html.SetValue(False)
        if not _PANDOC_EXTENSIONS or not _pandoc_available():
            self.chk_convert_html.Disable()
            self.chk_convert_html.SetLabel("ACB HTML file (Pandoc not installed)")
        sizer.Add(self.chk_convert_html, flag=wx.BOTTOM, border=12)

        # ── List indentation controls ─────────────────────────────────
        list_box = wx.StaticBox(page, label="List Indentation")
        list_sizer = wx.StaticBoxSizer(list_box, wx.VERTICAL)

        self.chk_flush_lists = wx.CheckBox(
            list_box,
            label="&Flush all lists to the left margin (ACB default)",
        )
        self.chk_flush_lists.SetName(
            "Flush all list items to the left margin with zero indentation"
        )
        self.chk_flush_lists.SetValue(C.LIST_INDENT_IN == 0.0)
        self.chk_flush_lists.Bind(wx.EVT_CHECKBOX, self._on_flush_lists_toggle)
        list_sizer.Add(self.chk_flush_lists, flag=wx.BOTTOM, border=8)

        indent_grid = wx.FlexGridSizer(cols=2, hgap=8, vgap=6)
        indent_grid.AddGrowableCol(1)

        lbl_left = wx.StaticText(list_box, label="Left indent (inches):")
        self.spin_list_indent = wx.SpinCtrlDouble(
            list_box,
            min=0.0,
            max=2.0,
            inc=0.05,
            value=str(C.LIST_INDENT_IN),
        )
        self.spin_list_indent.SetDigits(2)
        self.spin_list_indent.SetName("Left indent for list items in inches")
        indent_grid.Add(lbl_left, flag=wx.ALIGN_CENTER_VERTICAL)
        indent_grid.Add(self.spin_list_indent, flag=wx.EXPAND)

        lbl_hang = wx.StaticText(list_box, label="Hanging indent (inches):")
        self.spin_list_hanging = wx.SpinCtrlDouble(
            list_box,
            min=0.0,
            max=2.0,
            inc=0.05,
            value=str(C.LIST_HANGING_IN),
        )
        self.spin_list_hanging.SetDigits(2)
        self.spin_list_hanging.SetName(
            "Hanging indent for list bullet or number in inches"
        )
        indent_grid.Add(lbl_hang, flag=wx.ALIGN_CENTER_VERTICAL)
        indent_grid.Add(self.spin_list_hanging, flag=wx.EXPAND)

        list_sizer.Add(indent_grid, flag=wx.EXPAND | wx.BOTTOM, border=8)

        list_note = wx.StaticText(
            list_box,
            label=(
                "ACB guidelines require flush-left alignment for all text. "
                "Uncheck this option to keep standard Word list indentation "
                "(0.50 inch left indent, 0.25 inch hanging indent). "
                "You can also set custom values below."
            ),
        )
        list_note.Wrap(520)
        list_sizer.Add(list_note)

        sizer.Add(list_sizer, flag=wx.EXPAND | wx.BOTTOM, border=12)

        # Sync initial enabled state
        self._on_flush_lists_toggle(None)

        # ── Paragraph indentation controls ────────────────────────────
        para_box = wx.StaticBox(page, label="Paragraph Indentation")
        para_sizer = wx.StaticBoxSizer(para_box, wx.VERTICAL)

        self.chk_flush_paragraphs = wx.CheckBox(
            para_box,
            label="Flush all &paragraphs to the left margin (ACB default)",
        )
        self.chk_flush_paragraphs.SetName(
            "Remove all paragraph indentation including first-line indent"
        )
        self.chk_flush_paragraphs.SetValue(True)
        self.chk_flush_paragraphs.Bind(
            wx.EVT_CHECKBOX, self._on_flush_paragraphs_toggle
        )
        para_sizer.Add(self.chk_flush_paragraphs, flag=wx.BOTTOM, border=8)

        para_grid = wx.FlexGridSizer(cols=2, hgap=8, vgap=6)
        para_grid.AddGrowableCol(1)

        lbl_para = wx.StaticText(para_box, label="Left indent (inches):")
        self.spin_para_indent = wx.SpinCtrlDouble(
            para_box,
            min=0.0,
            max=2.0,
            inc=0.05,
            value=str(C.PARA_INDENT_IN),
        )
        self.spin_para_indent.SetDigits(2)
        self.spin_para_indent.SetName("Left indent for paragraphs in inches")
        para_grid.Add(lbl_para, flag=wx.ALIGN_CENTER_VERTICAL)
        para_grid.Add(self.spin_para_indent, flag=wx.EXPAND)

        lbl_first = wx.StaticText(para_box, label="First-line indent (inches):")
        self.spin_first_line_indent = wx.SpinCtrlDouble(
            para_box,
            min=0.0,
            max=2.0,
            inc=0.05,
            value=str(C.FIRST_LINE_INDENT_IN),
        )
        self.spin_first_line_indent.SetDigits(2)
        self.spin_first_line_indent.SetName(
            "First-line indent for paragraphs in inches"
        )
        para_grid.Add(lbl_first, flag=wx.ALIGN_CENTER_VERTICAL)
        para_grid.Add(self.spin_first_line_indent, flag=wx.EXPAND)

        para_sizer.Add(para_grid, flag=wx.EXPAND | wx.BOTTOM, border=8)
        sizer.Add(para_sizer, flag=wx.EXPAND | wx.BOTTOM, border=12)

        # Sync initial enabled state
        self._on_flush_paragraphs_toggle(None)

        # ── Heading detection controls ────────────────────────────────
        hd_box = wx.StaticBox(page, label="Heading Detection (Word only)")
        hd_sizer = wx.StaticBoxSizer(hd_box, wx.VERTICAL)

        self.chk_detect_headings = wx.CheckBox(
            hd_box,
            label="&Detect and convert faux headings to real heading styles",
        )
        self.chk_detect_headings.SetName(
            "Detect paragraphs that look like headings but lack heading styles"
        )
        self.chk_detect_headings.SetValue(False)
        self.chk_detect_headings.Bind(wx.EVT_CHECKBOX, self._on_detect_headings_toggle)
        hd_sizer.Add(self.chk_detect_headings, flag=wx.BOTTOM, border=6)

        self.chk_use_ai = wx.CheckBox(
            hd_box,
            label="Refine with &AI (requires Ollama running locally)",
        )
        self.chk_use_ai.SetName(
            "Use Ollama local AI to improve heading detection accuracy"
        )
        from acb_large_print.ai_provider import is_ai_available

        self.chk_use_ai.SetValue(is_ai_available())
        hd_sizer.Add(self.chk_use_ai, flag=wx.BOTTOM, border=6)

        threshold_row = wx.BoxSizer(wx.HORIZONTAL)
        lbl_thr = wx.StaticText(hd_box, label="Confidence threshold (0-100):")
        self.spin_heading_threshold = wx.SpinCtrl(
            hd_box,
            min=0,
            max=100,
            initial=C.HEADING_CONFIDENCE_THRESHOLD,
        )
        self.spin_heading_threshold.SetName(
            "Minimum confidence score for heading detection"
        )
        threshold_row.Add(lbl_thr, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=8)
        threshold_row.Add(self.spin_heading_threshold)
        hd_sizer.Add(threshold_row, flag=wx.BOTTOM, border=8)

        hd_note = wx.StaticText(
            hd_box,
            label=(
                "Detects bold, large-font paragraphs styled as Normal and "
                "converts them to Heading 1, 2, or 3. AI refinement uses "
                "Ollama to resolve ambiguous candidates."
            ),
        )
        hd_note.Wrap(500)
        hd_sizer.Add(hd_note)

        sizer.Add(hd_sizer, flag=wx.EXPAND | wx.BOTTOM, border=12)

        # Sync initial enabled state
        self._on_detect_headings_toggle(None)

        note = wx.StaticText(
            page,
            label=(
                "The CMS fragment is a single file you can paste directly into "
                "a WordPress or Drupal HTML block. The standalone version is a "
                "complete web page with a separate CSS file for hosting or email. "
                "The Markdown option converts to Markdown via MarkItDown. "
                "The ACB HTML option converts to accessible HTML with embedded "
                "ACB Large Print CSS via Pandoc."
            ),
        )
        note.Wrap(560)
        sizer.Add(note)

        page.SetSizer(sizer)

    # ── List indent toggle handler ──────────────────────────────────

    def _on_flush_lists_toggle(self, _event) -> None:
        """Enable or disable the custom indent fields based on the flush checkbox."""
        flush = self.chk_flush_lists.GetValue()
        self.spin_list_indent.Enable(not flush)
        self.spin_list_hanging.Enable(not flush)
        if flush:
            self.spin_list_indent.SetValue(0.0)
            self.spin_list_hanging.SetValue(0.0)
        else:
            # Revert to standard Word indent when unchecked
            std_left, std_hang = C.LIST_INDENT_STANDARD
            self.spin_list_indent.SetValue(std_left)
            self.spin_list_hanging.SetValue(std_hang)

    # ── Paragraph indent toggle handler ───────────────────────────────

    def _on_flush_paragraphs_toggle(self, _event) -> None:
        """Enable or disable paragraph indent fields based on the flush checkbox."""
        flush = self.chk_flush_paragraphs.GetValue()
        self.spin_para_indent.Enable(not flush)
        self.spin_first_line_indent.Enable(not flush)
        if flush:
            self.spin_para_indent.SetValue(0.0)
            self.spin_first_line_indent.SetValue(0.0)

    # ── Heading detection toggle handler ──────────────────────────────

    def _on_detect_headings_toggle(self, _event) -> None:
        """Enable or disable AI and threshold fields based on detect headings checkbox."""
        enabled = self.chk_detect_headings.GetValue()
        self.chk_use_ai.Enable(enabled)
        self.spin_heading_threshold.Enable(enabled)
        if not enabled:
            self.chk_use_ai.SetValue(False)
        else:
            from acb_large_print.ai_provider import is_ai_available

            self.chk_use_ai.SetValue(is_ai_available())

    # ── Step 4: Remediation ───────────────────────────────────────────

    def _build_step_fix(self) -> None:
        page = self._make_page()
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.fix_status = wx.StaticText(page, label="Applying fixes...")
        sizer.Add(self.fix_status, flag=wx.BOTTOM, border=8)

        self.fix_text = wx.TextCtrl(
            page,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP,
        )
        self.fix_text.SetName("Remediation results")
        mono = wx.Font(
            10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )
        self.fix_text.SetFont(mono)
        sizer.Add(self.fix_text, proportion=1, flag=wx.EXPAND)

        page.SetSizer(sizer)

    # ── Step 5: Verification ──────────────────────────────────────────

    def _build_step_verify(self) -> None:
        page = self._make_page()
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.verify_status = wx.StaticText(
            page,
            label="Re-auditing fixed document...",
        )
        sizer.Add(self.verify_status, flag=wx.BOTTOM, border=8)

        self.verify_text = wx.TextCtrl(
            page,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP,
        )
        self.verify_text.SetName("Verification audit results")
        mono = wx.Font(
            10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )
        self.verify_text.SetFont(mono)
        sizer.Add(self.verify_text, proportion=1, flag=wx.EXPAND)

        self.btn_view_verify = wx.Button(
            page,
            label="View &verification report in browser",
        )
        self.btn_view_verify.SetName("Open verification report in default web browser")
        self.btn_view_verify.Bind(wx.EVT_BUTTON, self._on_view_verify_report)
        self.btn_view_verify.Disable()
        sizer.Add(self.btn_view_verify, flag=wx.TOP, border=8)

        page.SetSizer(sizer)

    # ── Step 6: Save ──────────────────────────────────────────────────

    def _build_step_save(self) -> None:
        page = self._make_page()
        sizer = wx.BoxSizer(wx.VERTICAL)

        intro = wx.StaticText(
            page,
            label=("Choose where to save the fixed document and any HTML exports."),
        )
        intro.Wrap(560)
        sizer.Add(intro, flag=wx.BOTTOM, border=12)

        lbl_docx = wx.StaticText(page, label="Fixed &document:")
        sizer.Add(lbl_docx)
        self.save_docx_picker = wx.FilePickerCtrl(
            page,
            message="Save fixed document as",
            wildcard=(
                "Office Documents (*.docx;*.xlsx;*.pptx)|*.docx;*.xlsx;*.pptx|"
                "Word Documents (*.docx)|*.docx|"
                "Excel Workbooks (*.xlsx)|*.xlsx|"
                "PowerPoint Presentations (*.pptx)|*.pptx"
            ),
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
            page,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP,
        )
        self.done_text.SetName("Summary of all actions completed")
        mono = wx.Font(
            10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )
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
            if self._is_docx or self._can_convert or self._can_convert_html:
                # Disable heading detection for non-Word files
                self.chk_detect_headings.Enable(self._is_docx)
                if not self._is_docx:
                    self.chk_detect_headings.SetValue(False)
                    self._on_detect_headings_toggle(None)
                self._show_step(STEP_OPTIONS)
            else:
                # Skip export options for non-convertible formats
                self._show_step(STEP_FIX)
                wx.CallAfter(self._run_fix)

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
                "Please select a document to continue.",
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
        if p.suffix.lower() not in _SUPPORTED_EXTENSIONS:
            wx.MessageBox(
                "Please select a .docx, .xlsx, or .pptx file.",
                "Unsupported file type",
                wx.OK | wx.ICON_INFORMATION,
            )
            self.file_picker.SetFocus()
            return False
        self.src_path = p
        return True

    def _audit_by_extension(self, file_path: Path) -> AuditResult:
        """Dispatch to the correct auditor based on file extension."""
        ext = file_path.suffix.lower()
        if ext == ".xlsx":
            from .xlsx_auditor import audit_workbook

            return audit_workbook(file_path)
        elif ext == ".pptx":
            from .pptx_auditor import audit_presentation

            return audit_presentation(file_path)
        else:
            return audit_document(file_path)

    def _fix_by_extension(self, file_path: Path, output_path: Path):
        """Dispatch to the correct fixer based on file extension.

        Returns (output_path, total_fixes, fix_records, post_audit, warnings).
        """
        ext = file_path.suffix.lower()
        if ext == ".xlsx":
            from .xlsx_auditor import audit_workbook

            post_audit = audit_workbook(file_path)
            return (
                file_path,
                0,
                [],
                post_audit,
                [
                    "Excel workbooks cannot be auto-fixed yet. "
                    "Review the audit findings and fix them manually in Excel."
                ],
            )
        elif ext == ".pptx":
            from .pptx_auditor import audit_presentation

            post_audit = audit_presentation(file_path)
            return (
                file_path,
                0,
                [],
                post_audit,
                [
                    "PowerPoint presentations cannot be auto-fixed yet. "
                    "Review the audit findings and fix them manually in PowerPoint."
                ],
            )
        else:
            # Resolve heading detection options
            detect_headings = self._is_docx and self.chk_detect_headings.GetValue()
            ai_provider = None
            if detect_headings and self.chk_use_ai.GetValue():
                try:
                    from .ai_provider import get_provider

                    ai_provider = get_provider()
                except Exception:
                    pass  # Fall back to heuristic-only
            return fix_document(
                file_path,
                output_path,
                list_indent_in=self.spin_list_indent.GetValue(),
                list_hanging_in=self.spin_list_hanging.GetValue(),
                para_indent_in=self.spin_para_indent.GetValue(),
                first_line_indent_in=self.spin_first_line_indent.GetValue(),
                detect_headings=detect_headings,
                ai_provider=ai_provider,
                heading_threshold=self.spin_heading_threshold.GetValue(),
            )

    @property
    def _is_docx(self) -> bool:
        """True if the source file is a Word document."""
        return self.src_path is not None and self.src_path.suffix.lower() == ".docx"

    @property
    def _can_convert(self) -> bool:
        """True if the source file can be converted to Markdown."""
        return (
            bool(_CONVERT_EXTENSIONS)
            and self.src_path is not None
            and self.src_path.suffix.lower() in _CONVERT_EXTENSIONS
        )

    @property
    def _can_convert_html(self) -> bool:
        """True if the source file can be converted to HTML via Pandoc."""
        return (
            bool(_PANDOC_EXTENSIONS)
            and _pandoc_available()
            and self.src_path is not None
            and self.src_path.suffix.lower() in _PANDOC_EXTENSIONS
        )

    # ── Audit ─────────────────────────────────────────────────────────

    def _run_initial_audit(self) -> None:
        self.btn_next.Disable()
        self.btn_back.Disable()
        self.audit_status.SetLabel("Auditing document, please wait...")
        wx.BeginBusyCursor()
        try:
            self.pre_audit = self._audit_by_extension(self.src_path)
            report = generate_text_report(self.pre_audit)
            self.audit_text.SetValue(report)
            self.audit_text.SetInsertionPoint(0)

            score = self.pre_audit.score
            grade = self.pre_audit.grade
            n = len(self.pre_audit.findings)
            self.audit_status.SetLabel(
                f"Audit complete: score {score}/100 " f"(grade {grade}), {n} findings."
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
            self.fixed_path, self.total_fixes, _records, self.post_audit, warnings = (
                self._fix_by_extension(
                    self.src_path,
                    tmp,
                )
            )

            lines: list[str] = []
            for w in warnings:
                lines.append(f"WARNING: {w}")
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
                        f"  {i}. [{f.severity.value}] " f"{f.rule_id}: {f.message}"
                    )
            else:
                lines.append("All issues resolved. Document is fully compliant.")

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
        self.verify_status.SetLabel("Re-auditing fixed document, please wait...")
        wx.BeginBusyCursor()
        try:
            target = self.fixed_path if self.fixed_path else self.src_path
            self.post_audit = self._audit_by_extension(target)
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
            ext = self.src_path.suffix.lower()
            default_name = f"{self.src_path.stem}-acb-compliant{ext}"
            default_path = self.src_path.parent / default_name
            self.save_docx_picker.SetPath(str(default_path))
            self.html_dir_picker.SetPath(str(self.src_path.parent))
            # Hide HTML export controls for non-Word files
            show_html = self._is_docx
            self.html_dir_picker.Show(show_html)
            # Enable/disable HTML and Markdown checkboxes based on format
            self.chk_cms.Enable(show_html)
            self.chk_standalone.Enable(show_html)
            if not show_html:
                self.chk_cms.SetValue(False)
                self.chk_standalone.SetValue(False)

    def _do_save(self) -> bool:
        docx_dest = self.save_docx_picker.GetPath()
        if not docx_dest:
            wx.MessageBox(
                "Please choose a save location for the document.",
                "No save location",
                wx.OK | wx.ICON_INFORMATION,
            )
            self.save_docx_picker.SetFocus()
            return False

        docx_dest = Path(docx_dest)
        self.saved_files.clear()

        wx.BeginBusyCursor()
        try:
            # 1. Copy fixed document to chosen location
            src = self.fixed_path if self.fixed_path else self.src_path
            docx_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(docx_dest))
            self.saved_files.append(f"Document: {docx_dest}")

            # 2. Optional HTML exports (Word only)
            if self._is_docx:
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
                        src,
                        html_path,
                        title=title,
                        css_path=css_path,
                    )
                    self.saved_files.append(f"Standalone HTML: {html_path}")
                    self.saved_files.append(f"CSS stylesheet: {css_path}")

            # 3. Optional Markdown conversion (any convertible format)
            if self.chk_convert_md.GetValue() and self._can_convert:
                from .converter import convert_to_markdown

                md_path = docx_dest.with_suffix(".md")
                convert_to_markdown(src, output_path=md_path)
                self.saved_files.append(f"Markdown: {md_path}")

            # 4. Optional Pandoc HTML conversion
            if self.chk_convert_html.GetValue() and self._can_convert_html:
                from .pandoc_converter import convert_to_html

                html_path = docx_dest.with_suffix(".html")
                title = docx_dest.stem.replace("-", " ").replace("_", " ")
                convert_to_html(src, output_path=html_path, title=title)
                self.saved_files.append(f"ACB HTML: {html_path}")

            self.status_bar.SetStatusText(f"Saved {len(self.saved_files)} files")
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
            lines.append(f"Original findings: {len(self.pre_audit.findings)}")
        lines.append(f"Fixes applied:     {self.total_fixes}")
        if self.post_audit:
            lines.append(
                f"Final score:       {self.post_audit.score}/100 "
                f"(grade {self.post_audit.grade})"
            )
            lines.append(f"Remaining issues:  {len(self.post_audit.findings)}")
        lines.append("")

        lines.append("-" * 60)
        lines.append("Files saved:")
        lines.append("-" * 60)
        for f in self.saved_files:
            lines.append(f"  {f}")
        lines.append("")

        if self.post_audit and self.post_audit.passed:
            lines.append(
                "Document is fully compliant with ACB " "Large Print Guidelines."
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
    # Menu bar
    # ==================================================================

    def _build_menu_bar(self) -> None:
        """Build the application menu bar with a Help menu."""
        menu_bar = wx.MenuBar()

        help_menu = wx.Menu()
        self._id_guide = wx.NewIdRef()
        self._id_changelog = wx.NewIdRef()
        self._id_prd = wx.NewIdRef()
        self._id_about = wx.NewIdRef()

        help_menu.Append(self._id_guide, "&User Guide", "Open the user guide in your browser")
        help_menu.Append(self._id_changelog, "&Changelog", "Open the changelog in your browser")
        help_menu.Append(self._id_prd, "&Product Requirements Document", "Open the PRD in your browser")
        help_menu.AppendSeparator()
        help_menu.Append(self._id_about, "&About", f"About {__app_name__}")

        menu_bar.Append(help_menu, "&Help")
        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self._on_help_guide, id=self._id_guide)
        self.Bind(wx.EVT_MENU, self._on_help_changelog, id=self._id_changelog)
        self.Bind(wx.EVT_MENU, self._on_help_prd, id=self._id_prd)
        self.Bind(wx.EVT_MENU, self._on_help_about, id=self._id_about)

    def _find_docs_file(self, filename: str) -> Path | None:
        """Locate a file in the docs/ directory by traversing parents."""
        p = Path(__file__).resolve().parent
        for _ in range(10):
            candidate = p / "docs" / filename
            if candidate.is_file():
                return candidate
            candidate = p / filename
            if candidate.is_file():
                return candidate
            p = p.parent
        return None

    def _open_docs_file_in_browser(self, filename: str, title: str) -> None:
        """Find a markdown docs file, render it to temp HTML, and open in browser."""
        from . import __version__

        doc_path = self._find_docs_file(filename)
        if doc_path is None:
            wx.MessageBox(
                f"Could not locate {filename}.",
                "File Not Found",
                wx.OK | wx.ICON_INFORMATION,
            )
            return

        try:
            md_text = doc_path.read_text(encoding="utf-8")
        except OSError as exc:
            wx.MessageBox(
                f"Could not read {filename}:\n{exc}",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        html = self._md_to_html(md_text, title)
        tmp = Path(tempfile.mkdtemp()) / f"{doc_path.stem}.html"
        tmp.write_text(html, encoding="utf-8")
        webbrowser.open(tmp.as_uri())

    def _md_to_html(self, md_text: str, title: str) -> str:
        """Convert markdown to a simple accessible HTML page."""
        import re

        lines = md_text.splitlines()
        body_parts: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # Headings
            m = re.match(r'^(#{1,4})\s+(.*)', line)
            if m:
                level = len(m.group(1)) + 1  # h1 is the page title
                level = min(level, 6)
                text = m.group(2).strip()
                body_parts.append(f'<h{level}>{text}</h{level}>')
                i += 1
                continue

            # Horizontal rule
            if re.match(r'^[-*_]{3,}\s*$', line):
                body_parts.append('<hr>')
                i += 1
                continue

            # Unordered list
            if re.match(r'^[\-\*]\s+', line):
                items = []
                while i < len(lines) and re.match(r'^[\-\*]\s+', lines[i]):
                    items.append(f'<li>{re.sub(r"^[\-\*]\s+", "", lines[i])}</li>')
                    i += 1
                body_parts.append('<ul>' + ''.join(items) + '</ul>')
                continue

            # Ordered list
            if re.match(r'^\d+\.\s+', line):
                items = []
                while i < len(lines) and re.match(r'^\d+\.\s+', lines[i]):
                    items.append(f'<li>{re.sub(r"^\d+\.\s+", "", lines[i])}</li>')
                    i += 1
                body_parts.append('<ol>' + ''.join(items) + '</ol>')
                continue

            # Blank line -> paragraph break (skip)
            if not line.strip():
                i += 1
                continue

            # Paragraph
            para_lines = []
            while i < len(lines) and lines[i].strip():
                para_lines.append(lines[i])
                i += 1
            para = ' '.join(para_lines)
            # Inline: bold, code, links
            para = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', para)
            para = re.sub(r'`([^`]+)`', r'<code>\1</code>', para)
            para = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', para)
            body_parts.append(f'<p>{para}</p>')

        body = '\n'.join(body_parts)
        return (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            f'<meta charset="utf-8">\n<title>{title}</title>\n'
            '<style>\n'
            'body{font-family:Arial,sans-serif;font-size:18px;line-height:1.5;'
            'max-width:900px;margin:2rem auto;padding:0 1.5rem;color:#1a1a1a}\n'
            'h1,h2,h3{margin-top:2rem}\n'
            'code{background:#f4f4f4;padding:.1em .3em;border-radius:3px}\n'
            'hr{border:none;border-top:1px solid #ccc;margin:2rem 0}\n'
            'a{color:#003da5}\n'
            '</style>\n</head>\n<body>\n'
            f'<h1>{title}</h1>\n'
            f'{body}\n'
            '</body>\n</html>'
        )

    def _on_help_guide(self, _evt: wx.CommandEvent) -> None:
        self._open_docs_file_in_browser("user-guide.md", "GLOW User Guide")

    def _on_help_changelog(self, _evt: wx.CommandEvent) -> None:
        self._open_docs_file_in_browser("CHANGELOG.md", "GLOW Changelog")

    def _on_help_prd(self, _evt: wx.CommandEvent) -> None:
        self._open_docs_file_in_browser("prd.md", "GLOW Product Requirements Document")

    def _on_help_about(self, _evt: wx.CommandEvent) -> None:
        from . import __app_name__, __version__

        wx.MessageBox(
            f"{__app_name__} {__version__}\n\n"
            "Audits and fixes Word, Excel, and PowerPoint documents\n"
            "for compliance with the ACB Large Print Guidelines\n"
            "and WCAG 2.2 Level AA.\n\n"
            "Sponsored by Blind Information Technology Solutions (BITS),\n"
            "a special interest affiliate of the American Council of the Blind.",
            f"About {__app_name__}",
            wx.OK | wx.ICON_INFORMATION,
        )

    # ==================================================================
    # Shared helpers
    # ==================================================================

    def _open_report_in_browser(
        self,
        result: AuditResult,
        label: str,
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
