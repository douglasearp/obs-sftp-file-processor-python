-- ============================================================================
-- UPDATE TRIGGER: TRG_ACH_FILES_AUDIT to include Task-000013 fields
-- ============================================================================
-- This script updates the TRG_ACH_FILES_AUDIT trigger to include the new fields:
--   - CLIENT_ID
--   - CLIENT_NAME
--   - FILE_UPLOAD_FOLDER
--   - FILE_UPLOAD_FILENAME
--   - MEMO
--
-- Created: 2025-12-02
-- Task: Task-000013-Add-to-ACH-FILES
-- ============================================================================

CREATE OR REPLACE TRIGGER TRG_ACH_FILES_AUDIT
AFTER INSERT OR UPDATE ON ACH_FILES
FOR EACH ROW
BEGIN
    INSERT INTO AUDIT_ACH_FILES (
        FILE_ID,
        ORIGINAL_FILENAME,
        PROCESSING_STATUS,
        FILE_CONTENTS,
        CREATED_BY_USER,
        CREATED_DATE,
        UPDATED_BY_USER,
        UPDATED_DATE,
        CLIENT_ID,
        CLIENT_NAME,
        FILE_UPLOAD_FOLDER,
        FILE_UPLOAD_FILENAME,
        MEMO
    )
    VALUES (
        :NEW.FILE_ID,
        :NEW.ORIGINAL_FILENAME,
        :NEW.PROCESSING_STATUS,
        :NEW.FILE_CONTENTS,
        :NEW.CREATED_BY_USER,
        :NEW.CREATED_DATE,
        :NEW.UPDATED_BY_USER,
        :NEW.UPDATED_DATE,
        :NEW.CLIENT_ID,
        :NEW.CLIENT_NAME,
        :NEW.FILE_UPLOAD_FOLDER,
        :NEW.FILE_UPLOAD_FILENAME,
        :NEW.MEMO
    );
END;
/

-- ============================================================================
-- Verification
-- ============================================================================
-- Verify trigger was updated:
-- SELECT trigger_name, trigger_type, triggering_event, status
-- FROM user_triggers
-- WHERE trigger_name = 'TRG_ACH_FILES_AUDIT';

COMMIT;

