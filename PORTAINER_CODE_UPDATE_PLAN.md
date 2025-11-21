# Plan: Update Code in Portainer Without Breaking Oracle Installation

## Current Setup Analysis

### Portainer Container Configuration
- **Container**: `obs-sftp-file-processor` (or similar name)
- **Port**: `8001` (host) → `8000` (container)
- **Oracle Setup**: 
  - Oracle Instant Client installed via **bind mount** from Portainer server
  - Host path: `/opt/oracle/instantclient_23_3` (on Portainer server)
  - Container path: `/opt/oracle/instantclient_23_3`
  - Environment variable: `ORACLE_HOME=/opt/oracle/instantclient_23_3`
  - Volume mount configured in Portainer UI (not docker-compose.yml)

### Code Location
- Code is **baked into the Docker image** (not mounted as volume)
- Application code is in `/app` directory inside container
- Dependencies installed during image build

---

## ⚠️ IMPORTANT: Use Pre-Built Image File

**DO NOT try to build from Git or Dockerfile in Portainer** - you'll get this error:
```
stat /var/tmp/libpod_builder.../build/Dockerfile: no such file or directory
```

**Solution:** Use the pre-built `.tar` image file instead (Option 1 below).

---

## Update Strategy Options

### Option 1: Use Pre-Built Image File (Recommended - Easiest)

**Pros:**
- ✅ Clean, reproducible deployment
- ✅ Includes all latest code changes
- ✅ Preserves Oracle setup if done correctly
- ✅ Standard Docker workflow

**Cons:**
- ⚠️ Requires image rebuild
- ⚠️ Container will restart (brief downtime)

**Steps:**

1. **Build New Docker Image Locally:**
   ```bash
   # From your local machine
   cd /Users/dougearp/repos/obs-sftp-file-processor-python
   
   # Build the image
   docker build -t obs-sftp-file-processor:latest .
   ```

2. **Export Image for Portainer:**
   ```bash
   # Save image to tar file (this creates the file in your project root)
   docker save obs-sftp-file-processor:latest -o obs-sftp-file-processor-updated.tar
   ```
   
   **File Location:** The file will be created in your project root directory:
   - **File:** `obs-sftp-file-processor-updated.tar` (~370MB)
   - **Location:** `/Users/dougearp/repos/obs-sftp-file-processor-python/obs-sftp-file-processor-updated.tar`
   
   **Note:** Compression is optional. Portainer accepts both `.tar` and `.tar.gz` files.

3. **Import Image into Portainer:**
   - Go to Portainer UI: `https://10.1.3.28:9443/`
   - Navigate to **Images** (left sidebar)
   - Click **Import image from file** or **Upload** button
   - **Select the file:** `obs-sftp-file-processor-updated.tar`
   - **File location:** Project root directory (`/Users/dougearp/repos/obs-sftp-file-processor-python/`)
   - Wait for upload and import to complete (may take a few minutes for ~370MB file)
   - Verify the image appears in the images list

4. **Update Container in Portainer:**
   - Go to **Containers** → Find `obs-sftp-file-processor`
   - Click **Duplicate/Edit**
   - **IMPORTANT: Preserve these settings:**
     - **Image**: Select the newly imported image (or update tag to `latest`)
     - **Volumes**: 
       - ✅ Keep the Oracle bind mount:
         - Container: `/opt/oracle/instantclient_23_3`
         - Host: `/opt/oracle/instantclient_23_3`
         - Read-only: ✅ Yes
     - **Environment Variables**:
       - ✅ Keep `ORACLE_HOME=/opt/oracle/instantclient_23_3`
       - ✅ Keep all other Oracle config (ORACLE_HOST, ORACLE_PORT, etc.)
       - ✅ Keep SFTP config
   - Click **Deploy the container**
   - **Stop the old container first** (if Portainer doesn't do it automatically)

5. **Verify Oracle Still Works:**
   - Check container logs in Portainer
   - Look for: `"Using Oracle thick mode (ORACLE_HOME=/opt/oracle/instantclient_23_3)"`
   - Test endpoint: `curl http://10.88.0.2:8001/oracle/ach-files?limit=1`
   - Should return data, not Oracle errors

---

### Option 2: Build from Git in Portainer (⚠️ NOT RECOMMENDED)

**⚠️ WARNING:** This method often fails with the error:
```
stat /var/tmp/libpod_builder.../build/Dockerfile: no such file or directory
```

**Why it fails:**
- Portainer's build context may not include the Dockerfile
- Git repository structure may not match expected paths
- Build context issues with Portainer's build system

**If you must try this method:**

1. **In Portainer UI:**
   - Go to **Images** → **Build image**
   - **Build method**: Git repository
   - **Repository URL**: `https://github.com/douglasearp/obs-sftp-file-processor-python`
   - **Reference**: `main` (or your branch)
   - **Dockerfile location**: `Dockerfile` (must be in root of repo)
   - Click **Build the image**

2. **If build fails:**
   - Use Option 1 (pre-built image file) instead
   - This is the most reliable method

**Recommendation:** Use Option 1 (pre-built image file) to avoid build errors.

---

### Option 3: Update via Code Volume Mount (If Applicable)

**Only if code is currently mounted as volume:**

1. **Check Current Volume Mounts:**
   - In Portainer, go to container → **Volumes** tab
   - Check if `/app` or `/app/src` is mounted from host

2. **If Code is Mounted:**
   - Update code on Portainer server at the mount path
   - Restart container (code changes will be reflected)
   - **No Oracle impact** (Oracle is separate volume)

3. **If Code is NOT Mounted:**
   - Use Option 1 or 2 instead

---

## Critical Preservation Checklist

When updating the container, **MUST preserve:**

### ✅ Volume Mounts
- [ ] Oracle Instant Client bind mount:
  - Container: `/opt/oracle/instantclient_23_3`
  - Host: `/opt/oracle/instantclient_23_3`
  - Read-only: ✅ Yes
- [ ] Logs volume (if configured):
  - Container: `/app/logs`
  - Host: (wherever logs are stored)

### ✅ Environment Variables
- [ ] `ORACLE_HOME=/opt/oracle/instantclient_23_3` ⚠️ **CRITICAL**
- [ ] `ORACLE_HOST=10.1.0.111` (or your Oracle host)
- [ ] `ORACLE_PORT=1521`
- [ ] `ORACLE_SERVICE_NAME=...`
- [ ] `ORACLE_USERNAME=...`
- [ ] `ORACLE_PASSWORD=...`
- [ ] `ORACLE_SCHEMA=ACHOWNER`
- [ ] All SFTP configuration variables
- [ ] `PYTHONUNBUFFERED=1`

### ✅ Port Mapping
- [ ] Host port: `8001` → Container port: `8000`

### ✅ Platform
- [ ] Platform: `linux/amd64` (required for Oracle Instant Client)

---

## Step-by-Step: Safest Update Process

### Pre-Update Verification

1. **Document Current Configuration:**
   - In Portainer, go to container → **Duplicate/Edit**
   - **Screenshot or note down:**
     - All environment variables
     - All volume mounts (especially Oracle)
     - Port mappings
     - Platform setting
   - **Don't save** - just document

2. **Test Current Oracle Connection:**
   ```bash
   curl http://10.88.0.2:8001/oracle/ach-files?limit=1
   # Should return JSON data
   ```

3. **Check Container Logs:**
   - In Portainer → Container → **Logs**
   - Verify: `"Using Oracle thick mode (ORACLE_HOME=/opt/oracle/instantclient_23_3)"`
   - Note any current errors

### Update Process

1. **Build/Import New Image** (Option 1 or 2 above)

2. **Update Container:**
   - Go to container → **Duplicate/Edit**
   - Update image to new version
   - **Verify all settings match your documentation**
   - **Double-check Oracle volume mount is still there**
   - Click **Deploy the container**

3. **Post-Update Verification:**
   - Check logs for Oracle initialization
   - Test Oracle endpoint: `curl http://10.88.0.2:8001/oracle/ach-files?limit=1`
   - Test new endpoints (if any)
   - Verify health check: `curl http://10.88.0.2:8001/health`

### Rollback Plan

If Oracle breaks after update:

1. **Revert to Previous Image:**
   - In Portainer → Container → **Duplicate/Edit**
   - Change image back to previous version
   - **Ensure Oracle volume mount is still configured**
   - Deploy

2. **Verify Oracle Works:**
   - Check logs
   - Test endpoint

---

## Common Pitfalls to Avoid

### ❌ DON'T:
- Remove the Oracle volume mount when updating
- Change `ORACLE_HOME` environment variable
- Change the container path `/opt/oracle/instantclient_23_3`
- Use a different platform (must be `linux/amd64`)
- Forget to preserve environment variables

### ✅ DO:
- Document current config before updating
- Verify Oracle volume mount after update
- Test Oracle connection immediately after update
- Keep backup of working image/container config

---

## Quick Reference: Oracle Setup Requirements

**For Oracle to work, these must be preserved:**

1. **Volume Mount:**
   ```
   Host: /opt/oracle/instantclient_23_3
   Container: /opt/oracle/instantclient_23_3
   Type: Bind
   Read-only: Yes
   ```

2. **Environment Variable:**
   ```
   ORACLE_HOME=/opt/oracle/instantclient_23_3
   ```

3. **Platform:**
   ```
   linux/amd64
   ```

4. **Oracle Instant Client on Server:**
   ```
   /opt/oracle/instantclient_23_3/libclntsh.so must exist
   ```

---

## Summary

**Recommended Approach:** Option 1 (Rebuild and Import)

**Key Points:**
1. Build new image with updated code
2. Export and import to Portainer
3. Update container configuration
4. **CRITICAL**: Preserve Oracle volume mount and `ORACLE_HOME` environment variable
5. Verify Oracle still works after update

**Time Estimate:** 15-30 minutes (depending on image size and network speed)

**Risk Level:** Low (if you preserve Oracle configuration) ⚠️ Medium (if you forget to preserve Oracle mount)

