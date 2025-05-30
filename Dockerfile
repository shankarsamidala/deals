# Use Python 3.10 slim image for smaller size
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy core modules (shared across services)
COPY core/ ./core/

# Copy listener service files
COPY services/listener/ ./services/listener/

# Copy environment file
COPY .env .

# Create logs directory
RUN mkdir -p /app/logs

# Set proper permissions
RUN chmod +x services/listener/main.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; from services.listener.main import TelegramListenerService; \
    service = TelegramListenerService(); \
    result = asyncio.run(service.health_check()); \
    exit(0 if result['status'] == 'healthy' else 1)" || exit 1

# Expose port (for health checks if needed)
EXPOSE 8001

# Run the listener service
CMD ["python", "services/listener/main.py"]