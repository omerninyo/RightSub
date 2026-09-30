# syntax=docker/dockerfile:1
FROM python:3.11-slim

LABEL maintainer="Omer Ninyo <omer@rightsub.io>"
LABEL description="RightSub — Universal Subtitle Mastering & Webhook Daemon for Sonarr, Radarr, and Bazarr"

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RIGHTSUB_HOST=0.0.0.0
ENV RIGHTSUB_PORT=8775

# Install system dependencies (ffmpeg for subtitle extraction and media probing)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose Webhook server port
EXPOSE 8775

# Container healthcheck querying the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:' + str(__import__('os').environ.get('RIGHTSUB_PORT', 8775)) + '/health')" || exit 1

# Default command starts the Webhook daemon
CMD ["python3", "rightsub.py", "serve"]
