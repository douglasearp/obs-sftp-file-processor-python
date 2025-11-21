# Quick Start: Test Image in Local Portainer

## ✅ Status

- **Portainer running:** `http://localhost:8000` or `https://localhost:9443`
- **Image ready:** `obs-sftp-file-processor:portainer-v2` (3.1GB)
- **Image location:** Already in Docker, visible to Portainer

---

## Quick Steps

### 1. Open Portainer

**URL:** `http://localhost:8000` or `https://localhost:9443`

Login with your credentials.

### 2. Verify Image

1. Go to **Images** (left sidebar)
2. Look for: `obs-sftp-file-processor:portainer-v2`
3. If not visible, refresh or check: `docker images obs-sftp-file-processor:portainer-v2`

### 3. Create Test Container

1. Go to **Containers** → **Add container**

2. **Basic Settings:**
   - **Name:** `obs-sftp-file-processor-test`
   - **Image:** `obs-sftp-file-processor:portainer-v2`
   - **Restart:** `Unless stopped`

3. **Ports:**
   - **Container:** `8000`
   - **Host:** `8002` (to avoid conflict with Portainer on 8000)

4. **Environment Variables** (add these):
   ```
   SFTP_HOST=10.1.3.123
   SFTP_PORT=2022
   SFTP_USERNAME=6001_obstest
   SFTP_PASSWORD=[your password]
   SFTP_UPLOAD_FOLDER=upload
   SFTP_ARCHIVED_FOLDER=upload/archived
   
   ORACLE_HOST=10.1.0.111
   ORACLE_PORT=1521
   ORACLE_SERVICE_NAME=[your service name]
   ORACLE_USERNAME=[your username]
   ORACLE_PASSWORD=[your password]
   ORACLE_SCHEMA=ACHOWNER
   ORACLE_HOME=/opt/oracle/instantclient_23_3
   LD_LIBRARY_PATH=/opt/oracle/instantclient_23_3
   
   APP_DEBUG=true
   APP_LOG_LEVEL=DEBUG
   ```

5. **Volumes:**
   - **NO Oracle bind mount needed!** ✅ (Oracle is in image)
   - Optional: Map `./logs` → `/app/logs` for persistent logs

6. Click **Deploy the container**

### 4. Test

**Check logs:**
- Go to container → **Logs**
- Look for: "Using Oracle thick mode" ✅
- Should NOT see: "DPI-1047" errors ❌

**Test endpoints:**
```bash
# Health
curl http://localhost:8002/health

# Oracle
curl http://localhost:8002/oracle/ach-files?limit=2

# SFTP
curl http://localhost:8002/files

# Docs
open http://localhost:8002/docs
```

---

## Troubleshooting

**If image not visible:**
- Refresh Portainer page
- Check: `docker images | grep obs-sftp-file-processor`

**If container fails:**
- Check container logs
- Verify environment variables are set
- Check port 8002 is available

**If Oracle errors:**
- Check container console: `ls -la /opt/oracle/instantclient_23_3/libclntsh.so*`
- Verify `ORACLE_HOME` and `LD_LIBRARY_PATH` are set

---

## Full Guide

See `TEST_LOCAL_PORTAINER.md` for detailed instructions.


