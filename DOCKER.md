# Docker Deployment Guide

This guide explains how to build and run the obs-sftp-file-processor application using Docker.

## Prerequisites

- Docker installed and running
- Docker Compose (optional, for easier deployment)
- Oracle Instant Client (for thick mode support - optional)

## Quick Start

### Using Docker Compose (Recommended)

1. **Create environment file:**
   ```bash
   cp env.example .env
   cp env.oracle.example .env
   ```
   Edit `.env` with your actual credentials.

2. **Build and run:**
   ```bash
   docker-compose up -d
   ```

3. **Check logs:**
   ```bash
   docker-compose logs -f
   ```

4. **Access the API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

### Using Docker Directly

1. **Build the image:**
   ```bash
   docker build -t obs-sftp-file-processor .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name obs-sftp-file-processor \
     -p 8000:8000 \
     -e SFTP_HOST=10.1.3.123 \
     -e SFTP_PORT=22 \
     -e SFTP_USERNAME=sftpuser1 \
     -e SFTP_PASSWORD=TheNextB1gSFTP## \
     -e ORACLE_HOST=10.1.0.111 \
     -e ORACLE_PORT=1521 \
     -e ORACLE_SERVICE_NAME=PDB_ACHDEV01.privatesubnet1.obsnetwork1.oraclevcn.com \
     -e ORACLE_USERNAME=achowner \
     -e ORACLE_PASSWORD=JV!+x21=Of`jVzW[%)/r@  \
     -e ORACLE_SCHEMA=ACHOWNER \
     -v $(pwd)/logs:/app/logs \
     obs-sftp-file-processor
   ```

## Oracle Instant Client Setup

For thick mode support (required for network encryption), you need to add Oracle Instant Client:

### Option 1: Mount during build

1. Download Oracle Instant Client for Linux x64
2. Extract to `oracle/instantclient_23_3/` directory
3. Uncomment the volume mount in `docker-compose.yml`:
   ```yaml
   volumes:
     - ./oracle/instantclient_23_3:/opt/oracle/instantclient_23_3:ro
   ```

### Option 2: Copy during build

Modify the Dockerfile to copy the Instant Client:

```dockerfile
COPY oracle/instantclient_23_3 /opt/oracle/instantclient_23_3
```

### Option 3: Use thin mode (no Instant Client)

The application will automatically fall back to thin mode if Instant Client is not available. Note that thin mode does not support network encryption.

## Environment Variables

See `env.example` and `env.oracle.example` for all available environment variables.

### Required:
- `SFTP_HOST` - SFTP server hostname
- `SFTP_USERNAME` - SFTP username
- `SFTP_PASSWORD` - SFTP password
- `ORACLE_HOST` - Oracle database host
- `ORACLE_SERVICE_NAME` - Oracle service name
- `ORACLE_USERNAME` - Oracle username
- `ORACLE_PASSWORD` - Oracle password

### Optional:
- `SFTP_PORT` - SFTP port (default: 22)
- `ORACLE_PORT` - Oracle port (default: 1521)
- `ORACLE_SCHEMA` - Oracle schema (default: ACHOWNER)
- `APP_DEBUG` - Enable debug mode (default: false)
- `APP_LOG_LEVEL` - Logging level (default: INFO)

## Building for Production

For production builds, ensure:

1. Remove `--reload` flag in Dockerfile CMD
2. Set `APP_DEBUG=false`
3. Use proper logging configuration
4. Mount Oracle Instant Client if using thick mode
5. Set secure environment variables

## Troubleshooting

### Container won't start
- Check logs: `docker-compose logs`
- Verify environment variables are set
- Ensure ports are not in use

### Oracle connection fails
- Verify Oracle Instant Client is mounted (if using thick mode)
- Check network connectivity to Oracle server
- Verify credentials are correct

### SFTP connection fails
- Verify SFTP server is accessible from container
- Check SFTP credentials
- Test network connectivity

## Health Checks

The container includes a health check that verifies the API is responding:

```bash
docker inspect --format='{{.State.Health.Status}}' obs-sftp-file-processor
```

## Stopping the Container

```bash
# Using docker-compose
docker-compose down

# Using docker directly
docker stop obs-sftp-file-processor
docker rm obs-sftp-file-processor
```
