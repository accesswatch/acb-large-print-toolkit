"""Persistent tool-usage counters backed by SQLAlchemy.

Each call to ``record(tool)`` atomically increments the counter for that tool
and updates a ``last_used_at`` timestamp. Uses the main application database.

Tools tracked:
    audit       -- document audit (single or batch)
    fix         -- document fix
    convert     -- document conversion
    template    -- template builder
    whisperer   -- audio transcription (BITS Whisperer)
    chat        -- document chat
    speech      -- Speech Studio usage (preview/download/prepare)
    anthem_download -- Let it GLOW anthem downloads
"""

from __future__ import annotations

from datetime import UTC, datetime

from .db import db
from .models import ToolUsage, ToolUsageDetail


# Human-friendly display labels for each tool key
TOOL_LABELS: dict[str, str] = {
    "audit":     "Audit",
    "fix":       "Fix",
    "convert":   "Convert",
    "template":  "Template Builder",
    "whisperer": "BITS Whisperer",
    "chat":      "Document Chat",
    "speech":    "Speech Studio",
    "anthem_download": "Let it GLOW Download",
}


def _get_or_create_tool(tool: str) -> ToolUsage:
    """Get or create a ToolUsage record."""
    record = db.session.execute(
        db.select(ToolUsage).where(ToolUsage.tool == tool)
    ).scalar_one_or_none()
    if record is None:
        record = ToolUsage(tool=tool, count=0)
        db.session.add(record)
        db.session.flush()
    return record


def record(tool: str, detail: str | None = None) -> None:
    """Increment the counter for *tool*.  Silently swallows errors."""
    try:
        now = datetime.now(UTC)
        tool_record = _get_or_create_tool(tool)
        tool_record.count += 1
        tool_record.last_used_at = now
        
        if detail:
            detail_record = db.session.execute(
                db.select(ToolUsageDetail).where(
                    ToolUsageDetail.tool_id == tool_record.id,
                    ToolUsageDetail.detail_key == "detail",
                    ToolUsageDetail.detail_value == str(detail),
                )
            ).scalar_one_or_none()
            if detail_record is None:
                detail_record = ToolUsageDetail(
                    tool_id=tool_record.id,
                    detail_key="detail",
                    detail_value=str(detail),
                    count=1,
                    last_used_at=now,
                )
                db.session.add(detail_record)
            else:
                detail_record.count += 1
                detail_record.last_used_at = now
        
        db.session.commit()
    except Exception:
        db.session.rollback()


def record_details(tool: str, details: dict[str, object]) -> None:
    """Increment base tool usage and one or more detail dimensions.

    Example details: {"mode": "typed_preview", "voice": "kokoro:af_bella"}
    """
    try:
        now = datetime.now(UTC)
        tool_record = _get_or_create_tool(tool)
        tool_record.count += 1
        tool_record.last_used_at = now
        
        for k, v in (details or {}).items():
            if v is None:
                continue
            key = str(k).strip()
            val = str(v).strip()
            if not key or not val:
                continue
            
            detail_record = db.session.execute(
                db.select(ToolUsageDetail).where(
                    ToolUsageDetail.tool_id == tool_record.id,
                    ToolUsageDetail.detail_key == key,
                    ToolUsageDetail.detail_value == val,
                )
            ).scalar_one_or_none()
            if detail_record is None:
                detail_record = ToolUsageDetail(
                    tool_id=tool_record.id,
                    detail_key=key,
                    detail_value=val,
                    count=1,
                    last_used_at=now,
                )
                db.session.add(detail_record)
            else:
                detail_record.count += 1
                detail_record.last_used_at = now
        
        db.session.commit()
    except Exception:
        db.session.rollback()


def get_all() -> list[dict]:
    """Return all counters as a list of dicts sorted by count descending.

    Each dict has keys: ``tool``, ``label``, ``count``, ``last_used_at``.
    Tools that have never been used are included with count 0.
    """
    try:
        records = db.session.execute(
            db.select(ToolUsage)
        ).scalars().all()
        rows = {r.tool: {"count": r.count, "last_used_at": r.last_used_at} for r in records}
    except Exception:
        rows = {}

    result = []
    for tool, label in TOOL_LABELS.items():
        data = rows.get(tool, {})
        result.append(
            {
                "tool": tool,
                "label": label,
                "count": data.get("count", 0),
                "last_used_at": data.get("last_used_at"),
            }
        )
    return sorted(result, key=lambda r: r["count"], reverse=True)


def get_total() -> int:
    """Return the sum of all tool use counts."""
    return sum(r["count"] for r in get_all())


def get_detail_counts(tool: str, detail_key: str, limit: int = 10) -> list[dict]:
    """Return detail-level usage counts for one tool and key.

    Each item has: detail_value, count, last_used_at.
    """
    try:
        rows = db.session.execute(
            db.select(ToolUsageDetail.detail_value, ToolUsageDetail.count, ToolUsageDetail.last_used_at)
            .join(ToolUsage, ToolUsage.id == ToolUsageDetail.tool_id)
            .where(
                ToolUsage.tool == tool,
                ToolUsageDetail.detail_key == detail_key,
            )
            .order_by(ToolUsageDetail.count.desc(), ToolUsageDetail.detail_value.asc())
            .limit(int(limit))
        ).all()
        return [
            {
                "detail_value": r[0],
                "count": r[1],
                "last_used_at": r[2],
            }
            for r in rows
        ]
    except Exception:
        return []
