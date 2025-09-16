# Multi-stage build for Terraform Visualizer

# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./
COPY frontend/webpack.config.js ./
COPY frontend/tsconfig.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm install --save-dev typescript ts-loader webpack webpack-cli html-webpack-plugin css-loader style-loader file-loader

# Copy source code
COPY frontend/public ./public
COPY frontend/src ./src

# Build the frontend
RUN npm run build

# Stage 2: Python backend runtime
FROM python:3.12-slim AS runtime

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry: don't create venv, install to system Python
ENV POETRY_VENV_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_VIRTUALENVS_CREATE=false

# Install Python dependencies directly to system Python
RUN poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR

# Copy backend code
COPY backend ./backend
COPY app.py .

# Copy work directory structure
COPY work ./work

# Copy frontend build from previous stage to work directory for versioned builds
COPY --from=frontend-builder /app/frontend/../work/frontend/build ./work/frontend/build

# Copy test Terraform files for visualization (if they exist)
COPY --chown=appuser:appuser test-terraform ./terraform-examples

# Ensure work directory structure exists and set permissions
RUN mkdir -p work/frontend/build && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command - gunicorn is now in system PATH
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
