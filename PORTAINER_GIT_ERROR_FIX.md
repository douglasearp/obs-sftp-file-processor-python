# Fix Portainer Git Clone Error: "reference not found"

## ❌ Error You're Seeing

```
Unable to clone git repository: failed to clone git repository: reference not found
```

**This means:** Portainer can't access or find the Git repository/branch.

---

## ✅ BEST SOLUTION: Use Pre-Built Image (Avoids All Git Issues)

**Stop trying to build from Git!** Use the pre-built image file instead.

### Why This is Better:
- ✅ No Git access needed
- ✅ No network issues
- ✅ No authentication needed
- ✅ Faster deployment
- ✅ Already tested and working

### Steps:

1. **In Portainer:**
   - Go to **Images** (left sidebar)
   - Click **"Import image from file"** or **"Upload"** button
   - Upload: `obs-sftp-file-processor-portainer.tar.gz` (280MB)
   - Wait for import to complete

2. **Deploy:**
   - Go to **Containers** → **Add container**
   - Select the imported image
   - Configure and deploy

**File Location:** `obs-sftp-file-processor-portainer.tar.gz` in your project root

---

## ✅ Alternative: Fix Git Build (If You Must Build)

If Portainer doesn't have import option, fix the Git build:

### Step 1: Verify Repository Settings

**Repository URL:**
```
https://github.com/douglasearp/obs-sftp-file-processor-python.git
```

**Reference/Branch:**
- Try: `main` (most likely)
- Or try: `master` (if main doesn't work)
- Or try: `refs/heads/main` (full reference)

**Dockerfile Path:**
```
Dockerfile
```
(Leave as default, or explicitly set to `./Dockerfile`)

**Build Context:**
```
.
```
(Leave empty, or set to `.` for repository root)

### Step 2: Check Repository Access

The error might mean:
1. **Repository is private** - Portainer needs GitHub credentials
2. **Network blocked** - Portainer server can't reach GitHub
3. **Branch name wrong** - Try different branch names

### Step 3: Configure Git Authentication (If Private Repo)

If repository is private, you need to:

1. **Create GitHub Personal Access Token:**
   - GitHub → Settings → Developer settings → Personal access tokens
   - Generate token with `repo` scope
   - Copy the token

2. **In Portainer Build Settings:**
   - **Authentication:** Enable
   - **Username:** Your GitHub username
   - **Password/Token:** Paste the personal access token

3. **Repository URL:** Use HTTPS URL (same as above)

### Step 4: Alternative - Use Public Repository

If you can't use authentication, make repository public temporarily:
- GitHub → Repository Settings → Change visibility → Make public
- Build in Portainer
- Change back to private after

---

## 🔍 Troubleshooting Git Clone Error

### Check 1: Verify Branch Exists

```bash
# Check what branches exist
git ls-remote --heads origin

# Should show:
# refs/heads/main
```

### Check 2: Test Repository Access

From Portainer server (if you have SSH access):

```bash
# Test if server can access GitHub
curl -I https://github.com/douglasearp/obs-sftp-file-processor-python.git

# Test Git clone
git clone https://github.com/douglasearp/obs-sftp-file-processor-python.git /tmp/test-clone
cd /tmp/test-clone
git checkout main
ls Dockerfile  # Should exist
```

### Check 3: Portainer Git Settings

In Portainer build configuration:

**Correct Settings:**
- **Repository URL:** `https://github.com/douglasearp/obs-sftp-file-processor-python.git`
- **Reference:** `main` (try this first)
- **Dockerfile path:** `Dockerfile`
- **Build context:** `.` or leave empty

**Common Mistakes:**
- ❌ Wrong branch name (`master` instead of `main`)
- ❌ Wrong repository URL
- ❌ Dockerfile path in subdirectory
- ❌ Private repo without authentication

---

## 🚀 Recommended: Use Pre-Built Image

**Why use pre-built image:**
1. ✅ No Git access needed
2. ✅ No authentication required
3. ✅ No network issues
4. ✅ Faster (no build time)
5. ✅ Already tested
6. ✅ Avoids all these errors

**File to upload:**
- `obs-sftp-file-processor-portainer.tar.gz` (280MB)
- Contains latest code with updated SFTP credentials
- Ready to deploy immediately

---

## 📋 Quick Fix Steps

### Option 1: Import Pre-Built Image (EASIEST)

1. Portainer → **Images**
2. Click **"Import image from file"**
3. Upload: `obs-sftp-file-processor-portainer.tar.gz`
4. Deploy container

### Option 2: Fix Git Build

1. Portainer → **Images** → **Build image**
2. **Repository URL:** `https://github.com/douglasearp/obs-sftp-file-processor-python.git`
3. **Reference:** `main` (try this)
4. **Dockerfile path:** `Dockerfile`
5. **Authentication:** Enable if repo is private
6. Click **Build**

### Option 3: Use Docker Compose Stack

1. Portainer → **Stacks** → **Add stack**
2. **Build method:** Repository
3. **Repository URL:** `https://github.com/douglasearp/obs-sftp-file-processor-python.git`
4. **Reference:** `main`
5. **Compose path:** `docker-compose.yml`
6. **Environment variables:** Add all required vars
7. Click **Deploy**

---

## ✅ Verification

After successful import/build:

1. **Check Images list:**
   - Should see: `obs-sftp-file-processor:portainer-v2` or `obs-sftp-file-processor:latest`

2. **Deploy container:**
   - Use the image
   - Add environment variables
   - Configure volumes

3. **Test:**
   ```bash
   curl https://10.1.3.28:8001/health
   ```

---

## 💡 Why Git Clone Fails

Common reasons:
1. **Private repository** - Needs authentication
2. **Network blocked** - Portainer server can't reach GitHub
3. **Wrong branch** - Branch name doesn't match
4. **Repository URL wrong** - Typo in URL
5. **Git not installed** - Portainer server missing Git

**Solution:** Use pre-built image to avoid all these issues!

---

## 📝 Current Repository Info

- **Repository:** `https://github.com/douglasearp/obs-sftp-file-processor-python.git`
- **Branch:** `main`
- **Dockerfile:** Exists in root
- **Latest commit:** `b03618f` - "Update SFTP connection credentials"

---

**Remember:** The pre-built image (`obs-sftp-file-processor-portainer.tar.gz`) is the easiest solution and avoids Git clone errors entirely!

