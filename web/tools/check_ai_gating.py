#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from pathlib import Path

T = Path("./src/acb_large_print_web/templates").resolve()

# Tokens that indicate a template is already guarded by AI feature checks
guard_tokens = [
    'ai_whisperer_enabled',
    'ai_chat_enabled',
    'ai_available',
    'ai_used',
    'ai_heading_fix_enabled',
    # also accept direct Jinja access to flags dict
    'flags.',
]


def scan_templates(root: Path):
    """Heuristically scan templates for AI UI links that lack nearby Jinja guards.

    The scanner looks for common markers (URL endpoints, visible labels) and
    then checks a surrounding context window for any of the guard tokens or
    an `{% if ai_... %}` Jinja guard.
    """
    issues = []
    patterns = [
        r"url_for\(\s*'whisperer\.",
        r"url_for\(\s*'chat\.",
        r"/whisperer",
        r"/chat",
        r"BITS Whisperer",
        r"Document Chat",
        r"\bwhisperer_form\.html\b",
    ]

    combined = re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)

    for p in sorted(root.rglob('*.html')):
        try:
            text = p.read_text(encoding='utf8')
        except Exception:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if combined.search(line):
                # Expand context window to ±8 lines for robustness
                start = max(0, i - 8)
                end = min(len(lines), i + 8)
                context = '\n'.join(lines[start:end])

                # If any guard token or explicit Jinja conditional appears nearby, consider it guarded
                jinja_guard = re.search(r"{%-?\s*if\s+(ai_\w+|flags\.|ai_features\.)", context)
                if any(tok in context for tok in guard_tokens) or jinja_guard:
                    continue

                issues.append((p.relative_to(root.parent), i + 1, line.strip(), '\n'.join(lines[start:end])))
    return issues


def main():
    issues = scan_templates(T)
    if not issues:
        print('No potential ungated AI links found in templates (heuristic).')
        return 0
    print('Potential ungated AI links (heuristic):')
    for f, ln, snippet, ctx in issues:
        print(f"\nFile: {f} Line: {ln}\n  {snippet}\n  Context:\n{ctx}\n")
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
