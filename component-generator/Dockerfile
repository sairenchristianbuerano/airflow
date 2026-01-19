# Airflow Component Generator - Docker Image

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create data directories
RUN mkdir -p /app/data/generated_operators

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ANTHROPIC_API_KEY=""
ENV PORT=8095

# Expose port
EXPOSE 8095

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8095/api/airflow/component-generator/health')"

# Run the service
CMD ["python", "-m", "uvicorn", "src.service:app", "--host", "0.0.0.0", "--port", "8095"]
