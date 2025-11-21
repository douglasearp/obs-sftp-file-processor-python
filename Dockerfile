# Dockerfile for obs-sftp-file-processor
FROM python:3.11-slim

# Install system dependencies
# libaio1t64 is required for Oracle Instant Client thick mode (Debian Trixie package name)
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    libaio1t64 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so.1 \
    || true

# Install Oracle Instant Client
# Copy Oracle Instant Client from build context (already extracted)
COPY oracle/instantclient_23_3 /opt/oracle/instantclient_23_3

# Set permissions for Oracle Instant Client
RUN chmod -R 755 /opt/oracle/instantclient_23_3 && \
    echo "Oracle Instant Client installed successfully"

# Verify Oracle Instant Client installation
RUN ls -la /opt/oracle/instantclient_23_3/libclntsh.so* || echo "Warning: Oracle library not found"

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files and README (required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Install Python dependencies using uv
RUN uv sync --frozen

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Oracle Instant Client is installed in the image at /opt/oracle/instantclient_23_3
# Thick mode will be used when ORACLE_HOME is set

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV LANG=C.UTF-8
ENV HOME=/root
ENV ORACLE_HOME=/opt/oracle/instantclient_23_3
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_23_3

# Activate virtual environment and Oracle in PATH
ENV PATH="/app/.venv/bin:/opt/oracle/instantclient_23_3:${PATH}"

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
# Note: For production, remove --reload flag
CMD ["uvicorn", "src.obs_sftp_file_processor.main:app", "--host", "0.0.0.0", "--port", "8000"]