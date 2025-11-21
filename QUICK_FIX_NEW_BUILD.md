# Quick Fix: New Portainer Build Issues

## What's Missing Compared to Working Build

Based on the working Portainer configuration, here are the differences:

### Missing Environment Variables

The working build has these that our new build was missing:

1. **`LANG=C.UTF-8`** - Now added to Dockerfile ✅
2. **`HOME=/root`** - Now added to Dockerfile ✅

### Already Present (Good ✅)

- `ORACLE_HOME=/opt/oracle/instantclient_23_3` ✅
- `LD_LIBRARY_PATH=/opt/oracle/instantclient_23_3` ✅
- `PATH` includes `/opt/oracle/instantclient_23_3` ✅
- `PYTHONPATH=/app` ✅
- `PYTHONUNBUFFERED=1` ✅

---

## Most Common Issues

### Issue 1: Bind Mount Override (Most Likely)

**Problem:** If Portainer still has a bind mount configured for `/opt/oracle/instantclient_23_3`, it might:
- Override the Oracle in the image
- Point to an empty directory on the server
- Cause "library not found" errors

**Fix:**
1. Go to Portainer → Your container → **Duplicate/Edit**
2. Check **Volumes** section
3. **Remove** any bind mount for `/opt/oracle/instantclient_23_3`
4. Deploy container

**Why:** Since Oracle is now IN the image, you don't need a bind mount.

---

### Issue 2: Environment Variables Not Set in Portainer

**Problem:** Even though Dockerfile sets environment variables, Portainer might not pass them through, or they might be overridden.

**Fix:**
1. Go to Portainer → Your container → **Duplicate/Edit**
2. Check **Environment** section
3. Ensure these are set:
   - `ORACLE_HOME=/opt/oracle/instantclient_23_3`
   - `LD_LIBRARY_PATH=/opt/oracle/instantclient_23_3`
   - `LANG=C.UTF-8`
   - `HOME=/root`
4. Deploy container

---

### Issue 3: Oracle Not Actually in Image

**Problem:** Build might have failed silently, or Oracle wasn't copied correctly.

**Diagnosis:**
```bash
# Test locally
docker run --rm obs-sftp-file-processor:portainer-v2 \
  ls -la /opt/oracle/instantclient_23_3/libclntsh.so*

# Should show library files
```

**Fix:**
- Rebuild the image
- Verify Oracle is copied during build (check build logs)

---

## Quick Diagnostic Commands

**In Portainer container console:**

```bash
# 1. Check if Oracle directory exists
ls -la /opt/oracle/instantclient_23_3

# 2. Check if libraries exist
ls -la /opt/oracle/instantclient_23_3/libclntsh.so*

# 3. Check environment variables
env | grep -E "ORACLE|LD_LIBRARY|LANG|HOME"

# 4. Check file type (should be Linux x86-64)
file /opt/oracle/instantclient_23_3/libclntsh.so.23.1

# 5. Test Python can find Oracle
python3 -c "import oracledb; print('Oracle driver found')"
```

---

## Rebuild with Fixes

After updating the Dockerfile with `LANG` and `HOME`, rebuild:

```bash
# Rebuild
docker build --platform linux/amd64 -t obs-sftp-file-processor:portainer-v2 .

# Verify Oracle is in image
docker run --rm obs-sftp-file-processor:portainer-v2 \
  sh -c 'ls -la /opt/oracle/instantclient_23_3/libclntsh.so* && env | grep -E "ORACLE|LANG|HOME"'

# Export
docker save obs-sftp-file-processor:portainer-v2 -o obs-sftp-file-processor-portainer-v2.tar
```

---

## What to Check in Portainer

1. **Container Logs:**
   - Look for: "Using Oracle thick mode"
   - Look for: "DPI-1047" errors (means Oracle not found)

2. **Environment Variables:**
   - `ORACLE_HOME` should be set
   - `LD_LIBRARY_PATH` should be set
   - `LANG` should be set (now in Dockerfile)

3. **Volume Mounts:**
   - **Remove** bind mount for `/opt/oracle/instantclient_23_3` (Oracle is in image)

4. **Image:**
   - Should be `obs-sftp-file-processor:portainer-v2`
   - Size should be ~3.1GB (includes Oracle)

---

## Next Steps

1. ✅ **Dockerfile updated** with `LANG` and `HOME`
2. **Rebuild image** with the fixes
3. **Re-export** the image
4. **Re-import** to Portainer
5. **Remove bind mount** (if exists)
6. **Verify environment variables** are set
7. **Test** the container

---

## If Still Not Working

Please share:
1. **Container logs** (the error messages)
2. **Output of diagnostic commands** (from container console)
3. **Portainer container configuration** (environment variables and volumes)

This will help identify the exact issue.


