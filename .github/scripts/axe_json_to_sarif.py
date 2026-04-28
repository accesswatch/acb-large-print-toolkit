#!/usr/bin/env python3
"""Convert axe-core CLI JSON output to SARIF 2.1.0.

This keeps accessibility-regression workflow compatible with @axe-core/cli
versions that support JSON output but not a native SARIF reporter.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SARIF_VERSION = "2.1.0"
TOOL_NAME = "axe-core"
TOOL_URI = "https://github.com/dequelabs/axe-core-npm"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _result_level(impact: str | None) -> str:
    impact = (impact or "").lower()
    if impact in {"critical", "serious"}:
        return "error"
    if impact in {"moderate", "minor"}:
        return "warning"
    return "note"


def _node_locations(page_url: str, node: dict[str, Any]) -> list[dict[str, Any]]:
    # SARIF locations are file-oriented, but for web scans we can still use
    # URL artifact locations and include CSS selector in the message.
    return [
        {
            "physicalLocation": {
                "artifactLocation": {"uri": page_url},
            }
        }
    ]


def axe_to_sarif(axe_report: Any) -> dict[str, Any]:
    # axe CLI may emit a single result object or a list of per-url objects.
    runs_input = axe_report if isinstance(axe_report, list) else [axe_report]

    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []

    for page in runs_input:
        page_url = page.get("url", "unknown-url")
        for violation in page.get("violations", []):
            rule_id = violation.get("id", "axe-unknown")
            help_text = violation.get("help", "Accessibility issue")
            help_url = violation.get("helpUrl", TOOL_URI)
            impact = violation.get("impact")
            tags = violation.get("tags", [])

            if rule_id not in rules:
                rules[rule_id] = {
                    "id": rule_id,
                    "name": rule_id,
                    "shortDescription": {"text": help_text},
                    "helpUri": help_url,
                    "properties": {
                        "tags": tags,
                        "impact": impact,
                    },
                }

            for node in violation.get("nodes", []):
                selector = " > ".join(node.get("target", [])) or "unknown selector"
                failure_summary = node.get("failureSummary", "No failure summary provided")
                message = f"{help_text} at {selector}. {failure_summary}"
                results.append(
                    {
                        "ruleId": rule_id,
                        "level": _result_level(impact),
                        "message": {"text": message},
                        "locations": _node_locations(page_url, node),
                    }
                )

    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": TOOL_NAME,
                        "informationUri": TOOL_URI,
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: axe_json_to_sarif.py <axe-json-path> <sarif-output-path>")
        return 2

    axe_json_path = Path(sys.argv[1])
    sarif_path = Path(sys.argv[2])

    if not axe_json_path.exists():
        print(f"Input file not found: {axe_json_path}")
        return 2

    axe_report = _load_json(axe_json_path)
    sarif = axe_to_sarif(axe_report)

    sarif_path.parent.mkdir(parents=True, exist_ok=True)
    with sarif_path.open("w", encoding="utf-8") as f:
        json.dump(sarif, f, indent=2)

    print(f"Wrote SARIF: {sarif_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
