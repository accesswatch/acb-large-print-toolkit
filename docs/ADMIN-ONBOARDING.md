# GLOW Admin Onboarding Guide

This guide explains how to manage users, assign roles, and keep your GLOW authentication system secure.

---

## 1. Accessing the Keycloak Admin Console
- Go to http://localhost:8080/ (or your Keycloak URL)
- Log in with your admin credentials (default: admin/admin for dev)

---

## 2. Managing Users
- Go to the 'Users' section in your realm (e.g., 'glow')
- Add new users or search for existing ones

---

## 3. Assigning Roles
- Select a user
- Go to 'Role Mappings'
- Assign 'facilitator' or 'admin' as needed
- User will have access on next login

---

## 4. Adding Google Login
- See docs/AUTH-KEYCLOAK-GUIDED-SETUP.md for full instructions
- Add Google as an Identity Provider in Keycloak
- Users can now log in with any Google account

---

## 5. Security Best Practices
- Change the default admin password immediately
- Use HTTPS in production
- Back up your Keycloak database regularly
- For production, use a persistent database (e.g., Postgres)

---

## 6. Troubleshooting
- If a user can’t log in, check their role assignments
- For OIDC client issues, verify client_secrets.json and redirect URIs
- For advanced help, see Keycloak docs or contact your technical lead

---

You are now ready to manage GLOW users and roles securely!
