# Why Local Docker Works But Portainer Doesn't

## Key Differences

### Local Docker (Working ✅)

**Volume Mount:**
```yaml
volumes:
  - ${ORACLE_INSTANTCLIENT_PATH:-./oracle/instantclient_23_3}:/opt/oracle/instantclient_23_3:ro
```

**What this means:**
- Mounts from: `./oracle/instantclient_23_3` (relative to your project directory)
- Mounts to: `/opt/oracle/instantclient_23_3` (inside container)
- **Your local machine has:** `/Users/dougearp/repos/obs-sftp-file-processor-python/oracle/instantclient_23_3/`
- **This directory exists locally** with all the Oracle Instant Client libraries

**Environment Variables:**
- `ORACLE_HOME=/opt/oracle/instantclient_23_3` ✅ Set
- `LD_LIBRARY_PATH=/opt/oracle/instantclient_23_3` ✅ Set (in Dockerfile)

---

### Portainer Deployment (Not Working ❌)

**Most Likely Issues:**

1. **Oracle Instant Client Not on Portainer Server**
   - The volume mount in Portainer needs to point to a path **on the Portainer server**
   - Example: `/opt/oracle/instantclient_23_3` on the server at `10.1.3.28`
   - **If this directory doesn't exist on the server, the mount will be empty**

2. **Volume Mount Not Configured**
   - In Portainer UI, you need to manually add the volume mount
   - Container path: `/opt/oracle/instantclient_23_3`
   - Host path: `/opt/oracle/instantclient_23_3` (or wherever you put it on the server)
   - **If this isn't configured, the container won't have access to Oracle Instant Client**

3. **Wrong Host Path**
   - The host path in Portainer must be an **absolute path on the Portainer server**
   - Cannot use relative paths like `./oracle/instantclient_23_3`
   - Must be something like: `/opt/oracle/instantclient_23_3` or `/var/lib/oracle/instantclient_23_3`

4. **ORACLE_HOME Not Set**
   - Check if `ORACLE_HOME=/opt/oracle/instantclient_23_3` is in the environment variables
   - If missing, the code will try thin mode and fail with encryption error

---

## How to Fix Portainer

### Step 1: Extract Oracle Instant Client on Portainer Server

**SSH into the Portainer server (10.1.3.28):**

```bash
# Create directory
sudo mkdir -p /opt/oracle
cd /opt/oracle

# Download Oracle Instant Client (or upload from your machine)
# Visit: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html
# Download "Basic Package" (instantclient-basic-linux.x64-*.zip)

# Extract
unzip instantclient-basic-linux.x64-*.zip
mv instantclient_* instantclient_23_3

# Verify
ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
# Should show: libclntsh.so -> libclntsh.so.23.1
```

### Step 2: Configure Volume Mount in Portainer

1. **Go to your container in Portainer**
2. **Click "Duplicate/Edit"**
3. **Scroll to "Volumes" section**
4. **Click "Bind" tab**
5. **Add volume:**
   - **Container:** `/opt/oracle/instantclient_23_3`
   - **Host:** `/opt/oracle/instantclient_23_3` (or the path where you extracted it)
   - **Read-only:** ✅ Yes
6. **Verify Environment Variables:**
   - `ORACLE_HOME=/opt/oracle/instantclient_23_3` ✅ Must be set
7. **Click "Deploy the container"**

### Step 3: Verify

**Check container logs:**
```bash
# In Portainer, go to container → Logs
# Look for: "Using Oracle thick mode (ORACLE_HOME=/opt/oracle/instantclient_23_3)"
```

**Test the endpoint:**
```bash
curl http://10.88.0.2:8001/oracle/ach-files?limit=2
```

---

## Quick Checklist

**Local Docker (Working):**
- ✅ Oracle Instant Client exists at `./oracle/instantclient_23_3`
- ✅ Volume mount configured in `docker-compose.yml`
- ✅ `ORACLE_HOME` set in environment
- ✅ Libraries accessible in container

**Portainer (Needs Fix):**
- ❓ Oracle Instant Client extracted on Portainer server?
- ❓ Volume mount configured in Portainer UI?
- ❓ Correct host path specified?
- ❓ `ORACLE_HOME` environment variable set?
- ❓ Container can access `/opt/oracle/instantclient_23_3`?

---

## Summary

**The main difference:** Local Docker uses a volume mount from your local filesystem where Oracle Instant Client already exists. Portainer needs the Oracle Instant Client to be on the Portainer server's filesystem, and the volume mount must be configured in the Portainer UI.

**Solution:** Extract Oracle Instant Client on the Portainer server and configure the volume mount in Portainer's container settings.

