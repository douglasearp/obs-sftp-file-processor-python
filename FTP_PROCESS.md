# SFTP File Processing Workflow

## Overview

This document describes the complete process for processing files from the SFTP server: reading files from the upload folder, uploading their contents to the Oracle database, and moving the files to the archive folder.

## Process Flow

```
┌─────────────────┐
│  SFTP Upload    │
│     Folder      │
│  (upload/)      │
└────────┬────────┘
         │
         │ 1. Read File
         ▼
┌─────────────────┐
│  File Content   │
│   (in memory)   │
└────────┬────────┘
         │
         │ 2. Validate Client ID
         ▼
┌─────────────────┐
│  Client ID      │
│  Validation     │
└────────┬────────┘
         │
         │ 3. Rename File
         │    (add client_id prefix)
         ▼
┌─────────────────┐
│  Renamed File   │
│  (CLIENTID_...) │
└────────┬────────┘
         │
         │ 4. Create Database Records
         ▼
┌─────────────────┐     ┌─────────────────┐
│  ACH_FILES      │     │ ACH_FILES_BLOBS │
│   Table         │     │     Table       │
└─────────────────┘     └─────────────────┘
         │
         │ 5. Move to Archive
         ▼
┌─────────────────┐
│  SFTP Archive   │
│     Folder      │
│(upload/archived)│
└─────────────────┘
```

## API Endpoint

**Endpoint**: `POST /files/process-sftp-file`

**Base URL**: `http://localhost:8002` (or your server URL)

**Full URL**: `http://localhost:8002/files/process-sftp-file`

## Request Format

### Request Body

```json
{
  "file_name": "example_file.txt",
  "client_id": "6001",
  "created_by_user": "system-user"
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_name` | string | Yes | Name of the file in the SFTP upload folder |
| `client_id` | string | Yes | Client ID to prefix to the filename (must exist in active clients) |
| `created_by_user` | string | No | User who created the record (defaults to "system-user") |

### Example Request

```bash
curl -X POST "http://localhost:8002/files/process-sftp-file" \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "ach_file_20241121.txt",
    "client_id": "6001",
    "created_by_user": "admin@example.com"
  }'
```

## Process Steps

### Step 1: Validate Client ID

The system validates that the provided `client_id` exists in the active clients list from the Oracle database.

- **Query**: Retrieves all active clients from `CLIENTS` table
- **Validation**: Checks if `client_id` is in the active clients list
- **Error**: Returns 400 if client_id is not found

### Step 2: Read File from SFTP Upload Folder

The system reads the file content from the SFTP server.

- **Source Path**: `{upload_folder}/{file_name}`
  - Default upload folder: `upload`
  - Example: `upload/ach_file_20241121.txt`
- **Operation**: Reads file content as bytes, then decodes to UTF-8 string
- **Error**: Returns 404 if file doesn't exist

### Step 3: Rename File with Client ID Prefix

The filename is renamed to include the client ID prefix.

- **Original Filename**: `ach_file_20241121.txt`
- **Renamed Filename**: `CLIENTID_6001_ach_file_20241121.txt`
- **Format**: `CLIENTID_{client_id}_{original_filename}`
- **Note**: If filename already contains the client ID pattern, it's not renamed again

### Step 4: Create ACH_FILES Record

Creates a record in the `ACH_FILES` table.

**Table**: `ACH_FILES`

**Fields**:
- `ORIGINAL_FILENAME`: Renamed filename (e.g., `CLIENTID_6001_ach_file_20241121.txt`)
- `PROCESSING_STATUS`: Set to `"Pending"`
- `FILE_CONTENTS`: File content as CLOB
- `CREATED_BY_USER`: From request or defaults to `"system-user"`
- `CREATED_DATE`: Current timestamp (auto-generated)

**Returns**: `file_id` (auto-generated primary key)

**Error Handling**: If this step fails, the process stops and returns an error response.

### Step 5: Create ACH_FILES_BLOBS Record

Creates a corresponding record in the `ACH_FILES_BLOBS` table.

**Table**: `ACH_FILES_BLOBS`

**Fields**:
- `FILE_ID`: Foreign key to `ACH_FILES.FILE_ID` (from Step 4)
- `ORIGINAL_FILENAME`: Renamed filename
- `PROCESSING_STATUS`: Set to `"Pending"` initially, then updated to `"Completed"`
- `FILE_CONTENTS`: File content as CLOB
- `CREATED_BY_USER`: From request or defaults to `"system-user"`
- `CREATED_DATE`: Current timestamp (auto-generated)

**Returns**: `file_blob_id` (auto-generated primary key)

**Status Update**: After successful creation, status is updated to `"Completed"`

**Error Handling**: If this step fails, the `ACH_FILES` record remains, but the process returns an error.

### Step 6: Move File to Archive Folder

Moves the file from the upload folder to the archive folder on the SFTP server.

- **Source Path**: `upload/ach_file_20241121.txt`
- **Destination Path**: `upload/archived/CLIENTID_6001_ach_file_20241121.txt`
- **Operation**: 
  1. Ensures archive folder exists (creates if needed)
  2. Moves file using SFTP `rename` operation
- **Archive Folder**: `upload/archived` (subfolder of upload)

**Error Handling**: If this step fails, the database records are still created, but the file remains in the upload folder. The response indicates partial success.

## Response Format

### Success Response

```json
{
  "success": true,
  "message": "File processed successfully",
  "data": {
    "file_id": 12345,
    "file_blob_id": 67890,
    "original_filename": "ach_file_20241121.txt",
    "renamed_filename": "CLIENTID_6001_ach_file_20241121.txt",
    "processing_status": "Completed",
    "archived_path": "upload/archived/CLIENTID_6001_ach_file_20241121.txt"
  }
}
```

### Error Response

```json
{
  "success": false,
  "message": "Failed to create ACH_FILES record",
  "error": "ORA-00001: unique constraint violated",
  "details": {
    "file_id": null,
    "file_blob_id": null,
    "processing_status": "Failed",
    "stage": "file_creation"
  }
}
```

### Partial Success Response

If database records are created but file move fails:

```json
{
  "success": true,
  "message": "File processed successfully, but failed to move to archived folder: Connection timeout",
  "data": {
    "file_id": 12345,
    "file_blob_id": 67890,
    "original_filename": "ach_file_20241121.txt",
    "renamed_filename": "CLIENTID_6001_ach_file_20241121.txt",
    "processing_status": "Completed",
    "archived_path": "upload/archived/CLIENTID_6001_ach_file_20241121.txt"
  }
}
```

## Configuration

### SFTP Folders

Configured in `src/obs_sftp_file_processor/config.py`:

```python
upload_folder: str = "upload"
archived_folder: str = "upload/archived"
```

These can be overridden via environment variables:
- `SFTP_UPLOAD_FOLDER`
- `SFTP_ARCHIVED_FOLDER`

### Database Tables

#### ACH_FILES Table

Stores file metadata and contents:
- Primary Key: `FILE_ID` (auto-generated)
- File Contents: `FILE_CONTENTS` (CLOB)
- Status: `PROCESSING_STATUS` (Pending, Completed, Failed)

#### ACH_FILES_BLOBS Table

Stores file contents as BLOB/CLOB:
- Primary Key: `FILE_BLOB_ID` (auto-generated)
- Foreign Key: `FILE_ID` → `ACH_FILES.FILE_ID`
- File Contents: `FILE_CONTENTS` (CLOB)
- Status: `PROCESSING_STATUS` (Pending, Completed, Failed)

## Error Scenarios

### 1. Client ID Not Found

**Error**: `400 Bad Request`

**Message**: `"Client ID '6001' not found in active clients"`

**Action**: Verify client_id exists in the `CLIENTS` table with active status.

### 2. File Not Found

**Error**: `404 Not Found`

**Message**: `"File not found: upload/ach_file_20241121.txt"`

**Action**: Verify file exists in the SFTP upload folder.

### 3. Database Connection Error

**Error**: `500 Internal Server Error`

**Message**: `"Failed to create ACH_FILES record: ORA-12541: TNS:no listener"`

**Action**: Check Oracle database connectivity and configuration.

### 4. SFTP Connection Error

**Error**: `500 Internal Server Error`

**Message**: `"Failed to move file to archived folder: Authentication failed: transport shut down"`

**Action**: Check SFTP server connectivity and credentials. The system will automatically retry connections.

### 5. Large File Memory Error

**Error**: `500 Internal Server Error`

**Message**: `"ORA-04036: PGA memory used by the instance exceeds PGA_AGGREGATE_LIMIT"`

**Action**: For files >1MB, the system automatically uses DBMS_LOB for chunked writes. If this error persists, contact database administrator to increase PGA_AGGREGATE_LIMIT.

## Best Practices

### 1. File Naming

- Use descriptive filenames
- Include dates/timestamps in filenames
- Avoid special characters that might cause issues

### 2. Client ID Validation

- Always validate client_id before processing
- Use active clients only
- Handle inactive clients appropriately

### 3. Error Handling

- Check response `success` field
- Handle partial success scenarios
- Log errors for troubleshooting
- Retry failed operations when appropriate

### 4. File Size Considerations

- Files >1MB automatically use optimized DBMS_LOB writes
- Very large files (>100MB) may require additional configuration
- Monitor database PGA memory usage

### 5. Archive Folder Management

- Archive folder is automatically created if it doesn't exist
- Files are renamed with client_id prefix before archiving
- Original filename is preserved in database records

## Related Endpoints

### List Files in Upload Folder

```
GET /files?path=upload
```

Returns list of files available for processing.

### List Archived Files

```
GET /files/archived
```

Returns list of files in the archive folder.

### Get File from Database

```
GET /oracle/ach-files/{file_id}
```

Retrieves file content from `ACH_FILES` table.

### Get File Blob from Database

```
GET /oracle/ach-files-blobs/{file_blob_id}
```

Retrieves file content from `ACH_FILES_BLOBS` table.

## Example Workflow

### Complete Processing Example

```bash
# 1. List files in upload folder
curl -X GET "http://localhost:8002/files?path=upload"

# Response shows: ["ach_file_20241121.txt", "another_file.txt"]

# 2. Process a file
curl -X POST "http://localhost:8002/files/process-sftp-file" \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "ach_file_20241121.txt",
    "client_id": "6001",
    "created_by_user": "admin@example.com"
  }'

# Response:
# {
#   "success": true,
#   "message": "File processed successfully",
#   "data": {
#     "file_id": 12345,
#     "file_blob_id": 67890,
#     "original_filename": "ach_file_20241121.txt",
#     "renamed_filename": "6001_ach_file_20241121.txt",
#     "processing_status": "Completed",
#     "archived_path": "upload/archived/6001_ach_file_20241121.txt"
#   }
# }

# 3. Verify file moved to archive
curl -X GET "http://localhost:8002/files/archived"

# Response shows: ["CLIENTID_6001_ach_file_20241121.txt", ...]

# 4. Retrieve file from database
curl -X GET "http://localhost:8002/oracle/ach-files/12345"
```

## Troubleshooting

### File Not Processing

1. Check file exists in upload folder: `GET /files?path=upload`
2. Verify client_id is active: `GET /oracle/clients`
3. Check application logs for errors
4. Verify database connectivity: `GET /health`

### File Not Moving to Archive

1. Check SFTP connection: Verify credentials and connectivity
2. Check archive folder permissions on SFTP server
3. Review response message for specific error
4. File may still be in upload folder if move failed

### Database Records Not Created

1. Check Oracle database connectivity
2. Verify table permissions
3. Check for constraint violations (unique constraints, foreign keys)
4. Review database logs for detailed errors

## Security Considerations

1. **Authentication**: Ensure API endpoints are properly secured
2. **File Validation**: Validate file contents before processing
3. **Client ID Validation**: Always validate client_id against active clients
4. **Error Messages**: Don't expose sensitive information in error messages
5. **SFTP Credentials**: Store SFTP credentials securely (environment variables)

## Performance Notes

- Files are read into memory before database insertion
- Large files (>1MB) use optimized DBMS_LOB chunked writes
- SFTP connections are automatically managed and retried
- Database connections use connection pooling

## Related Documentation

- `ORA_04036_FIX.md` - Information about large file processing optimizations
- `SFTP_CONNECTION_FIX.md` - Information about SFTP connection management
- `database/README_ACH_FILES_BLOBS.md` - Database table documentation

