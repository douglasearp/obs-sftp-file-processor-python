# Fix Oracle Instant Client Error in Portainer

## Problem
The Docker container cannot find Oracle Instant Client:
```
DPI-1047: Cannot locate a 64-bit Oracle Client library: "/opt/oracle/instantclient_23_3/libclntsh.so: cannot open shared object file: No such file or directory"
```

## Solution: Configure Volume Mount in Portainer

### Step 1: Download and Extract Oracle Instant Client on Portainer Server

1. **SSH into your Portainer server** (where Portainer is running)

2. **Download Linux x86-64 Oracle Instant Client:**
   ```bash
   # Create directory for Oracle Instant Client
   sudo mkdir -p /opt/oracle
   cd /opt/oracle
   
   # Download (you'll need to accept license on Oracle website first)
   # Visit: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html
   # Download "Basic Package" (instantclient-basic-linux.x64-23.3.0.23.09.zip)
   # Then upload to server or download directly:
   wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-23.3.0.23.09.zip
   ```

3. **Extract Oracle Instant Client:**
   ```bash
   cd /opt/oracle
   unzip instantclient-basic-linux.x64-*.zip
   mv instantclient_* instantclient_23_3
   chmod -R 755 instantclient_23_3
   ```

4. **Verify the library exists:**
   ```bash
   ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
   ```
   You should see `libclntsh.so.23.1` or similar.

### Step 2: Configure Volume Mount in Portainer

1. **Open Portainer** at `https://10.1.3.28:9443/`

2. **Navigate to your container:**
   - Go to **Containers**
   - Find `obs-sftp-file-processor`
   - Click on it, then click **Duplicate/Edit**

3. **Add Volume Mount:**
   - Scroll to **Volumes** section
   - Click **Bind** tab
   - Click **map additional volume**
   - Configure:
     - **Container:** `/opt/oracle/instantclient_23_3`
     - **Host:** `/opt/oracle/instantclient_23_3` (or the path where you extracted it)
     - **Read-only:** ✅ Yes (check this box)

4. **Verify Environment Variables:**
   - Scroll to **Environment** section
   - Ensure `ORACLE_HOME=/opt/oracle/instantclient_23_3` is set
   - Ensure `LD_LIBRARY_PATH=/opt/oracle/instantclient_23_3` is set (if not, add it)

5. **Deploy:**
   - Click **Deploy the container**
   - Wait for container to restart

### Step 3: Verify Fix

1. **Check container logs:**
   - In Portainer, go to **Containers** → `obs-sftp-file-processor` → **Logs**
   - Look for: `Oracle thick mode initialized successfully`

2. **Test the endpoint:**
   ```bash
   curl http://10.88.0.2:8001/oracle/ach-files
   ```
   Should return data instead of error 500.

## Alternative: If You Can't Access Portainer Server Directly

If you can't SSH into the Portainer server, you can:

1. **Download Oracle Instant Client on your local machine**
2. **Upload to Portainer server** via SCP or file transfer
3. **Extract on the server** at a location accessible to Docker

## Quick Test Command

After fixing, test from inside the container:
```bash
docker exec obs-sftp-file-processor ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
```

If this shows the file, the volume mount is working correctly.

