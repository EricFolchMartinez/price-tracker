FROM python:3.10-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Build deps (kept as a safety net for ARM64 wheels). curl is used by the healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user. uid 1000 matches the 'tusk' user on the Raspberry Pi,
# so the bind-mounted ./data and ./logs are writable without chown gymnastics.
RUN useradd --uid 1000 --create-home --shell /bin/bash appuser \
    && mkdir -p /app/data /app/logs \
    && chown -R appuser:appuser /app
USER appuser

VOLUME /app/data
VOLUME /app/logs

EXPOSE 8501
EXPOSE 8000

# Streamlit exposes a health endpoint we can probe.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8501/_stcore/health || exit 1

CMD ["python", "src/run_services.py"]
