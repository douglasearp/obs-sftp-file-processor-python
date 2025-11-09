# Oracle Instant Client Setup for Thick Mode

## Current Status
The Docker container is configured to use **thick mode** (Oracle Instant Client required) because your Oracle database requires network encryption.

## Setup Options

### Option 1: Mount Oracle Instant Client as Volume (Recommended)

1. **Download Linux x86-64 Oracle Instant Client:**
   - Visit: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html
   - Accept license agreement
   - Download "Basic Package" (e.g., `instantclient-basic-linux.x64-23.3.0.23.09.zip`)

2. **Extract to project directory:**
   ```bash
   mkdir -p oracle
   cd oracle
   unzip ~/Downloads/instantclient-basic-linux.x64-*.zip
   mv instantclient_* instantclient_23_3
   cd ..
   ```

3. **Verify the directory exists:**
   ```bash
   ls -la ./oracle/instantclient_23_3/libclntsh.so*
   ```

4. **Restart Docker:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Option 2: Use Environment Variable

If you have Oracle Instant Client extracted elsewhere, set the path:

```bash
export ORACLE_INSTANTCLIENT_PATH=/path/to/your/instantclient_23_3
docker-compose up -d
```

## Verify Thick Mode

After setup, check the logs:

```bash
docker logs obs-sftp-file-processor | grep -i "thick mode"
```

You should see: `"Using Oracle thick mode (ORACLE_HOME=/opt/oracle/instantclient_23_3)"`

## Test Connection

```bash
curl http://localhost:8001/oracle/ach-files?limit=2
```

Should return data instead of encryption errors.

