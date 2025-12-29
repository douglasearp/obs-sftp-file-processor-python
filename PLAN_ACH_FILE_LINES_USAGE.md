# Plan: ACH_FILE_LINES Table Usage Locations

## Overview

This document provides a comprehensive plan listing all locations where the `ACH_FILE_LINES` table is used in the OBS SFTP File Processor application.

## Table Purpose

The `ACH_FILE_LINES` table stores individual lines from ACH files in a line-by-line format. Each record represents one line from an ACH file, including:
- Line number
- Line content (94-character NACHA record)
- Validation errors (if any)
- Metadata (created by, dates, etc.)

**Note**: This table is an alternative/legacy approach to storing ACH file data. The newer approach uses the ACH record type tables (ACH_FILE_HEADER, ACH_BATCH_HEADER, ACH_ENTRY_DETAIL, etc.) which parse and store structured data by record type.

## Service Layer Usage

### 1. AchFileLinesService Class
**File**: `src/obs_sftp_file_processor/ach_file_lines_service.py`

This is the dedicated service class for all ACH_FILE_LINES operations.

#### Methods:

1. **`delete_lines_by_file_id(file_id: int) -> int`**
   - **SQL**: `DELETE FROM ACH_FILE_LINES WHERE FILE_ID = :file_id`
   - **Purpose**: Deletes all ACH_FILE_LINES records for a specific FILE_ID
   - **Used By**: 
     - `/run-sync-process` endpoint (before inserting new lines)
     - `sync_sftp_to_oracle.py` script (before processing new lines)

2. **`create_ach_file_line(ach_file_line: AchFileLineCreate) -> int`**
   - **SQL**: `INSERT INTO ACH_FILE_LINES (...) VALUES (...) RETURNING FILE_LINES_ID INTO :file_lines_id`
   - **Purpose**: Creates a single ACH_FILE_LINES record
   - **Used By**: Currently not directly used (batch method is preferred)

3. **`create_ach_file_lines_batch(file_id: int, lines_data: List[Dict[str, Any]]) -> int`**
   - **SQL**: `INSERT INTO ACH_FILE_LINES (...) VALUES (...)`
   - **Purpose**: Creates multiple ACH_FILE_LINES records in a batch operation
   - **Used By**:
     - `/run-sync-process` endpoint (main usage)
     - `sync_sftp_to_oracle.py` script (main usage)
   - **Data Structure**:
     ```python
     lines_data = [
         {
             'line_number': int,
             'line_content': str,  # 94-character NACHA record
             'line_errors': Optional[str],  # Validation errors joined with '; '
             'created_by_user': str
         },
         ...
     ]
     ```

4. **`get_ach_file_lines(file_id: int, limit: int = 1000, offset: int = 0) -> List[AchFileLineResponse]`**
   - **SQL**: `SELECT ... FROM ACH_FILE_LINES WHERE FILE_ID = :file_id ORDER BY LINE_NUMBER OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY`
   - **Purpose**: Retrieves ACH_FILE_LINES records for a specific FILE_ID with pagination
   - **Used By**: Currently no API endpoint exposes this (potential future endpoint)
   - **Returns**: List of `AchFileLineResponse` objects

5. **`get_ach_file_lines_count(file_id: int) -> int`**
   - **SQL**: `SELECT COUNT(*) FROM ACH_FILE_LINES WHERE FILE_ID = :file_id`
   - **Purpose**: Gets count of ACH_FILE_LINES records for a specific FILE_ID
   - **Used By**: Currently not used in any endpoint (potential future usage)

## API Endpoint Usage

### 1. POST /run-sync-process
**File**: `src/obs_sftp_file_processor/main.py` (lines 1378-1503)

**Purpose**: Processes all ACH_FILES with status 'Pending' and creates ACH_FILE_LINES records

**Process Flow**:
1. Gets all ACH_FILES records with `PROCESSING_STATUS = 'Pending'`
2. For each file:
   - Parses file content using `parse_ach_file_content()` (from `ach_validator.py`)
   - Deletes existing ACH_FILE_LINES records for that FILE_ID
   - Creates batch data from validation results
   - Inserts all lines using `create_ach_file_lines_batch()`
   - Updates ACH_FILES status to 'Processed'

**Code Location**:
```python
@app.post("/run-sync-process")
async def run_sync_process(
    oracle_service: OracleService = Depends(get_oracle_service),
    sftp_service: SFTPService = Depends(get_sftp_service),
    ach_file_lines_service: AchFileLinesService = Depends(get_ach_file_lines_service)
):
    # ... code ...
    deleted_count = ach_file_lines_service.delete_lines_by_file_id(ach_file.file_id)
    lines_created = ach_file_lines_service.create_ach_file_lines_batch(ach_file.file_id, batch_data)
```

**Key Operations**:
- **DELETE**: Removes existing lines before inserting new ones
- **INSERT**: Creates new ACH_FILE_LINES records in batch
- **UPDATE**: Updates ACH_FILES.PROCESSING_STATUS to 'Processed'

## Standalone Script Usage

### 1. sync_sftp_to_oracle.py
**File**: `sync_sftp_to_oracle.py`

**Purpose**: Standalone script to sync SFTP files to Oracle and process ACH lines

**Class**: `SftpToOracleSync`

**Methods Using ACH_FILE_LINES**:

1. **`process_ach_file_lines(file_id: int, file_content: str) -> Dict[str, Any]`**
   - **Lines**: 124-177
   - **Process**:
     - Parses ACH file content using `parse_ach_file_content()`
     - Deletes existing ACH_FILE_LINES records
     - Creates batch data with validation results
     - Inserts lines using `create_ach_file_lines_batch()`
     - Returns statistics (total_lines, valid_lines, invalid_lines, lines_created)

2. **`process_all_pending_files() -> Dict[str, Any]`**
   - **Lines**: 181-204
   - **Process**:
     - Gets all ACH_FILES with status 'Pending'
     - Calls `process_ach_file_lines()` for each file
     - Updates file status to 'Processed'

**Usage Example**:
```python
sync_service = SftpToOracleSync()
# Process lines for a specific file
results = sync_service.process_ach_file_lines(file_id, file_content)
# Process all pending files
results = sync_service.process_all_pending_files()
```

## Model Definitions

### 1. ach_file_lines_models.py
**File**: `src/obs_sftp_file_processor/ach_file_lines_models.py`

**Models Defined**:

1. **`AchFileLineBase`**
   - Base model with common fields
   - Fields: `file_id`, `line_number`, `line_content`, `line_errors`, `created_by_user`, `updated_by_user`

2. **`AchFileLineCreate`**
   - Model for creating new ACH_FILE_LINES records
   - Extends `AchFileLineBase`

3. **`AchFileLineUpdate`**
   - Model for updating ACH_FILE_LINES records
   - Fields: `line_errors`, `updated_by_user`

4. **`AchFileLine`**
   - Complete model with all fields including primary key
   - Fields: All base fields + `file_lines_id`, `created_date`, `updated_date`

5. **`AchFileLineResponse`**
   - Response model for API endpoints
   - Fields: All fields from `AchFileLine`

6. **`AchFileLineListResponse`**
   - Response model for list endpoints
   - Fields: `lines: List[AchFileLineResponse]`, `total_count: int`

## Dependency Injection

### 1. get_ach_file_lines_service()
**File**: `src/obs_sftp_file_processor/main.py` (lines 107-110)

**Purpose**: FastAPI dependency function that provides `AchFileLinesService` instance

**Code**:
```python
def get_ach_file_lines_service() -> AchFileLinesService:
    """Dependency to get ACH file lines service instance."""
    return AchFileLinesService(config.oracle)
```

**Used By**:
- `/run-sync-process` endpoint (via `Depends(get_ach_file_lines_service)`)

## Integration with ACH Validator

### 1. parse_ach_file_content()
**File**: `src/obs_sftp_file_processor/ach_validator.py`

**Purpose**: Parses ACH file content and validates each line

**Returns**: `List[ACHLineValidation]`

**Used By**:
- `/run-sync-process` endpoint (to get line validations)
- `sync_sftp_to_oracle.py` (to get line validations)

**Data Flow**:
```
ACH File Content (string)
    ↓
parse_ach_file_content()
    ↓
List[ACHLineValidation] (with line_number, line_content, errors)
    ↓
Convert to batch_data format
    ↓
create_ach_file_lines_batch()
    ↓
ACH_FILE_LINES table
```

## Table Schema Reference

### ACH_FILE_LINES Table Structure

**Columns**:
- `FILE_LINES_ID` - Primary key (auto-generated)
- `FILE_ID` - Foreign key to ACH_FILES.FILE_ID
- `LINE_NUMBER` - Line number in the file (1-based)
- `LINE_CONTENT` - Full 94-character NACHA record line
- `LINE_ERRORS` - Validation errors (semicolon-separated)
- `CREATED_BY_USER` - User who created the record
- `CREATED_DATE` - Creation timestamp
- `UPDATED_BY_USER` - User who last updated
- `UPDATED_DATE` - Last update timestamp

**Indexes**:
- Primary key index on `FILE_LINES_ID`
- Index on `FILE_ID` for fast lookups

## Comparison with ACH Record Type Tables

### ACH_FILE_LINES vs. ACH Record Type Tables

| Aspect | ACH_FILE_LINES | ACH Record Type Tables |
|--------|----------------|----------------------|
| **Storage Format** | Line-by-line (raw) | Parsed by record type |
| **Data Structure** | Flat (all lines same structure) | Structured (different tables per type) |
| **Validation** | Stores validation errors | Validates during parsing |
| **Query Complexity** | Simple (all lines in one table) | Complex (requires JOINs) |
| **Use Case** | Line-by-line processing, validation | Structured data queries, reporting |
| **Populated By** | `/run-sync-process` endpoint | `/oracle/ach-files-update-by-file-id/{file_id}` |

### When to Use Each

**Use ACH_FILE_LINES when**:
- You need to process files line-by-line
- You need to see validation errors per line
- You need simple line-based queries
- You're doing batch validation processing

**Use ACH Record Type Tables when**:
- You need structured data queries
- You need to join with batch/file headers
- You're doing payment processing
- You need data for stored procedures (like Core Post SP)

## Current Usage Summary

### Active Usage
1. ✅ **`/run-sync-process` endpoint** - Main API endpoint that populates ACH_FILE_LINES
2. ✅ **`sync_sftp_to_oracle.py` script** - Standalone script for processing files

### Service Methods Available (Not Currently Exposed via API)
1. ⚠️ **`get_ach_file_lines()`** - Retrieves lines (no API endpoint)
2. ⚠️ **`get_ach_file_lines_count()`** - Gets count (no API endpoint)
3. ⚠️ **`create_ach_file_line()`** - Single line insert (not used, batch preferred)

### Potential Future Endpoints
Based on available service methods, these endpoints could be created:
- `GET /oracle/ach-file-lines/{file_id}` - Get lines for a file
- `GET /oracle/ach-file-lines/{file_id}/count` - Get line count
- `POST /oracle/ach-file-lines` - Create single line (unlikely needed)

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ACH File Processing                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  ACH_FILES Table (PROCESSING_STATUS = 'Pending')             │
│  - FILE_ID                                                  │
│  - FILE_CONTENTS (CLOB)                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  parse_ach_file_content()                                   │
│  - Splits file into lines                                   │
│  - Validates each line (94 chars, record type, etc.)       │
│  - Returns List[ACHLineValidation]                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  delete_lines_by_file_id()                                  │
│  - DELETE FROM ACH_FILE_LINES WHERE FILE_ID = :file_id      │
│  - Removes existing lines (clean slate)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  create_ach_file_lines_batch()                              │
│  - INSERT INTO ACH_FILE_LINES (batch)                       │
│  - Creates one record per line                              │
│  - Stores: line_number, line_content, line_errors          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  ACH_FILE_LINES Table                                       │
│  - One row per line in the ACH file                        │
│  - Includes validation errors                               │
│  - Ordered by LINE_NUMBER                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  UPDATE ACH_FILES                                           │
│  - PROCESSING_STATUS = 'Processed'                          │
└─────────────────────────────────────────────────────────────┘
```

## Key Files Reference

### Source Files
1. **Service**: `src/obs_sftp_file_processor/ach_file_lines_service.py`
   - Complete service implementation
   - All database operations

2. **Models**: `src/obs_sftp_file_processor/ach_file_lines_models.py`
   - Pydantic models for request/response

3. **Main Endpoint**: `src/obs_sftp_file_processor/main.py`
   - Lines 23: Import statement
   - Lines 107-110: Dependency injection function
   - Lines 1378-1503: `/run-sync-process` endpoint

4. **Standalone Script**: `sync_sftp_to_oracle.py`
   - Lines 15: Import statement
   - Lines 27: Service initialization
   - Lines 124-177: `process_ach_file_lines()` method
   - Lines 181-204: `process_all_pending_files()` method

5. **Validator**: `src/obs_sftp_file_processor/ach_validator.py`
   - `parse_ach_file_content()` function
   - Used to generate data for ACH_FILE_LINES

### Documentation Files
1. **API_ENDPOINTS_COMPARISON.md**
   - Documents differences between endpoints
   - Notes which endpoints create ACH_FILE_LINES

2. **PLAN_ORACLE_TABLES_LIST.md**
   - General table documentation
   - Includes ACH_FILE_LINES in table list

## SQL Operations Summary

### INSERT Operations
- **Single Insert**: `create_ach_file_line()` - Not commonly used
- **Batch Insert**: `create_ach_file_lines_batch()` - Primary method
  - Uses `cursor.executemany()` for efficiency
  - Inserts all lines for a file in one transaction

### SELECT Operations
- **Get Lines**: `get_ach_file_lines()` - With pagination support
- **Get Count**: `get_ach_file_lines_count()` - Simple count query

### DELETE Operations
- **Delete by FILE_ID**: `delete_lines_by_file_id()` - Removes all lines for a file
  - Used before inserting new lines (clean slate approach)

### UPDATE Operations
- Currently no direct UPDATE operations on ACH_FILE_LINES
- Updates are done via DELETE + INSERT pattern

## Integration Points

### 1. With ACH_FILES Table
- **Relationship**: Foreign key `FILE_ID` references `ACH_FILES.FILE_ID`
- **Usage**: All ACH_FILE_LINES operations are scoped to a specific FILE_ID
- **Lifecycle**: When ACH_FILES record is deleted, ACH_FILE_LINES records should be deleted (if CASCADE is configured)

### 2. With ACH Validator
- **Integration**: Uses `parse_ach_file_content()` to validate lines
- **Data Flow**: Validator returns `ACHLineValidation` objects which are converted to batch data

### 3. With Processing Status
- **Trigger**: Files with `PROCESSING_STATUS = 'Pending'` are processed
- **Result**: After processing, status is updated to 'Processed'
- **Location**: `/run-sync-process` endpoint handles this workflow

## Notes and Considerations

1. **Clean Slate Approach**: The service always deletes existing lines before inserting new ones. This ensures no duplicate lines if a file is reprocessed.

2. **Batch Processing**: All inserts use batch operations for efficiency, especially important for large ACH files with many lines.

3. **Validation Errors**: Line validation errors are stored in `LINE_ERRORS` column as semicolon-separated strings. This allows tracking which lines failed validation and why.

4. **No Direct API Endpoints**: Unlike ACH_FILES which has full CRUD endpoints, ACH_FILE_LINES is only populated via the `/run-sync-process` endpoint. There are no GET/POST/PUT/DELETE endpoints for individual line operations.

5. **Alternative to Record Type Tables**: ACH_FILE_LINES provides a simpler, line-by-line storage approach compared to the structured ACH record type tables. Both can coexist in the system.

6. **Performance Considerations**: 
   - Batch inserts are used for efficiency
   - Pagination is supported in `get_ach_file_lines()` for large files
   - Indexes on FILE_ID ensure fast lookups

7. **Future Enhancements**:
   - Could add API endpoints to retrieve lines
   - Could add filtering by validation status
   - Could add line-level update operations
   - Could add export functionality for lines with errors

