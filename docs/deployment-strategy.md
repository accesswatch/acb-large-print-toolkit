# Deployment Strategy: ACB Large Print Web Application

## Overview

This document describes the safe, failsafe deployment process for the GLOW Accessibility Toolkit web application. The strategy prioritizes **zero data loss**, **automatic rollback on failure**, and **transparent user communication** during maintenance.

---

## Deployment Workflow

### Phase 1: Pre-Deployment Preparation

1. **Backup the feedback database** (automatic via `ENABLE_PREDEPLOY_BACKUP=1`)
   - Prevents loss of user feedback if something goes wrong
   - Backup is stored in `~/app/backups/feedback/` with ISO8601 timestamp

2. **Enable Maintenance Mode** (`MAINTENANCE_MODE=1`)
   - All HTTP requests (except `/health`) receive a `503 Service Unavailable` response
   - Users see a clean, accessible "Under Maintenance" page
   - The `<title>` announces the reason and expected timeframe
   - `/health` endpoint remains available for deployment orchestration

3. **Pull latest code from Git** (if `.git` directory exists)
   - Ensures the Docker build reflects the latest commits
   - Baseline commit is captured for rollback

### Phase 2: Build & Start

4. **Build and start Docker containers**
   - `docker compose -f docker-compose.prod.yml up -d --build`
   - Web app, Pipeline (DAISY), and Ollama (AI) services start
   - Containers restart automatically on failure (`restart: unless-stopped`)

5. **Wait for health check** (up to 40 attempts × 3 seconds = ~2 minutes)
   - The deployment script polls `/health` until the app responds `200 OK`
   - If healthy within timeframe: proceed to Phase 3
   - If not: proceed to Phase 4 (Rollback)

### Phase 3: Success - Deployment Goes Live

6. **Disable Maintenance Mode** (`MAINTENANCE_MODE=0`)
   - Restart containers with the flag disabled (one more `docker compose up -d --build`)
   - Users now see the live application
   - All features are available

7. **Confirm deployment**
   - Health check still passes on the new code
   - URLs are shown for manual testing (main domain, app domain, etc.)
   - Container status is displayed

---

## Rollback Process (Automatic on Failure)

If the health check fails:

### Phase 4: Automatic Rollback

1. **Disable Maintenance Mode** immediately
   - Restart containers with `MAINTENANCE_MODE=0`
   - Ensures users see the **previous good version**, not a maintenance page

2. **Checkout previous Git commit** (if Git is available)
   - `git checkout -f <PRE_DEPLOY_COMMIT>`
   - Reverts all code to the last known-good state

3. **Rebuild and restart with previous code**
   - `docker compose up -d --build`
   - Containers re-pull from the previous commit

4. **Verify rollback health check**
   - Poll `/health` again (up to 40 attempts)
   - If rollback passes: deployment ends with rollback message
   - If rollback fails: **manual intervention required** (exit code 1, error message shown)

---

## Deployment Lifecycle

```
┌─────────────────────────────────────┐
│  User runs: bash deploy-app.sh      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  [PRE-FLIGHT CHECKS]                │
│  - Docker installed & running       │
│  - Required files present           │
│  - Git repository detected (if any) │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  [BACKUP] Feedback DB (optional)    │
│  → ~/app/backups/feedback/*.tar.gz  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ [ENABLE MAINTENANCE MODE]           │
│  MAINTENANCE_MODE=1 (env var)       │
│  Users see "Under Maintenance"      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  [BUILD & START]                    │
│  docker compose up -d --build       │
│  (Web, Pipeline, Ollama services)   │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌──────┴──────┐
        │ Health OK?  │
        └──┬──────┬───┘
       YES │      │ NO
           ▼      ▼
    ┌──────────┐  ┌────────────────┐
    │ [SUCCESS]│  │ [ROLLBACK]     │
    │ Disable  │  │ - Disable      │
    │ Maint.   │  │   maintenance  │
    │ Site     │  │ - Git checkout │
    │ LIVE     │  │   prev commit  │
    └──────────┘  │ - Rebuild      │
                  │ - Health check │
                  │   prev code    │
                  └────┬───────┬───┘
                   OK  │       │ FAIL
                       │       ▼
                       │   [MANUAL]
                       │   Intervent.
                       │   (Exit 1)
                       │
                       ▼
                   ┌─────────────┐
                   │ [COMPLETE]  │
                   │ Display     │
                   │ status & URLs
                   └─────────────┘
```

---

## Usage

### Automated Deployment

```bash
# On the production server as the deploy user:
bash ~/app/scripts/deploy-app.sh

# Or with custom configuration:
APP_DOMAIN=glow.example.com \
  bash ~/app/scripts/deploy-app.sh
```

### Manual Maintenance Mode Control

For operational tasks (without deploying code):

```bash
# Enable maintenance mode (e.g., for database migration, manual updates)
bash ~/app/scripts/maintenance-mode.sh on

# Disable maintenance mode (bring site back online)
bash ~/app/scripts/maintenance-mode.sh off

# Check current status
bash ~/app/scripts/maintenance-mode.sh status
```

---

## Exit Codes

| Code | Meaning | Recovery |
|------|---------|----------|
| 0 | Successful deployment | None needed; site is live |
| 1 | Pre-flight check failed | Fix missing files/setup and retry |
| 1 | Health check failed + rollback failed | **Manual intervention:** SSH to server, check Docker logs, potential restore from backup |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MAINTENANCE_MODE` | 0 (off) | Set to `1` to show maintenance page; `/health` always responds |
| `APP_ROOT` | `$HOME/app` | Directory containing the entire repository |
| `WEB_ROOT` | `$APP_ROOT/web` | Directory containing docker-compose.prod.yml and Dockerfile |
| `COMPOSE_FILE` | `docker-compose.prod.yml` | Docker Compose configuration file |
| `APP_DOMAIN` | `lp.csedesigns.com` | Primary domain (used in test URLs) |
| `APP_ALIAS_DOMAIN` | (empty) | Secondary domain alias (if configured) |
| `MAIN_DOMAIN` | `csedesigns.com` | Main site domain (used in test URLs) |
| `ENABLE_PREDEPLOY_BACKUP` | 1 | Create feedback DB backup before deploy (recommended: keep at 1) |

---

## Failsafe Features

### 1. **Multi-Level Health Checking**
- Both new deployment and rollback verify `/health` endpoint
- Failures are detected early (40 attempts over ~2 minutes)
- No silent failures

### 2. **Automatic Rollback**
- If new code fails health check, previous Git commit is checked out and rebuilt
- Existing users never see a broken site (either live app or maintenance page)
- Feedback database is protected with pre-deploy backup

### 3. **Maintenance Mode Transparency**
- Users see a clear, accessible "Under Maintenance" page
- No mysterious 5xx errors or timeout messages
- Expected timeframe is 15–30 minutes

### 4. **Manual Intervention Escalation**
- If rollback also fails, deployment exits with code 1 and descriptive error
- Admin is notified immediately and must investigate
- Server VPS emergency console (SolusVM) is always available as last-resort recovery

### 5. **Deployment Idempotency**
- Re-running `deploy-app.sh` is safe (same result each time)
- No state corruption from partial deployments
- Safe to re-trigger if network interruption occurs

---

## Monitoring & Testing

### During Deployment

```bash
# From any terminal, monitor the running deployment:
cd ~/app/web
docker compose -f docker-compose.prod.yml logs --tail 50 -f web

# In another terminal, check container health:
docker compose -f docker-compose.prod.yml ps
```

### Post-Deployment Testing

```bash
# Test main URLs (replace domain as needed):
curl -I https://lp.csedesigns.com/
curl -I https://lp.csedesigns.com/health
curl -I https://csedesigns.com/

# Check for maintenance mode (should see 503 if enabled):
curl -I https://lp.csedesigns.com/audit

# Verify health endpoint always works (200 OK):
curl -I https://lp.csedesigns.com/health
```

---

## Troubleshooting

### Deployment Hangs (Health Check Not Passing)

**Symptom:** Script shows `.` (dot) characters continuing for 2+ minutes.

**Resolution:**
1. Stop the script (Ctrl+C)
2. Check logs: `docker compose logs web --tail 50`
3. Common causes:
   - Database connection failed
   - Missing environment variable (e.g., `SECRET_KEY`)
   - Port 8000 already in use by another process
4. Fix the issue and re-run `deploy-app.sh` (automatic rollback will recover)

### Rollback Also Failed

**Symptom:** Script exits with "Rollback health check: FAILED" and exit code 1.

**Resolution:**
1. **This is rare but serious.** Manual intervention required.
2. SSH to the server as the deploy user
3. Check which commit was deployed: `git log --oneline -1`
4. Inspect container logs: `docker compose logs web --tail 100`
5. Manually restore from the pre-deploy backup (see `~/app/backups/feedback/`)
6. Once stable, commit the fix and re-deploy

### Maintenance Page Stuck Visible

**Symptom:** Deployment succeeded but users still see "Under Maintenance".

**Resolution:**
1. Manually disable maintenance mode: `bash ~/app/scripts/maintenance-mode.sh off`
2. Or wait for the next deployment (it will disable maintenance mode on success)

---

## Best Practices

1. **Always deploy during off-peak hours** (e.g., 10 PM – 6 AM)
2. **Keep pre-deploy backups enabled** (`ENABLE_PREDEPLOY_BACKUP=1`)
3. **Run deployment from a stable network** (avoid mobile hotspots)
4. **Have a terminal open with logs during deployment** (`docker compose logs -f`)
5. **Test key flows post-deployment:**
   - Upload a document to audit
   - Download an audit report
   - Check admin queue (if you have access)
6. **Announce scheduled maintenance** to users (via email, status page, etc.)

---

## Version Info

- **Deployment Script:** `/app/scripts/deploy-app.sh`
- **Maintenance Mode Toggle:** `/app/scripts/maintenance-mode.sh`
- **Docker Compose:** `/app/web/docker-compose.prod.yml`
- **Health Check Endpoint:** `GET /health` (returns `{"status": "healthy"}`)
- **Last Updated:** April 17, 2026
