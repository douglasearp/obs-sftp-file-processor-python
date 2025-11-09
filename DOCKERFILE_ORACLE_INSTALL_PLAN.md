# Plan: Install Oracle Instant Client in Dockerfile (No Bind Mount Needed)

## Goal
Modify the Dockerfile to download and install Oracle Instant Client during the Docker build process, so the Oracle libraries are included in the Docker image itself. This eliminates the need for a bind mount on the Portainer server.

---

## Option 1: Download During Build (Requires License Acceptance)

### How It Works
The Dockerfile would download Oracle Instant Client during the `docker build` process, extract it, and include it in the final image.

### Advantages
- ✅ No bind mount needed on Portainer server
- ✅ Works the same on local and remote
- ✅ Oracle Instant Client is part of the image
- ✅ Simpler deployment (no server-side setup)

### Disadvantages
- ❌ Requires accepting Oracle license during build
- ❌ Download URL may require authentication/cookies
- ❌ Larger Docker image size (~400MB+ for Oracle Instant Client)
- ❌ Build time increases (download + extract)
- ❌ Oracle may change download URLs

### Implementation Approach

**In Dockerfile:**
```dockerfile
# Download Oracle Instant Client during build
RUN mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    # Option A: Use direct download URL (requires license acceptance)
    wget --no-check-certificate \
         --header="Cookie: oraclelicense=accept-securebackup-cookie" \
         https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-23.3.0.23.09.zip && \
    unzip instantclient-basic-linux.x64-*.zip && \
    mv instantclient_* instantclient_23_3 && \
    rm -f instantclient-basic-linux.x64-*.zip && \
    chmod -R 755 instantclient_23_3
```

**Issues with this approach:**
- Oracle's download URLs often require:
  - License acceptance (cookie)
  - Authentication (login)
  - May block automated downloads
- The download URL format may change
- Oracle may detect automated downloads and block them

---

## Option 2: Copy from Build Context (Recommended if Possible)

### How It Works
Include the Oracle Instant Client zip file in your Git repository (or build context), and the Dockerfile copies and extracts it during build.

### Advantages
- ✅ Reliable (no network dependency during build)
- ✅ Works offline
- ✅ Consistent builds
- ✅ No license acceptance needed during build (you accept it once when downloading)

### Disadvantages
- ❌ Oracle Instant Client zip file is large (~70-100MB)
- ❌ Increases repository size
- ❌ May violate Oracle's redistribution terms (check license)
- ❌ Need to update zip file when Oracle releases new version

### Implementation Approach

**In Dockerfile:**
```dockerfile
# Copy Oracle Instant Client zip from build context
COPY oracle/instantclient-basic-linux.x64-*.zip /tmp/oracle/
RUN mkdir -p /opt/oracle && \
    cd /tmp/oracle && \
    unzip instantclient-basic-linux.x64-*.zip -d /opt/oracle && \
    mv /opt/oracle/instantclient_* /opt/oracle/instantclient_23_3 && \
    rm -rf /tmp/oracle && \
    chmod -R 755 /opt/oracle/instantclient_23_3
```

**Repository structure:**
```
obs-sftp-file-processor-python/
├── Dockerfile
├── docker-compose.yml
├── oracle/
│   └── instantclient-basic-linux.x64-23.3.0.23.09.zip  # Include this
└── ...
```

**Note:** Check Oracle's license terms - they may prohibit including the zip in your repository. You might need to:
- Add it to `.gitignore` and provide instructions
- Or use a private artifact repository
- Or download it during CI/CD build process

---

## Option 3: Multi-Stage Build with Oracle Client

### How It Works
Use a multi-stage build where one stage downloads/extracts Oracle Instant Client, and another stage copies it to the final image.

### Advantages
- ✅ Keeps final image smaller (only copies what's needed)
- ✅ Can handle complex extraction logic
- ✅ More control over the process

### Implementation Approach

```dockerfile
# Stage 1: Download and extract Oracle Instant Client
FROM alpine:latest AS oracle-client
RUN apk add --no-cache wget unzip && \
    mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    wget --no-check-certificate \
         --header="Cookie: oraclelicense=accept-securebackup-cookie" \
         https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-23.3.0.23.09.zip && \
    unzip instantclient-basic-linux.x64-*.zip && \
    mv instantclient_* instantclient_23_3

# Stage 2: Main application
FROM python:3.11-slim
# ... existing Dockerfile content ...
# Copy Oracle Instant Client from previous stage
COPY --from=oracle-client /opt/oracle/instantclient_23_3 /opt/oracle/instantclient_23_3
```

---

## Option 4: Build Argument for Download URL

### How It Works
Use a Docker build argument to pass the Oracle Instant Client download URL, allowing flexibility while keeping it optional.

### Advantages
- ✅ Flexible (can provide URL or use bind mount)
- ✅ Can work with different Oracle versions
- ✅ Doesn't require including zip in repository

### Implementation Approach

**In Dockerfile:**
```dockerfile
ARG ORACLE_INSTANTCLIENT_URL=""
ARG ORACLE_INSTANTCLIENT_VERSION="23.3.0.23.09"

# Install Oracle Instant Client if URL provided
RUN if [ -n "$ORACLE_INSTANTCLIENT_URL" ]; then \
        mkdir -p /opt/oracle && \
        cd /opt/oracle && \
        wget --no-check-certificate \
             --header="Cookie: oraclelicense=accept-securebackup-cookie" \
             "$ORACLE_INSTANTCLIENT_URL" -O oracle_client.zip && \
        unzip oracle_client.zip && \
        mv instantclient_* instantclient_23_3 && \
        rm -f oracle_client.zip && \
        chmod -R 755 instantclient_23_3 && \
        echo "Oracle Instant Client installed from URL"; \
    else \
        mkdir -p /opt/oracle/instantclient_23_3 && \
        echo "Oracle Instant Client not included - use bind mount or provide URL"; \
    fi
```

**Build with URL:**
```bash
docker build \
  --build-arg ORACLE_INSTANTCLIENT_URL="https://download.oracle.com/..." \
  -t obs-sftp-file-processor:latest .
```

---

## Recommended Approach for Portainer

### Best Option: Copy from Build Context (Option 2)

**Why:**
- Most reliable for Portainer deployments
- No network dependencies during build
- Works consistently across environments
- No authentication issues

**Implementation Steps:**

1. **Download Oracle Instant Client locally:**
   ```bash
   # Download from Oracle website
   # Save to: ./oracle/instantclient-basic-linux.x64-23.3.0.23.09.zip
   ```

2. **Update .gitignore:**
   ```gitignore
   # Oracle Instant Client (large file, may not want in Git)
   oracle/instantclient-basic-linux.x64-*.zip
   ```

3. **Update Dockerfile:**
   ```dockerfile
   # Copy Oracle Instant Client zip (if exists)
   COPY oracle/instantclient-basic-linux.x64-*.zip /tmp/oracle/ 2>/dev/null || true
   
   # Install Oracle Instant Client
   RUN if [ -f /tmp/oracle/instantclient-basic-linux.x64-*.zip ]; then \
        mkdir -p /opt/oracle && \
        cd /tmp/oracle && \
        unzip instantclient-basic-linux.x64-*.zip -d /opt/oracle && \
        mv /opt/oracle/instantclient_* /opt/oracle/instantclient_23_3 && \
        rm -rf /tmp/oracle && \
        chmod -R 755 /opt/oracle/instantclient_23_3 && \
        echo "Oracle Instant Client installed in image"; \
    else \
        mkdir -p /opt/oracle/instantclient_23_3 && \
        echo "Oracle Instant Client not in build - use bind mount"; \
    fi
   ```

4. **For Portainer:**
   - Include the zip file when building
   - Or use bind mount as fallback

---

## Trade-offs Summary

| Approach | Reliability | Image Size | Build Time | Portainer Ease |
|----------|------------|------------|------------|----------------|
| **Bind Mount** (Current) | ✅ High | ✅ Small | ✅ Fast | ❌ Requires server setup |
| **Copy from Context** | ✅ High | ❌ Large | ✅ Fast | ✅ Easy |
| **Download in Build** | ⚠️ Medium | ❌ Large | ❌ Slow | ✅ Easy |
| **Build Arg URL** | ⚠️ Medium | ❌ Large | ❌ Slow | ⚠️ Medium |

---

## Recommendation

**For Portainer deployment, I recommend:**

1. **Primary:** Include Oracle Instant Client in Dockerfile via COPY (Option 2)
   - Most reliable
   - Works the same everywhere
   - No server-side setup needed

2. **Fallback:** Keep bind mount option available
   - If you can't include zip in repository
   - If image size is a concern
   - If you want to update Oracle Client without rebuilding

**Implementation would involve:**
- Adding Oracle Instant Client zip to build context
- Updating Dockerfile to copy and extract it
- Removing the need for bind mount (but keeping it as optional fallback)
- Image size increases by ~70-100MB

---

## Questions to Consider

1. **Can you include Oracle Instant Client zip in your repository?**
   - Check Oracle license terms
   - Consider repository size limits
   - May need to use `.gitignore` and provide separately

2. **Is image size a concern?**
   - Current image: ~200-300MB
   - With Oracle Client: ~300-400MB
   - Still reasonable for most deployments

3. **Do you need to update Oracle Client frequently?**
   - If yes, bind mount might be better
   - If no, including in image is simpler

4. **Do you have control over Portainer build process?**
   - Can you provide build context with zip file?
   - Or does Portainer build from Git only?

