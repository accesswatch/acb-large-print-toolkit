FROM python:3.13-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies:
#   pandoc        -- Markdown/RST/ODT/RTF -> ACB HTML conversion
#   nodejs + npm  -- DAISY Ace EPUB accessibility checker
#   epubcheck     -- W3C-authoritative EPUB package validation
#   WeasyPrint system libs -- CSS-based PDF rendering
#   fonts-liberation -- Liberation Sans (metrically identical to Arial)
#                       for ACB BOP font compliance in PDF output
# DAISY Pipeline 2 runs as a separate Docker service (sidecar) -- see
# docker-compose.yml / docker-compose.prod.yml.  The web app connects to it
# via its REST API (no JRE or .deb needed in this image).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    pandoc nodejs npm epubcheck \
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
# Step 1: copy manifests and pre-install all dependencies (cached layer --
#         only reruns when pyproject.toml / requirements.txt change, not on
#         every source edit)
COPY web/pyproject.toml web/requirements.txt web/
RUN mkdir -p web/src/acb_large_print_web \
    && touch web/src/acb_large_print_web/__init__.py \
    && pip install --no-cache-dir ./web \
    && rm -rf web/src/acb_large_print_web
# Step 2: copy real source and reinstall the package only (deps already done)
COPY web/src/ web/src/
RUN pip install --no-cache-dir --no-deps ./web

# Pre-download Kokoro model files at build time (Tier 1 TTS engine).
# Model files come from the kokoro-onnx release assets.
# They are baked into the image so the container is self-contained;
# a bind-mount or named volume at /app/instance/speech_models/ can
# override them if an admin wants to manage models externally.
# Build with --build-arg SKIP_SPEECH_MODELS=1 to skip this step.
ARG SKIP_SPEECH_MODELS=0
RUN if [ "$SKIP_SPEECH_MODELS" != "1" ]; then \
      python -c "from pathlib import Path; import urllib.request; d=Path('/app/instance/speech_models'); d.mkdir(parents=True, exist_ok=True); base='https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0'; urllib.request.urlretrieve(f'{base}/kokoro-v1.0.onnx', d/'kokoro-v1.0.onnx'); urllib.request.urlretrieve(f'{base}/voices-v1.0.bin', d/'voices-v1.0.bin'); print('Kokoro models downloaded.')" \
      || echo 'Kokoro model download failed -- deploy-app.sh will retry at runtime.'; \
      python -c "from pathlib import Path; import urllib.request; d=Path('/app/instance/speech_models/piper'); d.mkdir(parents=True, exist_ok=True); base='https://huggingface.co/rhasspy/piper-voices/resolve/main'; voices=[('en_US-lessac-medium','en/en_US/lessac/medium/en_US-lessac-medium'),('en_US-amy-medium','en/en_US/amy/medium/en_US-amy-medium'),('en_US-ryan-high','en/en_US/ryan/high/en_US-ryan-high'),('en_US-hfc_female-medium','en/en_US/hfc_female/medium/en_US-hfc_female-medium'),('en_GB-alan-medium','en/en_GB/alan/medium/en_GB-alan-medium'),('en_GB-southern_english_female-low','en/en_GB/southern_english_female/low/en_GB-southern_english_female-low')]; downloaded=0; skipped=0; failed=0; \
for voice_id, rel in voices:\
    model=d/f'{voice_id}.onnx'; cfg=d/f'{voice_id}.onnx.json';\
    if model.exists() and cfg.exists():\
        skipped+=1;\
        continue;\
    try:\
        urllib.request.urlretrieve(f'{base}/{rel}.onnx', model);\
        urllib.request.urlretrieve(f'{base}/{rel}.onnx.json', cfg);\
        downloaded+=1;\
    except Exception:\
        failed+=1;\
print(f'Piper voice seeding complete. downloaded={downloaded} skipped={skipped} failed={failed}.')" \
      || echo 'Piper voice download failed -- deploy-app.sh will retry at runtime.'; \
    fi

# Long-form docs are pre-rendered locally into template partials by
# scripts/build-doc-pages.py and committed under web/src/.../templates/partials.

# Create a non-root user
RUN addgroup --system app && adduser --system --ingroup app app
RUN mkdir -p /app/instance /app/.gunicorn /app/instance/speech_models/piper \
    && chown -R app:app /app/instance /app/.gunicorn

ENV HOME=/app
USER app

EXPOSE 8000

# Run with gunicorn (production WSGI server)
CMD ["gunicorn", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "4", \
    "--timeout", "1800", \
    "--access-logfile", "-", \
    "acb_large_print_web.app:create_app()"]
