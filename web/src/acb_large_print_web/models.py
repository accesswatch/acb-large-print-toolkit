"""Database models for GLOW user accounts, profiles, and document history.

Auth provider model is deliberately flexible to support multiple backends:
- 'local'      : email + bcrypt password
- 'google'     : Google OAuth2 via Authlib
- 'microsoft'  : Microsoft Entra ID (Azure AD) via Authlib
- 'auth0'      : Auth0 tenant via Authlib
- 'wordpress'  : WordPress OAuth Server plugin via Authlib

A user can have multiple OAuth identities linked to one account (via UserOAuthIdentity).
The ``email`` field is the canonical deduplication key -- linking an OAuth account
to an existing email automatically merges the identities.

Privacy principles:
- API keys (UserProviderKey.encrypted_key) are always stored Fernet-encrypted.
- Audit report JSON stored on filesystem; only the path is in the DB.
- Users control every sync category via UserPrivacyConsent.
- Hard-delete is fully supported: all rows + report files are removed.
- 30-day audit history retention enforced by a cleanup helper.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from flask_login import UserMixin

from .db import db

# ---------------------------------------------------------------------------
# Constants & Enums
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    """User role hierarchy for role-based access control (RBAC).
    
    Roles are ordered from least to most privileged:
    - USER: Regular end-user (document auditing, conversions, account settings)
    - ADMIN: Administrator (user management, role elevation, system settings)
    - SUPER_ADMIN: Super admin (unrestricted, system configuration, dangerous operations)
    """
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

    @classmethod
    def hierarchy(cls) -> dict[str, int]:
        """Return privilege hierarchy: higher = more privileged."""
        return {
            cls.USER: 1,
            cls.ADMIN: 2,
            cls.SUPER_ADMIN: 3,
        }

    def has_privilege(self, required_role: "UserRole") -> bool:
        """Check if this role has at least the privilege of required_role."""
        return self.hierarchy().get(self.value, 0) >= self.hierarchy().get(required_role.value, 0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(UTC)


def _json_default(value: Any) -> str:
    return json.dumps(value or {})


def _json_load(raw: str | None) -> Any:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


# ---------------------------------------------------------------------------
# User (core identity)
# ---------------------------------------------------------------------------

class User(db.Model, UserMixin):
    """Core user identity record.
    
    Role-based access control (RBAC) is enforced via the `role` field:
    - USER (default): Regular end-user with document audit/conversion privileges
    - ADMIN: Can manage users, elevate roles, access admin routes
    - SUPER_ADMIN: Unrestricted access (system configuration, dangerous ops)
    """

    __tablename__ = "users"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    email: str = db.Column(db.String(254), unique=True, nullable=False, index=True)
    display_name: str = db.Column(db.String(120), nullable=False, default="")
    # bcrypt hash; NULL for OAuth-only accounts
    password_hash: bytes | None = db.Column(db.LargeBinary, nullable=True)
    # Primary auth provider; secondary providers stored in UserOAuthIdentity
    auth_provider: str = db.Column(db.String(32), nullable=False, default="local")
    is_active: bool = db.Column(db.Boolean, nullable=False, default=True)
    is_email_verified: bool = db.Column(db.Boolean, nullable=False, default=False)
    email_verify_token: str | None = db.Column(db.String(128), nullable=True)
    password_reset_token: str | None = db.Column(db.String(128), nullable=True)
    password_reset_expires: datetime | None = db.Column(db.DateTime(timezone=True), nullable=True)
    # Role-based access control: 'user', 'admin', 'super_admin'
    role: str = db.Column(db.String(16), nullable=False, default=UserRole.USER.value, index=True)
    # Admin promotion workflow: pending, approved, rejected
    promotion_request_status: str | None = db.Column(db.String(16), nullable=True)
    promotion_request_reason: str | None = db.Column(db.String(500), nullable=True)
    promotion_requested_at: datetime | None = db.Column(db.DateTime(timezone=True), nullable=True)
    promotion_reviewed_at: datetime | None = db.Column(db.DateTime(timezone=True), nullable=True)
    promotion_reviewed_by_id: int | None = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    last_login_at: datetime | None = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    oauth_identities: list["UserOAuthIdentity"] = db.relationship(
        "UserOAuthIdentity", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    provider_keys: list["UserProviderKey"] = db.relationship(
        "UserProviderKey", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    ai_settings: "UserAISettings | None" = db.relationship(
        "UserAISettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    privacy_consent: "UserPrivacyConsent | None" = db.relationship(
        "UserPrivacyConsent", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    audit_history: list["UserAuditHistory"] = db.relationship(
        "UserAuditHistory", back_populates="user", cascade="all, delete-orphan",
        order_by="UserAuditHistory.created_at.desc()", lazy="dynamic"
    )
    ui_preferences: "UserUIPreferences | None" = db.relationship(
        "UserUIPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    
    # Self-referential relationship for promotion reviews
    promotion_reviewed_by: "User | None" = db.relationship(
        "User", remote_side=[id], foreign_keys=[promotion_reviewed_by_id]
    )

    def set_password(self, password: str) -> None:
        """Hash and store a bcrypt password."""
        import bcrypt
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored bcrypt hash."""
        if not self.password_hash:
            return False
        import bcrypt
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash)
    
    def is_admin(self) -> bool:
        """Check if user has admin or super_admin role."""
        return self.role in (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value)
    
    def is_super_admin(self) -> bool:
        """Check if user has super_admin role."""
        return self.role == UserRole.SUPER_ADMIN.value
    
    def has_role(self, required_role: str | UserRole) -> bool:
        """Check if user's role meets or exceeds the required role."""
        if isinstance(required_role, UserRole):
            required = required_role.value
        else:
            required = required_role
        
        try:
            user_role_obj = UserRole(self.role)
            required_role_obj = UserRole(required)
            return user_role_obj.has_privilege(required_role_obj)
        except ValueError:
            return False
    
    def request_promotion(self, reason: str) -> None:
        """Request admin promotion. Must be approved by existing admin."""
        if self.role != UserRole.USER.value:
            raise ValueError("Only regular users can request promotion")
        self.promotion_request_status = "pending"
        self.promotion_request_reason = reason
        self.promotion_requested_at = _now()
    
    def approve_promotion(self, approver: "User", new_role: str = UserRole.ADMIN.value) -> None:
        """Approve a promotion request and elevate user role."""
        if not approver.is_admin():
            raise ValueError("Only admins can approve promotions")
        if new_role not in (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value):
            raise ValueError(f"Invalid target role: {new_role}")
        
        self.role = new_role
        self.promotion_request_status = "approved"
        self.promotion_reviewed_at = _now()
        self.promotion_reviewed_by_id = approver.id
    
    def reject_promotion(self, approver: "User") -> None:
        """Reject a promotion request."""
        if not approver.is_admin():
            raise ValueError("Only admins can reject promotions")
        
        self.promotion_request_status = "rejected"
        self.promotion_reviewed_at = _now()
        self.promotion_reviewed_by_id = approver.id

    def get_privacy_consent(self) -> "UserPrivacyConsent":
        """Return the user's privacy consent record, creating defaults if absent."""
        if not self.privacy_consent:
            consent = UserPrivacyConsent(user_id=self.id)
            db.session.add(consent)
            db.session.flush()
            self.privacy_consent = consent
        return self.privacy_consent

    def touch_login(self) -> None:
        self.last_login_at = _now()


# ---------------------------------------------------------------------------
# OAuth Identity (multiple providers per user)
# ---------------------------------------------------------------------------

class UserOAuthIdentity(db.Model):
    """Maps an external OAuth (provider, subject) pair to a GLOW user."""

    __tablename__ = "user_oauth_identities"
    __allow_unmapped__ = True
    __table_args__ = (
        db.UniqueConstraint("provider", "external_id", name="uq_oauth_provider_external"),
    )

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    provider: str = db.Column(db.String(32), nullable=False)  # google/microsoft/auth0/wordpress
    external_id: str = db.Column(db.String(256), nullable=False)  # OAuth 'sub' claim
    access_token_hint: str | None = db.Column(db.String(64), nullable=True)  # last 8 chars only
    created_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    last_used_at: datetime | None = db.Column(db.DateTime(timezone=True), nullable=True)

    user: "User" = db.relationship("User", back_populates="oauth_identities")


# ---------------------------------------------------------------------------
# Provider API Keys (encrypted at rest)
# ---------------------------------------------------------------------------

class UserProviderKey(db.Model):
    """Stores a user's AI provider API key, encrypted with Fernet.

    One row per (user, provider).  The key is NEVER stored in plaintext.
    The ``encrypted_key`` column holds a Fernet token; decryption requires
    the server's current SECRET_KEY.
    """

    __tablename__ = "user_provider_keys"
    __allow_unmapped__ = True
    __table_args__ = (
        db.UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    provider: str = db.Column(db.String(32), nullable=False)
    # Fernet-encrypted API key -- see encryption.py
    encrypted_key: str = db.Column(db.Text, nullable=False)
    default_model: str = db.Column(db.String(128), nullable=False, default="")
    # Serialized per-provider model catalog (refreshed on validation)
    models_json: str = db.Column(db.Text, nullable=False, default="{}")
    created_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    updated_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    user: "User" = db.relationship("User", back_populates="provider_keys")

    def get_plaintext_key(self) -> str:
        """Decrypt and return the API key.  Returns '' on decryption failure."""
        from .encryption import decrypt_safe
        return decrypt_safe(self.encrypted_key, default="")

    @classmethod
    def upsert(cls, user_id: int, provider: str, plaintext_key: str,
               default_model: str = "", models: list | None = None) -> "UserProviderKey":
        """Create or update a provider key record with an encrypted key."""
        from .encryption import encrypt
        import json
        record = db.session.execute(
            db.select(cls).where(cls.user_id == user_id, cls.provider == provider)
        ).scalar_one_or_none()
        encrypted = encrypt(plaintext_key)
        if record is None:
            record = cls(
                user_id=user_id,
                provider=provider,
                encrypted_key=encrypted,
                default_model=default_model,
                models_json=json.dumps(models or []),
            )
            db.session.add(record)
        else:
            record.encrypted_key = encrypted
            record.default_model = default_model
            if models is not None:
                record.models_json = json.dumps(models)
            record.updated_at = _now()
        return record


# ---------------------------------------------------------------------------
# AI Settings (non-sensitive: feature flags, model bindings, prompts, runtime)
# ---------------------------------------------------------------------------

class UserAISettings(db.Model):
    """Per-user AI feature configuration snapshot.

    All fields are JSON-serialized dicts to avoid schema churn as features evolve.
    Contains NO sensitive data (keys are in UserProviderKey).
    """

    __tablename__ = "user_ai_settings"
    __allow_unmapped__ = True

    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    feature_flags_json: str = db.Column(db.Text, nullable=False, default="{}")
    feature_models_json: str = db.Column(db.Text, nullable=False, default="{}")
    runtime_settings_json: str = db.Column(db.Text, nullable=False, default="{}")
    prompt_settings_json: str = db.Column(db.Text, nullable=False, default="{}")
    rule_profile_json: str = db.Column(db.Text, nullable=False, default="{}")
    updated_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    user: "User" = db.relationship("User", back_populates="ai_settings")

    @property
    def feature_flags(self) -> dict:
        return _json_load(self.feature_flags_json)

    @feature_flags.setter
    def feature_flags(self, value: dict) -> None:
        self.feature_flags_json = json.dumps(value or {})

    @property
    def feature_models(self) -> dict:
        return _json_load(self.feature_models_json)

    @feature_models.setter
    def feature_models(self, value: dict) -> None:
        self.feature_models_json = json.dumps(value or {})

    @property
    def runtime_settings(self) -> dict:
        return _json_load(self.runtime_settings_json)

    @runtime_settings.setter
    def runtime_settings(self, value: dict) -> None:
        self.runtime_settings_json = json.dumps(value or {})

    @property
    def prompt_settings(self) -> dict:
        return _json_load(self.prompt_settings_json)

    @prompt_settings.setter
    def prompt_settings(self, value: dict) -> None:
        self.prompt_settings_json = json.dumps(value or {})

    @property
    def rule_profile(self) -> dict:
        return _json_load(self.rule_profile_json)

    @rule_profile.setter
    def rule_profile(self, value: dict) -> None:
        self.rule_profile_json = json.dumps(value or {})

    @classmethod
    def for_user(cls, user_id: int) -> "UserAISettings":
        """Return or create the AI settings record for the given user."""
        record = db.session.get(cls, user_id)
        if record is None:
            record = cls(user_id=user_id)
            db.session.add(record)
            db.session.flush()
        return record


# ---------------------------------------------------------------------------
# Privacy Consent (granular per-category opt-in)
# ---------------------------------------------------------------------------

class UserPrivacyConsent(db.Model):
    """Controls which session data categories are persisted to the user profile.

    Privacy-first defaults:
    - AI keys: OFF (explicit opt-in required)
    - Everything else: ON (user gets value immediately; can opt out)
    """

    __tablename__ = "user_privacy_consent"
    __allow_unmapped__ = True

    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    # Sensitive: API keys encrypted at rest -- off by default
    sync_ai_keys: bool = db.Column(db.Boolean, nullable=False, default=False)
    # Non-sensitive settings -- on by default for convenience
    sync_ai_features: bool = db.Column(db.Boolean, nullable=False, default=True)
    sync_ai_prompts: bool = db.Column(db.Boolean, nullable=False, default=True)
    sync_ai_runtime: bool = db.Column(db.Boolean, nullable=False, default=True)
    sync_audit_history: bool = db.Column(db.Boolean, nullable=False, default=True)
    sync_ui_preferences: bool = db.Column(db.Boolean, nullable=False, default=True)
    sync_rule_profile: bool = db.Column(db.Boolean, nullable=False, default=True)
    updated_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    user: "User" = db.relationship("User", back_populates="privacy_consent")

    def allows(self, category: str) -> bool:
        """Return True if the user has consented to syncing ``category``."""
        return bool(getattr(self, f"sync_{category}", False))


# ---------------------------------------------------------------------------
# Audit History
# ---------------------------------------------------------------------------

class UserAuditHistory(db.Model):
    """Per-user audit history entry (metadata + optional report path).

    Files are stored in ``instance/user_reports/<user_id>/<id>.json``.
    Rows older than 30 days are pruned by ``prune_old_history()``.
    """

    __tablename__ = "user_audit_history"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    filename: str = db.Column(db.String(255), nullable=False, default="")
    file_ext: str = db.Column(db.String(16), nullable=False, default="")
    score: float | None = db.Column(db.Float, nullable=True)
    # JSON: {"critical": 2, "high": 5, "medium": 3, "low": 1}
    severity_counts_json: str = db.Column(db.Text, nullable=False, default="{}")
    # Relative path under instance/ where the report JSON/HTML is stored
    report_path: str | None = db.Column(db.String(512), nullable=True)
    created_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, index=True)

    user: "User" = db.relationship("User", back_populates="audit_history")

    @property
    def severity_counts(self) -> dict:
        return _json_load(self.severity_counts_json)

    @classmethod
    def prune_old_history(cls, user_id: int, keep_days: int = 30, keep_max: int = 10) -> int:
        """Delete entries older than *keep_days* or beyond *keep_max*.  Returns count deleted."""
        import os
        from flask import current_app
        cutoff = _now() - timedelta(days=keep_days)
        old = db.session.execute(
            db.select(cls).where(cls.user_id == user_id, cls.created_at < cutoff)
        ).scalars().all()
        # Also enforce max count
        all_entries = db.session.execute(
            db.select(cls).where(cls.user_id == user_id)
            .order_by(cls.created_at.desc())
        ).scalars().all()
        to_delete = set(old)
        if len(all_entries) > keep_max:
            to_delete.update(all_entries[keep_max:])

        for entry in to_delete:
            if entry.report_path:
                try:
                    full = os.path.join(current_app.instance_path, entry.report_path)
                    if os.path.exists(full):
                        os.remove(full)
                except OSError:
                    pass
            db.session.delete(entry)
        db.session.flush()
        return len(to_delete)


# ---------------------------------------------------------------------------
# UI Preferences (theme, cognitive mode, etc.)
# ---------------------------------------------------------------------------

class UserUIPreferences(db.Model):
    """Stores display/UX preferences that mirror the client-side localStorage values."""

    __tablename__ = "user_ui_preferences"
    __allow_unmapped__ = True

    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    theme: str = db.Column(db.String(16), nullable=False, default="auto")  # light/dark/auto
    cognitive_mode: str = db.Column(db.String(8), nullable=False, default="off")  # on/off
    updated_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    user: "User" = db.relationship("User", back_populates="ui_preferences")

    @classmethod
    def for_user(cls, user_id: int) -> "UserUIPreferences":
        record = db.session.get(cls, user_id)
        if record is None:
            record = cls(user_id=user_id)
            db.session.add(record)
            db.session.flush()
        return record


# ---------------------------------------------------------------------------
# Visitor Counter (global site-wide counter)
# ---------------------------------------------------------------------------

class VisitorCounter(db.Model):
    """Global site visitor counter - tracks unique sessions.

    Single row with id=1 stores the cumulative visit count.
    """

    __tablename__ = "visitor_counter"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True, default=1)
    visits: int = db.Column(db.Integer, nullable=False, default=0)

    @classmethod
    def increment_and_get(cls) -> int:
        """Atomically increment counter and return new value."""
        record = db.session.get(cls, 1)
        if record is None:
            record = cls(id=1, visits=1)
            db.session.add(record)
        else:
            record.visits += 1
        db.session.flush()
        return record.visits

    @classmethod
    def get_count(cls) -> int:
        """Return current count without incrementing."""
        record = db.session.get(cls, 1)
        return record.visits if record else 0


# ---------------------------------------------------------------------------
# Tool Usage (per-tool and detail-level tracking)
# ---------------------------------------------------------------------------

class ToolUsage(db.Model):
    """Tracks usage count and last_used_at per tool."""

    __tablename__ = "tool_usage"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    tool: str = db.Column(db.String(64), nullable=False, unique=True, index=True)
    count: int = db.Column(db.Integer, nullable=False, default=0)
    last_used_at: datetime | None = db.Column(db.DateTime(timezone=True), nullable=True)

    details: list["ToolUsageDetail"] = db.relationship(
        "ToolUsageDetail", back_populates="tool_usage", cascade="all, delete-orphan"
    )


class ToolUsageDetail(db.Model):
    """Detail dimensions for tool usage (e.g. mode, voice, engine)."""

    __tablename__ = "tool_usage_detail"
    __allow_unmapped__ = True
    __table_args__ = (
        db.UniqueConstraint("tool_id", "detail_key", "detail_value", name="uq_tool_detail"),
    )

    id: int = db.Column(db.Integer, primary_key=True)
    tool_id: int = db.Column(db.Integer, db.ForeignKey("tool_usage.id"), nullable=False, index=True)
    detail_key: str = db.Column(db.String(128), nullable=False)
    detail_value: str = db.Column(db.String(256), nullable=False)
    count: int = db.Column(db.Integer, nullable=False, default=0)
    last_used_at: datetime | None = db.Column(db.DateTime(timezone=True), nullable=True)

    tool_usage: "ToolUsage" = db.relationship("ToolUsage", back_populates="details")


# ---------------------------------------------------------------------------
# Speech Conversion Metrics (for adaptive runtime estimation)
# ---------------------------------------------------------------------------

class SpeechConversionMetric(db.Model):
    """Records telemetry for document-to-speech conversions for adaptive estimation."""

    __tablename__ = "speech_conversion_metric"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    created_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, index=True)
    engine: str = db.Column(db.String(64), nullable=False)
    voice: str = db.Column(db.String(128), nullable=False)
    speed: float = db.Column(db.Float, nullable=False)
    pitch: int = db.Column(db.Integer, nullable=False)
    word_count: int = db.Column(db.Integer, nullable=False, default=0)
    char_count: int = db.Column(db.Integer, nullable=False, default=0)
    source_size_bytes: int = db.Column(db.Integer, nullable=False, default=0)
    processing_seconds: float = db.Column(db.Float, nullable=False)
    audio_seconds: float = db.Column(db.Float, nullable=False, default=0.0)


# ---------------------------------------------------------------------------
# Feature Flags (system-wide toggles)
# ---------------------------------------------------------------------------

class FeatureFlag(db.Model):
    """System-wide feature flag storage (replaces JSON file backend)."""

    __tablename__ = "feature_flag"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(128), nullable=False, unique=True, index=True)
    value: bool = db.Column(db.Boolean, nullable=False)
    updated_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    @classmethod
    def get_flag(cls, name: str, default: bool = True) -> bool:
        """Get flag value or return default if not found."""
        record = db.session.execute(
            db.select(cls).where(cls.name == name)
        ).scalar_one_or_none()
        return record.value if record else default

    @classmethod
    def set_flag(cls, name: str, value: bool) -> "FeatureFlag":
        """Set or create a feature flag."""
        record = db.session.execute(
            db.select(cls).where(cls.name == name)
        ).scalar_one_or_none()
        if record is None:
            record = cls(name=name, value=value)
            db.session.add(record)
        else:
            record.value = value
            record.updated_at = _now()
        db.session.flush()
        return record


# ---------------------------------------------------------------------------
# Feature Flag Audit Trail
# ---------------------------------------------------------------------------

class FeatureFlagAudit(db.Model):
    """Audit trail for feature flag changes."""

    __tablename__ = "feature_flag_audit"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    flag_name: str = db.Column(db.String(128), nullable=False, index=True)
    old_value: bool | None = db.Column(db.Boolean, nullable=True)
    new_value: bool = db.Column(db.Boolean, nullable=False)
    changed_by: str | None = db.Column(db.String(256), nullable=True)  # email or username
    changed_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, index=True)

    @classmethod
    def record_change(cls, flag_name: str, old_value: bool | None, new_value: bool, changed_by: str | None = None) -> "FeatureFlagAudit":
        """Record a flag change in the audit trail."""
        entry = cls(flag_name=flag_name, old_value=old_value, new_value=new_value, changed_by=changed_by)
        db.session.add(entry)
        db.session.flush()
        return entry


# ---------------------------------------------------------------------------
# Magic Features (pronunciation dict and rule proposals)
# ---------------------------------------------------------------------------

class PronunciationDict(db.Model):
    """User-facing pronunciation dictionary for speech synthesis customization."""

    __tablename__ = "pronunciation_dict"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    term: str = db.Column(db.String(256), nullable=False, unique=True, index=True)
    replacement: str = db.Column(db.String(256), nullable=False)
    notes: str | None = db.Column(db.Text, nullable=True)
    updated_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)


class RuleProposal(db.Model):
    """Community rule proposal for ACB accessibility guideline updates."""

    __tablename__ = "rule_proposal"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(255), nullable=False)
    rationale: str = db.Column(db.Text, nullable=False)
    suggested_rule_id: str | None = db.Column(db.String(128), nullable=True)
    severity: str = db.Column(db.String(32), nullable=False)  # critical/high/medium/low
    submitted_by: str | None = db.Column(db.String(256), nullable=True)
    status: str = db.Column(db.String(16), nullable=False, default="pending", index=True)  # pending/approved/rejected
    created_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, index=True)


# ---------------------------------------------------------------------------
# AI Gateway Cost Tracking (OpenRouter budget enforcement)
# ---------------------------------------------------------------------------

class AICostLedger(db.Model):
    """Tracks AI inference costs for budget enforcement and monitoring."""

    __tablename__ = "ai_cost_ledger"
    __allow_unmapped__ = True


    id: int = db.Column(db.Integer, primary_key=True)
    created_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, index=True)
    provider: str = db.Column(db.String(32), nullable=False)  # openrouter/openai/ollama
    model: str = db.Column(db.String(128), nullable=False)
    input_tokens: int = db.Column(db.Integer, nullable=False, default=0)
    output_tokens: int = db.Column(db.Integer, nullable=False, default=0)
    cost_usd: float = db.Column(db.Float, nullable=False, default=0.0)
    session_id: str | None = db.Column(db.String(128), nullable=True, index=True)

    @classmethod
    def record_cost(cls, provider: str, model: str, input_tokens: int,
                   output_tokens: int, cost_usd: float, session_id: str | None = None) -> "AICostLedger":
        """Record an AI inference cost."""
        record = cls(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            session_id=session_id,
        )
        db.session.add(record)
        db.session.flush()
        return record

    @classmethod
    def get_monthly_cost(cls) -> float:
        """Sum total cost for current month (UTC)."""
        from datetime import timedelta
        now = _now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        result = db.session.execute(
            db.select(db.func.sum(cls.cost_usd)).where(cls.created_at >= month_start)
        ).scalar()
        return float(result or 0.0)
