# Deployment Guide: ACB Large Print Web Application

Step-by-step instructions for deploying the Flask web app on a bare Ubuntu VPS with Docker and Caddy. This guide assumes the RackNerd 8 GB VPS ($62.49/year) but works on any Ubuntu 24.04 server with root access.

---

## Prerequisites

- A VPS running Ubuntu 24.04 LTS with root/sudo SSH access
- A domain or subdomain with a DNS A record pointing to the VPS IP address
- The DNS record must be active before starting (Caddy needs it for TLS certificate issuance)

---

## Phase 1: Server Hardening (one-time, ~10 minutes)

### 1.1 Connect and update

```bash
ssh root@YOUR_SERVER_IP

apt update && apt upgrade -y
```

### 1.2 Create a non-root deploy user

```bash
adduser deploy
usermod -aG sudo deploy
```

### 1.3 Set up SSH key authentication for the deploy user

From your local machine:

```bash
ssh-copy-id deploy@YOUR_SERVER_IP
```

Then on the server, disable password authentication:

```bash
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

### 1.4 Configure the firewall

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status
```

Expected output: rules for OpenSSH, 80/tcp, and 443/tcp are ALLOW.

### 1.5 Enable automatic security updates

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

Select "Yes" when prompted.

---

## Phase 2: Install Docker (one-time, ~5 minutes)

### 2.1 Install Docker Engine and Compose

```bash
# Add Docker's official GPG key and repository
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 2.2 Allow the deploy user to run Docker without sudo

```bash
sudo usermod -aG docker deploy
```

Log out and back in for the group change to take effect:

```bash
exit
ssh deploy@YOUR_SERVER_IP
```

### 2.3 Verify Docker

```bash
docker run --rm hello-world
docker compose version
```

Both commands should succeed.

---

## Phase 3: Clone and Configure the App (~5 minutes)

### 3.1 Clone the repository

```bash
cd ~
git clone https://github.com/accesswatch/acb-large-print-toolkit.git app
cd app
```

### 3.2 Create the Caddyfile

Replace `YOUR_DOMAIN` with your actual domain (e.g., `lp.bits-acb.org`).

```bash
cat > web/Caddyfile << 'EOF'
YOUR_DOMAIN {
    reverse_proxy app:8000
    encode gzip

    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        Referrer-Policy strict-origin-when-cross-origin
        Permissions-Policy interest-cohort=()
    }
}
EOF
```

Edit the file to replace `YOUR_DOMAIN`:

```bash
sed -i 's/YOUR_DOMAIN/lp.bits-acb.org/' web/Caddyfile
```

### 3.3 Create a .env file for production settings

```bash
cat > web/.env << 'EOF'
FLASK_ENV=production
SECRET_KEY=your-random-secret-key-here
# Uncomment to enable feedback review at /feedback/review?key=<password>
# FEEDBACK_PASSWORD=change-me-in-production
LOG_LEVEL=INFO
EOF
```

Generate a secure SECRET_KEY:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Phase 4: Build and Launch (~3 minutes)

### 4.1 Build and start the containers

```bash
cd ~/app/web
docker compose up -d --build
```

This builds the web container:
- `web`: Flask + Gunicorn (port 8000)

If you added the Caddy service to docker-compose.yml (see Reference Files), it also starts:
- `caddy`: Reverse proxy (ports 80 and 443, public, auto-TLS)

Caddy automatically obtains a Let's Encrypt TLS certificate on first request.

### 4.2 Verify the app is running

```bash
# Check container status
docker compose ps

# Check logs
docker compose logs app --tail 20
docker compose logs caddy --tail 20

# Test the health endpoint locally
curl -s http://localhost:8000/health
```

Expected: both containers show "Up", health returns 200.

### 4.3 Test from a browser

Open `https://YOUR_DOMAIN` in a browser. You should see the landing page with links to audit, fix, template, export, guidelines, and feedback.

---

## Phase 5: Enable Auto-Restart on Reboot (~2 minutes)

Docker with the default restart policy in `docker-compose.yml` handles this, but confirm:

```bash
# Verify restart policy is set (should see "restart: unless-stopped" in compose file)
grep restart ~/app/web/docker-compose.yml

# Enable Docker to start on boot (usually already enabled)
sudo systemctl enable docker
```

Test by rebooting:

```bash
sudo reboot
```

After reconnecting, verify:

```bash
ssh deploy@YOUR_SERVER_IP
docker compose -f ~/app/web/docker-compose.yml ps
```

Both containers should be "Up".

---

## Phase 6: Set Up Monitoring (~5 minutes)

### 6.1 UptimeRobot (free tier)

1. Sign up at [uptimerobot.com](https://uptimerobot.com)
2. Add a new monitor:
   - Type: HTTP(s)
   - URL: `https://YOUR_DOMAIN/health`
   - Interval: 5 minutes
3. Configure alert contacts (email and/or SMS)

### 6.2 Basic server monitoring (optional)

```bash
# Disk usage alert -- add to deploy user's crontab
crontab -e
```

Add this line to email a warning if disk usage exceeds 80%:

```
0 6 * * * df -h / | awk 'NR==2 && int($5)>80 {print "Disk usage: "$5}' | mail -s "Disk Alert" you@example.com
```

---

## Routine Operations

### Deploying updates

```bash
ssh deploy@YOUR_SERVER_IP
cd ~/app
git pull origin main
cd web
docker compose up -d --build
```

The build takes about 30 seconds. There is a brief downtime (a few seconds) during container restart.

### Viewing logs

```bash
# App logs (Flask/Gunicorn)
docker compose -f ~/app/web/docker-compose.yml logs web --tail 50 -f

# Caddy logs (HTTP access) -- if Caddy is in your compose file
docker compose -f ~/app/web/docker-compose.yml logs caddy --tail 50 -f

# All logs
docker compose -f ~/app/web/docker-compose.yml logs --tail 50 -f
```

### Restarting the app

```bash
cd ~/app/web
docker compose restart web
```

### Stopping everything

```bash
cd ~/app/web
docker compose down
```

### Checking disk usage

```bash
# Overall
df -h /

# Docker-specific
docker system df
```

### Backing up feedback data

Feedback is stored in a SQLite database inside the `feedback-data` Docker volume:

```bash
# Copy the database out of the volume
docker compose -f ~/app/web/docker-compose.yml cp web:/app/instance/feedback.db ./feedback-backup.db

# Or access it directly via the volume mount
docker volume inspect web_feedback-data
```

### Viewing feedback

Set the `FEEDBACK_PASSWORD` environment variable in docker-compose.yml, then visit:

```
https://YOUR_DOMAIN/feedback/review?key=YOUR_PASSWORD
```

### Cleaning up old Docker images

```bash
docker image prune -a --filter "until=720h"
```

This removes images older than 30 days that are not in use.

### Renewing TLS certificates

Caddy handles this automatically. Certificates renew 30 days before expiry with no manual intervention. Caddy stores certificates in a Docker named volume (`caddy_data`).

### Updating the server OS

```bash
sudo apt update && sudo apt upgrade -y
```

Automatic security updates are enabled (Phase 1.5), but run this monthly for non-security package updates. Reboot if the kernel was updated:

```bash
sudo reboot
```

### Updating Docker Engine

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

---

## Reference Files

These files ship with the app in the `web/` directory and are ready to use:

### Dockerfile

```dockerfile
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install the core library first (changes less often)
COPY word-addon/pyproject.toml word-addon/
COPY word-addon/src/ word-addon/src/
RUN pip install --no-cache-dir ./word-addon

# Install the web app
COPY web/pyproject.toml web/requirements.txt web/
COPY web/src/ web/src/
RUN pip install --no-cache-dir ./web

# Create a non-root user
RUN addgroup --system app && adduser --system --ingroup app app
RUN mkdir -p /app/instance && chown app:app /app/instance

USER app

EXPOSE 8000

CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "acb_large_print_web.app:create_app()"]
```

### docker-compose.yml

```yaml
services:
  web:
    build:
      context: ..
      dockerfile: web/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      # - SECRET_KEY=your-secret-here
      # - FEEDBACK_PASSWORD=change-me-in-production
    volumes:
      - feedback-data:/app/instance
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

volumes:
  feedback-data:
```

For production with Caddy, add a Caddy service to docker-compose.yml:

```yaml
  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config

volumes:
  feedback-data:
  caddy_data:
  caddy_config:
```

When using Caddy, change the `web` service from `ports: ["8000:8000"]` to `expose: ["8000"]` so it is only accessible through the reverse proxy.

### Caddyfile

```
your.domain.com {
    reverse_proxy app:8000
    encode gzip

    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        Referrer-Policy strict-origin-when-cross-origin
        Permissions-Policy interest-cohort=()
    }
}
```

---

## Troubleshooting

### Caddy fails to get TLS certificate

- Verify DNS A record points to the VPS IP: `dig +short YOUR_DOMAIN`
- Verify ports 80 and 443 are open: `sudo ufw status`
- Check Caddy logs: `docker compose logs caddy`
- Common cause: DNS not propagated yet. Wait 5 minutes and restart Caddy.

### App container exits immediately

- Check logs: `docker compose logs web`
- Common cause: Python import error (missing dependency in requirements.txt)
- Test locally: `docker compose run --rm web python -c "from acb_large_print_web import create_app; print('OK')"`

### Upload fails with 413 error

- File exceeds 16 MB limit. This is by design. The limit is set in Flask's `MAX_CONTENT_LENGTH`.

### Permission denied errors in container

- The container runs as `app` (non-root). Only `/app/instance` and `/tmp` are writable.
- Check that the Dockerfile user creation and `chown` steps completed correctly.

### Out of disk space

```bash
docker system prune -a
sudo apt clean
```

### Connection refused on ports 80/443

```bash
sudo ufw status                    # firewall rules
docker compose ps                  # container status
sudo ss -tlnp | grep -E ':80|:443'  # what's listening
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Set to `development` for debug mode |
| `SECRET_KEY` | Random per-start | Flask session/CSRF secret. **Set a fixed value in production.** |
| `FEEDBACK_PASSWORD` | (unset) | Set to enable `/feedback/review?key=<password>`. Disabled when unset. |
| `LOG_LEVEL` | `INFO` | Python logging level (DEBUG, INFO, WARNING, ERROR) |
| `MAX_CONTENT_LENGTH` | `16777216` (16 MB) | Maximum upload file size in bytes |
