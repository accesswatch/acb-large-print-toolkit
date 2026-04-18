"""Customization warning detection and generation.

When users deviate from ACB Large Print Board of Publications defaults,
this module detects those deviations and provides appropriate messaging.
"""


def _getlist(form_data, key: str) -> list:
    """Return a list for *key* from either a Flask ImmutableMultiDict or a plain dict."""
    if hasattr(form_data, "getlist"):
        return form_data.getlist(key)
    val = form_data.get(key)
    if val is None:
        return []
    return val if isinstance(val, list) else [val]


def detect_audit_customizations(form_data) -> tuple[bool, list[str]]:
    """
    Detect if audit form deviates from ACB defaults.
    
    Returns (has_customizations, customization_reasons).
    """
    reasons = []
    
    # Check audit mode (default: full)
    mode = form_data.get("mode", "full")
    if mode != "full":
        if mode == "quick":
            reasons.append("Audit mode set to Quick (Critical/High findings only)")
        elif mode == "custom":
            reasons.append("Custom rule selection enabled")
    
    # Check standards profile (default: acb_2025)
    standards_profile = form_data.get("standards_profile", "acb_2025")
    if standards_profile != "acb_2025":
        reasons.append(f"Standards profile changed to {standards_profile}")
    
    # Check categories (default: acb, msac)
    categories = _getlist(form_data, "category") or ["acb", "msac"]
    if set(categories) != {"acb", "msac"}:
        reasons.append(f"Audit categories changed to: {', '.join(sorted(categories))}")
    
    # Check suppressed rules
    suppressed = []
    if form_data.get("suppress_link_text") == "on":
        suppressed.append("link text")
    if form_data.get("suppress_missing_alt_text") == "on":
        suppressed.append("missing alt text")
    if form_data.get("suppress_faux_heading") == "on":
        suppressed.append("faux heading")
    
    if suppressed:
        reasons.append(f"Rule suppressions enabled for: {', '.join(suppressed)}")
    
    return len(reasons) > 0, reasons


def detect_fix_customizations(form_data) -> tuple[bool, list[str]]:
    """
    Detect if fix form deviates from ACB defaults.
    
    Returns (has_customizations, customization_reasons).
    """
    reasons = []
    
    # Check fix mode (default: full)
    mode = form_data.get("mode", "full")
    if mode != "full":
        if mode == "essentials":
            reasons.append("Fix mode set to Essentials (Critical/High only)")
        elif mode == "custom":
            reasons.append("Custom rule selection enabled")
    
    # Check standards profile (default: acb_2025)
    standards_profile = form_data.get("standards_profile", "acb_2025")
    if standards_profile != "acb_2025":
        reasons.append(f"Standards profile changed to {standards_profile}")
    
    # Check categories (default: acb, msac)
    categories = _getlist(form_data, "category") or ["acb", "msac"]
    if set(categories) != {"acb", "msac"}:
        reasons.append(f"Audit categories changed to: {', '.join(sorted(categories))}")
    
    # Check typography customizations
    customizations = []
    
    try:
        bound = form_data.get("bound") == "on"
        if bound:
            customizations.append("Bound document mode")
    except (ValueError, TypeError):
        pass
    
    try:
        list_indent = float(form_data.get("list_indent_in", "0.5"))
        if list_indent != 0.5:
            customizations.append(f"List indent changed to {list_indent}\"")
    except (ValueError, TypeError):
        pass
    
    try:
        para_indent = float(form_data.get("para_indent_in", "0.0"))
        if para_indent != 0.0:
            customizations.append(f"Paragraph indent changed to {para_indent}\"")
    except (ValueError, TypeError):
        pass
    
    try:
        first_line_indent = float(form_data.get("first_line_indent_in", "0.0"))
        if first_line_indent != 0.0:
            customizations.append(f"First-line indent changed to {first_line_indent}\"")
    except (ValueError, TypeError):
        pass
    
    if form_data.get("preserve_heading_alignment") == "on":
        customizations.append("Heading alignment preservation enabled")
    
    if form_data.get("detect_headings") == "on":
        heading_accuracy = form_data.get("heading_accuracy", "balanced")
        if heading_accuracy != "balanced":
            customizations.append(f"Heading detection enabled ({heading_accuracy} accuracy)")
        else:
            customizations.append("Heading detection enabled")
    
    # Check suppressed rules
    suppressed = []
    if form_data.get("suppress_link_text") == "on":
        suppressed.append("link text")
    if form_data.get("suppress_missing_alt_text") == "on":
        suppressed.append("missing alt text")
    if form_data.get("suppress_faux_heading") == "on":
        suppressed.append("faux heading")
    
    if suppressed:
        customizations.append(f"Rule suppressions for: {', '.join(suppressed)}")
    
    if customizations:
        reasons.append("Document formatting customizations: " + "; ".join(customizations))
    
    return len(reasons) > 0, reasons


def generate_customization_warning(customization_reasons: list[str]) -> str:
    """Generate a warning message from customization reasons."""
    if not customization_reasons:
        return ""
    
    items = "\n".join(f"• {reason}" for reason in customization_reasons)
    
    warning = f"""For Your Information: Custom Settings Applied

This audit or fix was run with settings that differ from the 
American Council of the Blind Large Print Guidelines (Board of Publications specification). 
Your customizations may result in output that does not fully align with the standard ACB compliance criteria:

{items}

The ACB Large Print Guidelines define specific requirements for 
typography, spacing, emphasis styles, heading hierarchy, and other 
accessibility features optimized for individuals with low vision. 
When these defaults are modified, the resulting document may not 
conform to the ACB specification. This does not invalidate the fixes 
applied—only that the output may appear or behave differently from 
the standard ACB recommendation.

For more information about how your custom settings affect ACB 
conformance, visit the Guidelines section of this site."""

    return warning
