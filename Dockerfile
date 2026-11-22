# syntax=docker/dockerfile:1
FROM python:3.11-slim

LABEL maintainer="Omer Ninyo <omer@rightsub.io>"
LABEL description="RightSub — Universal Subtitle Mastering & Webhook Daemon for Sonarr, Radarr, and Bazarr"

# Prevent Python from writing .pyc files, enable unbuffered logging, and persist config
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RIGHTSUB_HOST=0.0.0.0
ENV RIGHTSUB_PORT=8775
ENV RIGHTSUB_CONFIG_DIR=/config

# Install system dependencies (ffmpeg for subtitle extraction and ca-certificates for HTTPS)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /config

WORKDIR /app

# Copy application runtime files (.dockerignore excludes tests/docs/scratch/.git)
COPY . .

# Expose Webhook server port
EXPOSE 8775

# Container healthcheck querying the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + str(os.environ.get('RIGHTSUB_PORT', 8775)) + '/health')" || exit 1

# Default command starts the Seed-Safe Webhook daemon and Web UI
CMD ["python3", "rightsub.py", "serve", "--seed-safe"]
