"""Tests for the Rules Reference route."""
from __future__ import annotations
import pytest
from flask import Flask
from .test_app import app, client

def test_rules_ref_page_loads(client):
    """Test that the /rules/ page loads and displays rules."""
    resp = client.get("/rules/")
    assert resp.status_code == 200
    assert b"Rules Reference" in resp.data
    assert b"browse all" in resp.data.lower()
    # Check for a known rule ID (e.g. MSAC-TEXT-UNDERLINE) or table structure
    assert b"MSAC-" in resp.data or b"ACB-" in resp.data

def test_rules_ref_filters(client):
    """Test that filters are present on the /rules/ page."""
    resp = client.get("/rules/")
    assert resp.status_code == 200
    assert b'id="filter-search"' in resp.data
    assert b'id="filter-severity"' in resp.data
    assert b'id="filter-format"' in resp.data

def test_rules_ref_selection_target(client):
    """Test that the selection target can be changed via query param."""
    resp = client.get("/rules/?target=fix")
    assert resp.status_code == 200
    assert b'option value="fix" selected' in resp.data
