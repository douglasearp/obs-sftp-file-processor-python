# Fix Portainer Build Error: "Dockerfile: no such file or directory"

## ❌ Error You're Seeing

```
stat /var/tmp/libpod_builder2257454457/build/Dockerfile: no such file or directory
```

**This means:** Portainer is trying to build from Dockerfile but can't find it in the build context.

---

## ✅ Solution 1: Use Pre-Built Image (EASIEST - Recommended)

**DO NOT BUILD** - Use the pre-built image file instead!

### Steps:

1. **In Portainer, go to Images (NOT Stacks or Build)**
   - Left sidebar → **Images**

2. **Look for "Import image" or "Upload image" button**
   - Different Portainer versions have different UI
   - May be called: "Import", "Upload", "Load image", "Import from file"

3. **Upload the file:**
   - File: `obs-sftp-file-processor-portainer.tar.gz` (280MB)
   - Location: Your project root directory
   - Wait for upload to complete

4. **Verify image appears:**
   - Should show: `obs-sftp-file-processor:portainer-v2` or similar

5. **Deploy container:**
   - Go to **Containers** → **Add container**
   - Select the imported image
   - Configure environment variables and volumes
   - Deploy

---

## ✅ Solution 2: Build from Git Repository (If Import Not Available)

If Portainer doesn't have "Import from file", build from GitHub:

### Option A: Build Image from Git

1. **Go to Images → Build image**

2. **Build Configuration:**
   - **Image name:** `obs-sftp-file-processor:latest`
   - **Build method:** Select **Repository**
   - **Repository URL:** `https://github.com/douglasearp/obs-sftp-file-processor-python.git`
   - **Reference:** `main` (or `master` if that's your default branch)
   - **Dockerfile path:** `Dockerfile` (leave as default, or explicitly set to `./Dockerfile`)
   - **Build context:** Leave empty (defaults to repository root)

3. **Click "Build the image"**

4. **Wait for build to complete** (may take 5-10 minutes)

### Option B: Create Stack from Git

1. **Go to Stacks → Add stack**

2. **Stack Configuration:**
   - **Name:** `obs-sftp-file-processor`
   - **Build method:** Select **Repository**
   - **Repository URL:** `https://github.com/douglasearp/obs-sftp-file-processor-python.git`
   - **Reference:** `main`
   - **Compose path:** `docker-compose.yml`
   - **Dockerfile path:** `Dockerfile` (if asked)

3. **Environment Variables:**
   - Add all required environment variables (see below)

4. **Click "Deploy the stack"**

---

## ✅ Solution 3: Fix Build Context (If Building Manually)

If you must build and get the Dockerfile error:

### The Problem:
Portainer can't find the Dockerfile because the build context is wrong.

### The Fix:

1. **Ensure Dockerfile is in repository root:**
   - Check: `https://github.com/douglasearp/obs-sftp-file-processor-python/blob/main/Dockerfile`
   - It should be at the root, not in a subdirectory

2. **Set correct build context:**
   - **Build context:** Leave empty or set to `.` (repository root)
   - **Dockerfile path:** `Dockerfile` or `./Dockerfile`
   - **DO NOT** set Dockerfile path to a subdirectory unless it's actually there

3. **Verify repository structure:**
   ```
   obs-sftp-file-processor-python/
   ├── Dockerfile          ← Must be here
   ├── docker-compose.yml
   ├── pyproject.toml
   ├── README.md
   └── src/
   ```

---

## ✅ Solution 4: Upload Project as Zip and Build

If Git build doesn't work:

1. **Create a zip of your project:**
   ```bash
   # Exclude unnecessary files
   zip -r obs-sftp-file-processor.zip . \
     -x "*.git*" \
     -x "*.venv*" \
     -x "*.pyc" \
     -x "__pycache__/*" \
     -x "*.log" \
     -x "node_modules/*" \
     -x ".env"
   ```

2. **In Portainer:**
   - Go to **Images → Build image**
   - **Build method:** Select **Upload**
   - Upload the zip file
   - **Dockerfile path:** `Dockerfile`
   - **Build context:** `.` (root of extracted zip)

3. **Build the image**

---

## 🔍 Troubleshooting the Build Error

### Check 1: Verify Dockerfile Exists in Repository

```bash
# Check on GitHub
https://github.com/douglasearp/obs-sftp-file-processor-python/blob/main/Dockerfile
```

If Dockerfile doesn't exist, you need to push it to GitHub first.

### Check 2: Verify Build Context

In Portainer build settings:
- **Build context:** Should be `.` or empty (repository root)
- **Dockerfile path:** Should be `Dockerfile` or `./Dockerfile`
- **NOT:** `/Dockerfile` or `src/Dockerfile` or any subdirectory

### Check 3: Check Portainer Logs

1. Go to **Activity logs** in Portainer
2. Look for the build attempt
3. Check what path it's trying to use
4. Verify the repository structure matches

### Check 4: Test Build Locally First

```bash
# Test that Dockerfile works locally
docker build --platform linux/amd64 -t test-build .

# If this works, the issue is Portainer configuration
# If this fails, fix Dockerfile first
```

---

## 📋 Recommended Approach

**BEST: Use Pre-Built Image (Solution 1)**
- ✅ No build time
- ✅ No Git access needed
- ✅ No Dockerfile needed
- ✅ Fastest deployment
- ✅ Already tested

**File to upload:** `obs-sftp-file-processor-portainer.tar.gz` (280MB)

---

## 🚀 Quick Steps to Fix Right Now

1. **Stop trying to build** - Use import instead
2. **Go to Images** (not Stacks, not Build)
3. **Find "Import" or "Upload" button**
4. **Upload:** `obs-sftp-file-processor-portainer.tar.gz`
5. **Wait for import**
6. **Deploy container** with the imported image

---

## 📝 Environment Variables for Deployment

Once image is imported/built, use these environment variables:

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

---

## 💡 Why This Error Happens

The error occurs because:
1. Portainer is trying to build from Dockerfile
2. The build context doesn't include the Dockerfile
3. This happens when:
   - Build context is set to wrong directory
   - Dockerfile path is incorrect
   - Repository structure doesn't match expectations
   - Git repository doesn't have Dockerfile in root

**Solution:** Use pre-built image instead of building!

---

## ✅ Verification

After importing/building, verify:

```bash
# In Portainer, check Images list
# Should see: obs-sftp-file-processor:portainer-v2 or obs-sftp-file-processor:latest

# Deploy container and test
curl https://10.1.3.28:8001/health
```

---

**Remember:** The pre-built image file (`obs-sftp-file-processor-portainer.tar.gz`) is the easiest solution and avoids all build errors!

