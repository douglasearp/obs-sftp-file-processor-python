# ACH_FILES_BLOBS Table Creation

This directory contains SQL scripts for creating the `ACH_FILES_BLOBS` table.

## Table Purpose

The `ACH_FILES_BLOBS` table stores file contents as CLOB for ACH files that have been processed from the SFTP server. This table works in conjunction with `ACH_FILES` to provide a complete record of processed files.

## Table Structure

- **FILE_BLOB_ID**: Primary key (auto-incrementing)
- **FILE_ID**: Foreign key to ACH_FILES.FILE_ID (NOT NULL, with CASCADE delete)
- **ORIGINAL_FILENAME**: Filename from SFTP (may include CLIENTID prefix)
- **PROCESSING_STATUS**: Status of processing (Pending, Completed, Failed)
- **FILE_CONTENTS**: File contents stored as CLOB
- **CREATED_BY_USER**: User who created the record
- **CREATED_DATE**: Timestamp when record was created
- **UPDATED_BY_USER**: User who last updated the record
- **UPDATED_DATE**: Timestamp when record was last updated

## Installation

### New Table Creation

1. Connect to your Oracle database as a user with CREATE TABLE privileges
2. Run the SQL script:
   ```sql
   @create_ach_files_blobs.sql
   ```
   Or copy and paste the contents into your SQL client

### Adding FILE_ID to Existing Table

If the table already exists without the FILE_ID column, use the ALTER script:

1. Connect to your Oracle database
2. Run the ALTER script:
   ```sql
   @alter_ach_files_blobs_add_file_id.sql
   ```
   **Note**: You may need to manually update existing rows with appropriate FILE_ID values before making the column NOT NULL.

## Verification

After creating the table, verify it was created correctly:

```sql
-- Check table exists
SELECT table_name, num_rows 
FROM user_tables 
WHERE table_name = 'ACH_FILES_BLOBS';

-- Check table structure
SELECT column_name, data_type, data_length, nullable, data_default
FROM user_tab_columns
WHERE table_name = 'ACH_FILES_BLOBS'
ORDER BY column_id;

-- Check indexes
SELECT index_name, index_type, uniqueness
FROM user_indexes
WHERE table_name = 'ACH_FILES_BLOBS';

-- Check foreign key constraint
SELECT constraint_name, constraint_type, r_constraint_name
FROM user_constraints
WHERE table_name = 'ACH_FILES_BLOBS'
AND constraint_name = 'FK_ACH_FILES_BLOBS_FILE_ID';
```

## Related Tables

- **ACH_FILES**: Stores file metadata (linked by FILE_ID foreign key with CASCADE delete)
- **ACH_FILE_LINES**: Stores individual lines from ACH files (linked by FILE_ID to ACH_FILES)

## Usage

The table is used by the FastAPI endpoint `POST /files/process-sftp-file` which:
1. Creates an `ACH_FILES` record
2. Creates an `ACH_FILES_BLOBS` record with the file contents
3. Updates the status to "Completed" on success

## Notes

- The table uses CLOB (Character Large Object) for file contents, suitable for text-based ACH files
- The table includes indexes on `FILE_ID`, `ORIGINAL_FILENAME`, `PROCESSING_STATUS`, and `CREATED_DATE` for performance
- The primary key uses Oracle's IDENTITY column feature for auto-incrementing
- The `FILE_ID` foreign key has `ON DELETE CASCADE`, so deleting an `ACH_FILES` record will automatically delete the corresponding `ACH_FILES_BLOBS` record

