"""Deployment branding profiles for template rendering."""

from __future__ import annotations

import os


def get_branding_context() -> dict[str, str | bool]:
    """Return template-safe branding values based on deployment profile.

    Set `GLOW_BRAND_PROFILE=uarizona` for the University of Arizona deployment.
    Any other value uses the default BITS/ACB presentation.
    """

    profile = os.environ.get("GLOW_BRAND_PROFILE", "bits").strip().lower()
    is_uarizona = profile in {"uarizona", "ua", "uofa", "university-of-arizona"}

    if is_uarizona:
        return {
            "brand_profile": "uarizona",
            "brand_is_uarizona": True,
            "brand_title_suffix": "GLOW Accessibility Toolkit",
            "brand_nav_label": "GLOW Accessibility",
            "brand_heading_label": "GLOW Accessibility Toolkit",
            "brand_whisperer_label": "Audio Whisperer",
            "brand_guidelines_name": "large-print accessibility guidelines",
            "brand_guidelines_summary": "large-print, WCAG, and APH guidance",
            "brand_about_heading": "About Large Print and Accessibility Guidelines",
            "brand_about_intro": "This toolkit applies large-print formatting and digital accessibility standards that support people with low vision and screen reader users.",
            "brand_footer_org_line": "A service provided by the University of Arizona Digital Accessibility team.",
            "brand_footer_story_line": "GLOW = Guided Layout & Output Workflow. Practical guidance for real-world accessibility work.",
            "brand_logo_file": "logo-uarizona.svg",
            "brand_logo_alt": "The University of Arizona",
            "brand_logo_height": "36",
            "brand_theme_class": "theme-uarizona",
            "brand_favicon": "favicon-uarizona.svg",
        }

    return {
        "brand_profile": "bits",
        "brand_is_uarizona": False,
        "brand_title_suffix": "GLOW (Guided Layout & Output Workflow)",
        "brand_nav_label": "GLOW Accessibility",
        "brand_heading_label": "GLOW Accessibility Toolkit",
        "brand_whisperer_label": "BITS Whisperer",
        "brand_guidelines_name": "ACB Large Print Guidelines",
        "brand_guidelines_summary": "ACB, WCAG, and APH submission guidance",
        "brand_about_heading": "About the ACB Large Print Guidelines",
        "brand_about_intro": "The American Council of the Blind (ACB) Large Print Guidelines specify formatting standards that make printed and digital documents readable for people with low vision.",
        "brand_footer_org_line": "A BITS community project. Blind Information Technology Solutions, a special interest affiliate of the American Council of the Blind.",
        "brand_footer_story_line": "GLOW = Guided Layout & Output Workflow. Magical guidance for real-world accessibility work.",
        "brand_logo_file": "logo-bits.png",
        "brand_logo_alt": "BITS – Blind Information Technology Solutions",
        "brand_logo_height": "44",
        "brand_theme_class": "theme-bits",
        "brand_favicon": "favicon.svg",
    }
