-- ============================================================================
-- ALTER TABLE: Add FILE_ID Column and Foreign Key to ACH_FILES_BLOBS
-- ============================================================================
-- Use this script if the ACH_FILES_BLOBS table already exists and you need
-- to add the FILE_ID column and foreign key constraint.
--
-- Created: 2025-11-09
-- ============================================================================

-- Step 1: Add FILE_ID column (nullable first to allow existing rows)
ALTER TABLE "ACH_FILES_BLOBS" 
ADD "FILE_ID" NUMBER(38,0);

-- Step 2: Update existing rows with a default FILE_ID if needed
-- NOTE: You may need to manually update existing rows with appropriate FILE_ID values
-- based on matching ORIGINAL_FILENAME with ACH_FILES.ORIGINAL_FILENAME
-- Example:
-- UPDATE ACH_FILES_BLOBS blobs
-- SET FILE_ID = (
--     SELECT FILE_ID 
--     FROM ACH_FILES files 
--     WHERE files.ORIGINAL_FILENAME = blobs.ORIGINAL_FILENAME
--     AND ROWNUM = 1
-- )
-- WHERE FILE_ID IS NULL;

-- Step 3: Make FILE_ID NOT NULL (only after all rows have been updated)
ALTER TABLE "ACH_FILES_BLOBS" 
MODIFY "FILE_ID" NUMBER(38,0) NOT NULL;

-- Step 4: Create index on FILE_ID for performance
CREATE INDEX "IDX_ACH_FILES_BLOBS_FILE_ID" 
ON "ACH_FILES_BLOBS" ("FILE_ID");

-- Step 5: Add foreign key constraint
ALTER TABLE "ACH_FILES_BLOBS" 
ADD CONSTRAINT "FK_ACH_FILES_BLOBS_FILE_ID" 
FOREIGN KEY ("FILE_ID") 
REFERENCES "ACH_FILES" ("FILE_ID") 
ON DELETE CASCADE 
ENABLE;

-- Step 6: Add comment to FILE_ID column
COMMENT ON COLUMN "ACH_FILES_BLOBS"."FILE_ID" IS 'Foreign key to ACH_FILES.FILE_ID';

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- Uncomment and run these queries to verify the changes:
--
-- SELECT column_name, data_type, nullable
-- FROM user_tab_columns
-- WHERE table_name = 'ACH_FILES_BLOBS'
-- AND column_name = 'FILE_ID';
--
-- SELECT constraint_name, constraint_type, r_constraint_name
-- FROM user_constraints
-- WHERE table_name = 'ACH_FILES_BLOBS'
-- AND constraint_name = 'FK_ACH_FILES_BLOBS_FILE_ID';
--
-- SELECT index_name, index_type
-- FROM user_indexes
-- WHERE table_name = 'ACH_FILES_BLOBS'
-- AND index_name = 'IDX_ACH_FILES_BLOBS_FILE_ID';

