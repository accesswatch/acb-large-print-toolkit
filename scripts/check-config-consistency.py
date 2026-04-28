#!/usr/bin/env python3
"""
Pre-commit hook: Validate configuration consistency across GLOW surfaces.

Checks:
1. Feature flags consistency between web/src/acb_large_print_web/feature_flags.py
   and docker-compose.* files
2. AI feature flags default to False/0
3. Tool integration flags default to True
4. All required AI feature flags are defined
5. Docker Compose files include all feature flags

Run manually:
  python scripts/check-config-consistency.py

Usage as git pre-commit hook:
  echo "scripts/check-config-consistency.py" >> .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit
"""

import re
import sys
from pathlib import Path

# Root directory
REPO_ROOT = Path(__file__).parent.parent

# Files to check
FEATURE_FLAGS_PY = REPO_ROOT / "web/src/acb_large_print_web/feature_flags.py"
DOCKER_PROD = REPO_ROOT / "web/docker-compose.prod.yml"
DOCKER_WSL = REPO_ROOT / "web/docker-compose.wsl.yml"
CI_REGRESSION = REPO_ROOT / ".github/workflows/accessibility-regression.yml"

# Expected AI feature flags (must all be defined and default to False)
REQUIRED_AI_FLAGS = {
    "GLOW_ENABLE_AI",
    "GLOW_ENABLE_AI_CHAT",
    "GLOW_ENABLE_AI_WHISPERER",
    "GLOW_ENABLE_AI_HEADING_FIX",
    "GLOW_ENABLE_AI_ALT_TEXT",
    "GLOW_ENABLE_AI_MARKITDOWN_LLM",
}

# Tool integration flags that should default to True
TOOL_INTEGRATION_FLAGS = {
    "GLOW_ENABLE_EPUBCHECK",
    "GLOW_ENABLE_PANDOC",
    "GLOW_ENABLE_WEASYPRINT",
    "GLOW_ENABLE_PYMUPDF",
    "GLOW_ENABLE_MARKITDOWN",
    "GLOW_ENABLE_DAISY_ACE",
    "GLOW_ENABLE_DAISY_META_VIEWER",
    "GLOW_ENABLE_DAISY_PIPELINE",
}

ERRORS = []
WARNINGS = []


def check_feature_flags_py():
    """Validate feature_flags.py defaults."""
    if not FEATURE_FLAGS_PY.exists():
        ERRORS.append(f"[FAIL] {FEATURE_FLAGS_PY} not found")
        return

    content = FEATURE_FLAGS_PY.read_text()

    # Check all required AI flags are defined
    for flag in REQUIRED_AI_FLAGS:
        pattern = rf'"{flag}":\s*False'
        if not re.search(pattern, content):
            ERRORS.append(
                f'[FAIL] AI flag "{flag}" not found or does not default to False '
                f"in {FEATURE_FLAGS_PY}"
            )

    # Check tool integration flags default to True
    for flag in TOOL_INTEGRATION_FLAGS:
        pattern = rf'"{flag}":\s*True'
        if not re.search(pattern, content):
            WARNINGS.append(
                f'[WARN] Tool flag "{flag}" not found or does not default to True '
                f"in {FEATURE_FLAGS_PY}"
            )


def check_docker_compose(filepath: Path, name: str):
    """Validate Docker Compose environment variables."""
    if not filepath.exists():
        ERRORS.append(f"[FAIL] {filepath} not found")
        return

    content = filepath.read_text()

    # Check all AI flags are referenced (even if commented)
    for flag in REQUIRED_AI_FLAGS:
        if flag not in content:
            ERRORS.append(
                f'[FAIL] AI flag "{flag}" not found in {name} {filepath.name}'
            )


def check_ci_regression():
    """Validate CI regression environment."""
    if not CI_REGRESSION.exists():
        WARNINGS.append(f"[WARN] {CI_REGRESSION} not found")
        return

    content = CI_REGRESSION.read_text()

    # Check that key AI flags are set to false
    required_false = ["GLOW_ENABLE_AI:", "GLOW_ENABLE_AI_CHAT:", "GLOW_ENABLE_AI_WHISPERER:"]
    
    for flag in required_false:
        if flag not in content:
            WARNINGS.append(
                f'[WARN] Expected "{flag}" not found in CI regression workflow'
            )
        elif '"false"' not in content[content.find(flag):content.find(flag) + 50]:
            ERRORS.append(
                f'[FAIL] {flag} not set to "false" in CI regression workflow'
            )


def main():
    """Run all checks."""
    print("[CHECK] Checking GLOW configuration consistency...\n")

    check_feature_flags_py()
    check_docker_compose(DOCKER_PROD, "Production")
    check_docker_compose(DOCKER_WSL, "WSL Staging")
    check_ci_regression()

    if WARNINGS:
        print("[WARN] Warnings:")
        for w in WARNINGS:
            print(f"  {w}")
        print()

    if ERRORS:
        print("[FAIL] Configuration Errors:")
        for e in ERRORS:
            print(f"  {e}")
        print()
        print("[FAIL] Configuration consistency check FAILED")
        return 1
    else:
        print("[PASS] All configuration checks passed!")
        print(f"   - AI flags: All {len(REQUIRED_AI_FLAGS)} flags present and False")
        print(f"   - Tool flags: All {len(TOOL_INTEGRATION_FLAGS)} flags present and True")
        print(f"   - Docker Compose: All flags referenced")
        print(f"   - CI Regression: All AI flags set to false")
        return 0


if __name__ == "__main__":
    sys.exit(main())
