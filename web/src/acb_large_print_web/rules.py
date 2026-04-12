"""Helper to expose rule metadata to Jinja2 templates."""

from __future__ import annotations

from acb_large_print.constants import (
    ACB_RULE_IDS,
    AUDIT_RULES,
    DocFormat,
    MSAC_RULE_IDS,
    RuleCategory,
    Severity,
)


def get_rules_by_severity() -> dict[str, list[dict]]:
    """Return AUDIT_RULES grouped by severity for template rendering.

    Returns a dict keyed by severity label ("Critical", "High", "Medium",
    "Low"), each containing a list of rule dicts with keys:
    rule_id, description, severity, acb_reference, category, auto_fixable.
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
            "category": rule.category.value,
            "auto_fixable": rule.auto_fixable,
            "formats": sorted(f.value for f in rule.formats),
        })
    return groups


def get_rules_by_category() -> dict[str, list[dict]]:
    """Return AUDIT_RULES grouped by category for template rendering.

    Returns a dict keyed by category value ("acb", "msac"), each
    containing a list of rule dicts.
    """
    groups: dict[str, list[dict]] = {"acb": [], "msac": []}
    for rule in AUDIT_RULES.values():
        groups[rule.category.value].append({
            "rule_id": rule.rule_id,
            "description": rule.description,
            "severity": rule.severity.value,
            "acb_reference": rule.acb_reference,
            "category": rule.category.value,
            "auto_fixable": rule.auto_fixable,
            "formats": sorted(f.value for f in rule.formats),
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


def get_rule_ids_by_category(*categories: str) -> set[str]:
    """Return rule IDs matching the given category values ('acb', 'msac')."""
    cat_set = set(categories)
    return {
        r.rule_id
        for r in AUDIT_RULES.values()
        if r.category.value in cat_set
    }


def get_rule_ids_by_format(fmt_str: str) -> set[str]:
    """Return rule IDs applicable to a document format ('docx', 'xlsx', 'pptx')."""
    try:
        fmt = DocFormat(fmt_str)
    except ValueError:
        return set(AUDIT_RULES.keys())  # unknown format: return all
    return {
        r.rule_id
        for r in AUDIT_RULES.values()
        if fmt in r.formats
    }


def filter_findings(findings: list, rule_ids: set[str]) -> list:
    """Filter a findings list to include only the given rule IDs."""
    return [f for f in findings if f.rule_id in rule_ids]
