# Plan: Complete List of Oracle Tables Used in OBS SFTP File Processor

## Overview

This document provides a comprehensive list of all Oracle database tables used in the OBS SFTP File Processor application. Tables are organized by category and include their purpose, key relationships, and usage context.

## Table Categories

### 1. Core ACH File Tables

#### ACH_FILES
- **Purpose**: Primary table storing ACH file metadata and file contents
- **Primary Key**: `FILE_ID` (auto-generated)
- **Key Columns**:
  - `FILE_ID` - Primary key
  - `ORIGINAL_FILENAME` - Original filename from SFTP
  - `PROCESSING_STATUS` - Status (Pending, Approved, Completed, Failed)
  - `FILE_CONTENTS` - File contents as CLOB
  - `CLIENT_ID` - Foreign key to ACH_CLIENTS
  - `CLIENT_NAME` - Client name
  - `FILE_UPLOAD_FOLDER` - SFTP upload folder path
  - `FILE_UPLOAD_FILENAME` - Original filename from SFTP
  - `MEMO` - Memo field for additional notes
  - `CREATED_BY_USER` - User who created the record
  - `CREATED_DATE` - Creation timestamp
  - `UPDATED_BY_USER` - User who last updated
  - `UPDATED_DATE` - Last update timestamp
- **Used By**:
  - `OracleService.create_ach_file()`
  - `OracleService.get_ach_file()`
  - `OracleService.get_ach_files()`
  - `OracleService.update_ach_file()`
  - `OracleService.update_ach_file_by_file_id()`
  - `OracleService.delete_ach_file()`
  - `OracleService.get_ach_files_count()`
  - Main endpoint: `/oracle/ach-files`
- **Relationships**:
  - Referenced by: `ACH_FILES_BLOBS`, `AUDIT_ACH_FILES`, `ACH_FILE_HEADER`, `ACH_BATCH_HEADER`, `ACH_ENTRY_DETAIL`, `ACH_ADDENDA`, `ACH_BATCH_CONTROL`, `ACH_FILE_CONTROL`
  - References: `ACH_CLIENTS` (via CLIENT_ID)

#### ACH_FILES_BLOBS
- **Purpose**: Stores file contents as BLOB/CLOB for ACH files (mirrors ACH_FILES structure)
- **Primary Key**: `FILE_BLOB_ID` (auto-generated)
- **Key Columns**:
  - `FILE_BLOB_ID` - Primary key
  - `FILE_ID` - Foreign key to ACH_FILES (NOT NULL, CASCADE delete)
  - `ORIGINAL_FILENAME` - Filename
  - `PROCESSING_STATUS` - Processing status
  - `FILE_CONTENTS` - File contents as CLOB
  - `CLIENT_ID` - Client ID
  - `CLIENT_NAME` - Client name
  - `FILE_UPLOAD_FOLDER` - Upload folder path
  - `FILE_UPLOAD_FILENAME` - Upload filename
  - `MEMO` - Memo field
  - `CREATED_BY_USER` - Creator
  - `CREATED_DATE` - Creation timestamp
  - `UPDATED_BY_USER` - Last updater
  - `UPDATED_DATE` - Update timestamp
- **Used By**:
  - `AchFileBlobsService.create_ach_file_blob()`
  - `AchFileBlobsService.get_ach_file_blob()`
  - `AchFileBlobsService.get_ach_file_blob_by_file_id()`
  - `AchFileBlobsService.update_ach_file_blob_status()`
  - Main endpoint: `/oracle/ach-files-blobs`
- **Relationships**:
  - Foreign key to `ACH_FILES.FILE_ID` (ON DELETE CASCADE)

#### AUDIT_ACH_FILES
- **Purpose**: Audit trail table that automatically stores all changes to ACH_FILES
- **Primary Key**: `AUDIT_ID` (auto-generated)
- **Key Columns**:
  - `AUDIT_ID` - Primary key
  - `FILE_ID` - Reference to ACH_FILES.FILE_ID (not a foreign key)
  - All columns from ACH_FILES (mirrors structure)
- **Used By**:
  - `OracleService.get_audit_ach_files_by_file_id()`
  - Trigger: `TRG_ACH_FILES_AUDIT` (fires on INSERT/UPDATE of ACH_FILES)
- **Relationships**:
  - Populated automatically by trigger on ACH_FILES changes

### 2. ACH Record Type Tables (Task-000015)

These tables store parsed ACH file records based on NACHA record types:

#### ACH_FILE_HEADER
- **Purpose**: Stores File Header Records (Record Type Code: 1)
- **Primary Key**: `FILE_HEADER_ID` (from sequence SEQ_FILE_HEADER)
- **Key Columns**:
  - `FILE_HEADER_ID` - Primary key
  - `FILE_ID` - Foreign key to ACH_FILES (NOT NULL, CASCADE delete)
  - `RECORD_TYPE_CODE` - Always '1'
  - `PRIORITY_CODE` - Priority code
  - `IMMEDIATE_DESTINATION` - Destination routing number
  - `IMMEDIATE_ORIGIN` - Origin routing number
  - `FILE_CREATION_DATE` - File creation date
  - `FILE_CREATION_TIME` - File creation time
  - `IMMEDIATE_DEST_NAME` - Destination name
  - `IMMEDIATE_ORIGIN_NAME` - Origin name
  - `REFERENCE_CODE` - Reference code
  - `RAW_RECORD` - Full 94-character raw record
  - `CREATED_DATE` - Creation timestamp
- **Used By**:
  - `OracleService.insert_ach_file_header()`
  - `OracleService.parse_and_insert_ach_records()`
  - Endpoint: `/oracle/ach-files-update-by-file-id/{file_id}` (parsing process)
- **Relationships**:
  - Foreign key to `ACH_FILES.FILE_ID` (ON DELETE CASCADE)

#### ACH_BATCH_HEADER
- **Purpose**: Stores Batch Header Records (Record Type Code: 5)
- **Primary Key**: `BATCH_HEADER_ID` (from sequence SEQ_BATCH_HEADER)
- **Key Columns**:
  - `BATCH_HEADER_ID` - Primary key
  - `FILE_ID` - Foreign key to ACH_FILES (NOT NULL, CASCADE delete)
  - `BATCH_NUMBER` - Batch number (NOT NULL)
  - `RECORD_TYPE_CODE` - Always '5'
  - `SERVICE_CLASS_CODE` - Service class code
  - `COMPANY_NAME` - Company name
  - `COMPANY_IDENTIFICATION` - Company ID
  - `STANDARD_ENTRY_CLASS_CODE` - Standard entry class (PPD, CCD, etc.)
  - `COMPANY_ENTRY_DESCRIPTION` - Entry description
  - `EFFECTIVE_ENTRY_DATE` - Effective entry date
  - `ORIGINATING_DFI_ID` - Originating DFI ID
  - `RAW_RECORD` - Full 94-character raw record
  - `CREATED_DATE` - Creation timestamp
- **Used By**:
  - `OracleService.insert_ach_batch_header()`
  - `OracleService.parse_and_insert_ach_records()`
  - `OracleService.get_ach_data_for_core_post_sp_approved()` (JOIN for batch data)
  - Endpoint: `/oracle/ach-files-update-by-file-id/{file_id}` (parsing process)
  - Endpoint: `/api/oracle/get-ach-data-for-core-post-sp-approved` (query JOIN)
- **Relationships**:
  - Foreign key to `ACH_FILES.FILE_ID` (ON DELETE CASCADE)
  - Referenced by: `ACH_ENTRY_DETAIL`, `ACH_ADDENDA`, `ACH_BATCH_CONTROL` (via BATCH_NUMBER)

#### ACH_ENTRY_DETAIL
- **Purpose**: Stores Entry Detail Records (Record Type Code: 6) - Individual payment transactions
- **Primary Key**: `ENTRY_DETAIL_ID` (from sequence SEQ_ENTRY_DETAIL)
- **Key Columns**:
  - `ENTRY_DETAIL_ID` - Primary key
  - `FILE_ID` - Foreign key to ACH_FILES (NOT NULL, CASCADE delete)
  - `BATCH_NUMBER` - Batch number (NOT NULL)
  - `RECORD_TYPE_CODE` - Always '6'
  - `TRANSACTION_CODE` - Transaction code (22=Credit, 27=Debit, etc.)
  - `RECEIVING_DFI_ID` - Receiving DFI ID
  - `CHECK_DIGIT` - Check digit
  - `DFI_ACCOUNT_NUMBER` - DFI account number
  - `AMOUNT` - Amount in cents (NUMBER)
  - `AMOUNT_DECIMAL` - Amount as decimal (NUMBER(12,2))
  - `INDIVIDUAL_ID_NUMBER` - Individual ID number
  - `INDIVIDUAL_NAME` - Individual name
  - `ADDENDA_RECORD_INDICATOR` - Addenda indicator (0 or 1)
  - `TRACE_NUMBER` - Trace number
  - `TRACE_SEQUENCE_NUMBER` - Trace sequence number
  - `RAW_RECORD` - Full 94-character raw record
  - `CREATED_DATE` - Creation timestamp
- **Used By**:
  - `OracleService.insert_ach_entry_detail()`
  - `OracleService.parse_and_insert_ach_records()`
  - `OracleService.get_ach_data_for_core_post_sp_approved()` (main table in query)
  - Endpoint: `/oracle/ach-files-update-by-file-id/{file_id}` (parsing process)
  - Endpoint: `/api/oracle/get-ach-data-for-core-post-sp-approved` (primary table)
- **Relationships**:
  - Foreign key to `ACH_FILES.FILE_ID` (ON DELETE CASCADE)
  - Referenced by: `ACH_ADDENDA` (via ENTRY_DETAIL_ID)

#### ACH_ADDENDA
- **Purpose**: Stores Addenda Records (Record Type Code: 7) - Additional payment information
- **Primary Key**: `ADDENDA_ID` (from sequence SEQ_ADDENDA)
- **Key Columns**:
  - `ADDENDA_ID` - Primary key
  - `FILE_ID` - Foreign key to ACH_FILES (NOT NULL, CASCADE delete)
  - `ENTRY_DETAIL_ID` - Foreign key to ACH_ENTRY_DETAIL (optional, CASCADE delete)
  - `BATCH_NUMBER` - Batch number (NOT NULL)
  - `RECORD_TYPE_CODE` - Always '7'
  - `ADDENDA_TYPE_CODE` - Addenda type code
  - `PAYMENT_RELATED_INFO` - Payment related information
  - `ADDENDA_SEQUENCE_NUMBER` - Addenda sequence number
  - `ENTRY_DETAIL_SEQUENCE_NUM` - Entry detail sequence number
  - `RAW_RECORD` - Full 94-character raw record
  - `CREATED_DATE` - Creation timestamp
- **Used By**:
  - `OracleService.insert_ach_addenda()`
  - `OracleService.parse_and_insert_ach_records()`
  - Endpoint: `/oracle/ach-files-update-by-file-id/{file_id}` (parsing process)
- **Relationships**:
  - Foreign key to `ACH_FILES.FILE_ID` (ON DELETE CASCADE)
  - Foreign key to `ACH_ENTRY_DETAIL.ENTRY_DETAIL_ID` (ON DELETE CASCADE, optional)

#### ACH_BATCH_CONTROL
- **Purpose**: Stores Batch Control Records (Record Type Code: 8) - Batch summary information
- **Primary Key**: `BATCH_CONTROL_ID` (from sequence SEQ_BATCH_CONTROL)
- **Key Columns**:
  - `BATCH_CONTROL_ID` - Primary key
  - `FILE_ID` - Foreign key to ACH_FILES (NOT NULL, CASCADE delete)
  - `BATCH_NUMBER` - Batch number (NOT NULL)
  - `RECORD_TYPE_CODE` - Always '8'
  - `SERVICE_CLASS_CODE` - Service class code
  - `ENTRY_ADDENDA_COUNT` - Entry/addenda count
  - `TOTAL_DEBIT_AMOUNT` - Total debit amount in cents
  - `TOTAL_DEBIT_AMOUNT_DECIMAL` - Total debit amount as decimal
  - `TOTAL_CREDIT_AMOUNT` - Total credit amount in cents
  - `TOTAL_CREDIT_AMOUNT_DECIMAL` - Total credit amount as decimal
  - `COMPANY_IDENTIFICATION` - Company identification
  - `ORIGINATING_DFI_ID` - Originating DFI ID
  - `RAW_RECORD` - Full 94-character raw record
  - `CREATED_DATE` - Creation timestamp
- **Used By**:
  - `OracleService.insert_ach_batch_control()`
  - `OracleService.parse_and_insert_ach_records()`
  - Endpoint: `/oracle/ach-files-update-by-file-id/{file_id}` (parsing process)
- **Relationships**:
  - Foreign key to `ACH_FILES.FILE_ID` (ON DELETE CASCADE)

#### ACH_FILE_CONTROL
- **Purpose**: Stores File Control Records (Record Type Code: 9) - File summary information
- **Primary Key**: `FILE_CONTROL_ID` (from sequence SEQ_FILE_CONTROL)
- **Key Columns**:
  - `FILE_CONTROL_ID` - Primary key
  - `FILE_ID` - Foreign key to ACH_FILES (NOT NULL, CASCADE delete)
  - `RECORD_TYPE_CODE` - Always '9'
  - `BATCH_COUNT` - Batch count
  - `BLOCK_COUNT` - Block count
  - `ENTRY_ADDENDA_COUNT` - Entry/addenda count
  - `TOTAL_DEBIT_AMOUNT` - Total debit amount in cents
  - `TOTAL_DEBIT_AMOUNT_DECIMAL` - Total debit amount as decimal
  - `TOTAL_CREDIT_AMOUNT` - Total credit amount in cents
  - `TOTAL_CREDIT_AMOUNT_DECIMAL` - Total credit amount as decimal
  - `RAW_RECORD` - Full 94-character raw record
  - `CREATED_DATE` - Creation timestamp
- **Used By**:
  - `OracleService.insert_ach_file_control()`
  - `OracleService.parse_and_insert_ach_records()`
  - `OracleService.get_ach_data_for_core_post_sp_approved()` (JOIN for reference code)
  - Endpoint: `/oracle/ach-files-update-by-file-id/{file_id}` (parsing process)
  - Endpoint: `/api/oracle/get-ach-data-for-core-post-sp-approved` (query JOIN)
- **Relationships**:
  - Foreign key to `ACH_FILES.FILE_ID` (ON DELETE CASCADE)

### 3. ACH File Lines Table

#### ACH_FILE_LINES
- **Purpose**: Stores individual lines from ACH files (line-by-line storage)
- **Primary Key**: `LINE_ID` (auto-generated)
- **Key Columns**:
  - `LINE_ID` - Primary key
  - `FILE_ID` - Foreign key to ACH_FILES
  - `LINE_NUMBER` - Line number in file
  - `LINE_CONTENT` - Line content (94 characters)
  - `RECORD_TYPE` - Record type code (1, 5, 6, 7, 8, 9)
  - `IS_VALID` - Validation status
  - `VALIDATION_ERRORS` - Validation error messages
  - `CREATED_DATE` - Creation timestamp
- **Used By**:
  - `AchFileLinesService.create_ach_file_line()`
  - `AchFileLinesService.create_ach_file_lines_batch()`
  - `AchFileLinesService.get_ach_file_lines()`
  - `AchFileLinesService.delete_lines_by_file_id()`
  - Endpoint: `/oracle/ach-file-lines`
- **Relationships**:
  - Foreign key to `ACH_FILES.FILE_ID`

### 4. Client Management Tables

#### ACH_CLIENTS
- **Purpose**: Stores client/company information
- **Primary Key**: `CLIENT_ID`
- **Key Columns**:
  - `CLIENT_ID` - Primary key (VARCHAR2)
  - `CLIENT_NAME` - Client name
  - `CLIENT_STATUS` - Status (Active, Inactive)
  - Additional client information columns
- **Used By**:
  - `OracleService.get_active_clients()`
  - Referenced by `ACH_FILES.CLIENT_ID`
  - Endpoint: `/oracle/ach-clients`
- **Relationships**:
  - Referenced by: `ACH_FILES` (via CLIENT_ID)

### 5. Authentication Tables

#### API_USERS
- **Purpose**: Stores API user accounts for JWT authentication
- **Primary Key**: `USER_ID` (auto-generated)
- **Key Columns**:
  - `USER_ID` - Primary key
  - `USERNAME` - Unique username
  - `PASSWORD_HASH` - Bcrypt hashed password
  - `EMAIL` - User email
  - `FULL_NAME` - User full name
  - `IS_ACTIVE` - Active status (1=active, 0=inactive)
  - `IS_ADMIN` - Admin flag (1=admin, 0=user)
  - `CREATED_DATE` - Account creation timestamp
  - `LAST_LOGIN` - Last login timestamp
  - `FAILED_LOGIN_ATTEMPTS` - Failed login counter
  - `LOCKED_UNTIL` - Account lock expiration
- **Used By**:
  - `OracleService.check_email_and_password_hash()`
  - Endpoint: `/oracle/auth/check-email-password-hash`
- **Relationships**:
  - Referenced by: `API_USER_ROLES` (via USER_ID)

#### API_USER_ROLES
- **Purpose**: Stores user roles for role-based access control
- **Primary Key**: `USER_ROLE_ID` (auto-generated)
- **Key Columns**:
  - `USER_ROLE_ID` - Primary key
  - `USER_ID` - Foreign key to API_USERS (NOT NULL, CASCADE delete)
  - `ROLE_NAME` - Role name (ADMIN, USER, etc.)
  - `CREATED_DATE` - Role assignment timestamp
- **Used By**:
  - Role-based access control (future implementation)
- **Relationships**:
  - Foreign key to `API_USERS.USER_ID` (ON DELETE CASCADE)

## Sequences

The following sequences are used for primary key generation:

1. **SEQ_FILE_HEADER** - For `ACH_FILE_HEADER.FILE_HEADER_ID`
2. **SEQ_BATCH_HEADER** - For `ACH_BATCH_HEADER.BATCH_HEADER_ID`
3. **SEQ_ENTRY_DETAIL** - For `ACH_ENTRY_DETAIL.ENTRY_DETAIL_ID`
4. **SEQ_ADDENDA** - For `ACH_ADDENDA.ADDENDA_ID`
5. **SEQ_BATCH_CONTROL** - For `ACH_BATCH_CONTROL.BATCH_CONTROL_ID`
6. **SEQ_FILE_CONTROL** - For `ACH_FILE_CONTROL.FILE_CONTROL_ID`

## Table Relationships Diagram

```
ACH_FILES (Primary)
    ├── ACH_FILES_BLOBS (1:1 via FILE_ID)
    ├── AUDIT_ACH_FILES (1:many via FILE_ID, trigger-based)
    ├── ACH_FILE_HEADER (1:1 via FILE_ID)
    ├── ACH_BATCH_HEADER (1:many via FILE_ID + BATCH_NUMBER)
    │   ├── ACH_ENTRY_DETAIL (1:many via FILE_ID + BATCH_NUMBER)
    │   │   └── ACH_ADDENDA (1:many via ENTRY_DETAIL_ID)
    │   └── ACH_BATCH_CONTROL (1:1 via FILE_ID + BATCH_NUMBER)
    ├── ACH_FILE_CONTROL (1:1 via FILE_ID)
    └── ACH_FILE_LINES (1:many via FILE_ID)
    
ACH_CLIENTS
    └── ACH_FILES (1:many via CLIENT_ID)

API_USERS
    └── API_USER_ROLES (1:many via USER_ID)
```

## Table Usage Summary

### Tables with High Usage (Core Functionality)
1. **ACH_FILES** - Primary table, used in all major operations
2. **ACH_ENTRY_DETAIL** - Core payment transaction data
3. **ACH_BATCH_HEADER** - Batch-level information
4. **ACH_FILES_BLOBS** - File content storage

### Tables with Medium Usage
5. **ACH_FILE_HEADER** - File-level metadata
6. **ACH_BATCH_CONTROL** - Batch summaries
7. **ACH_FILE_CONTROL** - File summaries
8. **ACH_CLIENTS** - Client lookups

### Tables with Low/Specialized Usage
9. **ACH_ADDENDA** - Additional payment information
10. **ACH_FILE_LINES** - Line-by-line storage (legacy/alternative)
11. **AUDIT_ACH_FILES** - Audit trail (automatic)
12. **API_USERS** - Authentication
13. **API_USER_ROLES** - Role management

## Indexes

All tables have appropriate indexes for performance:
- Primary key indexes (automatic)
- Foreign key indexes (on FILE_ID, USER_ID, etc.)
- Composite indexes (on FILE_ID + BATCH_NUMBER)
- Lookup indexes (on CLIENT_ID, USERNAME, EMAIL, etc.)

## Notes

1. **CASCADE DELETE**: Most child tables use ON DELETE CASCADE, so deleting an ACH_FILES record will automatically delete related records in child tables.

2. **CLOB Storage**: Both `ACH_FILES.FILE_CONTENTS` and `ACH_FILES_BLOBS.FILE_CONTENTS` use CLOB data type for large file storage. The application uses DBMS_LOB for efficient large file operations.

3. **Audit Trail**: `AUDIT_ACH_FILES` is automatically populated via trigger `TRG_ACH_FILES_AUDIT` whenever ACH_FILES is inserted or updated.

4. **Record Type Tables**: The six ACH record type tables (FILE_HEADER, BATCH_HEADER, ENTRY_DETAIL, ADDENDA, BATCH_CONTROL, FILE_CONTROL) are populated automatically when `/oracle/ach-files-update-by-file-id/{file_id}` is called.

5. **Sequences**: All ACH record type tables use sequences for primary key generation, ensuring unique IDs across all records.

