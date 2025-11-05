# Dockerfile for obs-sftp-file-processor
FROM python:3.11-slim

# Install system dependencies
# libaio1t64 is required for Oracle Instant Client thick mode (Debian Trixie package name)
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    wget \
    ca-certificates \
    libaio1t64 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so.1 \
    || true

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

# Install Oracle Instant Client
# Oracle Instant Client can be provided via:
# 1. Build argument (ORACLE_INSTANTCLIENT_URL) - download URL
# 2. Copy from build context (instantclient-basic-linux.x64-*.zip)
# 3. Or mount as volume at runtime (see docker-compose.yml)
#
# To download manually:
# 1. Visit https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html
# 2. Accept license agreement and download "Basic Package"
# 3. Place zip file in project root or use build arg
#
ENV ORACLE_HOME=/opt/oracle/instantclient_23_3
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_23_3

# Build argument for Oracle Instant Client URL
ARG ORACLE_INSTANTCLIENT_URL=""

# Create directory for Oracle Instant Client
RUN mkdir -p /tmp/oracle

# Install Oracle Instant Client
# Note: To include Oracle Instant Client in the image, either:
# 1. Download instantclient-basic-linux.x64-*.zip and place in project root, then rebuild
# 2. Use --build-arg ORACLE_INSTANTCLIENT_URL=<url> when building
# 3. Mount as volume at runtime (see docker-compose.yml volume mount)
RUN mkdir -p /opt/oracle /tmp/oracle && \
    cd /tmp/oracle && \
    # Try to download from URL if provided as build arg
    if [ -n "$ORACLE_INSTANTCLIENT_URL" ]; then \
        echo "Downloading Oracle Instant Client from URL"; \
        wget -q "$ORACLE_INSTANTCLIENT_URL" -O oracle_client.zip && \
        unzip -q oracle_client.zip -d /opt/oracle && \
        rm -f oracle_client.zip; \
    else \
        echo "Oracle Instant Client not included in build."; \
        echo "To install Oracle Instant Client:"; \
        echo "  1. Download from: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html"; \
        echo "  2. Place instantclient-basic-linux.x64-*.zip in project root and rebuild, OR"; \
        echo "  3. Mount as volume at runtime (see docker-compose.yml)"; \
        mkdir -p $ORACLE_HOME; \
    fi && \
    # Rename instantclient directory to expected name if it exists
    if [ -d /opt/oracle/instantclient_* ]; then \
        mv /opt/oracle/instantclient_* $ORACLE_HOME && \
        echo "Oracle Instant Client installed to $ORACLE_HOME"; \
        ls -la $ORACLE_HOME/ | head -10; \
    fi && \
    rm -rf /tmp/oracle

# Note: Oracle Instant Client should be mounted as a volume at runtime
# See docker-compose.yml for volume mount configuration
# Alternatively, you can download and extract during build by:
# 1. Downloading instantclient-basic-linux.x64-*.zip to project root
# 2. Uncommenting the COPY and RUN commands below
# 3. Rebuilding the image
#
# COPY instantclient-basic-linux.x64-*.zip /tmp/oracle/
# RUN cd /tmp/oracle && \
#     ORACLE_ZIP=$(ls instantclient-basic-linux.x64-*.zip | head -1) && \
#     unzip -q "$ORACLE_ZIP" -d /opt/oracle && \
#     rm -f "$ORACLE_ZIP" && \
#     if [ -d /opt/oracle/instantclient_* ]; then \
#         mv /opt/oracle/instantclient_* $ORACLE_HOME && \
#         echo "Oracle Instant Client installed from build"; \
#     fi && \
#     rm -rf /tmp/oracle

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