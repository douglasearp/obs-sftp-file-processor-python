# Troubleshooting: New Portainer Build Not Working

## Working vs New Build Comparison

### Working Portainer Container (from Task-000005-build-portainer)

**Image:** `obs-sftp-file-processor:portainer-v2@sha256:065200fe34abe62b6b2bcbaf9271f80693fb23036e2c513e81cb150c5af8d035`

**Environment Variables:**
- `container=podman` ⚠️ (Note: Portainer is using Podman, not Docker)
- `LD_LIBRARY_PATH=/opt/oracle/instantclient_23_3`
- `ORACLE_HOME=/opt/oracle/instantclient_23_3`
- `PATH=/app/.venv/bin:/opt/oracle/instantclient_23_3:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
- `PYTHONPATH=/app`
- `PYTHONUNBUFFERED=1`
- `LANG=C.UTF-8`
- `HOME=/root`

**Port:** `0.0.0.0:8001 → 8000/tcp`

**CMD:** `uvicorn src.obs_sftp_file_processor.main:app --host 0.0.0.0 --port 8000`

---

### New Build (What We Created)

**Image:** `obs-sftp-file-processor:portainer-v2` (new SHA256)

**Environment Variables (in Dockerfile):**
- `ORACLE_HOME=/opt/oracle/instantclient_23_3` ✅
- `LD_LIBRARY_PATH=/opt/oracle/instantclient_23_3` ✅
- `PATH=/app/.venv/bin:/opt/oracle/instantclient_23_3:${PATH}` ✅
- `PYTHONPATH=/app` ✅
- `PYTHONUNBUFFERED=1` ✅

**Missing from new build:**
- `LANG=C.UTF-8` ⚠️
- `HOME=/root` ⚠️
- `container=podman` (this is set by Portainer/Podman, not Dockerfile)

---

## Potential Issues

### Issue 1: Oracle Instant Client Not Accessible

**Symptoms:**
- Error: `DPI-1047: Cannot locate a 64-bit Oracle Client library`
- Error: `Thick mode initialization failed`

**Possible Causes:**
1. **Oracle libraries not in image** (unlikely, we verified)
2. **Permissions issue** - libraries not executable
3. **Architecture mismatch** - wrong Oracle Instant Client version
4. **Path issue** - `LD_LIBRARY_PATH` not set correctly at runtime

**Diagnosis:**
```bash
# In Portainer, go to container → Console
# Run these commands:

# Check if Oracle directory exists
ls -la /opt/oracle/instantclient_23_3

# Check if libraries exist
ls -la /opt/oracle/instantclient_23_3/libclntsh.so*

# Check environment variables
env | grep ORACLE
env | grep LD_LIBRARY_PATH

# Check file permissions
file /opt/oracle/instantclient_23_3/libclntsh.so.23.1
```

**Fix:**
- If libraries don't exist: Oracle wasn't copied into image correctly
- If permissions wrong: `chmod +x /opt/oracle/instantclient_23_3/libclntsh.so*`
- If environment variables missing: Set them in Portainer UI

---

### Issue 2: Environment Variables Not Set in Portainer

**Symptoms:**
- Container starts but Oracle connection fails
- Logs show "thin mode" instead of "thick mode"

**Diagnosis:**
Check Portainer container configuration:
1. Go to container → **Duplicate/Edit**
2. Check **Environment** section
3. Verify these are set:
   - `ORACLE_HOME=/opt/oracle/instantclient_23_3`
   - `LD_LIBRARY_PATH=/opt/oracle/instantclient_23_3`

**Fix:**
Add missing environment variables in Portainer UI

---

### Issue 3: Bind Mount Still Configured (Conflicting)

**Symptoms:**
- Container might be trying to use bind mount AND image Oracle
- Empty bind mount might override image Oracle

**Diagnosis:**
Check Portainer container configuration:
1. Go to container → **Duplicate/Edit**
2. Check **Volumes** section
3. Look for bind mount: `/opt/oracle/instantclient_23_3`

**Fix:**
- **Option A:** Remove the bind mount (since Oracle is in image)
- **Option B:** Keep bind mount but ensure it points to valid Oracle on server

---

### Issue 4: Missing LANG Environment Variable

**Symptoms:**
- Application might have encoding issues
- Python might not handle UTF-8 correctly

**Diagnosis:**
Check if `LANG` is set in container:
```bash
# In Portainer container console
echo $LANG
```

**Fix:**
Add to Dockerfile:
```dockerfile
ENV LANG=C.UTF-8
```

Or set in Portainer environment variables:
- `LANG=C.UTF-8`

---

### Issue 5: Podman vs Docker Differences

**Note:** Portainer is using Podman (`container=podman`)

**Potential Issues:**
- Podman might handle volumes differently
- Podman might have different security contexts
- Path resolution might differ

**Diagnosis:**
Check container runtime:
```bash
# In Portainer container console
cat /proc/1/cgroup | head -1
# Or
ps aux | head -1
```

**Fix:**
- Usually not an issue, but worth noting

---

## Diagnostic Checklist

Run through this checklist to identify the issue:

### ✅ Step 1: Verify Image Has Oracle

**In Portainer:**
1. Go to **Images**
2. Find `obs-sftp-file-processor:portainer-v2`
3. Check image size (should be ~3.1GB if Oracle is included)

**Or test locally:**
```bash
docker run --rm obs-sftp-file-processor:portainer-v2 \
  ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
# Should show library files
```

### ✅ Step 2: Check Container Environment Variables

**In Portainer:**
1. Go to container → **Duplicate/Edit**
2. Check **Environment** section
3. Verify:
   - `ORACLE_HOME=/opt/oracle/instantclient_23_3` ✅
   - `LD_LIBRARY_PATH=/opt/oracle/instantclient_23_3` ✅

**Or in container console:**
```bash
env | grep -E "ORACLE|LD_LIBRARY|PATH"
```

### ✅ Step 3: Check Container Logs

**In Portainer:**
1. Go to container → **Logs**
2. Look for:
   - ✅ "Using Oracle thick mode (ORACLE_HOME=/opt/oracle/instantclient_23_3)"
   - ✅ "Oracle thick mode initialized successfully"
   - ❌ "DPI-1047: Cannot locate a 64-bit Oracle Client library"
   - ❌ "Thick mode initialization failed"

### ✅ Step 4: Check Oracle Libraries in Container

**In Portainer container console:**
```bash
# Check directory exists
ls -ld /opt/oracle/instantclient_23_3

# Check libraries
ls -la /opt/oracle/instantclient_23_3/libclntsh.so*

# Check file type (should be Linux x86-64)
file /opt/oracle/instantclient_23_3/libclntsh.so.23.1

# Check permissions
stat /opt/oracle/instantclient_23_3/libclntsh.so.23.1
```

### ✅ Step 5: Check Volume Mounts

**In Portainer:**
1. Go to container → **Duplicate/Edit**
2. Check **Volumes** section
3. Look for bind mount to `/opt/oracle/instantclient_23_3`
4. **If bind mount exists:**
   - Check if host path exists on Portainer server
   - Check if it's empty (would override image Oracle)
   - Consider removing it (since Oracle is in image)

### ✅ Step 6: Test Oracle Connection

**In Portainer container console:**
```bash
# Test Python can find Oracle
python3 -c "import oracledb; print('Oracle driver found')"

# Test thick mode initialization
python3 -c "
import oracledb
import os
os.environ['ORACLE_HOME'] = '/opt/oracle/instantclient_23_3'
try:
    oracledb.init_oracle_client()
    print('Thick mode initialized successfully')
except Exception as e:
    print(f'Error: {e}')
"
```

---

## Quick Fixes to Try

### Fix 1: Add Missing Environment Variables

**Update Dockerfile:**
```dockerfile
ENV LANG=C.UTF-8
ENV HOME=/root
```

**Or set in Portainer UI:**
- `LANG=C.UTF-8`
- `HOME=/root`

### Fix 2: Remove Conflicting Bind Mount

**In Portainer:**
1. Go to container → **Duplicate/Edit**
2. **Volumes** section
3. Remove bind mount for `/opt/oracle/instantclient_23_3` (if exists)
4. Deploy container

### Fix 3: Rebuild with Explicit Oracle Verification

**Update Dockerfile to verify Oracle more thoroughly:**
```dockerfile
# After copying Oracle, add more verification
RUN ls -la /opt/oracle/instantclient_23_3/libclntsh.so* && \
    file /opt/oracle/instantclient_23_3/libclntsh.so.23.1 && \
    echo "Oracle Instant Client verified"
```

### Fix 4: Check Portainer Container Configuration Matches Working One

**Compare:**
1. Working container environment variables
2. New container environment variables
3. Working container volume mounts
4. New container volume mounts
5. Working container port mappings
6. New container port mappings

---

## Most Likely Issues (Based on Common Problems)

### 1. **Bind Mount Override** (Most Common)
- Working container might have bind mount that works
- New container might have empty bind mount that overrides image Oracle
- **Fix:** Remove bind mount or ensure it points to valid Oracle

### 2. **Environment Variables Not Set in Portainer**
- Dockerfile sets them, but Portainer might not pass them through
- **Fix:** Explicitly set in Portainer UI

### 3. **Oracle Not Actually in Image**
- Build might have failed silently
- **Fix:** Verify with `docker run --rm obs-sftp-file-processor:portainer-v2 ls -la /opt/oracle/instantclient_23_3/libclntsh.so*`

### 4. **Permissions Issue**
- Libraries might not be executable
- **Fix:** Add `chmod +x` in Dockerfile or check permissions

---

## Next Steps

1. **Run diagnostic checklist above**
2. **Check container logs** for specific error messages
3. **Compare working vs new container** configuration in Portainer
4. **Share findings** so we can identify the exact issue

---

## What to Share for Further Help

If still not working, please share:

1. **Container logs** (from Portainer → Container → Logs)
2. **Environment variables** (from Portainer → Container → Duplicate/Edit → Environment)
3. **Volume mounts** (from Portainer → Container → Duplicate/Edit → Volumes)
4. **Output of diagnostic commands** (from container console)
5. **Error messages** (exact text)

This will help identify the exact issue.


