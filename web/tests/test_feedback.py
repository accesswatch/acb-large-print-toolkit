"""Tests for feedback form and GitHub issue creation."""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def app():
    """Create app for testing."""
    from acb_large_print_web.app import create_app

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_feedback_form_get(client):
    """Test GET /feedback returns form."""
    response = client.get("/feedback/")
    assert response.status_code == 200
    assert b"Share Your Feedback" in response.data


def test_feedback_submit_valid(client):
    """Test valid feedback submission."""
    response = client.post(
        "/feedback/submit",
        data={
            "rating": "good",
            "task": "audit",
            "message": "Great tool!",
        },
    )
    assert response.status_code == 200


def test_feedback_submit_with_contact_info(client):
    """Test feedback submission with optional name/email."""
    response = client.post(
        "/feedback/submit",
        data={
            "name": "Alice Smith",
            "email": "alice@example.com",
            "rating": "excellent",
            "task": "fix",
            "message": "Amazing accessibility tool!",
        },
    )
    assert response.status_code == 200


def test_feedback_submit_missing_rating(client):
    """Test feedback submission fails without rating."""
    response = client.post(
        "/feedback/submit",
        data={
            "message": "No rating provided",
        },
    )
    assert response.status_code == 400
    assert b"Please select a rating" in response.data


def test_feedback_submit_missing_message(client):
    """Test feedback submission fails without message."""
    response = client.post(
        "/feedback/submit",
        data={
            "rating": "good",
        },
    )
    assert response.status_code == 400
    assert b"Please enter your feedback" in response.data


def test_feedback_submit_invalid_email(client):
    """Test feedback submission fails with invalid email."""
    response = client.post(
        "/feedback/submit",
        data={
            "email": "not-an-email",
            "rating": "good",
            "message": "Test feedback",
        },
    )
    assert response.status_code == 400
    assert b"valid email" in response.data


def test_feedback_review_requires_password(client):
    """Test feedback review page requires password."""
    response = client.get("/feedback/review")
    assert response.status_code == 404  # disabled when no password configured


def test_feedback_review_wrong_password(client, monkeypatch):
    """Test feedback review rejects wrong password."""
    monkeypatch.setenv("FEEDBACK_PASSWORD", "correct-password")
    from acb_large_print_web.app import create_app

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()

    response = client.get("/feedback/review?key=wrong-password")
    assert response.status_code == 403


def test_feedback_review_correct_password(client, monkeypatch):
    """Test feedback review allows correct password."""
    monkeypatch.setenv("FEEDBACK_PASSWORD", "correct-password")
    from acb_large_print_web.app import create_app

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()

    response = client.get("/feedback/review?key=correct-password")
    assert response.status_code == 200
