# Multi-stage build for CCC - Covenant Command Cycle
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 cccuser && \
    chown -R cccuser:cccuser /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/cccuser/.local

# Copy application code
COPY --chown=cccuser:cccuser . .

# Make sure scripts are executable
RUN chmod +x proxy_server.py 2>/dev/null || true

# Switch to non-root user
USER cccuser

# Add local bin to PATH
ENV PATH=/home/cccuser/.local/bin:$PATH

# Expose the proxy server port
EXPOSE 5111

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5111/health', timeout=5)" || exit 1

# Run the proxy server
CMD ["python", "proxy_server.py"]
