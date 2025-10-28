# Oracle Database Setup Guide

## Prerequisites

Your Oracle database requires network encryption, which means you need to install the Oracle Instant Client for thick mode support.

## Installation Steps

### 1. Download Oracle Instant Client

1. Go to: https://www.oracle.com/database/technologies/instant-client/downloads.html
2. Download the **Basic Package** for your platform (macOS/Linux/Windows)
3. Extract to a directory (e.g., `/opt/oracle/instantclient_21_8`)

### 2. Configure Environment Variables

**For macOS/Linux:**
```bash
export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_8:$LD_LIBRARY_PATH
export ORACLE_HOME=/opt/oracle/instantclient_21_8
```

**For Windows:**
```cmd
set PATH=C:\oracle\instantclient_21_8;%PATH%
set ORACLE_HOME=C:\oracle\instantclient_21_8
```

### 3. Test Connection

After installing the Oracle Instant Client, test the connection:

```bash
python test_oracle_connection.py
```

## Alternative: Mock Mode for Testing

If you want to test the application logic without Oracle connectivity, you can use the mock mode:

```bash
python test_oracle_mock.py
```

## Database Configuration

The application is configured to connect to:
- **Host**: 10.1.0.111
- **Port**: 1521
- **Service**: PDB_ACHDEV01.privatesubnet1.obsnetwork1.oraclevcn.com
- **Username**: achowner
- **Password**: TLcbbhQuiV7##sLv4tMr
- **Schema**: ACHOWNER

## API Endpoints

Once Oracle is connected, you can use these endpoints:

- `GET /oracle/ach-files` - List ACH_FILES records
- `POST /oracle/ach-files` - Create new ACH_FILES record
- `GET /oracle/ach-files/{id}` - Get specific ACH_FILES record
- `PUT /oracle/ach-files/{id}` - Update ACH_FILES record
- `DELETE /oracle/ach-files/{id}` - Delete ACH_FILES record
- `POST /sync/sftp-to-oracle` - Sync SFTP files to Oracle

## Testing the Complete Flow

1. Start the FastAPI server:
   ```bash
   uv run python main.py
   ```

2. Test SFTP to Oracle sync:
   ```bash
   python sync_sftp_to_oracle.py
   ```

3. Test all Oracle operations:
   ```bash
   python test_oracle_integration.py
   ```
