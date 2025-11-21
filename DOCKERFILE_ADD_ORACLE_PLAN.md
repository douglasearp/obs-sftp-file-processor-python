# Plan: Add Oracle Instant Client to Dockerfile for Portainer

## Current State

The Dockerfile currently:
- ✅ Installs `libaio1t64` (required for Oracle)
- ✅ Sets up environment variables (`ORACLE_HOME`, `LD_LIBRARY_PATH`)
- ❌ **Does NOT install Oracle Instant Client** - relies on bind mount
- ❌ Comment says "Using Oracle thin mode" but code uses thick mode

## Problem

When building the Docker image for Portainer:
- The image doesn't include Oracle Instant Client
- Portainer deployment requires either:
  1. Bind mount from Portainer server (current workaround)
  2. Oracle Instant Client baked into the image (better solution)

## Solution: Add Oracle Instant Client to Dockerfile

### Recommended Approach: Copy from Build Context

**Why this approach:**
- ✅ Most reliable (no network dependency during build)
- ✅ Works consistently across environments
- ✅ No authentication/license issues during build
- ✅ Image is self-contained (no bind mount needed)

### Implementation Plan

#### Step 1: Download Oracle Instant Client

**On your local machine:**

1. **Download Linux x86-64 Oracle Instant Client:**
   - Visit: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html
   - Accept license agreement
   - Download "Basic Package" (e.g., `instantclient-basic-linux.x64-23.3.0.23.09.zip`)
   - File size: ~70-100MB

2. **Place in project directory:**
   ```bash
   # Create oracle directory if it doesn't exist
   mkdir -p oracle
   
   # Move downloaded zip to oracle directory
   mv ~/Downloads/instantclient-basic-linux.x64-*.zip oracle/
   ```

3. **Verify file location:**
   ```bash
   ls -lh oracle/instantclient-basic-linux.x64-*.zip
   # Should show the zip file
   ```

#### Step 2: Update .gitignore (Optional)

**If you don't want to commit the zip file to Git:**

Add to `.gitignore`:
```
# Oracle Instant Client (large file)
oracle/instantclient-basic-linux.x64-*.zip
```

**Note:** If you exclude it from Git, you'll need to manually place it in the `oracle/` directory before building the Docker image.

#### Step 3: Update Dockerfile

**Add Oracle Instant Client installation after system dependencies:**

```dockerfile
# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    libaio1t64 \
    unzip \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so.1 \
    || true

# Install Oracle Instant Client
# Copy Oracle Instant Client zip from build context
COPY oracle/instantclient-basic-linux.x64-*.zip /tmp/oracle/

# Extract and install Oracle Instant Client
RUN mkdir -p /opt/oracle && \
    cd /tmp && \
    unzip oracle/instantclient-basic-linux.x64-*.zip -d /opt/oracle && \
    mv /opt/oracle/instantclient_* /opt/oracle/instantclient_23_3 && \
    rm -rf /tmp/oracle && \
    chmod -R 755 /opt/oracle/instantclient_23_3 && \
    echo "Oracle Instant Client installed successfully"

# Verify installation
RUN ls -la /opt/oracle/instantclient_23_3/libclntsh.so* || echo "Warning: Oracle library not found"
```

**Update the comment:**
```dockerfile
# Oracle Instant Client is installed in the image at /opt/oracle/instantclient_23_3
# Thick mode will be used when ORACLE_HOME is set
```

#### Step 4: Build New Image

**On your local machine:**

```bash
# Build the image with Oracle Instant Client included
docker build --platform linux/amd64 -t obs-sftp-file-processor:latest .

# Verify Oracle Instant Client is in the image
docker run --rm obs-sftp-file-processor:latest ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
# Should show the library files

# Export the image
docker save obs-sftp-file-processor:latest -o obs-sftp-file-processor-with-oracle.tar
```

#### Step 5: Import to Portainer

1. **Import the new image** (same as before)
2. **Update container** - you can now **remove the Oracle bind mount** since it's in the image
3. **Keep the environment variable:** `ORACLE_HOME=/opt/oracle/instantclient_23_3`

---

## Alternative: Conditional Installation

If you want to support both scenarios (with and without Oracle in image):

```dockerfile
# Copy Oracle Instant Client zip (if exists in build context)
COPY oracle/instantclient-basic-linux.x64-*.zip /tmp/oracle/ 2>/dev/null || echo "Oracle zip not found, will use bind mount"

# Install Oracle Instant Client if zip exists
RUN if [ -f /tmp/oracle/instantclient-basic-linux.x64-*.zip ]; then \
        mkdir -p /opt/oracle && \
        cd /tmp && \
        unzip oracle/instantclient-basic-linux.x64-*.zip -d /opt/oracle && \
        mv /opt/oracle/instantclient_* /opt/oracle/instantclient_23_3 && \
        rm -rf /tmp/oracle && \
        chmod -R 755 /opt/oracle/instantclient_23_3 && \
        echo "Oracle Instant Client installed in image"; \
    else \
        mkdir -p /opt/oracle/instantclient_23_3 && \
        echo "Oracle Instant Client not in image - use bind mount"; \
    fi
```

**This allows:**
- Building with Oracle included (if zip is in `oracle/` directory)
- Building without Oracle (falls back to bind mount)

---

## Benefits of Including Oracle in Image

### ✅ Advantages:
- **No bind mount needed** on Portainer server
- **Simpler deployment** - just import image and deploy
- **Consistent** - same image works everywhere
- **Self-contained** - image has everything it needs
- **Easier updates** - update image, not server files

### ⚠️ Trade-offs:
- **Larger image size** (~400-500MB instead of ~200MB)
- **Longer build time** (extraction step)
- **Need to download Oracle zip** once and include in build context

---

## File Structure After Changes

```
obs-sftp-file-processor-python/
├── Dockerfile                    # Updated with Oracle installation
├── docker-compose.yml
├── oracle/
│   └── instantclient-basic-linux.x64-23.3.0.23.09.zip  # Oracle Instant Client
├── src/
└── ...
```

---

## Verification Steps

After building the image:

1. **Check image size:**
   ```bash
   docker images obs-sftp-file-processor:latest
   # Should be larger (~400-500MB) due to Oracle Instant Client
   ```

2. **Verify Oracle libraries in image:**
   ```bash
   docker run --rm obs-sftp-file-processor:latest \
     ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
   # Should show library files
   ```

3. **Test Oracle connection:**
   ```bash
   docker run --rm \
     -e ORACLE_HOME=/opt/oracle/instantclient_23_3 \
     -e ORACLE_HOST=10.1.0.111 \
     -e ORACLE_PORT=1521 \
     -e ORACLE_SERVICE_NAME=... \
     -e ORACLE_USERNAME=... \
     -e ORACLE_PASSWORD=... \
     obs-sftp-file-processor:latest \
     python -c "from src.obs_sftp_file_processor.oracle_service import OracleService; print('Oracle works!')"
   ```

---

## Portainer Deployment After Changes

Once Oracle is in the image:

1. **Import the new image** to Portainer
2. **Update container configuration:**
   - Use the new image
   - **Remove Oracle bind mount** (no longer needed)
   - **Keep** `ORACLE_HOME=/opt/oracle/instantclient_23_3` environment variable
   - Keep all other Oracle/SFTP environment variables
3. **Deploy** - Oracle should work without bind mount

---

## Summary

**Current:** Image relies on bind mount from Portainer server  
**After:** Image includes Oracle Instant Client, no bind mount needed

**Steps:**
1. Download Oracle Instant Client zip
2. Place in `oracle/` directory
3. Update Dockerfile to copy and extract it
4. Build new image
5. Export and import to Portainer
6. Deploy without Oracle bind mount

**Result:** Simpler, more portable Docker image that works the same everywhere.


