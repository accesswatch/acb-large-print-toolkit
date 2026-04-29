#!/usr/bin/env python3
"""
Run both the desktop and web test suites from their respective project
directories so that each suite's pyproject.toml config and installed packages
are resolved correctly.

Each suite is run as a subprocess using the *current* Python interpreter to
ensure the active venv is used.  Exit code is the logical OR of both suite
return codes (non-zero if either fails).
"""
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

# (label, directory, extra pytest args)
SUITES = [
    ("desktop", REPO_ROOT / "desktop", ["-m", "not ollama and not stress"]),
    ("web",     REPO_ROOT / "web",     []),
]


def run_suite(label: str, cwd: Path, extra_args: list[str]) -> int:
    print(f"\n{'='*60}")
    print(f"  Running {label} tests in {cwd}")
    print(f"{'='*60}\n")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short"] + extra_args,
        cwd=cwd,
    )
    return result.returncode


def main() -> int:
    overall = 0
    for label, cwd, extra in SUITES:
        rc = run_suite(label, cwd, extra)
        if rc != 0:
            print(f"\n[FAIL] {label} tests exited with code {rc}")
            overall = rc
        else:
            print(f"\n[PASS] {label} tests passed")
    print(f"\nPYTEST_RETURN_CODE: {overall}")
    return overall


if __name__ == "__main__":
    sys.exit(main())
