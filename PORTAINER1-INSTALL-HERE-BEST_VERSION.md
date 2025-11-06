# Portainer: Import Image First, Then Deploy Container

## ⚠️ Important: Two-Step Process

You need to **import the image FIRST**, then deploy the container. Portainer won't show local images until they're imported.

---

## Step 1: Import the Image

### Option A: Via Portainer UI (If Available)

1. **Login to Portainer:**
   - URL: https://10.1.3.28:9443/
   - Username: `admin`
   - Password: `-(%I!7VUf74c':jh]HUq`

2. **Go to Images:**
   - Left sidebar → Click **Images**
   - (NOT "Containers" - that's for deploying, not importing)

3. **Find Import Option:**
   Look for one of these buttons/options:
   - **"Import image from file"**
   - **"Upload image"**
   - **"Load image"**
   - **"Import"** button
   - **"+"** button (may have import option)
   - **Three dots menu** (⋮) → "Import image"

4. **Upload the File:**
   - Click the import/upload button
   - Select: `obs-sftp-file-processor-portainer.tar.gz` (280MB)
   - Wait for upload and import (may take 2-5 minutes)
   - You should see progress/status

5. **Verify Image Appears:**
   - After import, check the Images list
   - Should see: `obs-sftp-file-processor:portainer-v2` or similar
   - If you see it, proceed to Step 2

### Option B: Via Docker CLI on Portainer Server (If UI Import Not Available)

If Portainer UI doesn't have import option, use SSH:

1. **Transfer file to Portainer server:**
   ```bash
   scp obs-sftp-file-processor-portainer.tar.gz user@10.1.3.28:/tmp/
   ```

2. **SSH into Portainer server:**
   ```bash
   ssh user@10.1.3.28
   ```

3. **Load the image:**
   ```bash
   gunzip -c /tmp/obs-sftp-file-processor-portainer.tar.gz | docker load
   ```

4. **Verify image loaded:**
   ```bash
   docker images | grep obs-sftp-file-processor
   ```

5. **Refresh Portainer:**
   - Go back to Portainer UI
   - Refresh the Images page
   - Image should now appear

---

## Step 2: Deploy Container (After Image is Imported)

Once the image appears in the Images list:

1. **Go to Containers:**
   - Left sidebar → Click **Containers**

2. **Add Container:**
   - Click **"Add container"** or **"+"** button

3. **Select Image:**
   - **Image:** Click the dropdown or search box
   - You should now see: `obs-sftp-file-processor:portainer-v2` or `obs-sftp-file-processor:latest`
   - Select it
   - (If you still only see Docker Hub, the image wasn't imported - go back to Step 1)

4. **Configure Container:**
   - **Name:** `obs-sftp-file-processor`
   - **Restart policy:** `Unless stopped`

5. **Port Mapping:**
   - Click **"Publish a new network port"** or **"Ports"** tab
   - **Container port:** `8000`
   - **Host port:** `8001` (or your preferred port)
   - **Protocol:** TCP

6. **Environment Variables:**
   Click **"Environment"** or **"Env"** tab and add:

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

7. **Volumes:**
   Click **"Volumes"** or **"Bind mounts"** tab:

   **Volume 1: Oracle Instant Client**
   - **Container:** `/opt/oracle/instantclient_23_3`
   - **Host:** `/opt/oracle/instantclient_23_3` (or path where Oracle Instant Client is on server)
   - **Read-only:** ✅ Yes

   **Volume 2: Logs**
   - **Container:** `/app/logs`
   - **Host:** `/var/log/obs-sftp-file-processor` (or your preferred path)
   - **Read-only:** ❌ No

8. **Health Check (Optional but Recommended):**
   - **Test:** `CMD-SHELL curl -f http://localhost:8000/health || exit 1`
   - **Interval:** `30s`
   - **Timeout:** `10s`
   - **Retries:** `3`
   - **Start period:** `40s`

9. **Deploy:**
   - Click **"Deploy the container"** or **"Create"**
   - Wait for container to start
   - Check logs to verify it's running

---

## 🔍 Troubleshooting: "Only Docker Hub Images" Issue

### Problem: Container deploy only shows Docker Hub images

**Cause:** The image hasn't been imported into Portainer's local Docker registry yet.

**Solution:** You MUST import the image first (Step 1) before deploying container (Step 2).

### Check if Image is Imported:

1. **Go to Images page:**
   - Left sidebar → **Images**
   - Look for `obs-sftp-file-processor` in the list
   - If you see it → Image is imported ✅
   - If you don't see it → Need to import first ❌

### If Import Option Not Visible:

Different Portainer versions have different UIs:

1. **Check Images page:**
   - Look for **"+"** button in top right
   - Look for **"Import"** or **"Upload"** button
   - Look for **three dots menu** (⋮) → may have import option
   - Look for **"Actions"** dropdown

2. **Check if you need to enable it:**
   - Some Portainer versions require admin permissions
   - Check your user role/permissions

3. **Use Docker CLI method:**
   - If UI import not available, use SSH method (Option B above)
   - This always works if you have server access

---

## 📋 Quick Checklist

- [ ] Step 1: Import image via Portainer UI or Docker CLI
- [ ] Verify image appears in Images list
- [ ] Step 2: Go to Containers → Add container
- [ ] Select the imported image (should now be available)
- [ ] Configure ports, environment variables, volumes
- [ ] Deploy container
- [ ] Verify container is running
- [ ] Test health endpoint

---

## 🎯 Key Points

1. **Import FIRST, Deploy SECOND** - Can't deploy if image isn't imported
2. **Images page** - Where you import
3. **Containers page** - Where you deploy
4. **If only Docker Hub shows** - Image not imported yet, go back to Images page

---

## 📦 File to Upload

- **File:** `obs-sftp-file-processor-portainer.tar.gz`
- **Size:** 280MB
- **Location:** Your project root directory
- **Contains:** Latest code with updated SFTP credentials

---

## ✅ After Successful Deployment

Test the container:

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

**Remember:** Import the image in the **Images** section first, then it will appear when you add a container!

