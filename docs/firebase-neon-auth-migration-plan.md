## Getting Started: Provisioning Neon and Firebase (Account Setup & Authentication Types)

Reference runbook:

- Full provider credential collection and env templates (production + local): `docs/oauth-credential-collection-runbook.md`

Before beginning any migration or configuration, you must have both Neon (PostgreSQL) and Firebase (Google Cloud) projects set up and ready. This section covers how to apply for, provision, and configure both services, including authentication types and key setup decisions.

### 1. Neon (PostgreSQL) Setup

- **Sign up:** Go to https://neon.tech/ and create a free account (supports GitHub, Google, or email sign-in).
- **Create a Project:** After logging in, create a new Neon project. Choose a project name and region close to your users.
- **Create a Database:** Each project can have one or more databases. Create a database (e.g., `glow` or `production`).
- **Get Connection String:** In the Neon dashboard, copy the PostgreSQL connection string (format: `postgresql://<user>:<password>@<host>/<db>?sslmode=require`).
- **Neon API Key (provided for MCP/client integration):** `napi_l61x9cksx0tb462ymy0wftrrc5rqfr5iwzo7zrv6q7bdt5bx471bjtn3jix7ta1k`
- **Roles & Access:** By default, Neon creates an admin user. For production, create a dedicated app user with a strong password and least-privilege access.
- **SSL:** Neon requires SSL connections. The default connection string includes `sslmode=require`.
- **Backups:** Neon provides automatic backups and branching. Review backup/restore options in the dashboard.

#### Neon API Key Backup Record

- **Primary key (active):** `napi_l61x9cksx0tb462ymy0wftrrc5rqfr5iwzo7zrv6q7bdt5bx471bjtn3jix7ta1k`
- **Stored in this runbook for recovery:** Yes
- **Last updated:** 2026-05-11
- **Usage:** MCP client authentication and Neon API operations
- **Rotation note:** Rotate this key immediately if this file is shared outside trusted operators.

### 2. Firebase Project Setup

- **Sign up:** Go to https://console.firebase.google.com/ and sign in with a Google account.
- **Create a Project:** Click “Add project” and follow the prompts. Name your project (e.g., `glow-prod`).
- **Enable Authentication:** In the Firebase console, go to “Authentication” > “Get started.”
	- **Providers:** Enable the authentication providers you want (Email/Password, Google, Microsoft, GitHub, etc.).
	- **Admin Approval:** For admin login, you can restrict access by email domain or explicit email allowlist (see `ADMIN_BOOTSTRAP_EMAILS`).
- **Service Account Key:** Go to “Project settings” > “Service accounts” > “Generate new private key.” Download the JSON file and store it securely (e.g., `/app/instance/firebase-service-account.json`).
- **Web Client Config:** In “Project settings” > “General,” register a web app. Copy the Web API Key, Auth Domain, App ID, and Project ID for client-side config.
- **Security:** Restrict service account key access. Rotate keys periodically. Never commit keys to source control.

### 3. Authentication Types Supported

- **End-User Authentication:**
	- Firebase Authentication (recommended): Supports Google, Microsoft, GitHub, Email/Password, and more.
	- Legacy OAuth/email/password: Retained as fallback during migration.
- **Admin Authentication:**
	- Firebase Authentication with approval gating (recommended): Only approved emails can access admin routes.
	- Legacy admin login: Supported during transition; can be disabled after cutover.
- **Account Linking:**
	- When a user signs in with Firebase, their account is linked to a local profile. Existing users can migrate by signing in with the same email.

### 3.1 Selected Provider Set (Recommended Baseline)

For your target setup, enable all of the following:

1. Email/Password
2. Passwordless Email Link
3. Google
4. GitHub
5. Microsoft (Entra ID)
6. Apple
7. Auth0
8. WordPress OAuth Server

#### Required App Environment Variables (OAuth + Firebase)

```env
# Firebase auth switch + web client config
FIREBASE_AUTH_ENABLED=1
FIREBASE_WEB_API_KEY=<firebase-web-api-key>
FIREBASE_AUTH_DOMAIN=<project>.firebaseapp.com
FIREBASE_APP_ID=<firebase-app-id>
FIREBASE_PROJECT_ID=<firebase-project-id>

# OAuth providers shown on /auth/login
GOOGLE_CLIENT_ID=<google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<google-oauth-client-secret>

GITHUB_CLIENT_ID=<github-oauth-client-id>
GITHUB_CLIENT_SECRET=<github-oauth-client-secret>

MICROSOFT_CLIENT_ID=<microsoft-app-client-id>
MICROSOFT_CLIENT_SECRET=<microsoft-app-client-secret>
MICROSOFT_TENANT_ID=common

APPLE_CLIENT_ID=<apple-services-id>
APPLE_CLIENT_SECRET=<apple-client-secret>

# Optional providers: Auth0 + WordPress OAuth Server
AUTH0_CLIENT_ID=<auth0-client-id>
AUTH0_CLIENT_SECRET=<auth0-client-secret>
AUTH0_DOMAIN=<your-tenant>.auth0.com

WORDPRESS_CLIENT_ID=<wordpress-oauth-client-id>
WORDPRESS_CLIENT_SECRET=<wordpress-oauth-client-secret>
WORDPRESS_BASE_URL=https://<your-wordpress-site>
WORDPRESS_OAUTH_LABEL=WordPress
```

#### OAuth Callback URLs to Register

Set these redirect URIs in each provider console:

- `https://<your-domain>/auth/oauth/google/callback`
- `https://<your-domain>/auth/oauth/github/callback`
- `https://<your-domain>/auth/oauth/microsoft/callback`
- `https://<your-domain>/auth/oauth/apple/callback`
- `https://<your-domain>/auth/oauth/auth0/callback`
- `https://<your-domain>/auth/oauth/wordpress/callback`

For local development:

- `http://localhost:5000/auth/oauth/google/callback`
- `http://localhost:5000/auth/oauth/github/callback`
- `http://localhost:5000/auth/oauth/microsoft/callback`
- `http://localhost:5000/auth/oauth/apple/callback`
- `http://localhost:5000/auth/oauth/auth0/callback`
- `http://localhost:5000/auth/oauth/wordpress/callback`

#### Firebase Console Provider Setup

- Enable **Email/Password** in Firebase Authentication providers.
- Enable **Email link (passwordless sign-in)** in Firebase Authentication providers.
- Enable **Google** in Firebase Authentication providers.
- Enable **GitHub** and set GitHub OAuth client ID/secret in Firebase.
- Enable **Microsoft** and set Microsoft OAuth client ID/secret and tenant settings in Firebase.
- Enable **Apple** and set Apple Services ID / key material in Firebase.

#### Passwordless Email Link Setup

- In Firebase Authentication, enable **Email link (passwordless sign-in)**.
- Set authorized domains in Firebase Auth settings to include your production domain.
- Verify outbound email delivery settings and template branding in Firebase.
- Keep Email/Password enabled as a fallback during rollout.

#### Apple Provider Setup

- Create an Apple Services ID for web sign-in.
- Configure return/callback URL to `/auth/oauth/apple/callback`.
- Generate Apple client secret and set `APPLE_CLIENT_ID` and `APPLE_CLIENT_SECRET`.
- Ensure email scope is enabled so account linking can use verified email.

#### Auth0 Provider Setup

- Create an Auth0 regular web application.
- Set callback URL to `/auth/oauth/auth0/callback` on your domain.
- Set `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`, and `AUTH0_DOMAIN`.
- Ensure Auth0 returns `email` in user profile claims.

#### Fast Credential Collection Runbook (Apple, Microsoft, Auth0)

Use these direct links to gather IDs/secrets quickly.

##### Microsoft Entra ID

- Portal: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade
- Add redirect URIs:
	- `https://glow.bits-acb.org/auth/oauth/microsoft/callback`
	- `http://localhost:5000/auth/oauth/microsoft/callback` (optional local dev)
- Copy values into env:
	- `MICROSOFT_CLIENT_ID=<Application (client) ID>`
	- `MICROSOFT_CLIENT_SECRET=<new client secret value>`
	- `MICROSOFT_TENANT_ID=common` (or specific tenant)

##### Apple Sign In

- Apple Developer: https://developer.apple.com/account/
- Create/configure Services ID return URLs:
	- `https://glow.bits-acb.org/auth/oauth/apple/callback`
	- `http://localhost:5000/auth/oauth/apple/callback` (optional local dev)
- Copy values into env:
	- `APPLE_CLIENT_ID=<Services ID>`
	- `APPLE_CLIENT_SECRET=<signed JWT client secret>`

##### Auth0

- Dashboard: https://manage.auth0.com/dashboard/
- Create/open Regular Web Application
- Set callbacks:
	- `https://glow.bits-acb.org/auth/oauth/auth0/callback`
	- `http://localhost:5000/auth/oauth/auth0/callback` (optional local dev)
- Copy values into env:
	- `AUTH0_CLIENT_ID=<client id>`
	- `AUTH0_CLIENT_SECRET=<client secret>`
	- `AUTH0_DOMAIN=<tenant>.auth0.com`

> Note: For Firebase-console-based Auth0/OIDC integration you need Firebase Identity Platform upgrade. App-level Auth0 (`/auth/oauth/auth0`) does not require that upgrade.

#### WordPress OAuth Provider Setup

- Install/configure a WordPress OAuth Server plugin on your WordPress instance.
- Set callback URL to `/auth/oauth/wordpress/callback` on your domain.
- Set `WORDPRESS_CLIENT_ID`, `WORDPRESS_CLIENT_SECRET`, and `WORDPRESS_BASE_URL`.
- Optionally set `WORDPRESS_OAUTH_LABEL` for custom button text in UI.

### 4. Summary: What You Need Before Proceeding

- Neon project and database provisioned, with connection string and credentials.
- Firebase project created, authentication providers enabled, service account key downloaded, and web client config values ready.
- Decision on which authentication providers to enable for end users and admins.
- Secure storage for all credentials and keys (never in source control).

---
## Neon Cutover and Decommission Process

### Objective
Migrate existing SQLite-backed runtime data to Neon PostgreSQL and reduce server complexity by decommissioning legacy local DB tooling where safe.

### Applies To
- `instance/ai_quota.db`
- `instance/feedback.db`
- `instance/visitor_counter.db`
- `instance/feature_flags.db`
- legacy installs may also include `instance/glow_users.db` and `instance/admin_auth.db`

### Prerequisites
- Neon database provisioned
- `DATABASE_URL` available
- App dependencies installed (`psycopg`, `SQLAlchemy` via `flask-sqlalchemy`)
- Maintenance window scheduled

### Step 1: Backup Existing Instance Data

```bash
mkdir -p backups
cp -r instance backups/instance-backup-$(date +%Y%m%d-%H%M%S)
```

### Step 2: Point App to Neon

Set environment variables:

```env
DATABASE_URL=postgresql://<user>:<password>@<host>/<db>?sslmode=require
DB_SSLMODE=require
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_APP_NAME=glow-web
```

### Step 3: Run Migration Script

Dry run with existing files list:

```bash
python scripts/migrate_sqlite_to_neon.py --instance-dir instance --target-url "$DATABASE_URL"
```

If re-running into existing rows and you want a clean replacement:

```bash
python scripts/migrate_sqlite_to_neon.py --instance-dir instance --target-url "$DATABASE_URL" --truncate
```

Optional explicit file list (recommended if your runtime has mixed legacy/new DBs):

```bash
python scripts/migrate_sqlite_to_neon.py --instance-dir instance --target-url "$DATABASE_URL" --files ai_quota.db feedback.db visitor_counter.db feature_flags.db glow_users.db admin_auth.db --truncate
```

### Step 4: Validate Data in Neon

Check expected tables and row counts for:
- user/profile/auth tables
- admin auth/request tables
- feature flags tables

Then smoke test app routes:
- `/auth/login`
- `/admin/login`
- `/settings`
- any route reading feature flags

### Step 5: Enable Queue + Worker (Optional but Recommended)

Use production compose with Redis + worker:

```bash
cd web
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 6: Decommission Legacy Local DB Tooling

After at least one successful release cycle on Neon:

1. Stop app containers
2. Archive old SQLite files from `instance/`
3. Remove old files from active runtime directory
4. Restart app and verify no file-based DB recreation is occurring

Suggested archive command:

```bash
mkdir -p backups/decommissioned-sqlite
mv instance/*.db backups/decommissioned-sqlite/
```

### Step 7: Keep Rollback Ready

Rollback is immediate:
- unset `DATABASE_URL`
- restore SQLite files from backup
- restart app

### Notes on Admin Auth
Current admin auth process now supports Firebase token sign-in and still keeps approval gates. If you continue to use legacy admin login methods during transition, keep `admin_auth.db` available until fully decommissioned. Newer installs may not have this file.

### Remaining Neon Setup (Server-Side)

If local verification is already done, these are the only remaining Neon tasks for production cutover:

1. Set production runtime env values (`DATABASE_URL`, `DB_SSLMODE`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_APP_NAME`) on the live host.
2. Run the migration script on the live host against the live `instance/` directory.
3. Validate row counts in Neon for `ai_cost_ledger`, `ai_quota_sessions`, `flags`, `feedback`, and `counter`.
4. Restart app services and verify `/auth/login`, `/admin/login`, and `/settings` against Neon-backed runtime.
5. Keep an instance backup for rollback before removing local SQLite files.

### Recommended Post-Cutover Tasks
- Add Alembic migrations for schema versioning
- Add CI check that `DATABASE_URL` is postgres in production
- Add startup health check for DB connectivity
- Add nightly Neon backups and restore drill
# Firebase + Neon Migration Plan (Execution + Developer Setup)

## Goal
Move GLOW authentication and profile storage to a production-ready architecture that supports:

- Firebase authentication for end users and admin users
- Neon PostgreSQL as the primary persistence layer
- Existing OAuth/email/password flows retained as fallback during rollout
- Privacy-first storage controls and encryption for sensitive keys

## Quick Status (7.0.0)

Implemented and ready to validate end-to-end:

- Async job infrastructure with worker-backed jobs, polling, and SSE status streaming
- Firebase-backed end-user login and admin login (approval gate preserved)
- Neon-ready SQLAlchemy DB integration with SQLite fallback for local recovery
- Account/privacy controls with encrypted provider-key persistence
- SQLite-to-Neon migration script and cutover/decommission runbook
- MCP workspace configuration for Firebase + Neon
- Project-level Agent Skills for Firebase + Neon workflows
- **NEW:** Complete role-based access control (RBAC) with admin promotion workflow

## Role-Based Access Control (RBAC) & Admin Management

GLOW 7.0.0 introduces a complete role-based access control system to manage user permissions and admin lifecycle. Every user account has a role that determines what operations they can perform.

### Role Hierarchy

Three core roles (ordered from least to most privileged):

| Role | Privilege Level | Capabilities |
|------|-----------------|--------------|
| **USER** | 1 (default) | Document auditing, conversion, personal account settings, privacy controls |
| **ADMIN** | 2 | User management, promotion approval, system settings, admin dashboard |
| **SUPER_ADMIN** | 3 | Unrestricted access, dangerous operations, direct role elevation/demotion |

### Admin Promotion Workflow

**For end-users requesting promotion to admin:**

1. **User Request** → `POST /user/request-promotion`
   - User submits reason for admin promotion
   - Status set to `pending`
   - Admins notified via email (if configured)

2. **Admin Review** → `GET /admin/promotions`
   - Existing admins view all pending requests
   - Review user's reason and account history

3. **Admin Approval** → `POST /admin/promotions/<user_id>/approve`
   - Admin approves promotion to `admin` role
   - User notified via email
   - User can now access admin routes

4. **Admin Rejection** → `POST /admin/promotions/<user_id>/reject`
   - Admin can reject with optional reason
   - User notified and can reapply later

**For super_admins managing roles directly:**

- `POST /admin/users/<user_id>/promote` — Direct promotion to admin/super_admin
- `POST /admin/users/<user_id>/demote` — Direct demotion to lower role
- `GET /admin/users` — View all users and their roles

### Initial Admin Setup

#### Bootstrap Admin (Recommended)

Set `SUPER_ADMIN_BOOTSTRAP_EMAILS` for the very first privileged operator when there are no users yet. Use `ADMIN_BOOTSTRAP_EMAILS` only for additional bootstrap admins who should not be full super admins.

Recommended first-account bootstrap for production:

```bash
export SUPER_ADMIN_BOOTSTRAP_EMAILS=jeff@jeffbishop.com
```

Additional admin bootstrap list:

```bash
export ADMIN_BOOTSTRAP_EMAILS=alice@example.com,bob@example.com
```

#### Production Deployment Checklist

- [ ] `SUPER_ADMIN_BOOTSTRAP_EMAILS` set with the first super admin
- [ ] `ADMIN_BOOTSTRAP_EMAILS` set only for any additional admin-only users
- [ ] `DATABASE_URL` pointing to production Neon instance
- [ ] `FIREBASE_AUTH_ENABLED=1` and Firebase credentials configured
- [ ] Role columns exist in `users` table (auto-created by SQLAlchemy)
- [ ] First super admin logs in and receives super_admin role
- [ ] Admin tests promotion approval workflow
- [ ] All `/admin/` routes require `@require_admin` or `@require_super_admin`

### Core Admin Routes

| Route | Method | Role | Purpose |
|-------|--------|------|---------|
| `/user/request-promotion` | GET/POST | USER | Submit request to become admin |
| `/admin/promotions` | GET | ADMIN+ | View pending promotion requests |
| `/admin/promotions/<id>/approve` | POST | ADMIN+ | Approve a promotion request |
| `/admin/promotions/<id>/reject` | POST | ADMIN+ | Reject a promotion request |
| `/admin/users` | GET | ADMIN+ | List all users and roles |
| `/admin/users/<id>/promote` | POST | SUPER_ADMIN | Direct promotion |
| `/admin/users/<id>/demote` | POST | SUPER_ADMIN | Direct demotion |

Existing admin routes (`/admin/login`, `/admin/queue`, `/admin/settings`, etc.) also enforce `@require_admin`.

Known caveats (handled in this runbook):

- Some `npx add-mcp` flows require interactive TTY and can fail in non-interactive shells
- `npx skills update --all` may report failed updates even when installed skills remain usable

## Operator Runbook (Step-by-Step, No Gaps)

Use this exact sequence. Do not skip phase gates.

### Phase 0: Preconditions and Backup Gate

1. Confirm toolchain:

```powershell
node -v
npm -v
npx -v
python --version
```

2. Create an instance backup before any migration work:

```powershell
New-Item -ItemType Directory -Force -Path backups | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item -Recurse -Force instance "backups/instance-backup-$stamp"
```

3. Gate check:

- PASS if backup directory exists and contains the `instance` snapshot.
- FAIL if backup step is incomplete. Stop here.

### Phase 1: Environment Configuration Gate

1. Update `web/.env` with Neon settings:

```env
DATABASE_URL=postgresql://<user>:<password>@<host>/<db>?sslmode=require
DB_SSLMODE=require
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_APP_NAME=glow-web
NEON_API_KEY=napi_l61x9cksx0tb462ymy0wftrrc5rqfr5iwzo7zrv6q7bdt5bx471bjtn3jix7ta1k
```

2. Update `web/.env` with Firebase server settings:

```env
FIREBASE_AUTH_ENABLED=1
FIREBASE_PROJECT_ID=glow-754e6
FIREBASE_CREDENTIALS_PATH=/app/instance/firebase-service-account.json
FIREBASE_ADMIN_AUTH_ENABLED=1
SUPER_ADMIN_BOOTSTRAP_EMAILS=jeff@jeffbishop.com
ADMIN_BOOTSTRAP_EMAILS=
```

3. Update `web/.env` with Firebase web client settings:

```env
FIREBASE_WEB_API_KEY=AIzaSyBPiunXUVRgZ6PWolckiRPA6UEeewspE1c
FIREBASE_AUTH_DOMAIN=glow-754e6.firebaseapp.com
FIREBASE_APP_ID=1:42316874705:web:65a067c3dad4db789bd6f0
FIREBASE_PROJECT_ID=glow-754e6
FIREBASE_MESSAGING_SENDER_ID=42316874705
FIREBASE_STORAGE_BUCKET=glow-754e6.firebasestorage.app
FIREBASE_MEASUREMENT_ID=G-25HEGKZV39
```

4. Queue controls (explicit):

```env
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
GLOW_CONVERT_ASYNC=1
```

5. Gate check:

- PASS if all values are present and non-placeholder.
- FAIL if any required setting is missing.

### Phase 1.1: Production Release-Candidate Env Block

Use this exact minimum block on the live host before the first auth smoke test:

```env
DATABASE_URL=postgresql://<user>:<password>@<host>/<db>?sslmode=require
DB_SSLMODE=require
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_APP_NAME=glow-web

FIREBASE_AUTH_ENABLED=1
FIREBASE_ADMIN_AUTH_ENABLED=1
FIREBASE_PROJECT_ID=<your-firebase-project-id>
FIREBASE_WEB_API_KEY=<your-firebase-web-api-key>
FIREBASE_AUTH_DOMAIN=<your-project>.firebaseapp.com
FIREBASE_APP_ID=<your-firebase-app-id>
FIREBASE_CREDENTIALS_PATH=/app/instance/firebase-service-account.json

SUPER_ADMIN_BOOTSTRAP_EMAILS=jeff@jeffbishop.com
ADMIN_BOOTSTRAP_EMAILS=
```

Notes:

- Keep `ADMIN_BOOTSTRAP_EMAILS` empty on first rollout unless you intentionally want additional non-super-admin bootstrap accounts.
- `SUPER_ADMIN_BOOTSTRAP_EMAILS` avoids a first-user privilege dead-end when the `users` table is empty.

### Phase 2: Dependency and Stack Bring-Up Gate

1. Install dependencies in the active environment:

```powershell
pip install -r web/requirements.txt
```

2. Start production topology (web + worker + redis):

```powershell
Set-Location web
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

3. Expected state:

- `web` service is healthy/running

### Phase 2.1: Release-Candidate Deploy Gate

Before any browser auth testing, confirm the deployed app is the auth-enabled branch and not the older public build.

Required checks:

- `/auth/login` returns `200 OK` instead of `404`
- Footer/app version matches the release-candidate branch you are testing
- Consent flow still works for anonymous users
- Public routes such as `/audit/`, `/convert/`, and `/about/` still work without login

If `/auth/login` is `404`, stop. You are still testing the old deployment, and Firebase passwordless cannot be validated yet.

### Phase 2.2: First Super-Admin Passwordless Smoke Test

Run this exact sequence after the release-candidate deploy:

1. Open `/consent/?next=/auth/login` on production.
2. Accept consent and continue.
3. Verify `/auth/login` renders the Firebase Email Link form.
4. Enter `jeff@jeffbishop.com` and request a sign-in link.
5. Confirm the email arrives and open the link in the same browser profile.
6. Complete login and verify the redirect lands on an authenticated account page.
7. Visit an admin-protected route such as `/admin/users` or `/admin/promotions`.
8. Verify admin access succeeds.
9. Verify the first seeded account is stored in Neon as `super_admin`.

Recommended Neon verification query:

```sql
SELECT email, role, is_active, is_email_verified
FROM users
WHERE email = 'jeff@jeffbishop.com';
```

Expected result:

- `email = jeff@jeffbishop.com`
- `role = super_admin`
- `is_active = true`
- `is_email_verified = true` or updated true after provider verification

### Phase 2.3: No-Login Regression Gate

After the first-account smoke test, immediately verify the public no-login promise still holds:

1. Open a fresh private/incognito window.
2. Complete consent only.
3. Verify the following still work without sign-in:
	- `/process/`
	- `/audit/`
	- `/fix/`
	- `/convert/`
	- `/template/`
	- `/speech/` if enabled
4. Confirm no route forces login for ordinary public document workflows.

This is the release gate for the promise that accounts are optional and GLOW still works as before for public users.
- `worker` service is running
- `redis` service is running

4. Gate check:

- PASS if all three services are up.
- FAIL if worker or redis is missing. Async paths are not production-ready without both.

### Phase 3: Data Migration Gate (SQLite -> Neon)

1. Dry run migration:

```powershell
Set-Location ..
python scripts/migrate_sqlite_to_neon.py --instance-dir instance --target-url "$env:DATABASE_URL"
```

2. If rerunning to replace existing imported rows:

```powershell
python scripts/migrate_sqlite_to_neon.py --instance-dir instance --target-url "$env:DATABASE_URL" --truncate
```

3. Optional explicit file list (mixed legacy/new runtime data):

```powershell
python scripts/migrate_sqlite_to_neon.py --instance-dir instance --target-url "$env:DATABASE_URL" --files ai_quota.db feedback.db visitor_counter.db feature_flags.db glow_users.db admin_auth.db --truncate
```

4. Gate check:

- PASS if script completes without exceptions and imported tables are present in Neon.
- FAIL on schema/import errors. Resolve before auth cutover testing.

### Phase 4: Auth and Admin Migration Gate

1. Validate user login paths:

- Local email/password login still works (fallback path)
- OAuth provider login still works (if configured)
- Firebase login endpoint `/auth/firebase-login` accepts valid ID token

2. Validate admin login paths:

- Admin login page shows Firebase button when `FIREBASE_ADMIN_AUTH_ENABLED=1`
- `/admin/login/firebase` accepts valid token for approved admin email
- Non-approved admin email is denied

3. Gate check:

- PASS if approved admin can sign in and unauthorized admin is blocked.
- FAIL if approval gate is bypassed or valid admin sign-in fails.

### Phase 5: Async Jobs and SSE Gate

1. Validate convert async queue:

- Submit a long conversion from `/convert`
- Confirm redirect to `/job/<id>/progress`
- Confirm state moves `PENDING -> STARTED -> PROGRESS -> SUCCESS`
- Download result from `/job/<id>/result`

2. Validate speech async queue:

- Submit speech job from `/speech`
- Confirm same status progression and downloadable output

3. Validate SSE updates:

- Open `/job/<id>/status` stream and confirm event updates until terminal state

4. Gate check:

- PASS if convert and speech complete via worker-backed jobs.
- FAIL if jobs stay stuck in `PENDING` or `STARTED`.

### Phase 6: Account, Privacy, and Encryption Gate

1. Validate account dashboard and privacy routes post-login:

- `/account`
- `/account/privacy`
- data export/delete flows

2. Validate encrypted provider key persistence:

- Save provider key
- Confirm retrieval succeeds in app
- Confirm storage is encrypted at rest (not plaintext)

3. Gate check:

- PASS if key roundtrip works and stored value is encrypted.
- FAIL if key is unreadable in app or plaintext in DB.

### Phase 7: MCP + Agent Skills Gate

1. Confirm workspace MCP config exists:

- `.vscode/mcp.json` includes `firebase` stdio and `neon` HTTP servers

2. Validate Firebase MCP diagnostics:

```powershell
npx -y firebase-tools@latest mcp --generate-tool-list
npx -y firebase-tools@latest mcp --generate-prompt-list
```

3. Validate skills install set:

```powershell
npx skills list
```

4. Gate check:

- PASS if Firebase MCP commands return tool/prompt lists and skills are listed.
- FAIL if MCP command execution fails or skill install set is missing.

### Phase 8: Final Sign-Off Gate

Do not declare completion until all are true:

- Neon DB active and validated
- Firebase user/admin auth validated with approval gate behavior
- Async convert + speech jobs verified end-to-end
- Account/privacy/encryption checks passed
- Migration script executed and documented
- MCP and skills diagnostics successful (or documented known caveat + workaround)

When all are true, cutover is ready for production rollout.

## Verification Matrix (Execute and Record)

| Area | Test | Expected | Result |
| --- | --- | --- | --- |
| Queue | Submit `/convert` job | Redirect to `/job/<id>/progress` | ☐ |
| Queue | Submit `/speech` job | Status reaches `SUCCESS` | ☐ |
| SSE | Open `/job/<id>/status` | Streaming status events appear | ☐ |
| Auth User | `/auth/firebase-login` | Valid token logs in | ☐ |
| Auth Admin | `/admin/login/firebase` approved email | Login succeeds | ☐ |
| Auth Admin Gate | `/admin/login/firebase` unapproved email | Login denied | ☐ |
| Account | `/account` and `/account/privacy` | Pages render authenticated | ☐ |
| Privacy | Export/Delete endpoints | Successful completion | ☐ |
| Encryption | Provider key persistence | Stored encrypted, readable in app | ☐ |
| Migration | `migrate_sqlite_to_neon.py` | Imports complete without exceptions | ☐ |
| MCP Firebase | `--generate-tool-list` | Tool list emitted | ☐ |
| Skills | `npx skills list` | Firebase + Neon skills visible | ☐ |

## Troubleshooting Matrix

| Symptom | Likely Cause | Action |
| --- | --- | --- |
| `ERR_TTY_INIT_FAILED` during `npx add-mcp` | Non-interactive shell | Use `.vscode/mcp.json` manual config and authenticate from client UI |
| Job stuck in `PENDING` | Worker not running or broker misconfigured | Check `docker compose -f web/docker-compose.prod.yml ps`, verify `worker` and `redis` |
| Job fails immediately | Missing converter dependency (Pandoc/WeasyPrint/Pipeline) | Validate tool availability and feature flags |
| Firebase login fails token verification | Wrong service account/project config | Verify `FIREBASE_PROJECT_ID` + credentials path/json |
| Admin Firebase login denied for valid user | Missing admin approval record/bootstrap list | Update `ADMIN_BOOTSTRAP_EMAILS` or admin records |
| `skills update --all` reports failures | Upstream skill update issue | Keep installed versions; continue with `npx skills list` verification and document exception |

## Branch Strategy
Do not kill or restart the branch.

Reason:
- Major feature foundation is already implemented (queue/jobs, profile sync, auth routes)
- Restarting would increase risk and duplicate work
- Safer path is incremental migration with feature flags and fallback paths

## Scope

### In Scope
- Neon-ready SQLAlchemy database configuration
- SQLite-to-Neon migration script and cutover process
- Firebase Admin SDK token verification on backend
- End-user Firebase login endpoint
- Admin Firebase login endpoint (with approval gating)
- Queue infra (Redis + worker) production compose support
- Required dependency updates
- Developer setup checklist

### Out of Scope (Phase 2)
- Full replacement of all legacy admin SQLite auth storage with SQLAlchemy models
- Frontend-only Firebase-only auth UX with no fallback options
- Full Alembic schema migration framework (recommended next)

## Architecture Decisions

1. Authentication
- Keep existing local + OAuth routes
- Add Firebase token sign-in endpoint
- Add admin Firebase token sign-in endpoint
- Continue requiring admin approval checks

2. Database
- SQLAlchemy remains the integration layer
- `DATABASE_URL` now supports Neon PostgreSQL with `psycopg`
- SQLite remains fallback for local/offline development

3. Job Queue
- Redis + Celery worker in production compose
- Eager mode fallback remains available when no broker is configured

4. Privacy + Encryption
- API keys remain encrypted using Fernet
- Consent-gated sync remains enforced

## What Has Been Executed

- Added Neon-capable DB URI normalization and engine tuning in `web/src/acb_large_print_web/db.py`
- Added Firebase helper module in `web/src/acb_large_print_web/firebase_auth.py`
- Added end-user Firebase login endpoint in `web/src/acb_large_print_web/routes/auth.py`
- Added admin Firebase login endpoint in `web/src/acb_large_print_web/routes/admin.py`
- Added Firebase admin login UI in `web/src/acb_large_print_web/templates/admin_login.html`
- Added account routes and account templates
- Added jobs progress template
- Wired app factory to initialize DB extensions and Celery, and register auth/account/jobs blueprints
- Updated production compose with Redis + worker + Neon/Firebase env passthrough
- Updated Python dependencies for auth/db/queue/firebase/postgres drivers
- Added migration script `scripts/migrate_sqlite_to_neon.py` for SQLite data import into Neon/Postgres
- Added decommission runbook `docs/neon-cutover-and-decommission-process.md`

## Developer Setup Checklist

## 1) Neon Setup

1. Create a Neon project and database.
2. Copy connection string.
3. Set env in `web/.env`:

```env
DATABASE_URL=postgresql://<user>:<password>@<host>/<db>?sslmode=require
DB_SSLMODE=require
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_APP_NAME=glow-web
```

4. If your URL starts with `postgres://`, code will normalize it automatically.
5. Start app and verify table creation on startup.

## 2) Firebase Setup (Backend)

1. Create/select Firebase project.
2. Enable authentication providers you need (Google, etc.).
3. Create service account key JSON.
4. Store JSON securely on server (recommended):

`/app/instance/firebase-service-account.json`

5. Set env in `web/.env`:

```env
FIREBASE_AUTH_ENABLED=1
FIREBASE_PROJECT_ID=glow-754e6
FIREBASE_CREDENTIALS_PATH=/app/instance/firebase-service-account.json
```

Alternative (not preferred for production):

```env
FIREBASE_CREDENTIALS_JSON={...raw-json...}
```

## 3) Firebase Setup (Frontend Web Config)

Set these in `web/.env` so templates can initialize Firebase client SDK:

```env
FIREBASE_WEB_API_KEY=AIzaSyBPiunXUVRgZ6PWolckiRPA6UEeewspE1c
FIREBASE_AUTH_DOMAIN=glow-754e6.firebaseapp.com
FIREBASE_APP_ID=1:42316874705:web:65a067c3dad4db789bd6f0
FIREBASE_PROJECT_ID=glow-754e6
FIREBASE_MESSAGING_SENDER_ID=42316874705
FIREBASE_STORAGE_BUCKET=glow-754e6.firebasestorage.app
FIREBASE_MEASUREMENT_ID=G-25HEGKZV39
```

## 4) Admin Firebase Sign-In Setup

1. Enable admin Firebase flow:

```env
FIREBASE_ADMIN_AUTH_ENABLED=1
```

2. Keep admin approval source configured:

```env
ADMIN_BOOTSTRAP_EMAILS=admin1@yourdomain.com,admin2@yourdomain.com
```

3. Admin login behavior:
- Firebase token is verified server-side
- Email must be in approved admin records
- Session still uses `admin_email` gate for admin routes

## 5) Queue + Worker Setup

1. Ensure Redis service is available (compose includes it).
2. Ensure worker starts in production compose.
3. Env values:

```env
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

## 6) Install Dependencies

In the active environment:

```bash
pip install -r web/requirements.txt
```

## 7) Run Stack

```bash
cd web
docker compose -f docker-compose.prod.yml up -d --build
```

## 8) Smoke Tests

- End-user login page renders
- `/auth/firebase-login` accepts valid token
- Admin login page shows Firebase admin button when enabled
- `/admin/login/firebase` accepts valid token for approved admin email
- Account dashboard and privacy pages load after login
- Async job progress page streams and downloads results
- DB writes appear in Neon

## 9) MCP Tooling Setup (Neon + Firebase)

Use these MCP setup steps to support development workflows in VS Code/Copilot and other MCP clients.

### Prerequisites

```powershell
node -v
npm -v
npx -v
```

### Neon MCP

Recommended full setup:

```powershell
npx neonctl@latest init
```

MCP-only setup:

```powershell
npx add-mcp https://mcp.neon.tech/mcp
```

Global user-level variant:

```powershell
npx add-mcp https://mcp.neon.tech/mcp -g
```

API key variant:

```powershell
$env:NEON_API_KEY="your-neon-api-key-here"
npx add-mcp https://mcp.neon.tech/mcp --header "Authorization: Bearer $env:NEON_API_KEY"
```

### Firebase MCP

Firebase MCP server command:

```powershell
npx -y firebase-tools@latest mcp
```

Authenticate CLI first:

```powershell
npm install -g firebase-tools
firebase login
firebase projects:list
```

No-global-install variant:

```powershell
npx -y firebase-tools@latest login
npx -y firebase-tools@latest projects:list
```

Tool/prompt diagnostics:

```powershell
npx -y firebase-tools@latest mcp --generate-tool-list
npx -y firebase-tools@latest mcp --generate-prompt-list
```

### VS Code project config

Use workspace file `.vscode/mcp.json`:

```json
{
	"servers": {
		"firebase": {
			"type": "stdio",
			"command": "npx",
			"args": ["-y", "firebase-tools@latest", "mcp"]
		},
		"neon": {
			"type": "http",
			"url": "https://mcp.neon.tech/mcp"
		}
	}
}
```

### Note about non-interactive shells

Some MCP bootstrap commands (for example `npx add-mcp ...`) may require an interactive TTY and can fail in scripted/non-interactive terminals with `ERR_TTY_INIT_FAILED`.
If that happens, use manual MCP config (as above) and complete auth flows from the editor/client UI.

## 10) Agent Skills Setup (Firebase + Neon)

Agent Skills provide workflow guidance to skills-capable coding agents. In this repository, project-level skills are installed into `.agents/skills/`.

### Install commands (project scope)

```powershell
npx skills add firebase/agent-skills -y
npx skills add neondatabase/agent-skills -y
```

### Verify installed skills

```powershell
npx skills list
```

### Installed in this repository

- Firebase skill pack: 14 skills installed
- Neon skill pack: 4 skills installed
- Install location: `.agents/skills/`

Current installed skill folders:

- `developing-genkit-dart`
- `developing-genkit-go`
- `developing-genkit-js`
- `developing-genkit-python`
- `firebase-ai-logic-basics`
- `firebase-app-hosting-basics`
- `firebase-auth-basics`
- `firebase-basics`
- `firebase-crashlytics`
- `firebase-data-connect`
- `firebase-firestore`
- `firebase-hosting-basics`
- `firebase-security-rules-auditor`
- `xcode-project-setup`
- `claimable-postgres`
- `neon-postgres`
- `neon-postgres-branches`
- `neon-postgres-egress-optimizer`

### Update and maintenance

```powershell
npx skills update --all
npx skills list
```

### Optional targeted Neon installs

```powershell
npx skills add https://github.com/neondatabase/agent-skills --skill neon-postgres -y
npx skills add https://github.com/neondatabase/agent-skills --skill claimable-postgres -y
npx skills add https://github.com/neondatabase/agent-skills --skill neon-postgres-egress-optimizer -y
```

### Scope guidance

- Project scope is recommended for repository-specific workflows.
- Global/user scope is useful for skills you want in all repositories.
- VS Code Copilot skill directories supported by the editor include `.github/skills/`, `.claude/skills/`, `.agents/skills/` (project-level) and user-level `~/.copilot/skills/`, `~/.claude/skills/`, `~/.agents/skills/`.

## Rollout Plan

Phase 1 (Current)
- Dual mode auth (existing + Firebase)
- Neon enabled via `DATABASE_URL`
- Admin Firebase flow added, approval still enforced

Phase 2
- Move legacy admin auth sqlite storage to SQLAlchemy models on Neon
- Add Alembic migrations
- Optional: disable legacy admin login methods

Phase 3
- Harden observability and alerts
- Add integration tests for Firebase and Neon paths

## Security Notes

- Keep service account JSON outside git and filesystem-restricted
- Rotate Firebase keys and Neon credentials periodically
- Continue encrypting provider API keys in DB
- Keep admin approval gate enabled even with Firebase

## Rollback Plan

- Set `FIREBASE_AUTH_ENABLED=0` to disable Firebase user login
- Set `FIREBASE_ADMIN_AUTH_ENABLED=0` to disable Firebase admin login
- Remove `DATABASE_URL` to fall back to local SQLite
- Keep OAuth/local auth routes operational during rollback
