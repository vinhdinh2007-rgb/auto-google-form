# ───────────────────────────────────────────────
# Stage 1: Build — install Python dependencies
# ───────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install only production dependencies into a virtual-env
# so we can COPY it cleanly into the runtime stage.
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ───────────────────────────────────────────────
# Stage 2: Runtime — slim production image
# ───────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Install Chromium + ChromeDriver (needed for Selenium)
RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -g 1001 autogg \
    && useradd -u 1001 -g autogg -m -s /bin/bash autogg

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder --chown=autogg:autogg /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY --chown=autogg:autogg app/ ./app/
COPY --chown=autogg:autogg templates/ ./templates/
COPY --chown=autogg:autogg static/ ./static/
COPY --chown=autogg:autogg auto.py .

# Tell Selenium where to find Chromium inside the container
ENV AUTOGG_CHROME_BINARY="/usr/bin/chromium"
ENV AUTOGG_CHROMEDRIVER="/usr/bin/chromedriver"
ENV AUTOGG_HEADLESS="true"
ENV AUTOGG_HOST="0.0.0.0"
ENV AUTOGG_PORT="5000"

EXPOSE 5000

# Switch to non-root user
USER autogg

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run with gunicorn in production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "auto:app"]
