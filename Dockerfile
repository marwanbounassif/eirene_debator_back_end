# Use Python 3.9 as base
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development image
FROM builder as dev

# Create required directories
RUN mkdir -p /app/app/logs /app/characters

# Copy application code (will be mounted in docker-compose)
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production image
FROM builder as prod

# Create required directories
RUN mkdir -p /app/app/logs /app/characters

# Copy only necessary files (no dev/test files)
COPY app /app/app/
COPY configs /app/configs/

# Run as non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]