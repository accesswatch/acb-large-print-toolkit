# Admin Bootstrap (password-only)

This document explains how to bootstrap a local admin account using a password-only method (no email). Use this for initial operator access during deployment or local development.

Important: only use a short-lived bootstrap password in production if you understand the risks. Prefer full admin setup (email or SSO) in production.

## Bootstrap by environment variable

Set the `ADMIN_PASSWORD` environment variable on the server before the first admin login. The app will prefer `ADMIN_PASSWORD` over older `ADMIN_LOCAL_PASSWORD` names.

Example (Linux, systemd unit or shell):

```bash
export ADMIN_PASSWORD="a-strong-temporary-password"
export FEATURE_FLAGS_BACKEND="json"  # optional
# start or restart the web service
systemctl restart glow-web.service
```

On Windows (PowerShell):

```powershell
$env:ADMIN_PASSWORD = 'a-strong-temporary-password'
# start the service or run the dev server
```

## Verify the admin account

1. Visit the admin login page (`/admin/login`) and choose password login.
2. Authenticate using the bootstrap password you set.
3. After first successful login, create a permanent admin user via the Admin UI and remove the bootstrap password.

## Rotate or remove the bootstrap password

- To remove bootstrap access, unset `ADMIN_PASSWORD` and restart the service.
- If the variable was set in a systemd unit, remove it from the unit file and reload the unit.

## Inspecting local admin DB (developer only)

The local bootstrap creates/updates an SQLite admin DB in `instance/admin_auth.db` when using local password auth. Inspect it for troubleshooting (do not store passwords in plaintext):

```bash
# open SQLite CLI for quick inspection
sqlite3 instance/admin_auth.db
.tables
SELECT id, email, created_at FROM admins;
```

## Security notes

- Avoid leaving the bootstrap password in environment variables on long-lived servers. If you must, rotate immediately after creating a permanent admin account.
- Enable `SECRET_KEY` in production to secure Flask sessions and CSRF tokens.
- Use a secrets manager (Vault, Azure Key Vault, AWS Secrets Manager) for production secrets rather than environment variables when possible.

## Next steps for operators

- Create a permanent admin account and remove the bootstrap password.
- Configure feature flags (see `instance/feature_flags.json` or the admin UI) to enable or disable features such as DAISY, PDF, and MarkItDown.
- Confirm `OPENROUTER_API_KEY` is set only if AI features are required and budget controls are in place.

