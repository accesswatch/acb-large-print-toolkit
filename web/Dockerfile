FROM python:3.13-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# DAISY Pipeline version (pinned for reproducibility)
ARG PIPELINE_VERSION=1.15.4

# Pipeline installs to /opt/daisy-pipeline2/bin/
ENV PATH="/opt/daisy-pipeline2/bin:${PATH}"

# Install system dependencies:
#   pandoc        -- Markdown/RST/ODT/RTF -> ACB HTML conversion
#   nodejs + npm  -- DAISY Ace EPUB accessibility checker
#   default-jre-headless -- Java runtime for DAISY Pipeline 2
#   curl          -- Download Pipeline .deb package
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       pandoc nodejs npm default-jre-headless curl \
    && rm -rf /var/lib/apt/lists/*

# Install DAISY Pipeline 2 (LGPL -- https://github.com/daisy/pipeline-assembly)
# Pipeline provides advanced document conversion: Word->EPUB, HTML->EPUB,
# EPUB->DAISY 2.02, EPUB->DAISY 3/DTBook
RUN curl -fsSL -o /tmp/pipeline2.deb \
       "https://github.com/daisy/pipeline-assembly/releases/download/v${PIPELINE_VERSION}/pipeline2-${PIPELINE_VERSION}_debian.deb" \
    && dpkg -i /tmp/pipeline2.deb || true \
    && apt-get update && apt-get install -f -y --no-install-recommends \
    && rm -f /tmp/pipeline2.deb \
    && rm -rf /var/lib/apt/lists/* \
    && dp2 --version

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

# Changelog (rendered as HTML by the /changelog route)
COPY CHANGELOG.md ./

# Create a non-root user
RUN addgroup --system app && adduser --system --ingroup app app
RUN mkdir -p /app/instance /app/.gunicorn && chown -R app:app /app/instance /app/.gunicorn

ENV HOME=/app
USER app

EXPOSE 8000

# Run with gunicorn (production WSGI server)
CMD ["gunicorn", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "2", \
    "--timeout", "120", \
    "--access-logfile", "-", \
    "acb_large_print_web.app:create_app()"]
