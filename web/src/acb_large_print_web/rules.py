"""Helper to expose rule metadata to Jinja2 templates."""

from __future__ import annotations

from acb_large_print.constants import AUDIT_RULES, Severity


def get_rules_by_severity() -> dict[str, list[dict]]:
    """Return AUDIT_RULES grouped by severity for template rendering.

    Returns a dict keyed by severity label ("Critical", "High", "Medium",
    "Low"), each containing a list of rule dicts with keys:
    rule_id, description, severity, acb_reference, auto_fixable.
    """
    groups: dict[str, list[dict]] = {
        "Critical": [],
        "High": [],
        "Medium": [],
        "Low": [],
    }
    for rule in AUDIT_RULES.values():
        groups[rule.severity.value].append({
            "rule_id": rule.rule_id,
            "description": rule.description,
            "severity": rule.severity.value,
            "acb_reference": rule.acb_reference,
            "auto_fixable": rule.auto_fixable,
        })
    return groups


def get_all_rule_ids() -> set[str]:
    """Return set of all rule IDs."""
    return set(AUDIT_RULES.keys())


def get_rule_ids_by_severity(*severities: str) -> set[str]:
    """Return rule IDs matching the given severity labels."""
    sev_set = set(severities)
    return {
        r.rule_id
        for r in AUDIT_RULES.values()
        if r.severity.value in sev_set
    }


def filter_findings(findings: list, rule_ids: set[str]) -> list:
    """Filter a findings list to include only the given rule IDs."""
    return [f for f in findings if f.rule_id in rule_ids]
