# Portainer Deployment Guide

This guide explains how to deploy the `obs-sftp-file-processor` Docker image to Portainer at `https://10.1.3.28:9443/`.

## Prerequisites

- Docker installed and running
- Access to Portainer at `https://10.1.3.28:9443/`
- Network connectivity between your machine and Portainer server
- Oracle Instant Client files available (for volume mounting)

## Method 1: Save Image as Tar and Import via Portainer UI (Recommended for Direct Deployment)

### Step 1: Build and Tag the Image

```bash
# Build the image with a specific tag
docker build --platform linux/amd64 -t obs-sftp-file-processor:latest .

# Tag it with a descriptive name
docker tag obs-sftp-file-processor:latest obs-sftp-file-processor:portainer
```

### Step 2: Save the Image to a Tar File

```bash
# Save the image to a tar file
docker save obs-sftp-file-processor:latest -o obs-sftp-file-processor.tar

# Compress it (optional, but recommended for large images)
gzip obs-sftp-file-processor.tar
# This creates: obs-sftp-file-processor.tar.gz
```

**Note:** The image is ~400MB, compressed will be ~150-200MB.

### Step 3: Import via Portainer UI

1. **Access Portainer:**
   - Navigate to `https://10.1.3.28:9443/`
   - Log in to Portainer

2. **Navigate to Images:**
   - Go to **Environments** → Select your environment
   - Click on **Images** in the left sidebar

3. **Import Image:**
   - Click **Import image from file** or **Upload** button
   - Select the `obs-sftp-file-processor.tar.gz` file
   - Wait for upload and import to complete

4. **Verify Image:**
   - Check that `obs-sftp-file-processor:latest` appears in the images list

### Step 4: Deploy Container

1. **Create Container:**
   - Go to **Containers** → **Add container**
   
2. **Configure Container:**
   - **Name:** `obs-sftp-file-processor`
   - **Image:** `obs-sftp-file-processor:latest`
   - **Restart policy:** `Unless stopped`

3. **Port Mapping:**
   - Click **Publish a new network port**
   - **Host port:** `8001` (or your preferred port)
   - **Container port:** `8000`

4. **Environment Variables:**
   Add the following environment variables:
   ```
   SFTP_HOST=10.1.3.123
   SFTP_PORT=22
   SFTP_USERNAME=sftpuser1
   SFTP_PASSWORD=<your-sftp-password>
   
   ORACLE_HOST=10.1.0.111
   ORACLE_PORT=1521
   ORACLE_SERVICE_NAME=<your-oracle-service-name>
   ORACLE_USERNAME=<your-oracle-username>
   ORACLE_PASSWORD=<your-oracle-password>
   ORACLE_SCHEMA=ACHOWNER
   ORACLE_HOME=/opt/oracle/instantclient_23_3
   
   APP_DEBUG=false
   APP_LOG_LEVEL=INFO
   PYTHONUNBUFFERED=1
   ```

5. **Volumes:**
   - **Bind Mount:** `/opt/oracle/instantclient_23_3` (host path) → `/opt/oracle/instantclient_23_3` (container path)
     - **Host path:** Path to your Oracle Instant Client directory on the Portainer server
     - **Container path:** `/opt/oracle/instantclient_23_3`
     - **Read-only:** Yes
   
   - **Bind Mount:** `/app/logs` (host path) → `/app/logs` (container path)
     - **Host path:** `/path/to/logs` (create this directory on the server)
     - **Container path:** `/app/logs`

6. **Health Check:**
   - **Test:** `CMD-SHELL curl -f http://localhost:8000/health || exit 1`
   - **Interval:** `30s`
   - **Timeout:** `10s`
   - **Retries:** `3`
   - **Start period:** `40s`

7. **Deploy:**
   - Click **Deploy the container**

---

## Method 2: Push to Docker Registry and Pull from Portainer

### Step 1: Tag Image for Registry

```bash
# Tag with your registry URL
docker tag obs-sftp-file-processor:latest 10.1.3.28:5000/obs-sftp-file-processor:latest

# Or if using Docker Hub:
docker tag obs-sftp-file-processor:latest yourusername/obs-sftp-file-processor:latest
```

### Step 2: Push to Registry

```bash
# For private registry:
docker push 10.1.3.28:5000/obs-sftp-file-processor:latest

# For Docker Hub:
docker login
docker push yourusername/obs-sftp-file-processor:latest
```

### Step 3: Pull Image in Portainer

1. Go to **Images** in Portainer
2. Click **Pull image**
3. Enter image name: `10.1.3.28:5000/obs-sftp-file-processor:latest` (or your Docker Hub image)
4. Click **Pull the image**

---

## Method 3: Use Docker Save/Load on Portainer Server

### Step 1: Save Image Locally

```bash
docker save obs-sftp-file-processor:latest | gzip > obs-sftp-file-processor.tar.gz
```

### Step 2: Transfer to Portainer Server

```bash
# Using SCP
scp obs-sftp-file-processor.tar.gz user@10.1.3.28:/tmp/

# Or using rsync
rsync -avz obs-sftp-file-processor.tar.gz user@10.1.3.28:/tmp/
```

### Step 3: Load on Portainer Server

SSH into the Portainer server and run:

```bash
# SSH into server
ssh user@10.1.3.28

# Load the image
docker load < /tmp/obs-sftp-file-processor.tar.gz

# Verify
docker images | grep obs-sftp-file-processor
```

### Step 4: Deploy in Portainer

Follow **Step 4** from Method 1 above.

---

## Method 4: Deploy Using docker-compose.yml in Portainer

### Step 1: Prepare docker-compose.yml

Create a `docker-compose.yml` file suitable for Portainer deployment:

```yaml
version: '3.8'

services:
  obs-sftp-file-processor:
    image: obs-sftp-file-processor:latest
    container_name: obs-sftp-file-processor
    platform: linux/amd64
    ports:
      - "8001:8000"
    environment:
      - SFTP_HOST=${SFTP_HOST:-10.1.3.123}
      - SFTP_PORT=${SFTP_PORT:-22}
      - SFTP_USERNAME=${SFTP_USERNAME:-sftpuser1}
      - SFTP_PASSWORD=${SFTP_PASSWORD}
      - ORACLE_HOST=${ORACLE_HOST:-10.1.0.111}
      - ORACLE_PORT=${ORACLE_PORT:-1521}
      - ORACLE_SERVICE_NAME=${ORACLE_SERVICE_NAME}
      - ORACLE_USERNAME=${ORACLE_USERNAME}
      - ORACLE_PASSWORD=${ORACLE_PASSWORD}
      - ORACLE_SCHEMA=${ORACLE_SCHEMA:-ACHOWNER}
      - ORACLE_HOME=/opt/oracle/instantclient_23_3
      - APP_DEBUG=${APP_DEBUG:-false}
      - APP_LOG_LEVEL=${APP_LOG_LEVEL:-INFO}
      - PYTHONUNBUFFERED=1
    volumes:
      - /path/to/oracle/instantclient_23_3:/opt/oracle/instantclient_23_3:ro
      - /path/to/logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Step 2: Deploy via Portainer Stack

1. Go to **Stacks** in Portainer
2. Click **Add stack**
3. **Name:** `obs-sftp-file-processor`
4. **Web editor:** Paste the docker-compose.yml content
5. **Environment variables:** Add your secrets (SFTP_PASSWORD, ORACLE_PASSWORD, etc.)
6. Click **Deploy the stack**

---

## Important Notes

### Oracle Instant Client Setup on Portainer Server

Before deploying, ensure Oracle Instant Client is available on the Portainer server:

```bash
# On the Portainer server (10.1.3.28), extract Oracle Instant Client:
mkdir -p /opt/oracle
cd /opt/oracle
# Upload and extract instantclient-basic-linux.x64-*.zip
unzip instantclient-basic-linux.x64-*.zip
mv instantclient_* instantclient_23_3
```

### Network Configuration

Ensure the Portainer server can access:
- **SFTP Server:** `10.1.3.123:22`
- **Oracle Database:** `10.1.0.111:1521`

### Security Considerations

- Use Portainer's **Secrets** feature for sensitive environment variables
- Ensure SSL/TLS certificates are properly configured for Portainer
- Consider using a private Docker registry instead of direct file transfer

### Verification

After deployment, verify the container:

```bash
# In Portainer, check container logs
# Or via SSH:
docker logs obs-sftp-file-processor

# Test health endpoint
curl http://10.1.3.28:8001/health
```

---

## Troubleshooting

### Image Import Fails

- Check file size limits in Portainer settings
- Ensure the tar file isn't corrupted
- Try compressing with `gzip` if file is too large

### Container Won't Start

- Verify all environment variables are set
- Check Oracle Instant Client volume mount path
- Review container logs in Portainer

### Oracle Connection Fails

- Verify Oracle Instant Client is mounted correctly
- Check `ORACLE_HOME` environment variable
- Ensure network connectivity to Oracle server

### Port Conflicts

- Change host port mapping if 8001 is already in use
- Update Portainer port mapping: `8002:8000` (or your preferred port)

---

## Quick Reference Commands

```bash
# Build image
docker build --platform linux/amd64 -t obs-sftp-file-processor:latest .

# Save image
docker save obs-sftp-file-processor:latest | gzip > obs-sftp-file-processor.tar.gz

# Load on server
docker load < obs-sftp-file-processor.tar.gz

# Verify
docker images | grep obs-sftp-file-processor
```

---

For more information, see:
- [Portainer Documentation](https://docs.portainer.io/)
- [Docker Documentation](https://docs.docker.com/)

