# ── EquiGuard Dockerfile ──────────────────────────────────────────────────────
# Builds a single image that can run EITHER the backend or the frontend
# depending on the CMD passed via docker-compose.
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# System deps needed by numba / llvmlite / matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash equiguard
WORKDIR /app

# Install Python deps first (cached layer — only rebuilds when requirements change)
COPY requirements.txt .
ENV SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Give ownership to the non-root user
RUN chown -R equiguard:equiguard /app
USER equiguard

# Create directory for the SQLite database
RUN mkdir -p /app/data

# Expose both service ports
EXPOSE 8000 8501

# Default: run the backend (overridden per-service in docker-compose.yml)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
