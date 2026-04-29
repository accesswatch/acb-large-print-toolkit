"""Portable rule-selection policy for GLOW audit and fix workflows.

A RulePolicy captures:
  - selected:   the rule IDs activated by mode/profile/category settings
  - suppressed: rule IDs the user explicitly silenced in the report
  - mode_label: human-readable description for audit report headers

Use filter_findings() as the single call-site for applying all rule-selection
logic to a list of Finding objects returned by any GLOW auditor.

This module imports only from acb_large_print.constants (no web/Flask imports)
so it is safe to use in the desktop wizard, CLI, and web routes alike.
"""

from __future__ import annotations

from dataclasses import dataclass

from acb_large_print.constants import AUDIT_RULES, DocFormat


@dataclass(frozen=True)
class RulePolicy:
    """Immutable rule-selection policy.

    Attributes
    ----------
    selected:
        Rule IDs activated by the user's mode, profile, and category choices.
        An empty frozenset means "no rules" (everything filtered out).
    suppressed:
        Rule IDs the user explicitly silenced.  These findings are audited
        internally but removed before the report is shown.
    mode_label:
        Short human-readable label displayed in audit report headers.
    """

    selected: frozenset[str]
    suppressed: frozenset[str]
    mode_label: str = "Full Audit -- all rules"

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------

    def effective_ids(self, doc_format: str | None = None) -> frozenset[str]:
        """Return the rule IDs that will produce visible findings.

        Parameters
        ----------
        doc_format:
            Optional lowercase format key ("docx", "xlsx", "pptx", "md",
            "pdf", "epub").  When given, intersects with rules that apply to
            that format before subtracting suppressed.
        """
        active = self.selected
        if doc_format:
            try:
                fmt = DocFormat(doc_format)
                format_ids = frozenset(
                    r.rule_id for r in AUDIT_RULES.values() if fmt in r.formats
                )
                active = active & format_ids
            except ValueError:
                pass  # unknown format string: keep full selected set
        return active - self.suppressed

    def filter_findings(self, findings: list, doc_format: str | None = None) -> list:
        """Return the subset of findings whose rule_id is in effective_ids().

        Parameters
        ----------
        findings:
            A list of Finding / AuditFinding objects (any object with a
            ``rule_id`` attribute).
        doc_format:
            Passed through to effective_ids().
        """
        effective = self.effective_ids(doc_format)
        return [f for f in findings if f.rule_id in effective]
