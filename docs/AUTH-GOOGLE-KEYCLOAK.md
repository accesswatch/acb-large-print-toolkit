# GLOW Authentication: Google Account Login via Keycloak

This document describes how to enable all Google account logins (Gmail, Workspace, etc.) for the GLOW conferencing platform using Keycloak as the identity broker. This approach is scalable for future GLOW-wide adoption and does not require the app to handle passwords or email delivery directly.

---

## 1. Google Cloud OAuth Setup

1. Go to https://console.cloud.google.com/
2. Create a new project (or use an existing one).
3. Go to “APIs & Services” → “Credentials”.
4. Click “Create Credentials” → “OAuth client ID”.
5. Choose “Web application”.
6. Set “Authorized redirect URIs” to your Keycloak instance:
   - `https://<your-keycloak-domain>/auth/realms/glow/broker/google/endpoint`
7. Do **not** set “Hosted Domain” (leave blank) to allow all Google accounts.
8. Save and copy the **Client ID** and **Client Secret**.

---

## 2. Keycloak Configuration

1. Log in to Keycloak admin console.
2. Select your realm (e.g., `glow`).
3. Go to “Identity Providers” → “Add provider” → “Google”.
4. Enter the Client ID and Secret from Google Cloud.
5. Leave “Hosted Domain” blank (enables all Google accounts).
6. Set “Default Scopes” to `openid email profile`.
7. Save.

---

## 3. GLOW OIDC Client Setup in Keycloak

1. In Keycloak, go to “Clients” → “Create client”.
2. Client ID: `glow-app`
3. Root URL: your GLOW app URL (e.g., `https://glow.yourdomain.org`)
4. Valid redirect URIs: `https://glow.yourdomain.org/*`
5. Set “Access Type” to “confidential”.
6. Save and note the client secret.

---

## 4. GLOW App Integration (Flask Example)

1. Install Flask OIDC:
   - `pip install flask-oidc`
2. Download Keycloak’s OIDC discovery JSON and save as `client_secrets.json`.
3. Configure OIDC in your Flask app:

```python
OIDC_CLIENT_SECRETS = 'client_secrets.json'
OIDC_RESOURCE_SERVER_ONLY = False
OIDC_SCOPES = ['openid', 'email', 'profile']
```

4. Protect routes with OIDC decorators:

```python
from flask_oidc import OpenIDConnect

oidc = OpenIDConnect(app)

@app.route('/protected')
@oidc.require_login
def protected():
    user_info = oidc.user_getinfo(['email', 'sub'])
    # ...existing code...
```

5. Use `oidc.user_getinfo()` to get user email and roles.

---

## 5. Role Mapping (Facilitator/Admin)

1. In Keycloak, create roles: `facilitator`, `admin`.
2. Assign roles to users/groups in Keycloak.
3. In GLOW, check for these roles in the OIDC token to control access.

---

## 6. Test the Flow

1. Go to GLOW login page.
2. Click “Sign in with Google”.
3. Authenticate with any Google account (Gmail, Workspace, etc.).
4. Confirm access to protected features.

---

## Future Expansion Considerations

- User Data Storage: For now, only store minimal user info (email, sub, roles) from OIDC claims. For future: plan for user profile, preferences, and audit logs as needed.
- Multiple Identity Providers: Keycloak can add Microsoft, GitHub, SAML, etc. later with no app code change.
- User Approval/Moderation: You can later restrict access by email domain, approval, or group membership.
- Consent and Privacy: Document what data is stored and why. For future: add user consent screens if storing more than minimal info.
- Scalability: Keycloak and OIDC scale to thousands of users and multiple apps.

---

## User Documentation (for Conference/Workshop)

**How to log in to GLOW:**
1. Go to the GLOW login page.
2. Click “Sign in with Google”.
3. Log in with your Google account (Gmail or Workspace).
4. You’ll be redirected back to GLOW and signed in.

**Who can log in?**
- Any user with a Google account (Gmail, Workspace, etc.).
- Facilitator/admin features require special roles (assigned by admin).

---

## Admin Documentation

**How to add a facilitator/admin:**
1. Log in to Keycloak admin console.
2. Go to “Users”, find the user (by email).
3. Assign the `facilitator` or `admin` role.
4. User will have access on next login.

---

**This setup is ready for future expansion to other providers and user data storage as GLOW adoption grows.**
