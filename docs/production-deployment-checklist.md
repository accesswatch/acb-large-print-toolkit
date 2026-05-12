# GLOW 7.0.0 Production Environment Checklist

Complete this checklist before deploying GLOW to production. Each section includes validation commands and expected outcomes.

## Current Status (May 11, 2026)

Reference runbook:

- Full operator guide for collecting provider credentials and filling env values: `docs/oauth-credential-collection-runbook.md`
- Live execution tracker and go/no-go snapshot: `docs/oauth-provider-progress-tracker.md`

### Completed in this rollout session
- [x] Firebase Authentication enabled in console
- [x] Email/Password provider enabled
- [x] Google provider enabled
- [x] Authorized domain `glow.bits-acb.org` added in Firebase Auth settings
- [x] Service account key placed at `web/instance/firebase-service-account.json`
- [x] Environment path configured for Firebase credentials in `web/.env`
- [x] Firebase Admin SDK initialization smoke-tested successfully (`firebase_init_ok: True`)
- [x] Login page smoke-tested successfully (`/auth/login` returns 200)

### Remaining to finish
- [ ] Configure remaining OAuth providers you intend to ship now (GitHub required for this release; Microsoft/Apple/Auth0/WordPress optional)
- [ ] Add production OAuth callback URLs in each provider console
- [ ] End-to-end browser sign-in test on production domain (Google and GitHub minimum)
- [ ] Set production env vars on the server (do not rely on local `.env`)
- [ ] Run production deployment and post-deploy verification

### Immediate Release-Candidate Gate
- [ ] Deploy the auth-enabled release-candidate build before attempting any Firebase smoke test
- [ ] Confirm `/auth/login` exists on production and does not return `404`
- [ ] Confirm public no-login routes still work after deploy

## Phase 1: Infrastructure Prerequisites

### 1.1 Domain & DNS
- [ ] DNS A record pointing `glow.bits-acb.org` to production server IP
  - **Validate:** `nslookup glow.bits-acb.org` should resolve to your server IP
- [ ] SSL certificate installed for `glow.bits-acb.org` (Let's Encrypt recommended)
  - **Validate:** `openssl s_client -connect glow.bits-acb.org:443` shows valid cert for domain
- [ ] Certificate auto-renewal configured (if using Let's Encrypt with certbot)
  - **Validate:** `sudo certbot renew --dry-run` completes successfully

### 1.2 Server Environment
- [ ] Python 3.11+ installed
  - **Validate:** `python --version` shows 3.11+
- [ ] Node.js 18+ installed (for any frontend build tasks)
  - **Validate:** `node --version` and `npm --version`
- [ ] Docker and Docker Compose installed
  - **Validate:** `docker --version` and `docker-compose --version`
- [ ] Redis 6+ accessible (local or managed service)
  - **Validate:** `redis-cli ping` returns `PONG`
- [ ] PostgreSQL client tools available
  - **Validate:** `psql --version` shows psql 12+

### 1.3 Firewall & Network
- [ ] Port 80 (HTTP) open for Let's Encrypt renewal and redirects
- [ ] Port 443 (HTTPS) open for production traffic
- [ ] Port 5000 (Flask app) only accessible internally (not public)
- [ ] Port 6379 (Redis) only accessible internally
- [ ] Port 5432 (PostgreSQL) only accessible from app server

## Phase 2: Neon PostgreSQL Setup

### 2.1 Neon Provisioning
- [ ] Neon account created at https://neon.tech/
- [ ] Neon project created with name `glow-prod`
- [ ] Database created (e.g., `glow` or `production`)
- [ ] Connection string obtained in format: `postgresql://user:pass@host/db?sslmode=require`

### 2.2 Neon Configuration
- [ ] SSL mode enabled (default)
  - **Validate:** Connection string includes `sslmode=require`
- [ ] Connection pool size set to 5
- [ ] Max overflow set to 10
- [ ] Automated backups enabled in Neon dashboard
- [ ] Branch-based dev/test environment created (optional but recommended)

### 2.3 Production .env Variables
```bash
# Neon PostgreSQL (REQUIRED)
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
DB_SSLMODE=require
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_APP_NAME=glow-web
```

**Validate:**
```bash
# Test connection (from server):
psql $DATABASE_URL -c "SELECT version();"
# Should return PostgreSQL version without SSL errors
```

## Phase 3: Firebase Setup

### 3.1 Firebase Project Provisioning
- [ ] Firebase project created at https://console.firebase.google.com/
- [ ] Web app registered in Firebase Console
- [ ] Service account key downloaded and stored securely

### 3.2 Firebase Authentication Configuration
- [ ] Email/Password authentication enabled
- [ ] Email link (passwordless) authentication enabled
- [ ] Google OAuth provider configured
- [ ] GitHub OAuth provider configured
- [ ] Microsoft (Entra) OAuth provider configured
- [ ] Apple Sign In configured
- [ ] Auth0 tenant configured (if using)
- [ ] WordPress OAuth plugin configured (if using)

### 3.3 Firebase Authorized Domains
In Firebase Console → Authentication → Settings:
- [ ] `glow.bits-acb.org` added to authorized domains
- [ ] `localhost` added for local development (optional)

### 3.4 OAuth Provider Configuration

#### Google
- [ ] Client ID obtained from Google Cloud Console
- [ ] Client Secret obtained
- [ ] Callback URL registered: `https://glow.bits-acb.org/auth/oauth/google/callback`
- [ ] OAuth scopes include email and profile

#### GitHub
- [ ] OAuth app created at https://github.com/settings/developers
- [ ] Client ID and secret obtained
- [ ] Authorization callback URL: `https://glow.bits-acb.org/auth/oauth/github/callback`

#### Microsoft
- [ ] App registration created in Azure Portal
- [ ] Client ID and secret obtained
- [ ] Redirect URI registered: `https://glow.bits-acb.org/auth/oauth/microsoft/callback`
- [ ] Email scope included in manifest

#### Apple
- [ ] Apple Services ID created (not App ID)
- [ ] Return URL registered: `https://glow.bits-acb.org/auth/oauth/apple/callback`
- [ ] Client secret generated

#### Auth0 (if used)
- [ ] Auth0 tenant URL set
- [ ] Client ID and secret obtained
- [ ] Application callback URL: `https://glow.bits-acb.org/auth/oauth/auth0/callback`

### 3.4.1 Fast Credential Collection Runbook (Apple, Microsoft, Auth0)

Use the centralized runbook for complete provider steps (all providers, production + local templates): `docs/oauth-credential-collection-runbook.md`

Use this section when you need to gather provider credentials quickly in one pass.

#### Microsoft Entra ID (Azure AD)

- Portal: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade
- Action:
  - Create or open app registration for GLOW
  - Add redirect URI (Web): `https://glow.bits-acb.org/auth/oauth/microsoft/callback`
  - Add local redirect URI (optional): `http://localhost:5000/auth/oauth/microsoft/callback`
  - Generate client secret under Certificates & secrets
  - Ensure delegated permissions include `openid`, `profile`, `email`
- Copy into env:
  - `MICROSOFT_CLIENT_ID=<Application (client) ID>`
  - `MICROSOFT_CLIENT_SECRET=<new client secret value>`
  - `MICROSOFT_TENANT_ID=common` (or your tenant ID if single-tenant)

#### Apple Sign In

- Apple Developer portal: https://developer.apple.com/account/
- Action:
  - Create/open a Services ID (web sign-in)
  - Configure Sign in with Apple return URL: `https://glow.bits-acb.org/auth/oauth/apple/callback`
  - Add local return URL (optional): `http://localhost:5000/auth/oauth/apple/callback`
  - Create/sign a client secret JWT for the Services ID
- Copy into env:
  - `APPLE_CLIENT_ID=<Services ID>`
  - `APPLE_CLIENT_SECRET=<signed JWT client secret>`

#### Auth0

- Auth0 dashboard: https://manage.auth0.com/dashboard/
- Action:
  - Create/open a Regular Web Application
  - Allowed Callback URLs: `https://glow.bits-acb.org/auth/oauth/auth0/callback`
  - Add local callback (optional): `http://localhost:5000/auth/oauth/auth0/callback`
  - Ensure app returns `email` claim
- Copy into env:
  - `AUTH0_CLIENT_ID=<client id>`
  - `AUTH0_CLIENT_SECRET=<client secret>`
  - `AUTH0_DOMAIN=<tenant>.auth0.com`

> Note: Firebase Auth does not expose Auth0 as a first-class provider in standard mode. For Firebase-console-based Auth0/OIDC you need Firebase Identity Platform upgrade. App-level Auth0 via `/auth/oauth/auth0` works without that upgrade.

#### WordPress (if used)
- [ ] OAuth Server plugin installed on WordPress
- [ ] Client ID and secret obtained
- [ ] Callback URL registered: `https://glow.bits-acb.org/auth/oauth/wordpress/callback`

### 3.5 Production .env Variables
```bash
# Firebase (REQUIRED)
FIREBASE_AUTH_ENABLED=1
FIREBASE_WEB_API_KEY=<your-web-api-key>
FIREBASE_AUTH_DOMAIN=<project>.firebaseapp.com
FIREBASE_PROJECT_ID=<your-project-id>
FIREBASE_APP_ID=<your-app-id>
GOOGLE_APPLICATION_CREDENTIALS=instance/firebase-service-account.json
FIREBASE_CREDENTIALS_PATH=instance/firebase-service-account.json

# OAuth Providers
GOOGLE_CLIENT_ID=<id>
GOOGLE_CLIENT_SECRET=<secret>

GITHUB_CLIENT_ID=<id>
GITHUB_CLIENT_SECRET=<secret>

MICROSOFT_CLIENT_ID=<id>
MICROSOFT_CLIENT_SECRET=<secret>
MICROSOFT_TENANT_ID=common

APPLE_CLIENT_ID=<id>
APPLE_CLIENT_SECRET=<secret>

AUTH0_CLIENT_ID=<id>
AUTH0_CLIENT_SECRET=<secret>
AUTH0_DOMAIN=<your-tenant>.auth0.com

WORDPRESS_CLIENT_ID=<id>
WORDPRESS_CLIENT_SECRET=<secret>
WORDPRESS_BASE_URL=https://<your-wordpress-site>
```

**Validate:**
```bash
# Test Firebase initialization:
cd /app
python -c "from firebase_admin import initialize_app; initialize_app(); print('✓ Firebase initialized')"
```

## Phase 4: Role-Based Access Control (RBAC)

### 4.1 RBAC Configuration
- [ ] Initial admin(s) identified
- [ ] `SUPER_ADMIN_BOOTSTRAP_EMAILS` set in production `.env` for the first privileged user
  - Example: `SUPER_ADMIN_BOOTSTRAP_EMAILS=jeff@jeffbishop.com`
- [ ] `ADMIN_BOOTSTRAP_EMAILS` set only if you want additional bootstrap admins
  - Example: `ADMIN_BOOTSTRAP_EMAILS=alice@example.com,bob@example.com`

### 4.2 Database Schema
- [ ] Neon database has `users` table with columns:
  - `role` (VARCHAR, default 'user')
  - `promotion_request_status` (VARCHAR, nullable)
  - `promotion_request_reason` (VARCHAR, nullable)
  - `promotion_requested_at` (TIMESTAMP, nullable)
  - `promotion_reviewed_at` (TIMESTAMP, nullable)
  - `promotion_reviewed_by_id` (INTEGER, FK to users.id, nullable)

**Validate:**
```bash
# From app container:
python -c "from app import db; db.create_all(); print('✓ Schema created')"
```

### 4.3 Email Configuration
- [ ] Email provider configured (SMTP or SendGrid/etc.)
  - **For SMTP:**
    ```bash
    EMAIL_CONFIGURED=1
    MAIL_SERVER=smtp.gmail.com
    MAIL_PORT=587
    MAIL_USE_TLS=1
    MAIL_USERNAME=<your-email>
    MAIL_PASSWORD=<app-password>
    ```
  - **For SendGrid:**
    ```bash
    EMAIL_CONFIGURED=1
    SENDGRID_API_KEY=<your-api-key>
    ```

**Validate:**
```bash
# From app, test email sending:
python -c "from app.email import send_email; send_email(to='test@example.com', subject='Test', html='<p>Test</p>'); print('✓ Email sent')"
```

## Phase 5: Application Configuration

### 5.1 Core Variables
```bash
# Flask
SECRET_KEY=<generate-with: python -c "import secrets; print(secrets.token_hex(32))">
LOG_LEVEL=INFO
SESSION_TIMEOUT_MINUTES=240

# Celery + Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
REDIS_HOST=redis
REDIS_PORT=6379
```

### 5.2 Feature Flags
- [ ] Feature flags initialized in `/instance/feature_flags.json`
- [ ] Celery task queue enabled
- [ ] Firebase authentication enabled
- [ ] RBAC enabled (no override env vars needed; should be default)

**Validate:**
```bash
# From app container:
python -c "from app.feature_flags import get_all_flags; print(get_all_flags())"
```

### 5.3 Production Docker Compose
- [ ] `docker-compose.prod.yml` includes:
  - Flask web service with all env vars
  - Celery worker service with same env vars
  - Redis service with persistent volume
  - All services on same network
  - Proper restart policies

**Validate:**
```bash
cd /app
docker-compose -f docker-compose.prod.yml config | grep -E "(services:|environment:)" | head -20
```

## Phase 6: Deployment & Validation

### 6.1 Pre-Deployment Backup
- [ ] Neon database backed up (automated by Neon)
- [ ] Any critical files backed up to external storage

### 6.2 Application Deployment
- [ ] Docker images built with all production tags
- [ ] Docker Compose services started: `docker-compose -f docker-compose.prod.yml up -d`
- [ ] Services are healthy: `docker-compose -f docker-compose.prod.yml ps`

**Validate:**
```bash
# All services should show "Up" status
docker-compose -f docker-compose.prod.yml ps
```

### 6.3 Application Health Checks
- [ ] App health endpoint responds: `curl https://glow.bits-acb.org/health`
  - Should return `200 OK`
- [ ] Database connectivity verified: `curl https://glow.bits-acb.org/health` (includes DB check)
- [ ] Celery worker is running and healthy
  - Check logs: `docker-compose -f docker-compose.prod.yml logs worker | tail -20`

### 6.4 Authentication Flows
- [ ] **Email/Password Login:** Test at `/auth/login` with test account
- [ ] **Firebase Email Link:** Request passwordless link, verify email delivery
- [ ] **Google OAuth:** Test OAuth flow redirects to Google and back
- [ ] **GitHub OAuth:** Test GitHub OAuth flow
- [ ] **Microsoft OAuth:** Test Entra ID flow
- [ ] **Apple Sign In:** Test Apple OAuth flow
- [ ] **First Super Admin Bootstrap:** `jeff@jeffbishop.com` receives `super_admin` on first successful login
- [ ] **Admin Bootstrap:** Verify `ADMIN_BOOTSTRAP_EMAILS` users get admin role on first login

### 6.5 RBAC & Admin Workflow
- [ ] First super admin logs in and receives `role='super_admin'` automatically
- [ ] Admin can access `/admin/promotions` and `/admin/users`
- [ ] Regular user can request promotion at `/user/request-promotion`
- [ ] Admin receives email notification for promotion request
- [ ] Admin can approve/reject from `/admin/promotions` or via email link
- [ ] User receives approval/rejection email notification
- [ ] Approved user's role updated to `admin` in database
- [ ] User can now access admin routes after session refresh

### 6.5.1 Public No-Login Regression Check
- [ ] In a fresh browser session, confirm consent flow still works without sign-in
- [ ] Verify `/process/`, `/audit/`, `/fix/`, `/convert/`, and `/template/` remain usable without an account
- [ ] Verify the About page states that accounts are optional and privacy-first

### 6.6 Email Delivery
- [ ] Test email delivery (use `/feedback` or admin interface to send test email)
- [ ] Promotion request email delivered to admin
- [ ] Approval notification email delivered to user
- [ ] Email template renders correctly (check HTML layout)
- [ ] Links in emails are correctly formatted with domain

### 6.7 Async Job Queue
- [ ] Document conversion dispatches to async job
- [ ] Job appears in `/admin/queue` with correct status
- [ ] Progress updates via SSE or polling
- [ ] Completed jobs show results on `/job/<job_id>`
- [ ] Failed jobs appear with error details

### 6.8 Data Security
- [ ] Database connections use SSL: `psql $DATABASE_URL -c "SELECT ssl_version();"` should return a version
- [ ] OAuth provider keys are encrypted at rest (Fernet encryption)
- [ ] No credentials logged or exposed in error messages

**Validate:**
```bash
# Check for secrets in logs:
docker-compose -f docker-compose.prod.yml logs app | grep -i "password\|secret\|key" | grep -v "SECRET_KEY=" | head -5
# Should be empty or only contain logging setup, not actual values
```

## Phase 7: Monitoring & Rollback Plan

### 7.1 Monitoring Setup
- [ ] Application logs aggregated and searchable
- [ ] Error tracking configured (e.g., Sentry, Rollbar)
- [ ] Database metrics monitored (Neon dashboard)
- [ ] Redis memory usage monitored
- [ ] Celery job queue depth monitored

### 7.2 Rollback Procedure
- [ ] Rollback documented and tested
- [ ] Previous Docker images tagged and stored
- [ ] Database backup tested and verified restorable
- [ ] Rollback procedure: `docker-compose -f docker-compose.prod.yml down; docker-compose -f docker-compose.prod.yml pull <previous-tag>; docker-compose -f docker-compose.prod.yml up -d`

### 7.3 Health Check Automation
- [ ] Monitoring tool configured to check `/health` endpoint every 60 seconds
- [ ] Alert threshold set if health checks fail 2+ times
- [ ] On-call runbook documented for common failures

## Phase 8: Final Validation

### 8.1 Smoke Tests
- [ ] User can sign up with email
- [ ] User can log in with email/password
- [ ] User can log in with OAuth (test at least one provider)
- [ ] User can access document auditing
- [ ] User can initiate document conversion (async job)
- [ ] User can request admin promotion
- [ ] Admin can review and approve promotions
- [ ] Admin dashboard shows accurate user list and roles

### 8.2 Security Scan
- [ ] SSL/TLS certificate is valid and trusted
  - Validate: `openssl s_client -connect glow.bits-acb.org:443 < /dev/null 2>/dev/null | grep "Verify return code"`
  - Should show "Verify return code: 0 (ok)"
- [ ] No HTTP traffic (all redirected to HTTPS)
- [ ] Security headers present (CSP, X-Frame-Options, etc.)
- [ ] OWASP Top 10 scan passed (optional but recommended)

### 8.3 Load Test (Light)
- [ ] Simulate 10 concurrent users for 5 minutes
- [ ] All requests complete successfully
- [ ] No errors or timeouts
- [ ] Response times acceptable (<2s for page loads)

### 8.4 Documentation Verification
- [ ] `/guide` page loads and renders correctly
- [ ] `/changelog` shows 7.0.0 release notes
- [ ] Help links in error messages point to correct documentation

## Phase 9: Deployment Sign-Off

- [ ] All checkboxes above completed and verified
- [ ] Deployment date: _______________
- [ ] Deployed by: _______________
- [ ] Reviewed by: _______________
- [ ] Rollback plan approved: ☐ Yes ☐ No
- [ ] 24-hour on-call rotation established: ☐ Yes ☐ No
- [ ] Team trained on operation and troubleshooting: ☐ Yes ☐ No

---

## Troubleshooting

### App won't start
1. Check logs: `docker-compose -f docker-compose.prod.yml logs app | tail -50`
2. Verify all environment variables set: `docker-compose -f docker-compose.prod.yml config | grep -A 50 "environment:"`
3. Verify Neon connectivity: `docker-compose -f docker-compose.prod.yml exec app psql $DATABASE_URL -c "SELECT 1;"`

### Firebase login not working
1. Check Firebase credentials in `.env`
2. Verify authorized domains in Firebase Console
3. Check logs for auth errors: `docker-compose -f docker-compose.prod.yml logs app | grep -i firebase`

### Emails not sending
1. Check email configuration in `.env`
2. Test SMTP connection: `docker-compose -f docker-compose.prod.yml exec app python -c "..."`
3. Check spam folder (Gmail, etc.)

### Celery jobs not processing
1. Check worker is running: `docker-compose -f docker-compose.prod.yml ps worker`
2. Check worker logs: `docker-compose -f docker-compose.prod.yml logs worker | tail -50`
3. Verify Redis connectivity: `docker-compose -f docker-compose.prod.yml exec worker redis-cli ping`

---

## Post-Deployment

- [ ] Monitor logs for 24 hours for any errors
- [ ] Check daily active users and engagement metrics
- [ ] Collect user feedback and issues
- [ ] Schedule post-launch retrospective
