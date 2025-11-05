# Dockerfile for obs-sftp-file-processor
FROM python:3.11-slim

# Install system dependencies
# Note: libaio1 is optional (only needed for Oracle Instant Client thick mode)
# If Oracle thick mode is required, install libaio1 separately or use a non-slim base image
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

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

# Set Oracle environment variables (will be set if Instant Client is added)
ENV ORACLE_HOME=/opt/oracle/instantclient_23_3
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_23_3

# Create Oracle directory (can be populated with Instant Client)
RUN mkdir -p $ORACLE_HOME

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

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