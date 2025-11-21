# Plan: Move Oracle Instant Client to /opt/oracle/instantclient_23_3 on Linux

## Context

This plan is for moving Oracle Instant Client from a local directory (e.g., `oracle/instantclient_23_3`) to the system directory `/opt/oracle/instantclient_23_3` on a Linux server (e.g., the Portainer server at `10.1.3.28`).

**Purpose:**
- Set up Oracle Instant Client on the Portainer server for bind mount
- Or relocate Oracle Instant Client to a standard system location
- Ensure proper permissions for Docker/container access

---

## Prerequisites

1. **Access to Linux server:**
   - SSH access to the server (e.g., `10.1.3.28`)
   - Root or sudo privileges

2. **Oracle Instant Client location:**
   - Current location: `oracle/instantclient_23_3` (or wherever it currently is)
   - Target location: `/opt/oracle/instantclient_23_3`

3. **Disk space:**
   - Oracle Instant Client requires ~200-300MB
   - Ensure `/opt` has sufficient space

---

## Option 1: Move (Relocate) - Recommended if Source is Temporary

**Use when:**
- Oracle Instant Client is in a temporary location
- You want to free up space in the original location
- You're setting it up for the first time

### Steps

1. **SSH into the Linux server:**
   ```bash
   ssh user@10.1.3.28
   # Or use your preferred SSH method
   ```

2. **Navigate to the source directory:**
   ```bash
   cd /path/to/oracle
   # Or wherever your oracle/instantclient_23_3 is located
   ```

3. **Create target directory structure:**
   ```bash
   sudo mkdir -p /opt/oracle
   ```

4. **Move the directory:**
   ```bash
   sudo mv instantclient_23_3 /opt/oracle/instantclient_23_3
   ```
   
   **Or if the full path is needed:**
   ```bash
   sudo mv /path/to/oracle/instantclient_23_3 /opt/oracle/instantclient_23_3
   ```

5. **Set permissions:**
   ```bash
   sudo chmod -R 755 /opt/oracle/instantclient_23_3
   sudo chown -R root:root /opt/oracle/instantclient_23_3
   ```

6. **Verify the move:**
   ```bash
   ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
   # Should show library files
   ```

---

## Option 2: Copy (Keep Original) - Recommended if Source is Needed

**Use when:**
- You want to keep the original location
- Source is in a project directory you want to preserve
- You're creating a system-wide installation

### Steps

1. **SSH into the Linux server:**
   ```bash
   ssh user@10.1.3.28
   ```

2. **Create target directory:**
   ```bash
   sudo mkdir -p /opt/oracle
   ```

3. **Copy the directory:**
   ```bash
   sudo cp -r /path/to/oracle/instantclient_23_3 /opt/oracle/instantclient_23_3
   ```
   
   **Or if you're in the oracle directory:**
   ```bash
   sudo cp -r instantclient_23_3 /opt/oracle/instantclient_23_3
   ```

4. **Set permissions:**
   ```bash
   sudo chmod -R 755 /opt/oracle/instantclient_23_3
   sudo chown -R root:root /opt/oracle/instantclient_23_3
   ```

5. **Verify the copy:**
   ```bash
   ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
   # Should show library files
   ```

---

## Option 3: Transfer from Remote and Install

**Use when:**
- Oracle Instant Client is on your local machine (Mac)
- You need to transfer it to the Linux server
- You're setting up for the first time

### Steps

1. **On your local machine, compress the Oracle directory (optional):**
   ```bash
   cd /Users/dougearp/repos/obs-sftp-file-processor-python
   tar -czf oracle-instantclient.tar.gz oracle/instantclient_23_3
   ```

2. **Transfer to Linux server:**
   ```bash
   scp oracle-instantclient.tar.gz user@10.1.3.28:/tmp/
   ```

3. **SSH into the Linux server:**
   ```bash
   ssh user@10.1.3.28
   ```

4. **Extract to /opt/oracle:**
   ```bash
   sudo mkdir -p /opt/oracle
   cd /tmp
   sudo tar -xzf oracle-instantclient.tar.gz -C /opt/oracle
   sudo mv /opt/oracle/oracle/instantclient_23_3 /opt/oracle/instantclient_23_3
   sudo rmdir /opt/oracle/oracle 2>/dev/null || true
   ```

5. **Set permissions:**
   ```bash
   sudo chmod -R 755 /opt/oracle/instantclient_23_3
   sudo chown -R root:root /opt/oracle/instantclient_23_3
   ```

6. **Clean up:**
   ```bash
   rm /tmp/oracle-instantclient.tar.gz
   ```

7. **Verify:**
   ```bash
   ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
   ```

---

## Option 4: Download and Extract Directly on Server

**Use when:**
- You don't have Oracle Instant Client locally
- You want to download it directly on the server
- You have internet access on the server

### Steps

1. **SSH into the Linux server:**
   ```bash
   ssh user@10.1.3.28
   ```

2. **Create target directory:**
   ```bash
   sudo mkdir -p /opt/oracle
   cd /opt/oracle
   ```

3. **Download Oracle Instant Client:**
   ```bash
   # Note: You'll need to accept Oracle license first
   # Visit: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html
   # Download "Basic Package" (instantclient-basic-linux.x64-23.3.0.23.09.zip)
   
   # Then upload to server or download directly:
   wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-23.3.0.23.09.zip
   # Or use curl:
   curl -O https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-23.3.0.23.09.zip
   ```

4. **Extract:**
   ```bash
   sudo unzip instantclient-basic-linux.x64-*.zip
   sudo mv instantclient_* instantclient_23_3
   ```

5. **Set permissions:**
   ```bash
   sudo chmod -R 755 /opt/oracle/instantclient_23_3
   sudo chown -R root:root /opt/oracle/instantclient_23_3
   ```

6. **Clean up:**
   ```bash
   sudo rm instantclient-basic-linux.x64-*.zip
   ```

7. **Verify:**
   ```bash
   ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
   ```

---

## Permission Considerations

### Why Set Permissions?

- **755 (rwxr-xr-x):** Allows read/execute for all, write for owner
- **root:root ownership:** Standard for system directories
- **Docker access:** Containers running as root can access it
- **Security:** Prevents unauthorized modifications

### If Docker Runs as Non-Root User

If your Docker containers run as a non-root user, you may need:

```bash
# Option A: Add Docker group to directory
sudo chgrp -R docker /opt/oracle/instantclient_23_3
sudo chmod -R 755 /opt/oracle/instantclient_23_3

# Option B: Make it world-readable (less secure)
sudo chmod -R 755 /opt/oracle/instantclient_23_3
```

---

## Verification Steps

After moving/copying, verify the installation:

1. **Check directory exists:**
   ```bash
   ls -ld /opt/oracle/instantclient_23_3
   # Should show: drwxr-xr-x ... /opt/oracle/instantclient_23_3
   ```

2. **Check key libraries:**
   ```bash
   ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
   # Should show:
   # libclntsh.so -> libclntsh.so.23.1
   # libclntsh.so.23.1 (actual file)
   ```

3. **Check file type (should be Linux x86-64):**
   ```bash
   file /opt/oracle/instantclient_23_3/libclntsh.so.23.1
   # Should show: ELF 64-bit LSB shared object, x86-64
   ```

4. **Test from Docker container (if applicable):**
   ```bash
   docker run --rm -v /opt/oracle/instantclient_23_3:/opt/oracle/instantclient_23_3:ro \
     alpine:latest ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
   # Should show the library files
   ```

---

## Common Issues and Solutions

### Issue 1: Permission Denied

**Error:** `Permission denied` when accessing files

**Solution:**
```bash
sudo chmod -R 755 /opt/oracle/instantclient_23_3
sudo chown -R root:root /opt/oracle/instantclient_23_3
```

### Issue 2: Directory Not Found

**Error:** `No such file or directory`

**Solution:**
- Verify the source path is correct
- Check if you have read access to the source
- Ensure target directory exists: `sudo mkdir -p /opt/oracle`

### Issue 3: Insufficient Space

**Error:** `No space left on device`

**Solution:**
```bash
# Check available space
df -h /opt

# If needed, clean up or use a different location
# Alternative: /usr/local/oracle/instantclient_23_3
```

### Issue 4: Wrong Architecture

**Error:** Library won't load or wrong file type

**Solution:**
- Ensure you're using Linux x86-64 Oracle Instant Client
- Not macOS or ARM version
- Verify with: `file /opt/oracle/instantclient_23_3/libclntsh.so.23.1`

---

## For Portainer Bind Mount

After moving to `/opt/oracle/instantclient_23_3`, configure Portainer:

1. **In Portainer UI:**
   - Go to your container → **Duplicate/Edit**
   - Scroll to **Volumes** section
   - Click **Bind** tab
   - Add volume:
     - **Container:** `/opt/oracle/instantclient_23_3`
     - **Host:** `/opt/oracle/instantclient_23_3`
     - **Read-only:** ✅ Yes

2. **Environment Variables:**
   - `ORACLE_HOME=/opt/oracle/instantclient_23_3` ✅ Must be set

3. **Deploy:**
   - Click **Deploy the container**
   - Check logs for Oracle initialization

---

## Summary

**Recommended Approach:**
- **If setting up fresh:** Option 4 (Download directly on server)
- **If you have it locally:** Option 3 (Transfer and extract)
- **If it's already on server:** Option 1 (Move) or Option 2 (Copy)

**Key Steps:**
1. Create `/opt/oracle` directory
2. Move/copy `instantclient_23_3` to `/opt/oracle/instantclient_23_3`
3. Set permissions: `chmod -R 755` and `chown -R root:root`
4. Verify libraries exist
5. Configure Portainer bind mount (if needed)

**Result:**
- Oracle Instant Client at `/opt/oracle/instantclient_23_3`
- Proper permissions for Docker access
- Ready for Portainer bind mount

---

## Quick Reference Commands

```bash
# Create directory
sudo mkdir -p /opt/oracle

# Move (if source is temporary)
sudo mv /path/to/oracle/instantclient_23_3 /opt/oracle/instantclient_23_3

# Copy (if keeping original)
sudo cp -r /path/to/oracle/instantclient_23_3 /opt/oracle/instantclient_23_3

# Set permissions
sudo chmod -R 755 /opt/oracle/instantclient_23_3
sudo chown -R root:root /opt/oracle/instantclient_23_3

# Verify
ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
```


