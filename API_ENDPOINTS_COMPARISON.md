# API Endpoints Comparison: `/sync/sftp-to-oracle` vs `/run-sync-process`

## Overview

Both endpoints sync SFTP files to Oracle, but they differ in scope and processing depth.

---

## POST `/sync/sftp-to-oracle`

### Purpose
**Basic sync** - Only copies SFTP files to Oracle `ACH_FILES` table.

### What It Does

1. **Step 1: SFTP to Oracle Sync**
   - Lists files from SFTP `upload` directory
   - Reads each file from SFTP
   - Creates `ACH_FILES` records in Oracle
   - Sets `PROCESSING_STATUS = 'Pending'`
   - **STOPS HERE** - No line processing

### What It Does NOT Do
- ❌ Does NOT process ACH file lines
- ❌ Does NOT create `ACH_FILE_LINES` records
- ❌ Does NOT validate ACH line format
- ❌ Does NOT update file status to 'Processed'
- ❌ Does NOT parse file contents into individual lines

### Response Format
```json
{
  "total_files": 5,
  "successful_syncs": 4,
  "failed_syncs": 1,
  "errors": ["Failed to sync file.txt: ..."]
}
```

### Use Case
- Quick file sync without processing
- Testing SFTP to Oracle connection
- Initial file import
- When you only need files in `ACH_FILES` table

---

## POST `/run-sync-process`

### Purpose
**Complete sync and processing** - Syncs SFTP files AND processes ACH lines.

### What It Does

1. **Step 1: SFTP to Oracle Sync** (Same as `/sync/sftp-to-oracle`)
   - Lists files from SFTP `upload` directory
   - Reads each file from SFTP
   - Creates `ACH_FILES` records in Oracle
   - Sets `PROCESSING_STATUS = 'Pending'`

2. **Step 2: ACH File Line Processing** (Additional step)
   - Finds all `ACH_FILES` with `PROCESSING_STATUS = 'Pending'`
   - For each pending file:
     - Deletes existing `ACH_FILE_LINES` records for that file
     - Parses file contents into individual lines (split by CRLF)
     - Validates each line against FED ACH specification
     - Creates `ACH_FILE_LINES` records with:
       - `LINE_NUMBER` (sequential order)
       - `LINE_CONTENT` (the actual line text)
       - `LINE_ERRORS` (validation errors if any)
     - Updates file status to `PROCESSING_STATUS = 'Processed'`

### Response Format
```json
{
  "status": "Successfully Executed",
  "message": "Sync process completed successfully. 4 files synced, 4 files processed, 125 lines created.",
  "details": {
    "sync_results": {
      "total_files": 5,
      "successful_syncs": 4,
      "failed_syncs": 1,
      "errors": []
    },
    "line_results": {
      "files_processed": 4,
      "total_lines_created": 125,
      "files_with_errors": 0,
      "errors": []
    }
  }
}
```

### Use Case
- Complete end-to-end processing
- Production workflows
- When you need `ACH_FILE_LINES` table populated
- When you need ACH line validation
- When you want files marked as 'Processed'

---

## Side-by-Side Comparison

| Feature | `/sync/sftp-to-oracle` | `/run-sync-process` |
|---------|------------------------|---------------------|
| **SFTP File Sync** | ✅ Yes | ✅ Yes |
| **Creates ACH_FILES Records** | ✅ Yes | ✅ Yes |
| **Processes ACH Lines** | ❌ No | ✅ Yes |
| **Creates ACH_FILE_LINES Records** | ❌ No | ✅ Yes |
| **Validates ACH Line Format** | ❌ No | ✅ Yes |
| **Updates Status to 'Processed'** | ❌ No | ✅ Yes |
| **Processing Time** | Fast (~seconds) | Slower (~minutes for large files) |
| **Response Complexity** | Simple | Detailed (2-step results) |
| **Use Case** | Quick sync | Complete processing |

---

## Workflow Comparison

### `/sync/sftp-to-oracle` Workflow:
```
SFTP Files → ACH_FILES Table (Status: 'Pending')
     ↓
   DONE
```

### `/run-sync-process` Workflow:
```
SFTP Files → ACH_FILES Table (Status: 'Pending')
     ↓
Parse & Validate Lines
     ↓
ACH_FILE_LINES Table (with validation errors)
     ↓
Update ACH_FILES Status to 'Processed'
     ↓
   DONE
```

---

## When to Use Which Endpoint

### Use `/sync/sftp-to-oracle` when:
- ✅ You only need files copied to Oracle
- ✅ You want quick sync without processing
- ✅ You'll process lines later manually
- ✅ Testing SFTP/Oracle connectivity
- ✅ You don't need `ACH_FILE_LINES` populated yet

### Use `/run-sync-process` when:
- ✅ You need complete end-to-end processing
- ✅ You need `ACH_FILE_LINES` table populated
- ✅ You want ACH line validation
- ✅ You want files automatically marked as 'Processed'
- ✅ Production workflow requiring full processing
- ✅ You need validation errors captured in `LINE_ERRORS`

---

## Example Scenarios

### Scenario 1: Initial File Import
**Use:** `/sync/sftp-to-oracle`
- Quick import of files
- Review files before processing
- Process lines later if needed

### Scenario 2: Scheduled Production Job
**Use:** `/run-sync-process`
- Complete automated processing
- All data structures populated
- Files marked as processed
- Validation errors captured

### Scenario 3: Testing
**Use:** `/sync/sftp-to-oracle`
- Faster for testing
- Verify SFTP/Oracle connection
- Check file import without full processing

### Scenario 4: Production Workflow
**Use:** `/run-sync-process`
- Full processing pipeline
- All tables populated
- Ready for downstream processes

---

## Performance Considerations

### `/sync/sftp-to-oracle`
- **Speed:** Fast (seconds)
- **Database Operations:** Only `ACH_FILES` inserts
- **Processing:** Minimal (file read + insert)

### `/run-sync-process`
- **Speed:** Slower (minutes for large files)
- **Database Operations:** 
  - `ACH_FILES` inserts
  - `ACH_FILE_LINES` deletes + inserts
  - `ACH_FILES` updates
- **Processing:** Heavy (parse, validate, batch insert)

---

## Response Time Comparison

For 5 files with ~100 lines each:

| Endpoint | Approximate Time |
|----------|------------------|
| `/sync/sftp-to-oracle` | 5-10 seconds |
| `/run-sync-process` | 30-60 seconds |

---

## Error Handling

### `/sync/sftp-to-oracle`
- Returns simple error list
- Files that fail sync are reported
- No line-level error details

### `/run-sync-process`
- Returns detailed error breakdown
- Separate errors for sync vs. line processing
- Line-level validation errors in `LINE_ERRORS` column
- Status indicates overall success/failure

---

## Summary

**`/sync/sftp-to-oracle`:**
- Simple, fast sync
- Only creates `ACH_FILES` records
- Files remain in 'Pending' status
- No line processing

**`/run-sync-process`:**
- Complete processing pipeline
- Creates `ACH_FILES` AND `ACH_FILE_LINES` records
- Validates ACH lines
- Updates files to 'Processed' status
- More comprehensive but slower

**Recommendation:** Use `/run-sync-process` for production workflows that need complete processing. Use `/sync/sftp-to-oracle` for quick imports or testing.

