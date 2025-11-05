# Oracle Instant Client Setup for Docker

## Problem
The Docker container cannot find Oracle Instant Client libraries because they are not installed in the Linux container. You're getting this error:
```
DPI-1047: Cannot locate a 64-bit Oracle Client library: "/opt/oracle/instantclient_23_3/libclntsh.so: cannot open shared object file: No such file or directory"
```

## Why This Happens
- Your Mac has macOS Oracle Instant Client (at `~/oracle/instantclient_23_3`)
- Docker runs **Linux** containers, so it needs **Linux x86-64** Oracle Instant Client
- The Docker container's `/opt/oracle/instantclient_23_3` directory is empty

## Solution Options

### Option 1: Mount Oracle Instant Client as Volume (Recommended for Development)

**Steps:**

1. **Download Linux x86-64 Oracle Instant Client:**
   - Visit: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html
   - Accept license agreement
   - Download "Basic Package" (e.g., `instantclient-basic-linux.x64-23.3.0.23.09.zip`)

2. **Extract to project directory:**
   ```bash
   mkdir -p oracle
   cd oracle
   unzip ~/Downloads/instantclient-basic-linux.x64-*.zip
   mv instantclient_* instantclient_23_3
   cd ..
   ```

3. **Update docker-compose.yml:**
   Uncomment the Oracle Instant Client volume mount (line 38):
   ```yaml
   volumes:
     - ./logs:/app/logs
     - ./oracle/instantclient_23_3:/opt/oracle/instantclient_23_3:ro
   ```

4. **Restart Docker:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Option 2: Include in Docker Build

1. Download Linux x86-64 Oracle Instant Client zip file
2. Place it in project root as `instantclient-basic-linux.x64-*.zip`
3. Uncomment the COPY and RUN commands in Dockerfile (lines 88-97)
4. Rebuild:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Option 3: Use Build Argument

```bash
docker-compose build --build-arg ORACLE_INSTANTCLIENT_URL=<download_url>
docker-compose up -d
```

## Verify Installation

After setup, verify Oracle Instant Client is accessible:
```bash
docker exec obs-sftp-file-processor ls -la /opt/oracle/instantclient_23_3/
```

You should see `libclntsh.so` in the output.

## Test Oracle Connection

Once installed, test the connection:
```bash
curl http://localhost:8001/oracle/ach-files?limit=5
```

## Quick Start (Recommended)

```bash
# 1. Download Oracle Instant Client Basic for Linux x86-64
# 2. Extract to ./oracle/instantclient_23_3/
# 3. Uncomment volume mount in docker-compose.yml
# 4. Restart:
docker-compose down && docker-compose up -d
```

