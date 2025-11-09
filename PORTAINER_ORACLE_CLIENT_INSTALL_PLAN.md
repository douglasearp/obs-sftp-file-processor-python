# Plan: Install Oracle Instant Client on Portainer Server for Bind Mount

## Goal
Install Oracle Instant Client on the Portainer server at `/opt/oracle/instantclient_23_3` so it can be bind-mounted into the Docker container.

---

## Step 1: Access Portainer Server

**Option A: SSH Access (Recommended)**
```bash
# SSH into the Portainer server
ssh user@10.1.3.28
# Or use whatever credentials you have
```

**Option B: Portainer Web Terminal**
1. Go to https://10.1.3.28:9443/
2. Login to Portainer
3. Go to **Containers** → Find any running container → **Console** tab
4. Or go to **Environments** → **Host** → **Console** (if available)

---

## Step 2: Download Oracle Instant Client

**On the Portainer server (10.1.3.28), download Oracle Instant Client:**

### Option A: Direct Download (If Server Has Internet Access)

```bash
# Create directory
sudo mkdir -p /opt/oracle
cd /opt/oracle

# Download Oracle Instant Client Basic Package
# Note: You'll need to accept the license on Oracle's website first
# Visit: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html
# Then get the direct download URL (requires authentication)

# Example (you'll need to replace with actual URL after accepting license):
wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-23.3.0.23.09.zip

# Or use curl:
curl -O https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-23.3.0.23.09.zip
```

### Option B: Transfer from Your Local Machine

**On your local machine:**
```bash
# If you already have the zip file locally
scp ./oracle/instantclient-basic-linux.x64-*.zip user@10.1.3.28:/tmp/

# Or if you need to download it first:
# 1. Download from Oracle website to your local machine
# 2. Transfer to server:
scp ~/Downloads/instantclient-basic-linux.x64-*.zip user@10.1.3.28:/tmp/
```

**On the Portainer server:**
```bash
# Move from /tmp to /opt/oracle
sudo mkdir -p /opt/oracle
sudo mv /tmp/instantclient-basic-linux.x64-*.zip /opt/oracle/
cd /opt/oracle
```

---

## Step 3: Extract Oracle Instant Client

**On the Portainer server:**

```bash
# Ensure you're in /opt/oracle
cd /opt/oracle

# Install unzip if not available
sudo apt-get update
sudo apt-get install -y unzip

# Extract the zip file
sudo unzip instantclient-basic-linux.x64-*.zip

# Rename to the expected directory name
sudo mv instantclient_* instantclient_23_3

# Verify extraction
ls -la /opt/oracle/instantclient_23_3/
# Should show files like: libclntsh.so, libnnz.so, etc.

# Verify the main library exists
ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
# Should show: libclntsh.so -> libclntsh.so.23.1
```

---

## Step 4: Set Permissions

**On the Portainer server:**

```bash
# Ensure proper permissions (readable by Docker)
sudo chmod -R 755 /opt/oracle/instantclient_23_3

# Verify Docker can read it (if running as non-root)
# Docker typically runs as root, but verify:
sudo ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
```

---

## Step 5: Verify Installation

**On the Portainer server:**

```bash
# Check directory structure
ls -la /opt/oracle/instantclient_23_3/ | head -10

# Check for key libraries
ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
ls -la /opt/oracle/instantclient_23_3/libnnz.so*

# Check file type (should be Linux x86-64 ELF)
file /opt/oracle/instantclient_23_3/libclntsh.so.23.1
# Should show: ELF 64-bit LSB shared object, x86-64
```

---

## Step 6: Configure Bind Mount in Portainer

**In Portainer UI:**

1. **Navigate to your container:**
   - Go to https://10.1.3.28:9443/
   - Click **Containers** in left sidebar
   - Find `obs-sftp-file-processor`
   - Click on it, then click **Duplicate/Edit**

2. **Add Volume Mount:**
   - Scroll down to **Volumes** section
   - Click **Bind** tab
   - Click **"map additional volume"** or **"+"** button
   - Configure:
     - **Container:** `/opt/oracle/instantclient_23_3`
     - **Host:** `/opt/oracle/instantclient_23_3`
     - **Read-only:** ✅ Check this box (Yes)
   - Click **Save** or **Apply**

3. **Verify Environment Variables:**
   - Scroll to **Environment** section
   - Ensure these are set:
     - `ORACLE_HOME=/opt/oracle/instantclient_23_3`
     - `LD_LIBRARY_PATH=/opt/oracle/instantclient_23_3` (optional, but recommended)

4. **Deploy:**
   - Click **Deploy the container**
   - Wait for container to restart

---

## Step 7: Verify It Works

**Check container logs in Portainer:**
1. Go to container → **Logs** tab
2. Look for: `"Using Oracle thick mode (ORACLE_HOME=/opt/oracle/instantclient_23_3)"`
3. Should NOT see: `"DPI-1047: Cannot locate a 64-bit Oracle Client library"`

**Test the endpoint:**
```bash
curl http://10.88.0.2:8001/oracle/ach-files?limit=2
# Should return data, not an error
```

**Verify inside container (if you have console access):**
```bash
# In Portainer, go to container → Console
ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
# Should show the symlinks and library files
```

---

## Troubleshooting

### Issue: "No such file or directory" when extracting
**Solution:** Ensure you have `unzip` installed:
```bash
sudo apt-get install -y unzip
```

### Issue: Permission denied
**Solution:** Check permissions:
```bash
sudo chmod -R 755 /opt/oracle/instantclient_23_3
sudo chown -R root:root /opt/oracle/instantclient_23_3
```

### Issue: Volume mount shows empty in container
**Solution:** 
- Verify the host path is correct (must be absolute path)
- Verify the directory exists on the server: `ls -la /opt/oracle/instantclient_23_3`
- Check Portainer volume mount configuration matches exactly

### Issue: Wrong architecture
**Solution:** Ensure you downloaded **Linux x86-64** version, not ARM64 or macOS:
```bash
file /opt/oracle/instantclient_23_3/libclntsh.so.23.1
# Should show: x86-64, not aarch64
```

---

## Summary Checklist

- [ ] SSH or console access to Portainer server (10.1.3.28)
- [ ] Download Oracle Instant Client Linux x86-64 Basic Package
- [ ] Extract to `/opt/oracle/instantclient_23_3` on server
- [ ] Verify libraries exist: `ls -la /opt/oracle/instantclient_23_3/libclntsh.so*`
- [ ] Set permissions: `chmod -R 755 /opt/oracle/instantclient_23_3`
- [ ] Configure bind mount in Portainer UI:
  - Container: `/opt/oracle/instantclient_23_3`
  - Host: `/opt/oracle/instantclient_23_3`
  - Read-only: Yes
- [ ] Set environment variable: `ORACLE_HOME=/opt/oracle/instantclient_23_3`
- [ ] Deploy container
- [ ] Verify logs show "thick mode" initialized
- [ ] Test endpoint returns data

---

## Alternative: If You Can't Access Portainer Server Directly

If you can't SSH or use console on the Portainer server, you could:

1. **Use a temporary container to extract:**
   - Deploy a temporary container with volume mount to `/opt/oracle`
   - Copy the zip file into the container
   - Extract inside the container
   - The files will persist on the host via the volume mount

2. **Use Portainer's file browser (if available):**
   - Some Portainer installations have file browser
   - Upload the zip file
   - Extract via console

3. **Ask your system administrator:**
   - Request they install Oracle Instant Client at `/opt/oracle/instantclient_23_3`

