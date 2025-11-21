# ORA-04036 PGA Memory Fix

## Problem

When updating large CLOB values in `ACH_FILES`, Oracle was throwing:
```
ORA-04036: PGA memory used by the instance or PDB exceeds PGA_AGGREGATE_LIMIT
```

This error occurs when Oracle tries to load large CLOB values entirely into PGA (Program Global Area) memory during UPDATE operations.

## Root Cause

The original code used direct CLOB assignment:
```sql
UPDATE ACH_FILES 
SET FILE_CONTENTS = :file_contents
WHERE FILE_ID = :file_id
```

For large CLOBs (>1MB), this causes Oracle to:
1. Load the entire old CLOB into PGA memory
2. Allocate memory for the new CLOB value
3. Process the update
4. The audit trigger also copies the CLOB, doubling memory usage

## Solution

The fix uses Oracle's `DBMS_LOB` package to write CLOBs in chunks, which:
- Reduces PGA memory usage by processing data in smaller pieces
- Avoids loading entire CLOBs into memory at once
- Uses efficient chunked writes (32KB chunks)

### Implementation

For files larger than 1MB, the code now:
1. Locks the row with `FOR UPDATE`
2. Gets the CLOB locator
3. Truncates the existing CLOB
4. Writes new content in 32KB chunks using `DBMS_LOB.WRITEAPPEND`

### Code Changes

**File**: `src/obs_sftp_file_processor/oracle_service.py`

**Methods Updated**:
- `update_ach_file()` - General update method
- `update_ach_file_by_file_id()` - Specific file_id update method

Both methods now:
- Check file size (>1MB threshold)
- Use `DBMS_LOB` for large files
- Use standard UPDATE for small files

## Usage

No API changes required. The fix is transparent to API consumers:

```python
# Small file (<1MB) - uses standard UPDATE
PUT /oracle/ach-files/{file_id}
{
  "file_contents": "small content..."
}

# Large file (>1MB) - automatically uses DBMS_LOB
PUT /oracle/ach-files/{file_id}
{
  "file_contents": "very large content..."  # >1MB
}
```

## Additional Recommendations

### 1. Database Configuration

If you continue to see PGA issues, consider:

**Increase PGA_AGGREGATE_LIMIT** (requires DBA):
```sql
ALTER SYSTEM SET PGA_AGGREGATE_LIMIT = 4G SCOPE=SPFILE;
-- Restart database required
```

**Monitor PGA Usage**:
```sql
SELECT 
    name,
    value/1024/1024/1024 AS value_gb
FROM v$parameter
WHERE name LIKE '%PGA%'
ORDER BY name;
```

### 2. Alternative: Use ACH_FILES_BLOBS Table

For very large files, consider using the `ACH_FILES_BLOBS` table instead:
- Designed specifically for large file storage
- Better separation of concerns
- Can use different storage parameters

### 3. Consider File Size Limits

Add validation to reject extremely large files:
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
if len(file_contents) > MAX_FILE_SIZE:
    raise HTTPException(400, "File too large")
```

### 4. Monitor and Log

The fix includes logging:
- Large file updates are logged with size information
- Helps identify which files are causing issues

## Testing

Test with files of various sizes:
1. Small files (<1MB) - should use standard UPDATE
2. Medium files (1-10MB) - should use DBMS_LOB
3. Large files (>10MB) - should use DBMS_LOB with chunking

## Performance Impact

- **Small files**: No performance impact (uses standard UPDATE)
- **Large files**: Slightly slower due to chunked writes, but prevents memory errors
- **Memory usage**: Significantly reduced PGA memory consumption

## Related Oracle Documentation

- [DBMS_LOB Package](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_LOB.html)
- [ORA-04036 Error](https://docs.oracle.com/error-help/db/ora-04036/)
- [PGA Memory Management](https://docs.oracle.com/en/database/oracle/oracle-database/19/cncpt/memory-architecture.html#GUID-4A8BC96A-4B0A-4B8F-8B8F-8B8F8B8F8B8F)

