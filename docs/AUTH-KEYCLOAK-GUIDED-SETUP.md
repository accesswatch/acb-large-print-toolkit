# GLOW Authentication & Keycloak Integration: Full Guided Setup

This guide walks you through deploying Keycloak, configuring Google login, integrating with GLOW, and onboarding users/admins. Follow each step in order for a smooth, secure rollout.

---

## 1. Deploy Keycloak (Docker Quick Start)

**For local/dev:**
```sh
docker run -p 8080:8080 -e KEYCLOAK_ADMIN=admin -e KEYCLOAK_ADMIN_PASSWORD=admin quay.io/keycloak/keycloak:24.0.3 start-dev
```
- Visit http://localhost:8080/
- Log in with admin/admin

**For production:**
- Deploy on a VM, Kubernetes, or use a managed Keycloak provider (see docs).
- Set strong admin credentials and enable HTTPS.

---

## 2. Initial Keycloak Admin Setup
- Log in to the Keycloak admin console.
- Create a new realm (e.g., `glow`).
- Create roles: `facilitator`, `admin` (under Realm Roles).

---

## 3. Create OIDC Client for GLOW
- In the `glow` realm, go to Clients → Create client.
- Client ID: `glow-app`
- Client type: OpenID Connect
- Root URL: your GLOW app URL (e.g., `https://glow.yourdomain.org`)
- Valid redirect URIs: `https://glow.yourdomain.org/*`
- Access Type: confidential
- Save and note the client secret.

---

## 4. Add Google as an Identity Provider
- Go to Identity Providers → Add provider → Google.
- In Google Cloud Console:
  - Create a project, enable OAuth consent screen.
  - Create OAuth credentials (Web application).
  - Set redirect URI: `https://<your-keycloak-domain>/auth/realms/glow/broker/google/endpoint`
  - Copy Client ID and Secret to Keycloak.
- Leave "Hosted Domain" blank to allow all Google accounts.
- Save.

---

## 5. Download OIDC Client Secrets for GLOW
- In Keycloak, go to Clients → `glow-app` → Installation.
- Download the `client_secrets.json` (format: OIDC JSON).
- Place this file in `web/src/acb_large_print_web/` in your GLOW repo.

---

## 6. Integrate OIDC in GLOW
- Ensure `flask-oidc` is in `requirements.txt`.
- The app factory in `app.py` auto-registers OIDC if installed.
- Use the decorators from `oidc_auth.py` to protect routes:

```python
from acb_large_print_web.oidc_auth import require_login, require_role

@app.route('/facilitator')
@require_login
@require_role('facilitator')
def facilitator_dashboard():
    ...
```

---

## 7. Assign Roles to Users
- In Keycloak admin, go to Users → select user → Role Mappings.
- Assign `facilitator` or `admin` as needed.
- Users will have access on next login.

---

## 8. User Onboarding (for Conference/Workshop)
- Go to the GLOW login page.
- Click “Sign in with Google”.
- Log in with any Google account.
- If assigned, facilitator/admin features will be available.

---

## 9. Admin Onboarding
- Log in to Keycloak admin console.
- Add new users or assign roles as above.
- Monitor login activity and manage roles as needed.

---

## 10. Production/Scaling Notes
- Use HTTPS for Keycloak and GLOW in production.
- Back up Keycloak database regularly.
- For high availability, run Keycloak in a cluster or use a managed provider.
- Document your admin credentials and OIDC secrets securely.

---

**You now have a secure, scalable, and user-friendly authentication system for GLOW, ready for both conference and future org-wide use.**

If you need step-by-step screenshots, troubleshooting, or advanced SSO (SAML, Microsoft, etc.), just ask!
