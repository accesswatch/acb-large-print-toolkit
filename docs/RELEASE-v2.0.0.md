# v2.0.0 Release Summary: April 17, 2026

## Overview

GLOW Accessibility Toolkit v2.0.0 is now released with a complete overhaul of web accessibility, form state management, and a safe, failsafe deployment strategy with integrated maintenance mode.

---

## Major Additions

### 1. **Web Accessibility Complete Sweep** (224/224 tests pass)

#### Submit-State Feedback on All Long-Running Forms
- **Forms covered:** `process_form`, `template_form`, `fix_review_headings`, `admin_login`, `chat_form`, `feedback_form`, `admin_request_access`, `consent`, `whisperer_retrieve`
- **Behavior:** Submit button disables immediately on submit; `aria-live` status paragraph announces what's happening
- **Examples:**
  - "Uploading…" on file upload forms
  - "Building…" on template creation
  - "Sending…" on admin sign-in
  - "Thinking…" on chat questions

#### Download Processing State
- **Form:** `fix_result` download button
- **Behavior:** Shows "Preparing your download…" and disables for 4 seconds
- **Prevents:** Double-submission on slow connections

#### Confirmation Dialogs on Destructive Actions
- **Locations:** Admin approve/deny, admin queue cancel/re-queue, privacy consent-clear
- **Security:** User must confirm email/action to prevent accidental operations

#### Aria-Describedby on Form Inputs
- **Whisperer retrieve password** – references hint paragraph
- **Whisperer password confirm** – dedicated hint + aria-describedby
- **Improves:** Screen reader clarity and autocomplete support

#### Decorative Emoji Accessibility
- **Process_choose action icons** – wrapped with `aria-hidden="true"`
- **Chat export buttons** – wrapped decorative emoji
- **Outcome:** Screen readers hear button labels only, not emoji noise

#### Button Disabled State CSS
- **File:** `forms.css`
- **Change:** Explicit `:disabled` and `[aria-disabled="true"]` styles for `btn-primary` and `btn-secondary`
- **Benefit:** Consistent visual feedback across all browsers

#### HTTP 403 Error Handler
- **App:** `app.py`
- **Change:** New `@app.errorhandler(403)` renders styled `error.html`
- **Triggers:** Admin access denials, OAuth failures, feedback review auth
- **Consistency:** Matches 404/500 error page styling

### 2. **Maintenance Mode System** (Reusable, Failsafe)

#### Maintenance.html Template
- **Clean, accessible "Under Maintenance" page**
- **Shows:** Pulse indicator, expected timeframe, reassurance about data safety
- **Responsive:** Works on all screen sizes
- **Accessible:** WCAG 2.2 AA compliant

#### Flask Integration
- **Middleware:** `check_maintenance_mode()` in `app.py`
- **Behavior:** When `MAINTENANCE_MODE=1`, all requests (except `/health`) return 503 Service Unavailable
- **Health check always works:** Allows monitoring and deployment orchestration to continue

#### Deployment-Time Activation
- **deploy-app.sh enhanced:**
  1. **Enable maintenance mode** before Docker build starts
  2. Users see "Under Maintenance" during deployment
  3. Disable maintenance mode on successful health check
  4. Site goes live automatically when deployment succeeds
  5. If deployment fails, disable maintenance mode and rollback to previous code

#### Manual Operational Control
- **maintenance-mode.sh script:**
  - `bash ~/app/scripts/maintenance-mode.sh on` – Show maintenance page
  - `bash ~/app/scripts/maintenance-mode.sh off` – Bring site live
  - `bash ~/app/scripts/maintenance-mode.sh status` – Check current status
- **Use case:** Database migrations, security patches, manual updates without code redeployment

### 3. **Deployment Strategy** (Safe, Failsafe, Well-Documented)

#### Complete Lifecycle
1. **Pre-flight checks** – Docker, files, Git
2. **Backup feedback DB** (optional but recommended)
3. **Enable maintenance mode** – Users informed
4. **Pull latest code** from Git
5. **Build and start** Docker containers
6. **Health check** – 40 attempts over 2 minutes
7. **On success:** Disable maintenance mode → site goes live
8. **On failure:** Disable maintenance mode → rollback to previous Git commit
9. **Rollback verification** – Health check on old code
10. **Display status** – URLs to test, container logs

#### Automatic Rollback
- Previous Git commit is checked out if new deployment fails health check
- **Users never see a broken site** — they see either the live app or maintenance page
- Feedback database protected via pre-deploy backup

#### Exit Codes
- `0` – Deployment succeeded; site is live
- `1` – Pre-flight check failed (fix config and retry)
- `1` – Health check failed and rollback also failed (manual intervention needed)

#### Environment Variables
- `MAINTENANCE_MODE` – `0` (off) or `1` (on)
- `APP_ROOT`, `WEB_ROOT`, `COMPOSE_FILE` – Paths and file names
- `APP_DOMAIN`, `APP_ALIAS_DOMAIN`, `MAIN_DOMAIN` – Hostnames for test URLs
- `ENABLE_PREDEPLOY_BACKUP` – `1` (recommended) or `0`

---

## Documentation

### New Files
- **`docs/deployment-strategy.md`** – Complete deployment lifecycle, troubleshooting, best practices
- **`scripts/maintenance-mode.sh`** – Reusable maintenance mode toggle script
- **`web/src/acb_large_print_web/templates/maintenance.html`** – Maintenance page template

### Updated Files
- **`CHANGELOG.md`** – Changed from `[Unreleased]` to `[2.0.0] - 2026-04-17`
- **`scripts/deploy-app.sh`** – Enhanced with maintenance mode activation/deactivation
- **`docs/deployment.md`** – Added quick-reference links to maintenance and strategy docs
- **`.github/copilot-instructions.md`** – Updated deployment section with new tools and docs

---

## Testing

**All 224 tests pass** after maintenance mode integration:
- No Flask app functionality broken by middleware
- `/health` endpoint still works during maintenance mode
- Maintenance mode can be toggled without rebuilding containers
- All submit-state feedback forms work correctly

---

## Usage

### Standard Deployment
```bash
bash ~/app/scripts/deploy-app.sh
```
- Automatically shows maintenance page
- Deploys new code
- Disables maintenance page on success
- Automatic rollback on failure

### Manual Maintenance
```bash
# Before database migration or manual updates
bash ~/app/scripts/maintenance-mode.sh on

# After the work is done
bash ~/app/scripts/maintenance-mode.sh off

# Check status anytime
bash ~/app/scripts/maintenance-mode.sh status
```

### Monitoring During Deployment
```bash
cd ~/app/web
docker compose -f docker-compose.prod.yml logs --tail 50 -f web
```

---

## Key Features

✅ **Zero Data Loss** – Pre-deploy backup + rollback protection
✅ **Transparent to Users** – Clear "Under Maintenance" page during deployment
✅ **Automatic Recovery** – Rollback to previous code on failed health check
✅ **Reusable** – Maintenance mode can be toggled for non-deployment maintenance
✅ **Well-Documented** – Complete strategy guide + troubleshooting
✅ **Failsafe** – Multiple health checks, rollback verification, escalation to manual intervention
✅ **Accessible** – Maintenance page meets WCAG 2.2 AA; all forms have aria-live feedback
✅ **Observable** – /health endpoint works even during maintenance; monitoring systems unaffected

---

## Breaking Changes

None. This release is backward compatible. The maintenance mode is opt-in (enabled only during deployment or when explicitly toggled).

---

## Next Steps

1. **Tag the release:** `git tag -a v2.0.0 -m "Release v2.0.0: Maintenance mode + accessibility sweep"`
2. **Push to GitHub:** `git push origin main --tags`
3. **Deploy to production:** `bash ~/app/scripts/deploy-app.sh`
4. **Verify:** Test `/health`, main domain, and app domain URLs
5. **Announce to users:** Share the CHANGELOG and updated guidelines

---

## Version Info

| Component | Version | Released |
|-----------|---------|----------|
| **GLOW Toolkit** | 2.0.0 | 2026-04-17 |
| **Flask Web App** | 2.0.0 | 2026-04-17 |
| **Desktop CLI/GUI** | 2.0.0 | 2026-04-17 |
| **Documentation** | Complete & Verified | 2026-04-17 |

---

## Credits

- **ACB Guidelines Compliance:** American Council of the Blind Large Print Guidelines (Rev. May 2025)
- **WCAG Standards:** W3C WCAG 2.2 Level AA
- **Accessibility Validators:** Axe DevTools, Accessibility Insights, DAISY Ace
- **Deployment Safety:** Inspired by industry-standard blue-green deployment patterns
