# Why Local Docker Works But Remote Portainer Doesn't

## Quick Answer

**Local Docker works because:**
- ✅ Oracle Instant Client exists at `./oracle/instantclient_23_3` on your Mac
- ✅ Volume mount in `docker-compose.yml` automatically mounts it
- ✅ Environment variables are set correctly
- ✅ Network access to Oracle/SFTP servers works

**Remote Portainer doesn't work because:**
- ❌ Oracle Instant Client is **NOT on the Portainer server** (or not mounted)
- ❌ Volume mount must be configured **manually in Portainer UI** (not automatic)
- ❌ Environment variables might be missing or incorrect
- ❌ Network access might be different

---

## Detailed Comparison

### 1. Oracle Instant Client Volume Mount

#### Local Docker (Working ✅)

**Configuration in `docker-compose.yml`:**
```yaml
volumes:
  - ${ORACLE_INSTANTCLIENT_PATH:-./oracle/instantclient_23_3}:/opt/oracle/instantclient_23_3:ro
```

**What happens:**
- Docker Compose automatically mounts `./oracle/instantclient_23_3` from your Mac
- This directory exists at: `/Users/dougearp/repos/obs-sftp-file-processor-python/oracle/instantclient_23_3/`
- Contains all Oracle Instant Client libraries (`libclntsh.so`, etc.)
- Container can access them at `/opt/oracle/instantclient_23_3`

**Result:** ✅ Oracle libraries are available in the container

---

#### Remote Portainer (Not Working ❌)

**What's different:**
- Portainer doesn't use `docker-compose.yml` automatically
- Volume mounts must be configured **manually in Portainer UI**
- The mount path must point to a location **on the Portainer server** (not your Mac)

**Common issues:**
1. **Oracle Instant Client not on Portainer server:**
   - The server at `10.1.3.28` doesn't have `/opt/oracle/instantclient_23_3/`
   - Or it's in a different location
   - Empty mount = empty directory in container

2. **Volume mount not configured:**
   - Must manually add bind mount in Portainer UI
   - Container path: `/opt/oracle/instantclient_23_3`
   - Host path: `/opt/oracle/instantclient_23_3` (on server)
   - If not configured, container has empty directory

3. **Wrong host path:**
   - Using relative path like `./oracle/instantclient_23_3` (doesn't work)
   - Must use absolute path on server: `/opt/oracle/instantclient_23_3`

**Result:** ❌ Oracle libraries are NOT available → `DPI-1047` error

---

### 2. Environment Variables

#### Local Docker (Working ✅)

**In `docker-compose.yml`:**
```yaml
environment:
  - ORACLE_HOME=/opt/oracle/instantclient_23_3
  - ORACLE_HOST=${ORACLE_HOST:-10.1.0.111}
  - ORACLE_PORT=${ORACLE_PORT:-1521}
  - ORACLE_SERVICE_NAME=${ORACLE_SERVICE_NAME}
  - ORACLE_USERNAME=${ORACLE_USERNAME}
  - ORACLE_PASSWORD=${ORACLE_PASSWORD}
  # ... etc
```

**What happens:**
- Docker Compose automatically sets all environment variables
- Reads from `.env` file or uses defaults
- `ORACLE_HOME` is set correctly

**Result:** ✅ Environment variables are set

---

#### Remote Portainer (Might Be Missing ❌)

**What's different:**
- Environment variables must be set **manually in Portainer UI**
- If you imported image without configuring, variables might be missing
- `ORACLE_HOME` might not be set → code tries thin mode → fails with encryption error

**Common issues:**
1. **Missing `ORACLE_HOME`:**
   - Code tries thin mode
   - Database requires encryption (thick mode only)
   - Error: `DPY-3001: Native Network Encryption and Data Integrity is only supported in python-oracledb thick mode`

2. **Missing Oracle connection variables:**
   - `ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_SERVICE_NAME`, etc.
   - Connection fails with "connection refused" or "TNS" errors

3. **Missing SFTP variables:**
   - `SFTP_HOST`, `SFTP_PORT`, `SFTP_USERNAME`, `SFTP_PASSWORD`
   - SFTP operations fail

**Result:** ❌ Missing environment variables → connection failures

---

### 3. Network Access

#### Local Docker (Working ✅)

**Network configuration:**
- Docker network can access:
  - Oracle at `10.1.0.111:1521`
  - SFTP at `10.1.3.123:2022`
- Your Mac's network allows these connections

**Result:** ✅ Network connectivity works

---

#### Remote Portainer (Might Be Different ⚠️)

**What's different:**
- Portainer server is at `10.1.3.28` (different network)
- Container network might be different
- Firewall rules might block connections
- Network routing might be different

**Common issues:**
1. **Oracle server not accessible:**
   - Portainer server can't reach `10.1.0.111:1521`
   - Firewall blocking port 1521
   - Network routing issue

2. **SFTP server not accessible:**
   - Portainer server can't reach `10.1.3.123:2022`
   - Firewall blocking port 2022
   - Network routing issue

3. **DNS resolution:**
   - Hostnames might not resolve correctly
   - Use IP addresses instead

**Result:** ⚠️ Network connectivity might fail

---

### 4. Image Differences

#### Local Docker (Working ✅)

**Image:**
- Built locally with all dependencies
- Includes application code
- Uses correct platform (`linux/amd64`)

**Result:** ✅ Image is correct

---

#### Remote Portainer (Might Be Different ⚠️)

**What's different:**
- Image might be older version
- Missing latest code changes
- Built with different settings
- Platform mismatch (ARM64 vs x86-64)

**Common issues:**
1. **Old image:**
   - Using image without latest code
   - Missing bug fixes or features

2. **Platform mismatch:**
   - Image built for wrong architecture
   - Oracle Instant Client for wrong platform

**Result:** ⚠️ Image might be outdated or wrong platform

---

## Diagnostic Checklist

### For Portainer Container:

**Check 1: Oracle Instant Client Volume Mount**
```bash
# In Portainer, check container logs for:
DPI-1047: Cannot locate a 64-bit Oracle Client library
```
- ✅ **If you see this:** Oracle Instant Client is NOT mounted or missing on server
- ✅ **Fix:** Install Oracle Instant Client on Portainer server and configure bind mount

**Check 2: Environment Variables**
```bash
# In Portainer UI, check Environment section:
ORACLE_HOME=/opt/oracle/instantclient_23_3  # Must be set
ORACLE_HOST=10.1.0.111                      # Must be set
ORACLE_PORT=1521                           # Must be set
ORACLE_SERVICE_NAME=...                    # Must be set
ORACLE_USERNAME=...                        # Must be set
ORACLE_PASSWORD=...                        # Must be set
```
- ✅ **If missing:** Add them in Portainer UI

**Check 3: Volume Mount Configuration**
```bash
# In Portainer UI, check Volumes section:
Container: /opt/oracle/instantclient_23_3
Host: /opt/oracle/instantclient_23_3       # Must exist on Portainer server
Read-only: Yes
```
- ✅ **If not configured:** Add bind mount in Portainer UI
- ✅ **If host path doesn't exist:** Install Oracle Instant Client on server

**Check 4: Network Connectivity**
```bash
# Test from Portainer server (if you have SSH access):
curl http://10.1.0.111:1521  # Oracle (might not respond, but should connect)
curl http://10.1.3.123:2022  # SFTP (might not respond, but should connect)
```
- ✅ **If connection refused:** Network/firewall issue
- ✅ **If timeout:** Network routing issue

**Check 5: Container Logs**
```bash
# In Portainer, check container logs for:
- "Using Oracle thick mode" → ✅ Good
- "Thick mode initialization failed" → ❌ Oracle Instant Client issue
- "Failed to create Oracle connection pool" → ❌ Oracle connection issue
- "SFTP connection established" → ✅ Good
- "Failed to connect to SFTP" → ❌ SFTP connection issue
```

---

## Most Common Issue: Oracle Instant Client

**90% of the time, the issue is:**

1. **Oracle Instant Client not on Portainer server**
2. **Volume mount not configured in Portainer UI**

**Solution:**

### Step 1: Install Oracle Instant Client on Portainer Server

**SSH into Portainer server (10.1.3.28):**
```bash
# Create directory
sudo mkdir -p /opt/oracle
cd /opt/oracle

# Download Oracle Instant Client (or upload from your machine)
# Visit: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html
# Download "Basic Package" (instantclient-basic-linux.x64-23.3.0.23.09.zip)

# Extract
unzip instantclient-basic-linux.x64-*.zip
mv instantclient_* instantclient_23_3
chmod -R 755 instantclient_23_3

# Verify
ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
# Should show: libclntsh.so -> libclntsh.so.23.1
```

### Step 2: Configure Volume Mount in Portainer

1. **Go to container in Portainer UI**
2. **Click "Duplicate/Edit"**
3. **Scroll to "Volumes" section**
4. **Click "Bind" tab**
5. **Add volume:**
   - **Container:** `/opt/oracle/instantclient_23_3`
   - **Host:** `/opt/oracle/instantclient_23_3`
   - **Read-only:** ✅ Yes
6. **Verify Environment Variables:**
   - `ORACLE_HOME=/opt/oracle/instantclient_23_3` ✅ Must be set
7. **Click "Deploy the container"**

### Step 3: Verify

**Check container logs:**
- Should see: "Using Oracle thick mode (ORACLE_HOME=/opt/oracle/instantclient_23_3)"
- Should NOT see: "DPI-1047" error

**Test endpoint:**
```bash
curl http://10.88.0.2:8001/oracle/ach-files?limit=2
# Should return data, not error 500
```

---

## Alternative Solution: Include Oracle in Image

**Instead of bind mount, include Oracle Instant Client in the Docker image:**

See: `DOCKERFILE_ADD_ORACLE_PLAN.md`

**Benefits:**
- ✅ No bind mount needed
- ✅ Works the same everywhere
- ✅ Simpler deployment

**Trade-off:**
- ⚠️ Larger image size (~400-500MB)

---

## Summary

| Aspect | Local Docker | Remote Portainer | Issue |
|--------|-------------|------------------|-------|
| **Oracle Instant Client** | ✅ Exists locally, auto-mounted | ❌ Must be on server, manually mounted | **Most common issue** |
| **Volume Mount** | ✅ Automatic via docker-compose.yml | ❌ Must configure in Portainer UI | **Most common issue** |
| **Environment Variables** | ✅ Automatic via docker-compose.yml | ⚠️ Must set manually in Portainer UI | Common issue |
| **Network Access** | ✅ Works from your Mac | ⚠️ Might be different on server | Less common |
| **Image** | ✅ Built locally | ⚠️ Might be older version | Less common |

**Most likely cause:** Oracle Instant Client not mounted or not on Portainer server.

**Quick fix:** Install Oracle Instant Client on Portainer server and configure bind mount in Portainer UI.


