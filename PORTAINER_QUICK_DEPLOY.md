# Portainer Quick Deployment Guide

## ⚠️ Important: Use Pre-Built Image (Not Build from Source)

**DO NOT** use "Build from source" or "Build from Dockerfile" in Portainer.  
**USE** the pre-built image file we created: `obs-sftp-file-processor-portainer.tar.gz`

---

## Method 1: Import Pre-Built Image (Recommended - Easiest)

### Step 1: Access Portainer
- URL: https://10.1.3.28:9443/
- Username: `admin`
- Password: `-(%I!7VUf74c':jh]HUq`

### Step 2: Import Image
1. Go to **Environments** → Select your environment
2. Click **Images** in left sidebar
3. Look for **"Import image from file"** or **"Upload"** button
4. Click it and select: `obs-sftp-file-processor-portainer.tar.gz`
5. Wait for upload and import (may take 2-5 minutes for 93MB file)
6. Verify image appears: `obs-sftp-file-processor:portainer`

### Step 3: Deploy Container
1. Go to **Containers** → **Add container**
2. **Name:** `obs-sftp-file-processor`
3. **Image:** Select `obs-sftp-file-processor:portainer` from dropdown
4. **Restart policy:** `Unless stopped`
5. **Ports:** Map `8000` (container) → `8001` (host)
6. **Environment Variables:** (see below)
7. **Volumes:** (see below)
8. Click **Deploy the container**

---

## Method 2: Build from Git Repository (If Import Doesn't Work)

If Portainer doesn't have "Import from file" option, you can build from Git:

### Step 1: Push Code to GitHub
```bash
# Ensure code is on GitHub
git push origin main
```

### Step 2: Build in Portainer
1. Go to **Stacks** → **Add stack**
2. **Name:** `obs-sftp-file-processor`
3. **Build method:** Select **Repository**
4. **Repository URL:** `https://github.com/douglasearp/obs-sftp-file-processor-python.git`
5. **Repository reference:** `main` (or your branch)
6. **Dockerfile path:** `Dockerfile` (should auto-detect)
7. **Compose path:** `docker-compose.yml` (optional, or use manual build)

### Step 3: Manual Build (Alternative)
1. Go to **Images** → **Build image**
2. **Image name:** `obs-sftp-file-processor:latest`
3. **Build method:** **Repository**
4. **Repository URL:** `https://github.com/douglasearp/obs-sftp-file-processor-python.git`
5. **Reference:** `main`
6. **Dockerfile path:** `Dockerfile`
7. Click **Build the image**

**Note:** This requires the Portainer server to have:
- Git installed
- Network access to GitHub
- Docker build capabilities

---

## Method 3: Upload via Docker Load (If You Have SSH Access)

If you have SSH access to the Portainer server (10.1.3.28):

```bash
# Transfer the image file
scp obs-sftp-file-processor-portainer.tar.gz user@10.1.3.28:/tmp/

# SSH into server
ssh user@10.1.3.28

# Load the image
gunzip -c /tmp/obs-sftp-file-processor-portainer.tar.gz | docker load

# Verify
docker images | grep obs-sftp-file-processor

# Tag if needed
docker tag obs-sftp-file-processor:portainer obs-sftp-file-processor:latest
```

Then in Portainer, the image will appear in the Images list.

---

## Container Configuration

### Environment Variables

Add these in Portainer container settings:

```
SFTP_HOST=10.1.3.123
SFTP_PORT=2022
SFTP_USERNAME=6001_obstest
SFTP_PASSWORD=OEL%7@71ov6I0@=V"`Tn
SFTP_TIMEOUT=30

ORACLE_HOST=10.1.0.111
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=PDB_ACHDEV01.privatesubnet1.obsnetwork1.oraclevcn.com
ORACLE_USERNAME=achowner
ORACLE_PASSWORD=TLcbbhQuiV7##sLv4tMr
ORACLE_SCHEMA=ACHOWNER
ORACLE_HOME=/opt/oracle/instantclient_23_3

APP_DEBUG=false
APP_LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
```

### Volumes

**Volume 1: Oracle Instant Client**
- **Container:** `/opt/oracle/instantclient_23_3`
- **Host:** `/opt/oracle/instantclient_23_3` (or path where Oracle Instant Client is on server)
- **Read-only:** Yes

**Volume 2: Logs**
- **Container:** `/app/logs`
- **Host:** `/var/log/obs-sftp-file-processor` (or your preferred path)
- **Read-only:** No

### Ports

- **Container port:** `8000`
- **Host port:** `8001` (or your preferred port)
- **Protocol:** TCP

### Health Check

- **Test:** `CMD-SHELL curl -f http://localhost:8000/health || exit 1`
- **Interval:** `30s`
- **Timeout:** `10s`
- **Retries:** `3`
- **Start period:** `40s`

---

## Troubleshooting the "Dockerfile not found" Error

### Error: `stat /var/tmp/libpod_builder.../build/Dockerfile: no such file or directory`

**Cause:** Portainer is trying to build from Dockerfile but can't find it.

**Solutions:**

1. **Use Pre-Built Image (Recommended):**
   - Don't use "Build from source"
   - Use "Import image from file" instead
   - Upload `obs-sftp-file-processor-portainer.tar.gz`

2. **If Building from Git:**
   - Ensure Dockerfile is in repository root
   - Check repository URL is correct
   - Verify branch name (usually `main`)
   - Ensure Portainer server has Git access

3. **If Building from Upload:**
   - Upload entire project directory as zip
   - Extract on Portainer server
   - Point build context to extracted directory
   - Ensure Dockerfile is in root of extracted directory

4. **Check Build Context:**
   - Build context must include Dockerfile
   - Dockerfile path must be relative to build context
   - If Dockerfile is in subdirectory, specify path: `./Dockerfile`

---

## Recommended Approach

**Best Method:** Use the pre-built image (`obs-sftp-file-processor-portainer.tar.gz`)

**Why:**
- ✅ No build time needed
- ✅ No Git access required
- ✅ No Dockerfile needed
- ✅ Faster deployment
- ✅ Consistent image (already tested)

**Steps:**
1. Upload `obs-sftp-file-processor-portainer.tar.gz` to Portainer
2. Import image
3. Deploy container with environment variables
4. Done!

---

## Verification

After deployment, test:

```bash
# Health check
curl https://10.1.3.28:8001/health

# List files
curl https://10.1.3.28:8001/files?path=upload
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "..."
}
```

---

## File Location

The pre-built image is in your project root:
- **File:** `obs-sftp-file-processor-portainer.tar.gz`
- **Size:** 93MB
- **Ready to upload:** Yes

---

**Portainer URL:** https://10.1.3.28:9443/  
**Username:** admin  
**Password:** -(%I!7VUf74c':jh]HUq

