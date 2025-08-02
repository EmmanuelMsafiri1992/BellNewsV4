# Use a specific tag to ensure we get the right version
FROM python:3.12.8-slim-bookworm

# Install ALL dependencies in one layer to avoid cache issues
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    build-essential \
    libc6-dev \
    make \
    libasound2-dev \
    alsa-utils \
    libasound2 \
    portaudio19-dev \
    libsndfile1 \
    pkg-config \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify we have the right Python version
RUN python3 --version && which python3

WORKDIR /bellapp

# Copy and install requirements
COPY requirements.txt .
RUN python3 -m venv venv
RUN venv/bin/pip install --upgrade pip setuptools wheel
RUN venv/bin/pip install --no-cache-dir -v -r requirements.txt

# Copy application
COPY . .

# Optional: Clean up build deps (comment out if issues persist)
# RUN apt-get update && apt-get purge -y \
#     gcc g++ python3-dev build-essential libc6-dev make pkg-config libffi-dev \
#     && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

EXPOSE 5000 5001
ENV PYTHONUNBUFFERED=1
ENV IN_DOCKER=1
CMD ["venv/bin/python3", "launch_vcns_timer.py"]