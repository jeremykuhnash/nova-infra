# Multi-stage build for Terraform Visualizer

# Stage 1: Base image with common dependencies
FROM python:3.12-slim AS base

# Install system dependencies
# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gcc \
    git \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
# hadolint ignore=DL3013
RUN pip install --no-cache-dir poetry==1.8.0

WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry: don't create venv, install to system Python
ENV POETRY_VENV_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_VIRTUALENVS_CREATE=false

# Stage 2: Development/Test stage for CI
FROM base AS test

# Install all dependencies including dev dependencies
RUN poetry install --no-root && rm -rf "$POETRY_CACHE_DIR"

# Copy all application code
COPY backend ./backend
COPY tests ./tests
COPY app.py .
COPY Makefile .

# Create work directory for test outputs
RUN mkdir -p work/coverage work/ruff work/mypy work/pytest

# Run tests by default in this stage
CMD ["make", "test"]

# Stage 3: Frontend builder
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./
COPY frontend/webpack.config.js ./
COPY frontend/tsconfig.json ./

# Install dependencies
# hadolint ignore=DL3016
RUN npm ci --only=production && \
    npm install --save-dev typescript ts-loader webpack webpack-cli html-webpack-plugin css-loader style-loader file-loader

# Copy source code
COPY frontend/public ./public
COPY frontend/src ./src

# Build the frontend (outputs to ../work/frontend/build)
RUN npm run build

# Stage 4: Frontend test stage
FROM node:18-alpine AS frontend-test

WORKDIR /app/frontend

# Copy package files and install all dependencies including dev
COPY frontend/package*.json ./
RUN npm ci

# Copy source code
COPY frontend/ ./

# Run linting and tests
RUN npm run lint || true
RUN npm run build

# Stage 5: Production runtime
FROM base AS production

# Install only production dependencies
RUN poetry install --only=main --no-root && rm -rf "$POETRY_CACHE_DIR"

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy backend code
COPY backend ./backend
COPY app.py .

# Create work directory structure (don't copy from host)
RUN mkdir -p work

# Copy frontend build from builder stage (from ../work/frontend/build)
COPY --from=frontend-builder /app/work/frontend/build ./static

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
