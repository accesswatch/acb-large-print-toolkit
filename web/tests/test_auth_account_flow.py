from __future__ import annotations

from pathlib import Path

import pytest

from acb_large_print_web.app import create_app
from acb_large_print_web.db import db
from acb_large_print_web.models import User


@pytest.fixture()
def app(tmp_path: Path):
    import os

    os.environ.setdefault("FIREBASE_AUTH_ENABLED", "1")
    os.environ.setdefault("FIREBASE_WEB_API_KEY", "test-api-key")
    os.environ.setdefault("FIREBASE_AUTH_DOMAIN", "test-project.firebaseapp.com")
    os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")
    os.environ.setdefault("FIREBASE_APP_ID", "test-app-id")

    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "MAX_CONTENT_LENGTH": 500 * 1024 * 1024,
        }
    )
    application.instance_path = str(tmp_path / "instance")
    Path(application.instance_path).mkdir(parents=True, exist_ok=True)
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def _login_as_user(client, app, *, email: str, display_name: str = "") -> User:
    with app.app_context():
        user = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                display_name=display_name,
                auth_provider="passwordless",
                is_active=True,
                is_email_verified=True,
            )
            db.session.add(user)
            db.session.commit()

        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess.permanent = True

        return user


def test_home_page_stays_public_for_anonymous_visitors(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Create Account" not in response.location.encode() if response.location else True


def test_login_page_is_sign_in_only(client):
    response = client.get("/auth/login")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "sign in to an existing GLOW account" in body
    assert "enrolled automatically" not in body


def test_register_page_is_explicit_account_creation(client):
    response = client.get("/auth/register")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "create a GLOW account" in body
    assert "Already have an account?" in body


def test_firebase_login_requires_existing_account_when_not_creating(client, app, monkeypatch):
    monkeypatch.setenv("FIREBASE_AUTH_ENABLED", "1")

    from acb_large_print_web import firebase_auth

    monkeypatch.setattr(firebase_auth, "is_enabled", lambda: True)
    monkeypatch.setattr(
        firebase_auth,
        "verify_id_token",
        lambda _token: {
            "uid": "firebase-user-1",
            "email": "new-user@example.com",
            "email_verified": True,
            "firebase": {"sign_in_provider": "emailLink"},
        },
    )

    response = client.post(
        "/auth/firebase-login",
        json={"idToken": "token-1", "createAccount": False},
    )

    assert response.status_code == 404
    payload = response.get_json()
    assert payload["code"] == "account_not_found"

    with app.app_context():
        assert db.session.execute(
            db.select(User).where(User.email == "new-user@example.com")
        ).scalar_one_or_none() is None


def test_firebase_login_rejects_invalid_token(client, monkeypatch):
    monkeypatch.setenv("FIREBASE_AUTH_ENABLED", "1")

    from acb_large_print_web import firebase_auth

    monkeypatch.setattr(firebase_auth, "is_enabled", lambda: True)

    def _raise_invalid(_token: str):
        raise RuntimeError("expired token")

    monkeypatch.setattr(firebase_auth, "verify_id_token", _raise_invalid)

    response = client.post(
        "/auth/firebase-login",
        json={"idToken": "bad-token", "createAccount": False},
    )

    assert response.status_code == 401
    payload = response.get_json()
    assert payload["error"] == "Invalid or expired Firebase token."


def test_firebase_login_create_account_leaves_display_name_blank(client, app, monkeypatch):
    monkeypatch.setenv("FIREBASE_AUTH_ENABLED", "1")

    from acb_large_print_web import firebase_auth

    monkeypatch.setattr(firebase_auth, "is_enabled", lambda: True)
    monkeypatch.setattr(
        firebase_auth,
        "verify_id_token",
        lambda _token: {
            "uid": "firebase-user-2",
            "email": "blank-name@example.com",
            "email_verified": True,
            "firebase": {"sign_in_provider": "emailLink"},
        },
    )

    response = client.post(
        "/auth/firebase-login",
        json={"idToken": "token-2", "createAccount": True},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True

    with app.app_context():
        user = db.session.execute(
            db.select(User).where(User.email == "blank-name@example.com")
        ).scalar_one()
        assert user.display_name == ""


def test_firebase_login_existing_user_signs_in_without_creating_duplicate(client, app, monkeypatch):
    monkeypatch.setenv("FIREBASE_AUTH_ENABLED", "1")

    _login_as_user(
        client,
        app,
        email="existing-user@example.com",
        display_name="",
    )

    from acb_large_print_web import firebase_auth
    from acb_large_print_web.models import UserOAuthIdentity

    monkeypatch.setattr(firebase_auth, "is_enabled", lambda: True)
    monkeypatch.setattr(
        firebase_auth,
        "verify_id_token",
        lambda _token: {
            "uid": "firebase-user-existing",
            "email": "existing-user@example.com",
            "name": "Existing User",
            "email_verified": True,
            "firebase": {"sign_in_provider": "github.com"},
        },
    )

    response = client.post(
        "/auth/firebase-login",
        json={"idToken": "token-existing", "createAccount": False},
    )

    assert response.status_code == 200

    with app.app_context():
        users = db.session.execute(
            db.select(User).where(User.email == "existing-user@example.com")
        ).scalars().all()
        assert len(users) == 1
        user = users[0]
        assert user.display_name == "Existing User"
        assert user.auth_provider == "github"
        identity = db.session.execute(
            db.select(UserOAuthIdentity).where(UserOAuthIdentity.external_id == "firebase-user-existing")
        ).scalar_one()
        assert identity.user_id == user.id


def test_firebase_login_existing_identity_succeeds_without_create_account(client, app, monkeypatch):
    monkeypatch.setenv("FIREBASE_AUTH_ENABLED", "1")

    from acb_large_print_web import firebase_auth
    from acb_large_print_web.models import User, UserOAuthIdentity

    with app.app_context():
        user = User(
            email="identity-user@example.com",
            display_name="Identity User",
            auth_provider="passwordless",
            is_active=True,
            is_email_verified=False,
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(
            UserOAuthIdentity(
                user_id=user.id,
                provider="firebase",
                external_id="firebase-identity-1",
            )
        )
        db.session.commit()

    monkeypatch.setattr(firebase_auth, "is_enabled", lambda: True)
    monkeypatch.setattr(
        firebase_auth,
        "verify_id_token",
        lambda _token: {
            "uid": "firebase-identity-1",
            "email": "identity-user@example.com",
            "email_verified": True,
            "firebase": {"sign_in_provider": "emailLink"},
        },
    )

    response = client.post(
        "/auth/firebase-login",
        json={"idToken": "token-identity", "createAccount": False},
    )

    assert response.status_code == 200

    with app.app_context():
        user = db.session.execute(
            db.select(User).where(User.email == "identity-user@example.com")
        ).scalar_one()
        assert user.auth_provider == "passwordless"
        assert user.is_email_verified is True


def test_account_dashboard_blanks_email_like_display_name_and_includes_csrf(client, app):
    _login_as_user(
        client,
        app,
        email="prefill@example.com",
        display_name="prefill@example.com",
    )

    response = client.get("/account/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'name="csrf_token"' in body
    assert 'id="display_name" name="display_name" type="text" value=""' in body


def test_profile_update_allows_clearing_display_name(client, app):
    _login_as_user(
        client,
        app,
        email="clear-name@example.com",
        display_name="Needs Clearing",
    )

    response = client.post(
        "/account/profile",
        data={"display_name": ""},
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)

    with app.app_context():
        user = db.session.execute(
            db.select(User).where(User.email == "clear-name@example.com")
        ).scalar_one()
        assert user.display_name == ""