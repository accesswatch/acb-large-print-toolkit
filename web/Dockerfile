FROM python:3.13-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies:
#   pandoc        -- Markdown/RST/ODT/RTF -> ACB HTML conversion
#   nodejs + npm  -- DAISY Ace EPUB accessibility checker
#   WeasyPrint system libs -- CSS-based PDF rendering
#   fonts-liberation -- Liberation Sans (metrically identical to Arial)
#                       for ACB BOP font compliance in PDF output
# DAISY Pipeline 2 runs as a separate Docker service (sidecar) -- see
# docker-compose.yml / docker-compose.prod.yml.  The web app connects to it
# via its REST API (no JRE or .deb needed in this image).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    pandoc nodejs npm \
    ffmpeg \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
    libffi-dev shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install DAISY Ace globally (MIT license -- https://github.com/daisy/ace)
# Ace provides 100+ axe-core accessibility checks for EPUB publications
# Source vendored in vendor/daisy-ace/ for offline builds and auditing
# Note: ace --version requires Electron's libglib-2.0 which isn't in slim;
# verify install by checking the CLI entry point exists instead.
RUN npm install -g @daisy/ace --no-fund --no-audit \
    && npm cache clean --force \
    && which ace

# Install the core library (audit, fix, convert, export -- no CLI/GUI)
# The .dockerignore excludes desktop-only files (cli.py, gui.py, __main__.py)
COPY desktop/pyproject.toml desktop/
COPY desktop/src/ desktop/src/
RUN pip install --no-cache-dir ./desktop

# Install the web app
COPY web/pyproject.toml web/requirements.txt web/
COPY web/src/ web/src/
RUN pip install --no-cache-dir ./web

# Long-form docs are pre-rendered locally into template partials by
# scripts/build-doc-pages.py and committed under web/src/.../templates/partials.

# Create a non-root user
RUN addgroup --system app && adduser --system --ingroup app app
RUN mkdir -p /app/instance /app/.gunicorn /app/.cache/huggingface/hub \
    && chown -R app:app /app/instance /app/.gunicorn /app/.cache

ENV HOME=/app \
    XDG_CACHE_HOME=/app/.cache \
    HF_HOME=/app/.cache/huggingface \
    HUGGINGFACE_HUB_CACHE=/app/.cache/huggingface/hub
USER app

EXPOSE 8000

# Run with gunicorn (production WSGI server)
CMD ["gunicorn", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "4", \
    "--timeout", "1800", \
    "--access-logfile", "-", \
    "acb_large_print_web.app:create_app()"]
