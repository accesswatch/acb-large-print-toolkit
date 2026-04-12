FROM python:3.13-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
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
