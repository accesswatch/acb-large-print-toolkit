#!/usr/bin/env python3
"""
Comprehensive pre-commit quality gate for GLOW v2.5.0+ release cadence.

Checks:
1. Configuration consistency across surfaces
2. CHANGELOG.md has [Unreleased] section for significant changes
3. Feature flags are documented
4. Documentation is properly built from markdown
5. Prose quality (Vale - optional)
6. Python imports organized (isort - optional)

Usage:
  python scripts/pre-commit-check.py
  
Or from git pre-commit hook:
  echo "python scripts/pre-commit-check.py" >> .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit
"""

import subprocess
import sys
import re
import io
from pathlib import Path

# Force UTF-8 output encoding for Windows compatibility
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).parent.parent
ERRORS = []
WARNINGS = []

def run_check(name: str, func) -> bool:
    """Run a check and report results."""
    try:
        print(f"\n{'=' * 70}")
        print(f"[CHECK] {name}")
        print('=' * 70)
        result = func()
        if result:
            print(f"[PASS] {name} passed")
        else:
            print(f"[FAIL] {name} failed")
            ERRORS.append(name)
        return result
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        ERRORS.append(f"{name} (error: {e})")
        return False


def check_version_consistency():
    """0. Version consistency check (release-blocking)."""
    try:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts/check-version-consistency.py")],
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running version check: {e}")
        return False


def check_config_consistency():
    """1. Configuration consistency check."""
    try:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts/check-config-consistency.py")],
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running config check: {e}")
        return False


def check_changelog():
    """2. Verify CHANGELOG.md is updated."""
    changelog = REPO_ROOT / "CHANGELOG.md"
    if not changelog.exists():
        print("[FAIL] CHANGELOG.md not found")
        return False
    
    content = changelog.read_text()
    if "## [Unreleased]" in content:
        print("[INFO] CHANGELOG.md has [Unreleased] section")
        return True
    else:
        print("[WARN] CHANGELOG.md missing [Unreleased] section")
        print("   (Only required if making significant changes)")
        return True  # Warning, not blocking


def check_feature_flags_documented():
    """3. Check new feature flags are documented."""
    try:
        # Get git diff of staged changes
        result = subprocess.run(
            ["git", "diff", "--cached", "-U0"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        
        # Find new GLOW_ENABLE_* flags
        new_flags = set(re.findall(r'GLOW_ENABLE_[A-Z_]+', result.stdout))
        
        if not new_flags:
            print("[INFO] No new feature flags detected")
            return True
        
        feature_flags_doc = REPO_ROOT / "docs/feature-flags.md"
        if not feature_flags_doc.exists():
            print("[WARN] docs/feature-flags.md not found")
            return True
        
        doc_content = feature_flags_doc.read_text()
        undocumented = []
        
        for flag in new_flags:
            if flag not in doc_content:
                undocumented.append(flag)
        
        if undocumented:
            print(f"[WARN] Undocumented flags: {', '.join(undocumented)}")
            print("   Please add to docs/feature-flags.md")
            return False
        else:
            print(f"[INFO] All {len(new_flags)} new flags documented")
            return True
    except Exception as e:
        print(f"[WARN] Could not check feature flags: {e}")
        return True  # Non-blocking


def build_documentation():
    """4. Rebuild HTML partials from markdown."""
    try:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts/build-doc-pages.py")],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("[PASS] Documentation built successfully")
            # Stage generated files
            subprocess.run(
                [
                    "git",
                    "add",
                    "web/src/acb_large_print_web/templates/partials/guide_body.html",
                    "web/src/acb_large_print_web/templates/partials/changelog_body.html",
                    "web/src/acb_large_print_web/templates/partials/prd_body.html",
                    "web/src/acb_large_print_web/templates/partials/faq_body.html",
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
            )
            return True
        else:
            print(f"[FAIL] Documentation build failed:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"[WARN] Could not build documentation: {e}")
        return True  # Non-blocking


def check_prose_quality():
    """5. Prose quality check with Vale (optional)."""
    try:
        # Check if Vale is available
        result = subprocess.run(
            ["vale", "--version"],
            capture_output=True,
        )
        if result.returncode != 0:
            print("[INFO] Vale not installed (prose check skipped)")
            print("   Install Vale for prose linting: https://vale.sh/")
            return True
        
        # Get modified markdown files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        
        md_files = [f for f in result.stdout.split("\n") if f.endswith((".md", ".markdown"))]
        
        if not md_files:
            print("[INFO] No markdown changes detected")
            return True
        
        print(f"[CHECK] Linting: {', '.join(md_files)}")
        result = subprocess.run(
            ["vale"] + md_files,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            print("[PASS] Prose quality check passed")
            return True
        else:
            print(f"[WARN] Prose quality warnings (non-blocking):\n{result.stdout}")
            return True  # Warning, not blocking
    except Exception as e:
        print(f"[INFO] Could not run prose check: {e}")
        return True  # Non-blocking


def check_python_imports():
    """6. Python import organization (optional)."""
    try:
        # Check if isort is available
        result = subprocess.run(
            [sys.executable, "-m", "isort", "--version"],
            capture_output=True,
        )
        if result.returncode != 0:
            print("[INFO] isort not installed (import check skipped)")
            return True
        
        # Get modified Python files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        
        py_files = [f for f in result.stdout.split("\n") if f.endswith(".py")]
        
        if not py_files:
            print("[INFO] No Python changes detected")
            return True
        
        # Check imports
        result = subprocess.run(
            [sys.executable, "-m", "isort", "--check-only"] + py_files,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            print(f"[PASS] Python imports properly organized ({len(py_files)} files)")
            return True
        else:
            print("[WARN] Python import order issues (auto-fixing):")
            subprocess.run(
                [sys.executable, "-m", "isort"] + py_files,
                cwd=str(REPO_ROOT),
                capture_output=True,
            )
            subprocess.run(
                ["git", "add"] + py_files,
                cwd=str(REPO_ROOT),
                capture_output=True,
            )
            print("  Fixed and staged")
            return True  # Auto-fixed, non-blocking
    except Exception as e:
        print(f"[INFO] Could not check imports: {e}")
        return True  # Non-blocking


def main():
    """Run all pre-commit checks."""
    print("\n" + "=" * 70)
    print("[GLOW] Pre-Commit Quality Gate (v2.5.0+)")
    print("=" * 70)
    
    checks = [
        ("Version Consistency", check_version_consistency),
        ("Configuration Consistency", check_config_consistency),
        ("CHANGELOG.md Verification", check_changelog),
        ("Feature Flags Documentation", check_feature_flags_documented),
        ("Documentation Build", build_documentation),
        ("Prose Quality (Vale)", check_prose_quality),
        ("Python Imports (isort)", check_python_imports),
    ]
    
    for name, check_func in checks:
        run_check(name, check_func)
    
    # Final result
    print("\n" + "=" * 70)
    if ERRORS:
        print(f"[FAIL] {len(ERRORS)} check(s) failed:")
        for error in ERRORS:
            print(f"   - {error}")
        print("\nPlease fix the issues above and stage changes, then try again.")
        print("To bypass: git commit --no-verify")
        return 1
    else:
        print("[PASS] All pre-commit checks passed!")
        print("   Commit is ready with high quality standards")
        print("   Release cadence maintained")
        return 0


if __name__ == "__main__":
    sys.exit(main())
