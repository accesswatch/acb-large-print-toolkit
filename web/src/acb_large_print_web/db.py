"""SQLAlchemy + Flask-Login extension singletons.

Import ``db`` and ``login_manager`` here; call ``init_extensions(app)``
from ``create_app`` to bind them to the Flask application.
"""

from __future__ import annotations

import os
from pathlib import Path

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()


def init_extensions(app) -> None:
    """Bind SQLAlchemy and Flask-Login to the application and create tables."""
    # Database URI -- defaults to SQLite with WAL mode in instance/ volume.
    # Override with DATABASE_URL env var for Neon/PostgreSQL.
    # In testing mode, use in-memory SQLite for isolation.
    if app.config.get("TESTING", False):
        db_uri = "sqlite:///:memory:"
    else:
        db_uri = _resolve_database_uri(app)
        if not db_uri:
            instance_dir = Path(app.instance_path)
            instance_dir.mkdir(parents=True, exist_ok=True)
            db_path = instance_dir / "glow_users.db"
            db_uri = f"sqlite:///{db_path}"

    app.config.setdefault("SQLALCHEMY_DATABASE_URI", db_uri)
    app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", _engine_options_for_uri(db_uri))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    db.init_app(app)

    # Flask-Login configuration
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # type: ignore[assignment]
    login_manager.login_message = "Please sign in to access this page."
    login_manager.login_message_category = "info"
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def _load_user(user_id: str):
        from .models import User
        return db.session.get(User, int(user_id))

    # Create all tables and configure database (inside app context)
    with app.app_context():
        from . import models as _models  # noqa: F401 -- ensures models are registered
        db.create_all()

        # Enable WAL mode for SQLite for better concurrent read performance.
        if db_uri.startswith("sqlite") and not db_uri.endswith(":memory:"):
            from sqlalchemy import event, text

            @event.listens_for(db.engine, "connect", insert=True)
            def _set_wal_mode(dbapi_conn, _conn_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()


def _resolve_database_uri(app) -> str:
    """Resolve and normalize DB URI for SQLite or Neon/Postgres."""
    db_uri = (os.environ.get("DATABASE_URL") or "").strip()
    if not db_uri:
        return ""

    # Common PaaS URI variant.
    if db_uri.startswith("postgres://"):
        db_uri = "postgresql://" + db_uri[len("postgres://"):]

    # Prefer psycopg (v3) driver for stable SQLAlchemy 2.x support.
    if db_uri.startswith("postgresql://") and not db_uri.startswith("postgresql+psycopg://"):
        db_uri = "postgresql+psycopg://" + db_uri[len("postgresql://"):]

    return db_uri


def _engine_options_for_uri(db_uri: str) -> dict:
    """Return SQLAlchemy engine options based on backend type."""
    if db_uri.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
            "pool_pre_ping": True,
        }

    if db_uri.startswith("postgresql"):
        # Neon benefits from short-lived pooled connections and pre-ping.
        return {
            "pool_pre_ping": True,
            "pool_recycle": 1800,
            "pool_timeout": 30,
            "pool_size": int(os.environ.get("DB_POOL_SIZE", "5")),
            "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", "10")),
            "connect_args": {
                # Neon requires TLS in production.
                "sslmode": os.environ.get("DB_SSLMODE", "require"),
                "application_name": os.environ.get("DB_APP_NAME", "glow-web"),
            },
        }

    return {"pool_pre_ping": True}
