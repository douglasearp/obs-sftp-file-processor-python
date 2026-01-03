# Plan: SWAPS Implementation Status

## Overview

This document outlines the current status of SWAPS functionality and what needs to be implemented.

## Current Status

**❌ NO SWAPS LOGIC EXISTS YET**

- Task file exists: `Tasks/Tasks-000017-SWAPS`
- Table exists in Oracle: `ACH_ACCOUNT_NUMBER_SWAPS`
- **No implementation found:**
  - ❌ No Pydantic models
  - ❌ No service methods
  - ❌ No API endpoints
  - ❌ No integration with existing code

## Table Structure

The `ACH_ACCOUNT_NUMBER_SWAPS` table is already created in Oracle with the following structure:

| Column Name | Null? | Type | Description |
|------------|-------|------|-------------|
| `SWAP_ID` | NOT NULL | NUMBER(38) | Primary key (auto-generated) |
| `ORIGINAL_DFI_ACCOUNT_NUMBER` | NULL | VARCHAR2(17) | Original DFI account number |
| `SWAP_ACCOUNT_NUMBER` | NULL | VARCHAR2(17) | Swapped/replacement account number |
| `SWAP_MEMO` | NOT NULL | VARCHAR2(255) | Memo/description for the swap |

## Required Implementation

### 1. Pydantic Models
**File**: `src/obs_sftp_file_processor/ach_account_swaps_models.py`

Models needed:
- `AchAccountSwapBase` - Base model with common fields
- `AchAccountSwapCreate` - Model for creating records
- `AchAccountSwapUpdate` - Model for updating records
- `AchAccountSwap` - Complete model with all fields
- `AchAccountSwapResponse` - Response model for API
- `AchAccountSwapListResponse` - Response model for list endpoints

**Fields**:
- `swap_id: int` - Primary key
- `original_dfi_account_number: Optional[str]` - Original account number
- `swap_account_number: Optional[str]` - Swapped account number
- `swap_memo: str` - Memo (required)

### 2. Service Methods
**File**: `src/obs_sftp_file_processor/oracle_service.py`

CRUD operations needed:
- `create_ach_account_swap()` - INSERT operation
- `get_ach_account_swap()` - SELECT by SWAP_ID
- `get_ach_account_swaps()` - SELECT list with filtering
- `get_ach_account_swaps_count()` - COUNT with filtering
- `update_ach_account_swap()` - UPDATE operation
- `delete_ach_account_swap()` - DELETE operation

**Filtering options**:
- By `ORIGINAL_DFI_ACCOUNT_NUMBER`
- By `SWAP_ACCOUNT_NUMBER`
- Pagination (limit/offset)

### 3. API Endpoints
**File**: `src/obs_sftp_file_processor/main.py`

Endpoints needed:
- `GET /oracle/ach-account-swaps` - List swaps (with pagination and filters)
- `GET /oracle/ach-account-swaps/{swap_id}` - Get specific swap
- `POST /oracle/ach-account-swaps` - Create new swap
- `PUT /oracle/ach-account-swaps/{swap_id}` - Update swap
- `DELETE /oracle/ach-account-swaps/{swap_id}` - Delete swap

**Query Parameters for GET list**:
- `limit` - Maximum records (default: 100)
- `offset` - Skip records (default: 0)
- `original_dfi_account_number` - Filter by original account
- `swap_account_number` - Filter by swap account

## Implementation Pattern

Follow the same pattern as `FI_HOLIDAYS` implementation:
1. Create models file (similar to `fi_holidays_models.py`)
2. Add service methods to `OracleService` class
3. Add API endpoints to `main.py`
4. Use schema prefix: `{self.config.db_schema}.ACH_ACCOUNT_NUMBER_SWAPS`
5. Include proper error handling and logging

## Use Case

SWAPS appear to be used for mapping/replacing account numbers in ACH processing:
- **Original Account**: The account number that appears in ACH files
- **Swap Account**: The replacement account number to use instead
- **Memo**: Description/reason for the swap

This could be used during ACH processing to:
- Replace account numbers before processing
- Handle account number corrections
- Map old accounts to new accounts

## Integration Points

Potential integration with:
- `ACH_ENTRY_DETAIL` table - When processing entry details, check if account number needs to be swapped
- ACH file processing - Apply swaps during file parsing/processing
- Core Post SP endpoint - Apply swaps before calling stored procedure

## Next Steps

1. **Create Models** - Implement Pydantic models
2. **Create Service Methods** - Implement CRUD operations in OracleService
3. **Create API Endpoints** - Implement REST API endpoints
4. **Test Implementation** - Verify all CRUD operations work
5. **Documentation** - Update API documentation
6. **Integration** - Consider where swaps should be applied in processing flow

## Notes

- Table name: `ACH_ACCOUNT_NUMBER_SWAPS` (note the plural "SWAPS")
- Primary key: `SWAP_ID` (likely auto-generated via sequence)
- `SWAP_MEMO` is NOT NULL, so must always be provided
- Both account number fields are nullable (VARCHAR2(17))
- No timestamps or user tracking fields in the table structure provided

