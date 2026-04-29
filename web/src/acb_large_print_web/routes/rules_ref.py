"""Rules Reference route -- deep-dive rule browser."""
from __future__ import annotations

from flask import Blueprint, render_template, request

from acb_large_print.constants import AUDIT_RULES
from acb_large_print_web.rules import (
    _APH_PROFILE_RULE_IDS,
    PROFILE_ACB_2025,
    PROFILE_APH_SUBMISSION,
    PROFILE_COMBINED_STRICT,
    PROFILE_LABELS,
    _rule_to_dict,
)
from acb_large_print_web.rule_reference_metadata import RULE_EXTENDED_METADATA

rules_ref_bp = Blueprint("rules_ref", __name__)

# Format display labels
_FORMAT_LABELS: dict[str, str] = {
    "docx": "Word",
    "xlsx": "Excel",
    "pptx": "PowerPoint",
    "md": "Markdown",
    "pdf": "PDF",
    "epub": "ePub",
}

# Severity sort order (lower = higher priority)
_SEV_ORDER: dict[str, int] = {
    "Critical": 0,
    "High": 1,
    "Medium": 2,
    "Low": 3,
}

# ACB 2025 profile = all ACB-* and MSAC-* rules for DOCX
# Combined strict = union of all three profiles
_ACB_2025_RULE_IDS: set[str] = {
    r.rule_id
    for r in AUDIT_RULES.values()
    if any(f.value == "docx" for f in r.formats)
}
_COMBINED_STRICT_RULE_IDS: set[str] = (
    _ACB_2025_RULE_IDS | _APH_PROFILE_RULE_IDS
)


def _build_rule_list() -> list[dict]:
    """Return all rules with extended metadata and profile membership."""
    rules = []
    for rule in AUDIT_RULES.values():
        d = _rule_to_dict(rule)
        meta = RULE_EXTENDED_METADATA.get(rule.rule_id, {})
        d["full_description"] = meta.get("full_description", "")
        d["suppress_guidance"] = meta.get("suppress_guidance", "")
        d["profiles"] = []
        if rule.rule_id in _APH_PROFILE_RULE_IDS:
            d["profiles"].append(PROFILE_APH_SUBMISSION)
        if rule.rule_id in _ACB_2025_RULE_IDS:
            d["profiles"].append(PROFILE_ACB_2025)
        if rule.rule_id in _COMBINED_STRICT_RULE_IDS:
            d["profiles"].append(PROFILE_COMBINED_STRICT)
        d["format_labels"] = [_FORMAT_LABELS.get(f, f) for f in d["formats"]]
        rules.append(d)
    # Sort: severity first, then rule_id
    rules.sort(key=lambda r: (_SEV_ORDER.get(r["severity"], 99), r["rule_id"]))
    return rules


@rules_ref_bp.route("/", methods=["GET"])
def rules_ref_page():
    rules = _build_rule_list()
    default_target = request.args.get("target", "audit")
    if default_target not in {"audit", "fix"}:
        default_target = "audit"

    # Collect unique filter values
    all_formats = sorted({f for r in rules for f in r["formats"]})
    all_severities = ["Critical", "High", "Medium", "Low"]
    all_categories = sorted({r["category"] for r in rules})
    all_profiles = [
        PROFILE_APH_SUBMISSION,
        PROFILE_ACB_2025,
        PROFILE_COMBINED_STRICT,
    ]

    return render_template(
        "rules_ref.html",
        rules=rules,
        all_formats=all_formats,
        format_labels=_FORMAT_LABELS,
        all_severities=all_severities,
        all_categories=all_categories,
        all_profiles=all_profiles,
        profile_labels=PROFILE_LABELS,
        total_rules=len(rules),
        default_target=default_target,
    )
