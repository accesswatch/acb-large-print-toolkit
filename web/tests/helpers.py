from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def pretty_flag_label(name: str) -> str:
    """Return a human-friendly label for a flag name.

    Example: 'GLOW_ENABLE_AI_CHAT' -> 'Ai Chat'
    """
    if name.startswith("GLOW_ENABLE_"):
        short = name[len("GLOW_ENABLE_"):]
    else:
        short = name
    return short.replace("_", " ").title()


def assert_flag_rendered(html: str, flag_name: str) -> None:
    """Assert that an admin flag appears in the rendered admin HTML with
    an accessible `id` and a readable label element association.
    """
    # Expect an input id like `flag-GLOW_ENABLE_AI`
    input_id = f"flag-{flag_name}"
    if input_id not in html:
        raise AssertionError(f"Expected flag input id '{input_id}' in admin HTML")

    # Expect a <label for="flag-..."> to associate a readable label with the input
    label_for = f'for="{input_id}"'
    if label_for not in html:
        raise AssertionError(f"Expected label element with for='{input_id}' to appear for {flag_name}")


def parse_iso_ts(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        # datetime.fromisoformat accepts the format produced by datetime.isoformat
        dt = datetime.fromisoformat(ts)
        # If naive assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None
