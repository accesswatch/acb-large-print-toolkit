"""Rule-based WCAG language checks for extracted document text.

This module is intentionally deterministic (non-AI) so it can run in web,
desktop CLI, and batch pipelines at scale.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re


_AMBIGUOUS_LINK_TEXT_RE = re.compile(
    r"(?im)\[[ \t]*(click here|here|read more|learn more|more|this link|link|details|info)[ \t]*\]\([^)]+\)"
)
_BARE_URL_RE = re.compile(r"(?i)\bhttps?://[^\s)>\]]+")
_DIRECTIONAL_INSTRUCTION_RE = re.compile(
    r"(?i)\b(click here|see above|see below|use the button above|the link below)\b"
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-]*")

_LANG_META_RE = re.compile(r"(?im)^\s*(lang|language)\s*:\s*['\"]?([A-Za-z0-9-]+)")
_HTML_LANG_RE = re.compile(r"(?is)<html[^>]*\blang\s*=\s*['\"]([A-Za-z0-9-]+)['\"]")
_XML_LANG_RE = re.compile(r"(?is)\bxml:lang\s*=\s*['\"]([A-Za-z0-9-]+)['\"]")


@dataclass(frozen=True)
class LanguageFinding:
    rule_id: str
    severity: str
    wcag: str
    message: str
    snippet: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class LanguageReport:
    stage: str
    findings: tuple[LanguageFinding, ...]

    @property
    def total(self) -> int:
        return len(self.findings)

    @property
    def error_count(self) -> int:
        return sum(1 for item in self.findings if item.severity.lower() == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for item in self.findings if item.severity.lower() == "warning")

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": self.stage,
            "total": self.total,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "findings": [item.to_dict() for item in self.findings],
        }


def _snippet(text: str, limit: int = 120) -> str:
    cleaned = " ".join(text.strip().split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def _language_declared(text: str) -> bool:
    if _HTML_LANG_RE.search(text):
        return True
    if _XML_LANG_RE.search(text):
        return True

    if text.lstrip().startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            front_matter = text[: end + 4]
            if _LANG_META_RE.search(front_matter):
                return True
    return False


def analyze_text_for_wcag_language(text: str, *, stage: str) -> LanguageReport:
    findings: list[LanguageFinding] = []

    if not _language_declared(text):
        findings.append(
            LanguageFinding(
                rule_id="WCAG-LANG-DECLARATION",
                severity="error",
                wcag="3.1.1",
                message="Document language is not declared (for example `lang: en` or `<html lang=\"en\">`).",
            )
        )

    for match in _AMBIGUOUS_LINK_TEXT_RE.finditer(text):
        findings.append(
            LanguageFinding(
                rule_id="WCAG-DESCRIPTIVE-LINK-TEXT",
                severity="warning",
                wcag="2.4.4",
                message="Link text is ambiguous; use descriptive wording instead of generic phrases.",
                snippet=_snippet(match.group(0)),
            )
        )

    for match in _BARE_URL_RE.finditer(text):
        findings.append(
            LanguageFinding(
                rule_id="WCAG-RAW-URL-LINK-TEXT",
                severity="warning",
                wcag="2.4.4",
                message="Bare URL detected; wrap it with descriptive link text.",
                snippet=_snippet(match.group(0)),
            )
        )

    for match in _DIRECTIONAL_INSTRUCTION_RE.finditer(text):
        findings.append(
            LanguageFinding(
                rule_id="WCAG-CLEAR-INSTRUCTIONS",
                severity="warning",
                wcag="3.3.2",
                message="Instruction wording depends on visual position; prefer explicit action labels.",
                snippet=_snippet(match.group(0)),
            )
        )

    for sentence in _SENTENCE_SPLIT_RE.split(text):
        words = _WORD_RE.findall(sentence)
        if len(words) > 32:
            findings.append(
                LanguageFinding(
                    rule_id="PLAIN-LANGUAGE-LONG-SENTENCE",
                    severity="warning",
                    wcag="3.1.5",
                    message="Long sentence may reduce readability; consider splitting for plain language clarity.",
                    snippet=_snippet(sentence),
                )
            )
            if len(findings) >= 40:
                break

    return LanguageReport(stage=stage, findings=tuple(findings))


def format_language_report_for_error(report: LanguageReport, *, max_items: int = 4) -> str:
    if not report.findings:
        return ""
    lines = [f"WCAG language processing ({report.stage}) found {report.total} issue(s):"]
    for item in report.findings[:max_items]:
        wcag = f"WCAG {item.wcag}" if item.wcag else "WCAG"
        lines.append(f"- {item.rule_id} ({wcag}): {item.message}")
    if report.total > max_items:
        lines.append(f"- ...and {report.total - max_items} more.")
    return "\n".join(lines)
