-- ============================================================================
-- ALTER TABLE: Add Task-000013 fields to AUDIT_ACH_FILES table
-- ============================================================================
-- This script adds the following fields to AUDIT_ACH_FILES:
--   - CLIENT_ID (from ACH_CLIENTS)
--   - CLIENT_NAME (from ACH_CLIENTS)
--   - FILE_UPLOAD_FOLDER VARCHAR2(255)
--   - FILE_UPLOAD_FILENAME VARCHAR2(255)
--   - MEMO VARCHAR2(512)
--
-- Created: 2025-12-02
-- Task: Task-000013-Add-to-ACH-FILES
-- ============================================================================

-- Step 1: Add CLIENT_ID column
ALTER TABLE AUDIT_ACH_FILES 
ADD CLIENT_ID VARCHAR2(50);

-- Step 2: Add CLIENT_NAME column
ALTER TABLE AUDIT_ACH_FILES 
ADD CLIENT_NAME VARCHAR2(255);

-- Step 3: Add FILE_UPLOAD_FOLDER column
ALTER TABLE AUDIT_ACH_FILES 
ADD FILE_UPLOAD_FOLDER VARCHAR2(255);

-- Step 4: Add FILE_UPLOAD_FILENAME column
ALTER TABLE AUDIT_ACH_FILES 
ADD FILE_UPLOAD_FILENAME VARCHAR2(255);

-- Step 5: Add MEMO column
ALTER TABLE AUDIT_ACH_FILES 
ADD MEMO VARCHAR2(512);

-- Step 6: Add comments for documentation
COMMENT ON COLUMN AUDIT_ACH_FILES.CLIENT_ID IS 'Client ID from ACH_CLIENTS table';
COMMENT ON COLUMN AUDIT_ACH_FILES.CLIENT_NAME IS 'Client name from ACH_CLIENTS table';
COMMENT ON COLUMN AUDIT_ACH_FILES.FILE_UPLOAD_FOLDER IS 'Folder path where file was uploaded from SFTP';
COMMENT ON COLUMN AUDIT_ACH_FILES.FILE_UPLOAD_FILENAME IS 'Original filename from SFTP upload folder';
COMMENT ON COLUMN AUDIT_ACH_FILES.MEMO IS 'Memo field for additional notes';

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- Uncomment to verify the changes:
--
-- SELECT column_name, data_type, data_length, nullable
-- FROM user_tab_columns
-- WHERE table_name = 'AUDIT_ACH_FILES'
-- AND column_name IN ('CLIENT_ID', 'CLIENT_NAME', 'FILE_UPLOAD_FOLDER', 'FILE_UPLOAD_FILENAME', 'MEMO')
-- ORDER BY column_name;

COMMIT;

