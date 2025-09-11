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
FROM python:3.11-slim AS runtime

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend ./backend
COPY app.py .

# Copy frontend build from previous stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Copy test Terraform files for visualization (if they exist)
COPY --chown=appuser:appuser test-terraform ./terraform-examples

# Create work directory for tf_entities.json
RUN mkdir -p work/build && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Run the application with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "60", "backend.api:app"]
