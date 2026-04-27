#!/usr/bin/env python3
"""Sweep repository tests for potential unguarded AI usages.

Writes a report to `web/tools/ungarded_ai_tests.txt` listing test files
that reference AI endpoints or helpers but lack AI markers or guards.

This is a read-only reporter (does not modify tests).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "ungarded_ai_tests.txt"

PATTERNS = [
    r"openrouter",
    r"whisperer",
    r"ai_gateway",
    r"OPENROUTER_API_KEY",
    r"ai_chat_enabled",
    r"ai_whisperer_enabled",
    r"/whisperer",
    r"/chat",
]

MARKER_REGEX = re.compile(r"pytest\.mark\.(ai_live|ai_whisper)|@pytest\.mark\.(ai_live|ai_whisper)|pytestmark\s*=\s*\[.*?ai_live|ai_whisper", re.S)


def scan_file(p: Path) -> List[str]:
    try:
        text = p.read_text(encoding="utf8")
    except Exception:
        return []
    lower = text.lower()
    found = any(re.search(pat, lower) for pat in PATTERNS)
    if not found:
        return []
    # If file contains explicit markers/guards, consider it OK
    if MARKER_REGEX.search(text) or "ai_whisper" in text or "ai_live" in text:
        return []

    # Otherwise collect snippets with matches
    lines = text.splitlines()
    snippets = []
    for i, line in enumerate(lines, start=1):
        for pat in PATTERNS:
            if re.search(pat, line, re.I):
                start = max(1, i - 3)
                end = min(len(lines), i + 3)
                ctx = "\n".join(lines[start - 1:end])
                snippets.append(f"Line {i}: {line.strip()}\nContext:\n{ctx}\n---")
                break
    return snippets


def main() -> int:
    tests = list(ROOT.rglob("tests/**/*.py")) + list(ROOT.rglob("**/tests/**/*.py"))
    tests = sorted(set(tests))
    report_lines: List[str] = []
    for t in tests:
        snippets = scan_file(t)
        if snippets:
            report_lines.append(f"FILE: {t.relative_to(ROOT)}\n")
            report_lines.extend(snippets)
            report_lines.append("\n")

    if not report_lines:
        print("No unguarded AI test usages detected.")
        if OUT.exists():
            OUT.unlink()
        return 0

    OUT.write_text("\n".join(report_lines), encoding="utf8")
    print(f"Wrote report: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())