# Portainer Deployment Instructions

## Quick Deployment Guide for Portainer

**Portainer URL:** https://10.1.3.28:9443/  
**Username:** admin  
**Password:** -(%I!7VUf74c':jh]HUq

---

## Step 1: Prepare Docker Image (Already Done)

The Docker image has been prepared and saved as:
- **File:** `obs-sftp-file-processor-portainer.tar.gz`
- **Size:** ~150-200MB (compressed)
- **Image Name:** `obs-sftp-file-processor:portainer`

---

## Step 2: Upload Image to Portainer

### Option A: Via Portainer UI (Recommended)

1. **Access Portainer:**
   - Navigate to: https://10.1.3.28:9443/
   - Login with:
     - Username: `admin`
     - Password: `-(%I!7VUf74c':jh]HUq`

2. **Navigate to Images:**
   - Select your **Environment** (usually "primary" or "local")
   - Click **Images** in the left sidebar

3. **Import Image:**
   - Click **Import image from file** or **Upload** button
   - Select the file: `obs-sftp-file-processor-portainer.tar.gz`
   - Wait for upload and import to complete (may take a few minutes)
   - Verify `obs-sftp-file-processor:portainer` appears in the images list

### Option B: Via Docker CLI on Portainer Server

If you have SSH access to the Portainer server (10.1.3.28):

```bash
# Transfer the file to the server
scp obs-sftp-file-processor-portainer.tar.gz user@10.1.3.28:/tmp/

# SSH into the server
ssh user@10.1.3.28

# Load the image
gunzip -c /tmp/obs-sftp-file-processor-portainer.tar.gz | docker load

# Verify
docker images | grep obs-sftp-file-processor
```

---

## Step 3: Deploy Container in Portainer

### Container Configuration

1. **Go to Containers:**
   - Click **Containers** in the left sidebar
   - Click **Add container**

2. **Basic Settings:**
   - **Name:** `obs-sftp-file-processor`
   - **Image:** `obs-sftp-file-processor:portainer`
   - **Restart policy:** `Unless stopped`

3. **Network & Ports:**
   - Click **Publish a new network port**
   - **Container port:** `8000`
   - **Host port:** `8001` (or your preferred port)
   - **Protocol:** TCP

4. **Environment Variables:**
   Click **Environment** and add these variables:

   ```
   # SFTP Configuration
   SFTP_HOST=10.1.3.123
   SFTP_PORT=2022
   SFTP_USERNAME=6001_obstest
   SFTP_PASSWORD=OEL%7@71ov6I0@=V"`Tn
   SFTP_TIMEOUT=30
   
   # Oracle Configuration
   ORACLE_HOST=10.1.0.111
   ORACLE_PORT=1521
   ORACLE_SERVICE_NAME=PDB_ACHDEV01.privatesubnet1.obsnetwork1.oraclevcn.com
   ORACLE_USERNAME=achowner
   ORACLE_PASSWORD=JV!+x21=Of`jVzW[%)/r@ 
   ORACLE_SCHEMA=ACHOWNER
   ORACLE_HOME=/opt/oracle/instantclient_23_3
   
   # Application Configuration
   APP_DEBUG=false
   APP_LOG_LEVEL=INFO
   PYTHONUNBUFFERED=1
   ```

5. **Volumes (Important!):**
   
   **Volume 1: Oracle Instant Client**
   - Click **Bind** tab
   - **Container:** `/opt/oracle/instantclient_23_3`
   - **Host:** `/path/to/oracle/instantclient_23_3` (adjust to actual path on Portainer server)
   - **Read-only:** ✅ Yes
   
   **Volume 2: Logs Directory**
   - Click **Bind** tab
   - **Container:** `/app/logs`
   - **Host:** `/path/to/logs` (create this directory on Portainer server)
   - **Read-only:** ❌ No

   **Note:** Ensure Oracle Instant Client is extracted on the Portainer server at the specified path.

6. **Health Check:**
   - **Test:** `CMD-SHELL curl -f http://localhost:8000/health || exit 1`
   - **Interval:** `30s`
   - **Timeout:** `10s`
   - **Retries:** `3`
   - **Start period:** `40s`

7. **Deploy:**
   - Click **Deploy the container**
   - Wait for container to start
   - Check logs to verify it's running correctly

---

## Step 4: Verify Deployment

1. **Check Container Status:**
   - Go to **Containers**
   - Verify `obs-sftp-file-processor` shows as **Running** and **Healthy**

2. **Test Health Endpoint:**
   ```bash
   curl https://10.1.3.28:8001/health
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "version": "0.1.0",
     "timestamp": "..."
   }
   ```

3. **Test API Endpoint:**
   ```bash
   curl https://10.1.3.28:8001/files?path=upload
   ```

4. **View Logs:**
   - In Portainer, click on the container
   - Go to **Logs** tab
   - Verify no errors and SFTP connection is successful

---

## Prerequisites on Portainer Server

Before deploying, ensure the Portainer server has:

1. **Oracle Instant Client:**
   ```bash
   # On Portainer server (10.1.3.28)
   mkdir -p /opt/oracle
   cd /opt/oracle
   # Extract instantclient-basic-linux.x64-*.zip here
   unzip instantclient-basic-linux.x64-*.zip
   mv instantclient_* instantclient_23_3
   ```

2. **Logs Directory:**
   ```bash
   mkdir -p /var/log/obs-sftp-file-processor
   chmod 755 /var/log/obs-sftp-file-processor
   ```

3. **Network Access:**
   - Can reach SFTP server: `10.1.3.123:2022`
   - Can reach Oracle database: `10.1.0.111:1521`

---

## Troubleshooting

### Container Won't Start

- Check container logs in Portainer
- Verify all environment variables are set correctly
- Ensure Oracle Instant Client volume is mounted correctly
- Check network connectivity to SFTP and Oracle servers

### Oracle Connection Fails

- Verify `ORACLE_HOME` environment variable is set
- Check Oracle Instant Client is mounted at `/opt/oracle/instantclient_23_3`
- Verify Oracle credentials are correct
- Test network connectivity to Oracle server

### SFTP Connection Fails

- Verify SFTP credentials are correct
- Check SFTP server is accessible from Portainer server
- Verify port 2022 is open and accessible
- Check firewall rules

### Port Conflicts

- If port 8001 is in use, change to another port (e.g., 8002)
- Update port mapping in container settings

---

## File Locations

- **Docker Image:** `obs-sftp-file-processor-portainer.tar.gz` (in project root)
- **Deployment Guide:** This file
- **Docker Compose:** `docker-compose.yml` (for local reference)

---

## Security Notes

⚠️ **Important Security Considerations:**

1. **HTTPS:** Ensure Portainer is accessed via HTTPS (port 9443)
2. **Credentials:** Never commit passwords to git
3. **Environment Variables:** Use Portainer's secrets feature for sensitive values
4. **Network:** Ensure proper firewall rules are in place
5. **Access Control:** Limit Portainer access to authorized users only

---

## Support

If you encounter issues:

1. Check container logs in Portainer
2. Verify all prerequisites are met
3. Test network connectivity from Portainer server
4. Review deployment configuration
5. Check Oracle Instant Client installation

---

## Next Steps After Deployment

1. ✅ Verify health endpoint responds
2. ✅ Test SFTP file listing endpoint
3. ✅ Test Oracle database endpoints
4. ✅ Monitor logs for any errors
5. ✅ Set up monitoring/alerting (optional)
6. ✅ Configure backup for logs (optional)

---

**Deployment Date:** $(date)  
**Image Version:** obs-sftp-file-processor:portainer  
**Portainer URL:** https://10.1.3.28:9443/

