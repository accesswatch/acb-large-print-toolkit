# GLOW OAuth Credential Collection Runbook

Use this as the single operator guide for collecting provider credentials and filling environment variables for production and local development.

Progress tracking and go-live snapshot:

- `docs/oauth-provider-progress-tracker.md`

## Scope

- Providers covered: Google, GitHub, Microsoft Entra, Apple, Auth0, WordPress OAuth Server
- Output of this runbook: complete env blocks for production and localhost development

## Production Callback URLs

- Google: `https://glow.bits-acb.org/auth/oauth/google/callback`
- GitHub: `https://glow.bits-acb.org/auth/oauth/github/callback`
- Microsoft: `https://glow.bits-acb.org/auth/oauth/microsoft/callback`
- Apple: `https://glow.bits-acb.org/auth/oauth/apple/callback`
- Auth0: `https://glow.bits-acb.org/auth/oauth/auth0/callback`
- WordPress: `https://glow.bits-acb.org/auth/oauth/wordpress/callback`

## Local Development Callback URLs

- Google: `http://localhost:5000/auth/oauth/google/callback`
- GitHub: `http://localhost:5000/auth/oauth/github/callback`
- Microsoft: `http://localhost:5000/auth/oauth/microsoft/callback`
- Apple: `http://localhost:5000/auth/oauth/apple/callback`
- Auth0: `http://localhost:5000/auth/oauth/auth0/callback`
- WordPress: `http://localhost:5000/auth/oauth/wordpress/callback`

## Provider Console Links and What to Copy

### Google

- Console: <https://console.cloud.google.com/apis/credentials>
- Create OAuth client type: Web application
- Add production + local redirect URIs (above)
- Copy:
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`

### GitHub

- Console: <https://github.com/settings/developers>
- Create OAuth App
- Authorization callback URL:
  - Production: `https://glow.bits-acb.org/auth/oauth/github/callback`
  - Local: `http://localhost:5000/auth/oauth/github/callback`
- Copy:
  - `Ov23li7l5O1nwh1dw9vG`
  - `0c24f73653db088b17f2be704f4f22fb44a51497`

### Microsoft Entra ID

- Console: <https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade>
- Create or open app registration
- Add redirect URIs (production + local)
- Create new client secret under Certificates & secrets
- Ensure delegated scopes include: `openid`, `profile`, `email`
- Copy:
  - `MICROSOFT_CLIENT_ID` (Application client ID)
  - `MICROSOFT_CLIENT_SECRET` (secret value)
  - `MICROSOFT_TENANT_ID` (`common` unless single-tenant)

### Apple Sign In

- Console: <https://developer.apple.com/account/>
- Create or open a Services ID (not App ID)
- Configure Sign in with Apple return URLs (production + local)
- Generate/sign client secret JWT
- Copy:
  - `APPLE_CLIENT_ID` (Services ID)
  - `APPLE_CLIENT_SECRET` (signed JWT)

### Auth0

- Console: <https://manage.auth0.com/dashboard/>
- Create or open a Regular Web Application
- Add callback URLs (production + local)
- Ensure profile includes email claim
- Copy:
  - `AUTH0_CLIENT_ID`
  - `AUTH0_CLIENT_SECRET`
  - `AUTH0_DOMAIN` (for example `tenant.auth0.com`)

Note on Firebase:

- App-level Auth0 (`/auth/oauth/auth0`) works without Firebase Identity Platform.
- Firebase-console OIDC/Auth0 provider requires Firebase Identity Platform upgrade.

### WordPress OAuth Server

- On your WordPress site, install/configure OAuth Server plugin
- Register callback URLs (production + local)
- Copy:
  - `WORDPRESS_CLIENT_ID`
  - `WORDPRESS_CLIENT_SECRET`
  - `WORDPRESS_BASE_URL`

## Production Environment Template

```env
GOOGLE_CLIENT_ID=REPLACE_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=REPLACE_GOOGLE_CLIENT_SECRET

GITHUB_CLIENT_ID=REPLACE_GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET=REPLACE_GITHUB_CLIENT_SECRET

MICROSOFT_CLIENT_ID=REPLACE_MICROSOFT_CLIENT_ID
MICROSOFT_CLIENT_SECRET=REPLACE_MICROSOFT_CLIENT_SECRET
MICROSOFT_TENANT_ID=common

APPLE_CLIENT_ID=REPLACE_APPLE_SERVICES_ID
APPLE_CLIENT_SECRET=REPLACE_APPLE_CLIENT_SECRET_JWT

AUTH0_CLIENT_ID=REPLACE_AUTH0_CLIENT_ID
AUTH0_CLIENT_SECRET=REPLACE_AUTH0_CLIENT_SECRET
AUTH0_DOMAIN=REPLACE_AUTH0_DOMAIN

WORDPRESS_CLIENT_ID=REPLACE_WORDPRESS_CLIENT_ID
WORDPRESS_CLIENT_SECRET=REPLACE_WORDPRESS_CLIENT_SECRET
WORDPRESS_BASE_URL=https://REPLACE_WORDPRESS_SITE
WORDPRESS_OAUTH_LABEL=WordPress
```

## Local Development Template

```env
# Set only the providers you are actively testing locally.

GOOGLE_CLIENT_ID=REPLACE_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=REPLACE_GOOGLE_CLIENT_SECRET

GITHUB_CLIENT_ID=REPLACE_GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET=REPLACE_GITHUB_CLIENT_SECRET

MICROSOFT_CLIENT_ID=REPLACE_MICROSOFT_CLIENT_ID
MICROSOFT_CLIENT_SECRET=REPLACE_MICROSOFT_CLIENT_SECRET
MICROSOFT_TENANT_ID=common

APPLE_CLIENT_ID=REPLACE_APPLE_SERVICES_ID
APPLE_CLIENT_SECRET=REPLACE_APPLE_CLIENT_SECRET_JWT

AUTH0_CLIENT_ID=REPLACE_AUTH0_CLIENT_ID
AUTH0_CLIENT_SECRET=REPLACE_AUTH0_CLIENT_SECRET
AUTH0_DOMAIN=REPLACE_AUTH0_DOMAIN

WORDPRESS_CLIENT_ID=REPLACE_WORDPRESS_CLIENT_ID
WORDPRESS_CLIENT_SECRET=REPLACE_WORDPRESS_CLIENT_SECRET
WORDPRESS_BASE_URL=https://REPLACE_WORDPRESS_SITE
WORDPRESS_OAUTH_LABEL=WordPress
```

## Completion Checklist

- [ ] Collected Google client ID + secret
- [x] Collected GitHub client ID + secret
- [ ] Collected Microsoft client ID + secret
- [ ] Collected Apple Services ID + client secret JWT
- [ ] Collected Auth0 client ID + secret + domain
- [ ] Collected WordPress client ID + secret + base URL
- [ ] Added production callback URLs in each provider
- [ ] Added local callback URLs in each provider
- [ ] Filled production env on server
- [ ] Ran browser sign-in tests for required providers
