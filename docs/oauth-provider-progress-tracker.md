# GLOW OAuth Provider Progress Tracker

Use this file during rollout calls. Update one row at a time as credentials are collected, configured, and validated.

## Current Run Metadata

- Operator:
- Date: 2026-05-11
- Target environment: `production` | `local` | `both`
- Primary domain: `glow.bits-acb.org`

## Baseline (Pre-Collection)

- Checked file: `web/.env`
- Result: no provider OAuth credential variables detected for Apple, Microsoft, Auth0, GitHub, or WordPress.
- Action: use `docs/oauth-credential-collection-runbook.md` to collect and populate required values.

## Provider Collection and Configuration Status

| Provider | Console Ready | Credentials Copied | Env Set | Callback URLs Set | Login Test Passed | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Google | [ ] | [ ] | [ ] | [ ] | [ ] | |
| GitHub | [ ] | [ ] | [ ] | [ ] | [ ] | |
| Microsoft Entra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| Apple | [ ] | [ ] | [ ] | [ ] | [ ] | |
| Auth0 | [ ] | [ ] | [ ] | [ ] | [ ] | |
| WordPress OAuth | [ ] | [ ] | [ ] | [ ] | [ ] | Optional unless required by deployment scope |

## Required Environment Variables Checklist

- [ ] `GOOGLE_CLIENT_ID`
- [ ] `GOOGLE_CLIENT_SECRET`
- [ ] `GITHUB_CLIENT_ID`
- [ ] `GITHUB_CLIENT_SECRET`
- [ ] `MICROSOFT_CLIENT_ID`
- [ ] `MICROSOFT_CLIENT_SECRET`
- [ ] `MICROSOFT_TENANT_ID`
- [ ] `APPLE_CLIENT_ID`
- [ ] `APPLE_CLIENT_SECRET`
- [ ] `AUTH0_CLIENT_ID`
- [ ] `AUTH0_CLIENT_SECRET`
- [ ] `AUTH0_DOMAIN`
- [ ] `WORDPRESS_CLIENT_ID` (if using WordPress provider)
- [ ] `WORDPRESS_CLIENT_SECRET` (if using WordPress provider)
- [ ] `WORDPRESS_BASE_URL` (if using WordPress provider)

## Validation Log

Record each completed login test with timestamp and result.

| Time (UTC) | Provider | Environment | Result | Details |
| --- | --- | --- | --- | --- |
| | | | PASS/FAIL | |

## Go-Live Snapshot

### Readiness Summary

- Providers required for launch:
- Providers passing end-to-end:
- Blocking gaps:
- Non-blocking gaps:

### Final Go/No-Go Checklist

- [ ] All required provider credentials collected
- [ ] All required env vars present on production server
- [ ] All required callback URLs configured in provider consoles
- [ ] End-to-end login test passed for each required provider
- [ ] On-call owner assigned for day-1 auth support

### Decision

- Status: `GO` | `NO-GO`
- Approved by:
- Timestamp (UTC):
