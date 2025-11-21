# Portainer v3 Deployment Guide

## Image Information

- **Image Name:** `obs-sftp-file-processor:portainer-v3`
- **Image Size:** 12.8GB
- **Export File:** `obs-sftp-file-processor-portainer-v3.tar` (5.7GB)
- **Platform:** `linux/amd64`
- **Python Version:** 3.11.14

## Features Included

✅ **Oracle Instant Client** - Thick mode support included in image  
✅ **Oracle Connection Test** - Tests Oracle connection on startup  
✅ **Pydantic Schema Fix** - No more schema field warning  
✅ **SFTP Archived Folder** - Auto-creates archived folder on startup  
✅ **All Latest Code** - Includes all recent updates and fixes  

## Deployment Steps

### Step 1: Upload Image to Portainer

1. **Access Portainer:**
   - Navigate to your Portainer instance
   - Login with your credentials

2. **Import Image:**
   - Go to **Images** (left sidebar)
   - Click **Import image from file** or **Upload** button
   - Select: `obs-sftp-file-processor-portainer-v3.tar`
   - Wait for upload and import to complete (may take 5-10 minutes for 5.7GB file)

3. **Verify Image:**
   - Check that `obs-sftp-file-processor:portainer-v3` appears in the images list

### Step 2: Deploy Container

1. **Create Container:**
   - Go to **Containers** → **Add container**

2. **Basic Settings:**
   - **Name:** `obs-sftp-file-processor` (or your preferred name)
   - **Image:** `obs-sftp-file-processor:portainer-v3`
   - **Restart policy:** `Unless stopped`

3. **Port Mapping:**
   - **Container Port:** `8000`
   - **Host Port:** `8001` (or your preferred port)

4. **Environment Variables:**
   Add these environment variables:

   ```
   # Oracle Configuration
   ORACLE_HOME=/opt/oracle/instantclient_23_3
   ORACLE_HOST=10.1.0.111
   ORACLE_PORT=1521
   ORACLE_SERVICE_NAME=PDB_ACHDEV01.privatesubnet1.obsnetwork1.oraclevcn.com
   ORACLE_USERNAME=achowner
   ORACLE_PASSWORD=<your-oracle-password>
   ORACLE_SCHEMA=ACHOWNER
   
   # SFTP Configuration
   SFTP_HOST=10.1.3.123
   SFTP_PORT=2022
   SFTP_USERNAME=6001_obstest
   SFTP_PASSWORD=<your-sftp-password>
   SFTP_UPLOAD_FOLDER=upload
   SFTP_ARCHIVED_FOLDER=upload/archived
   
   # Application Configuration
   APP_DEBUG=false
   APP_LOG_LEVEL=INFO
   PYTHONUNBUFFERED=1
   ```

5. **Volumes:**
   - **NO Oracle bind mount needed!** ✅ (Oracle is in the image)
   - Optional: Map `./logs` → `/app/logs` for persistent logs

6. **Click "Deploy the container"**

### Step 3: Verify Deployment

1. **Check Logs:**
   - Go to container → **Logs**
   - Look for these startup messages:
     ```
     Testing Oracle database connection on startup...
     Using Oracle thick mode (ORACLE_HOME=/opt/oracle/instantclient_23_3)
     Oracle connection pool established successfully
     ✅ Oracle connection test successful
     Archived folder 'upload/archived' verified/created on startup
     INFO:     Uvicorn running on http://0.0.0.0:8000
     ```

2. **Test Endpoints:**
   ```bash
   # Health check
   curl http://<portainer-host>:8001/health
   
   # Oracle clients
   curl http://<portainer-host>:8001/oracle/clients
   
   # API docs
   open http://<portainer-host>:8001/docs
   ```

## What's New in v3

- ✅ Oracle connection test on startup (visible in logs)
- ✅ Fixed Pydantic schema field warning
- ✅ Improved error handling
- ✅ All latest code updates

## Troubleshooting

### Oracle Connection Fails

**Check:**
- Environment variables are set correctly
- Network connectivity to Oracle database
- Oracle credentials are correct
- Check container logs for specific error messages

### Image Import Fails

**Solutions:**
- Ensure you have enough disk space (need ~6GB free)
- Check network connection (upload may take time)
- Try importing in smaller chunks if possible

### Container Won't Start

**Check:**
- Port conflicts (ensure port 8001 is available)
- Environment variables are properly formatted
- Container logs for specific errors

## Comparison with Previous Versions

| Feature | v2 | v3 |
|---------|----|----|
| Oracle Instant Client | ✅ | ✅ |
| Oracle Startup Test | ❌ | ✅ |
| Schema Warning Fix | ✅ | ✅ |
| Latest Code | ✅ | ✅ |

## Support

For issues or questions:
1. Check container logs first
2. Verify environment variables
3. Test network connectivity
4. Review this deployment guide

---

**Image File:** `obs-sftp-file-processor-portainer-v3.tar` (5.7GB)  
**Ready for:** Remote Portainer deployment  
**Status:** ✅ Production Ready

