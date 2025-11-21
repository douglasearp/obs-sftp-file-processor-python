# Test New Image in Local Portainer

## Current Status

✅ **Image exists locally:** `obs-sftp-file-processor:portainer-v2` (3.1GB)  
✅ **Portainer running:** `portainer`, `portainer_agent`, `portainer_edge_agent`  
✅ **Image ready for testing**

---

## Step 1: Access Local Portainer

1. **Open browser:**
   - URL: `http://localhost:9000` (or check port with `docker ps`)
   - Or: `http://127.0.0.1:9000`

2. **Login:**
   - Use your Portainer credentials
   - If first time, create admin account

---

## Step 2: Verify Image is Available

1. **In Portainer UI:**
   - Go to **Environments** → Select **local** (or your local environment)
   - Click **Images** in left sidebar
   - Look for: `obs-sftp-file-processor:portainer-v2`
   - If not visible, it should appear (Docker images are automatically visible to Portainer)

2. **If image not visible:**
   - Go to **Images** → **Import image**
   - Or verify image exists: `docker images obs-sftp-file-processor:portainer-v2`

---

## Step 3: Create Test Container

1. **Go to Containers:**
   - Click **Containers** in left sidebar
   - Click **Add container**

2. **Basic Settings:**
   - **Name:** `obs-sftp-file-processor-test`
   - **Image:** Select `obs-sftp-file-processor:portainer-v2` from dropdown
   - **Restart policy:** `Unless stopped`

3. **Network & Ports:**
   - Click **Publish a new network port**
   - **Container port:** `8000`
   - **Host port:** `8002` (to avoid conflict with local API on 8000)
   - **Protocol:** TCP

4. **Environment Variables:**
   Add these (click **Add environment variable** for each):

   **SFTP Configuration:**
   - `SFTP_HOST` = `10.1.3.123`
   - `SFTP_PORT` = `2022`
   - `SFTP_USERNAME` = `6001_obstest`
   - `SFTP_PASSWORD` = `[your SFTP password]`
   - `SFTP_UPLOAD_FOLDER` = `upload`
   - `SFTP_ARCHIVED_FOLDER` = `upload/archived`

   **Oracle Configuration:**
   - `ORACLE_HOST` = `10.1.0.111`
   - `ORACLE_PORT` = `1521`
   - `ORACLE_SERVICE_NAME` = `[your service name]`
   - `ORACLE_USERNAME` = `[your Oracle username]`
   - `ORACLE_PASSWORD` = `[your Oracle password]`
   - `ORACLE_SCHEMA` = `ACHOWNER`
   - `ORACLE_HOME` = `/opt/oracle/instantclient_23_3` ✅ (already in image)
   - `LD_LIBRARY_PATH` = `/opt/oracle/instantclient_23_3` ✅ (already in image)

   **Application Configuration:**
   - `PYTHONUNBUFFERED` = `1` ✅ (already in image)
   - `LANG` = `C.UTF-8` ✅ (already in image)
   - `HOME` = `/root` ✅ (already in image)
   - `APP_DEBUG` = `true` (for testing)
   - `APP_LOG_LEVEL` = `DEBUG` (for testing)

5. **Volumes (Optional):**
   - **Logs:** Map `./logs` → `/app/logs` (if you want persistent logs)
   - **NO Oracle bind mount needed!** ✅ Oracle is in the image

6. **Deploy:**
   - Click **Deploy the container**
   - Wait for container to start

---

## Step 4: Verify Container is Working

### Check Container Status

1. **In Portainer:**
   - Go to **Containers** → `obs-sftp-file-processor-test`
   - Check **Status** - should be "Running" (green)

### Check Container Logs

1. **In Portainer:**
   - Go to **Containers** → `obs-sftp-file-processor-test` → **Logs**
   - Look for:
     - ✅ "Using Oracle thick mode (ORACLE_HOME=/opt/oracle/instantclient_23_3)"
     - ✅ "Application startup complete"
     - ✅ "Uvicorn running on http://0.0.0.0:8000"
   - Should NOT see:
     - ❌ "DPI-1047: Cannot locate a 64-bit Oracle Client library"
     - ❌ "Thick mode initialization failed"

### Test Container Console

1. **In Portainer:**
   - Go to **Containers** → `obs-sftp-file-processor-test` → **Console**
   - Click **Connect**

2. **Run diagnostic commands:**
   ```bash
   # Check Oracle directory exists
   ls -la /opt/oracle/instantclient_23_3
   
   # Check libraries exist
   ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
   
   # Check environment variables
   env | grep -E "ORACLE|LD_LIBRARY|LANG|HOME"
   
   # Check file type
   file /opt/oracle/instantclient_23_3/libclntsh.so.23.1
   ```

### Test API Endpoints

1. **Health Check:**
   ```bash
   curl http://localhost:8002/health
   # Should return: {"status":"healthy"}
   ```

2. **Oracle Connection:**
   ```bash
   curl http://localhost:8002/oracle/ach-files?limit=2
   # Should return ACH files data, not error 500
   ```

3. **SFTP Connection:**
   ```bash
   curl http://localhost:8002/files
   # Should return list of SFTP files
   ```

4. **API Docs:**
   - Open browser: `http://localhost:8002/docs`
   - Should show FastAPI documentation

---

## Step 5: Compare with Working Container

If you have the working container running:

1. **Compare Logs:**
   - Working container logs
   - New test container logs
   - Look for differences

2. **Compare Environment Variables:**
   - Working container → **Duplicate/Edit** → **Environment**
   - Test container → **Duplicate/Edit** → **Environment**
   - Compare values

3. **Compare Volume Mounts:**
   - Working container → **Duplicate/Edit** → **Volumes**
   - Test container → **Duplicate/Edit** → **Volumes**
   - Note any differences

---

## Troubleshooting

### Issue: Container Won't Start

**Check:**
- Container logs for errors
- Environment variables are set correctly
- Port 8002 is not already in use

**Fix:**
- Check logs for specific error
- Verify all required environment variables are set
- Try different host port (e.g., 8003)

### Issue: Oracle Not Working

**Symptoms:**
- Error: `DPI-1047: Cannot locate a 64-bit Oracle Client library`
- Logs show "Thick mode initialization failed"

**Diagnosis:**
```bash
# In container console
ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
env | grep ORACLE
```

**Fix:**
- Verify Oracle libraries exist in container
- Check environment variables are set
- Check container logs for specific error

### Issue: Can't Access API

**Symptoms:**
- `curl http://localhost:8002/health` fails
- Connection refused

**Fix:**
- Check container is running
- Verify port mapping (8002 → 8000)
- Check firewall settings
- Try: `docker ps` to see port mappings

---

## Quick Test Commands

```bash
# Check if container is running
docker ps | grep obs-sftp-file-processor-test

# Check container logs
docker logs obs-sftp-file-processor-test

# Test health endpoint
curl http://localhost:8002/health

# Test Oracle endpoint
curl http://localhost:8002/oracle/ach-files?limit=1

# Test SFTP endpoint
curl http://localhost:8002/files

# Check environment variables in container
docker exec obs-sftp-file-processor-test env | grep -E "ORACLE|LD_LIBRARY|LANG"

# Check Oracle libraries in container
docker exec obs-sftp-file-processor-test ls -la /opt/oracle/instantclient_23_3/libclntsh.so*
```

---

## Success Criteria

✅ Container starts without errors  
✅ Logs show "Using Oracle thick mode"  
✅ Health endpoint returns `{"status":"healthy"}`  
✅ Oracle endpoint returns data (not error 500)  
✅ SFTP endpoint returns file list  
✅ API docs accessible at `http://localhost:8002/docs`

---

## Next Steps After Successful Test

If the test container works:

1. **Note any differences** from working container
2. **Document any fixes** needed
3. **Rebuild image** if needed (with any fixes)
4. **Export updated image** for remote Portainer
5. **Deploy to remote Portainer** using same configuration

---

## Cleanup

After testing, you can remove the test container:

1. **In Portainer:**
   - Go to **Containers** → `obs-sftp-file-processor-test`
   - Click **Stop** (if running)
   - Click **Remove**

**Or via command line:**
```bash
docker stop obs-sftp-file-processor-test
docker rm obs-sftp-file-processor-test
```


