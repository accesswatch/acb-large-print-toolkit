#!/usr/bin/env python3
"""Migrate GLOW SQLite databases into Neon/PostgreSQL.

This script copies table schemas and row data from one or more SQLite files
into a PostgreSQL database (for example Neon) using SQLAlchemy.

Usage:
  python scripts/migrate_sqlite_to_neon.py --target-url "$DATABASE_URL"
  python scripts/migrate_sqlite_to_neon.py --instance-dir instance --truncate

Environment:
  DATABASE_URL can be used instead of --target-url.
"""

from __future__ import annotations

import argparse
import os
from collections import defaultdict, deque
from pathlib import Path
from typing import Iterable

from sqlalchemy import MetaData, Table, create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

DEFAULT_SQLITE_FILES = (
    "ai_quota.db",
    "feedback.db",
    "visitor_counter.db",
    "feature_flags.db",
    # Legacy files kept for backward compatibility in older installs.
    "glow_users.db",
    "admin_auth.db",
)


def normalize_target_url(url: str) -> str:
    url = (url or "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and not url.startswith("postgresql+psycopg://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def ordered_tables(engine: Engine, table_names: list[str]) -> list[str]:
    """Best-effort topological sort based on FK dependencies."""
    insp = inspect(engine)
    deps: dict[str, set[str]] = defaultdict(set)
    reverse: dict[str, set[str]] = defaultdict(set)

    for t in table_names:
        for fk in insp.get_foreign_keys(t):
            referred = fk.get("referred_table")
            if referred and referred in table_names and referred != t:
                deps[t].add(referred)
                reverse[referred].add(t)

    indegree = {t: len(deps[t]) for t in table_names}
    q = deque([t for t in table_names if indegree[t] == 0])
    out: list[str] = []

    while q:
        t = q.popleft()
        out.append(t)
        for nxt in reverse[t]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                q.append(nxt)

    # fallback for cycles
    for t in table_names:
        if t not in out:
            out.append(t)
    return out


def truncate_target_tables(dst_engine: Engine, table_names: Iterable[str]) -> None:
    names = [n for n in table_names]
    if not names:
        return
    quoted = ", ".join(f'"{n}"' for n in names)
    with dst_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))


def migrate_sqlite_file(sqlite_file: Path, dst_engine: Engine, truncate: bool) -> tuple[int, int]:
    src_engine = create_engine(f"sqlite:///{sqlite_file}")
    src_inspector = inspect(src_engine)
    table_names = src_inspector.get_table_names()

    if not table_names:
        print(f"[skip] {sqlite_file.name}: no tables found")
        return 0, 0

    ordered = ordered_tables(src_engine, table_names)

    src_metadata = MetaData()
    src_metadata.reflect(bind=src_engine)

    # Ensure target tables exist with reflected metadata.
    dst_metadata = MetaData()
    for name in ordered:
        table = src_metadata.tables[name]
        table.to_metadata(dst_metadata)

    dst_metadata.create_all(bind=dst_engine)

    if truncate:
        truncate_target_tables(dst_engine, ordered)

    inserted_total = 0
    skipped_total = 0

    for name in ordered:
        src_table = src_metadata.tables[name]
        dst_table = Table(name, MetaData(), autoload_with=dst_engine)

        with src_engine.connect() as src_conn:
            rows = [dict(r._mapping) for r in src_conn.execute(src_table.select())]

        if not rows:
            print(f"  - {name}: 0 rows")
            continue

        chunk_size = 500
        inserted = 0
        skipped = 0

        with dst_engine.begin() as dst_conn:
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i:i + chunk_size]
                try:
                    dst_conn.execute(dst_table.insert(), chunk)
                    inserted += len(chunk)
                except IntegrityError:
                    # fallback row-by-row to skip duplicates/conflicts
                    for row in chunk:
                        try:
                            dst_conn.execute(dst_table.insert(), row)
                            inserted += 1
                        except IntegrityError:
                            skipped += 1

        inserted_total += inserted
        skipped_total += skipped
        print(f"  - {name}: inserted={inserted} skipped={skipped}")

    return inserted_total, skipped_total


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate GLOW SQLite DBs to Neon/PostgreSQL")
    parser.add_argument("--instance-dir", default="instance", help="Directory containing SQLite files")
    parser.add_argument("--target-url", default=os.environ.get("DATABASE_URL", ""), help="Postgres/Neon SQLAlchemy URL")
    parser.add_argument("--files", nargs="*", default=list(DEFAULT_SQLITE_FILES), help="SQLite file names to migrate")
    parser.add_argument("--truncate", action="store_true", help="Truncate destination tables before insert")
    args = parser.parse_args()

    target_url = normalize_target_url(args.target_url)
    if not target_url:
        raise SystemExit("Missing --target-url and DATABASE_URL is not set")

    if not target_url.startswith("postgresql"):
        raise SystemExit("Target URL must be PostgreSQL/Neon")

    instance_dir = Path(args.instance_dir)
    if not instance_dir.exists():
        raise SystemExit(f"Instance dir not found: {instance_dir}")

    dst_engine = create_engine(target_url)

    total_inserted = 0
    total_skipped = 0

    for filename in args.files:
        sqlite_path = instance_dir / filename
        if not sqlite_path.exists():
            print(f"[skip] {filename}: file not found")
            continue
        print(f"[migrate] {sqlite_path}")
        inserted, skipped = migrate_sqlite_file(sqlite_path, dst_engine, truncate=args.truncate)
        total_inserted += inserted
        total_skipped += skipped

    print("\nMigration complete")
    print(f"Rows inserted: {total_inserted}")
    print(f"Rows skipped : {total_skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
