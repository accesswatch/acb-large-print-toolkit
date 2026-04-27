"""Guardrails preventing redundant landmark ARIA usage in templates."""

from __future__ import annotations

from pathlib import Path


TEMPLATES_ROOT = Path(__file__).resolve().parents[1] / "src" / "acb_large_print_web" / "templates"


def _template_paths() -> list[Path]:
    return sorted(TEMPLATES_ROOT.rglob("*.html"))


def test_no_section_aria_labelledby_landmarks() -> None:
    """Avoid creating noisy region landmarks from generic section blocks."""
    offenders: list[str] = []
    for path in _template_paths():
        text = path.read_text(encoding="utf-8")
        if "<section" in text and "aria-labelledby=" in text:
            # Keep this strict and simple: section blocks should not carry aria-labelledby.
            for line_no, line in enumerate(text.splitlines(), start=1):
                if "<section" in line and "aria-labelledby=" in line:
                    rel = path.relative_to(TEMPLATES_ROOT.parent.parent.parent)
                    offenders.append(f"{rel}:{line_no}: {line.strip()}")

    assert not offenders, (
        "Found section landmarks with aria-labelledby. "
        "Remove redundant section landmark naming to reduce landmark noise:\n"
        + "\n".join(offenders)
    )


def test_no_redundant_footer_contentinfo_role() -> None:
    """Footer already maps to contentinfo; explicit role is redundant."""
    offenders: list[str] = []
    for path in _template_paths():
        text = path.read_text(encoding="utf-8")
        if "<footer role=\"contentinfo\"" in text:
            for line_no, line in enumerate(text.splitlines(), start=1):
                if "<footer role=\"contentinfo\"" in line:
                    rel = path.relative_to(TEMPLATES_ROOT.parent.parent.parent)
                    offenders.append(f"{rel}:{line_no}: {line.strip()}")

    assert not offenders, (
        "Found redundant footer role contentinfo declarations:\n"
        + "\n".join(offenders)
    )


def test_no_redundant_native_landmark_roles() -> None:
    """Native landmark elements should not redeclare equivalent ARIA landmark roles."""
    redundant_patterns = {
        '<header role="banner"': "header already maps to banner",
        '<nav role="navigation"': "nav already maps to navigation",
        '<main role="main"': "main already maps to main",
        '<footer role="contentinfo"': "footer already maps to contentinfo",
        '<aside role="complementary"': "aside already maps to complementary",
    }

    offenders: list[str] = []
    for path in _template_paths():
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            for pattern, reason in redundant_patterns.items():
                if pattern in stripped:
                    rel = path.relative_to(TEMPLATES_ROOT.parent.parent.parent)
                    offenders.append(f"{rel}:{line_no}: {stripped} ({reason})")

    assert not offenders, (
        "Found redundant landmark role declarations on native semantic elements:\n"
        + "\n".join(offenders)
    )
