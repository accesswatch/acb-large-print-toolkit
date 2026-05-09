#!/usr/bin/env python3
"""Backfill/sync GLOW feedback entries into GitHub issues.

This script reads rows from instance/feedback.db and creates issues in a target
GitHub repository for entries that are not already synced.

Usage examples:
  python scripts/sync-feedback-to-github.py
  python scripts/sync-feedback-to-github.py --db s:/code/glow/instance/feedback.db --repo Community-Access/glow --assignee accesswatch

Environment variables:
  FEEDBACK_GITHUB_TOKEN    Required unless --token is supplied
  FEEDBACK_GITHUB_REPO     Default repository (default: Community-Access/glow)
  FEEDBACK_GITHUB_ASSIGNEE Default assignee (default: accesswatch)
  FEEDBACK_GITHUB_LABELS   Comma-separated labels (default: feedback,user-feedback)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib import error as urlerror
from urllib import request as urlrequest


@dataclass
class SyncConfig:
    token: str
    repo: str
    assignee: str
    labels: list[str]


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS feedback ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  timestamp TEXT NOT NULL,"
        "  name TEXT,"
        "  email TEXT,"
        "  rating TEXT NOT NULL,"
        "  task TEXT,"
        "  message TEXT NOT NULL,"
        "  github_issue_number INTEGER,"
        "  github_issue_url TEXT,"
        "  github_sync_status TEXT,"
        "  github_sync_error TEXT,"
        "  github_synced_at TEXT"
        ")"
    )
    cols = {r[1] for r in conn.execute("PRAGMA table_info(feedback)").fetchall()}
    required = {
        "name": "TEXT",
        "email": "TEXT",
        "github_issue_number": "INTEGER",
        "github_issue_url": "TEXT",
        "github_sync_status": "TEXT",
        "github_sync_error": "TEXT",
        "github_synced_at": "TEXT",
    }
    for col, col_type in required.items():
        if col not in cols:
            conn.execute(f"ALTER TABLE feedback ADD COLUMN {col} {col_type}")
    conn.commit()


def create_issue(cfg: SyncConfig, row: sqlite3.Row) -> tuple[Optional[int], Optional[str], Optional[str]]:
    title = f"[Feedback] {row['rating'].capitalize()} | {row['task'] or 'general'} | {row['timestamp'][:10]}"
    
    body_parts = [
        "## User Feedback Submission\n",
        f"- Feedback ID: `{row['id']}`\n",
        f"- Submitted at (UTC): `{row['timestamp']}`\n",
        f"- Rating: `{row['rating']}`\n",
        f"- Task: `{row['task'] or 'not specified'}`\n",
    ]
    
    if row.get("name") or row.get("email"):
        body_parts.append("- **Contributor contact:**\n")
        if row.get("name"):
            body_parts.append(f"  - Name: {row['name']}\n")
        if row.get("email"):
            body_parts.append(f"  - Email: {row['email']}\n")
    
    body_parts.extend([
        "\n### Message\n",
        f"{row['message']}\n",
        "\n---\n",
        "Source: GLOW web feedback form backfill sync.",
    ])
    
    body = "".join(body_parts)
    
    payload = {
        "title": title,
        "body": body,
        "labels": cfg.labels,
    }
    if cfg.assignee:
        payload["assignees"] = [cfg.assignee]

    req = urlrequest.Request(
        f"https://api.github.com/repos/{cfg.repo}/issues",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {cfg.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "glow-feedback-backfill",
        },
    )
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("number"), data.get("html_url"), None
    except urlerror.HTTPError as exc:
        try:
            details = exc.read().decode("utf-8")
        except Exception:
            details = str(exc)
        return None, None, f"HTTP {exc.code}: {details}"
    except Exception as exc:  # noqa: BLE001
        return None, None, str(exc)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync feedback.db rows into GitHub issues")
    parser.add_argument("--db", default="s:/code/glow/instance/feedback.db", help="Path to feedback.db")
    parser.add_argument("--repo", default="Community-Access/glow", help="Target owner/repo")
    parser.add_argument("--assignee", default="accesswatch", help="GitHub assignee username")
    parser.add_argument("--labels", default="feedback,user-feedback", help="Comma-separated labels")
    parser.add_argument("--token", default="", help="GitHub token (overrides FEEDBACK_GITHUB_TOKEN)")
    parser.add_argument("--limit", type=int, default=0, help="Max rows to sync (0 = all)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = args.token.strip() or __import__("os").environ.get("FEEDBACK_GITHUB_TOKEN", "").strip()
    if not token:
        print("ERROR: GitHub token missing. Set FEEDBACK_GITHUB_TOKEN or use --token")
        return 2

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    labels = [x.strip() for x in args.labels.split(",") if x.strip()]
    cfg = SyncConfig(token=token, repo=args.repo.strip(), assignee=args.assignee.strip(), labels=labels)

    limit_clause = ""
    params: tuple = ()
    if args.limit and args.limit > 0:
        limit_clause = " LIMIT ?"
        params = (args.limit,)

    rows = conn.execute(
        "SELECT id, timestamp, name, email, rating, task, message, github_issue_number "
        "FROM feedback WHERE github_issue_number IS NULL ORDER BY id ASC" + limit_clause,
        params,
    ).fetchall()

    if not rows:
        print("No unsynced feedback rows found.")
        conn.close()
        return 0

    print(f"Found {len(rows)} unsynced feedback rows.")
    ok = 0
    failed = 0
    for row in rows:
        issue_number, issue_url, err = create_issue(cfg, row)
        if issue_number and issue_url:
            ok += 1
            conn.execute(
                "UPDATE feedback SET github_issue_number=?, github_issue_url=?, github_sync_status=?, github_sync_error=?, github_synced_at=? WHERE id=?",
                (issue_number, issue_url, "synced", None, datetime.now(timezone.utc).isoformat(), row["id"]),
            )
            print(f"synced id={row['id']} -> issue #{issue_number}")
        else:
            failed += 1
            conn.execute(
                "UPDATE feedback SET github_sync_status=?, github_sync_error=? WHERE id=?",
                ("failed", err, row["id"]),
            )
            print(f"failed id={row['id']}: {err}")
        conn.commit()

    conn.close()
    print(f"Done. synced={ok}, failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
