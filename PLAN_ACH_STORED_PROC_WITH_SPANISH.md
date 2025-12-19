# Plan: ACH Stored Procedure Query with Spanish Aliases

## Overview

This document outlines the plan for creating an Oracle SQL query that extracts data from ACH record type tables to populate parameters for the stored procedure `BE_K_INTERFAZ_ACH.BE_P_PROCESA_PAGO`.

The stored procedure processes ACH payment records (Record Type 6 - Entry Detail Records) and requires data from multiple ACH record type tables.

## Stored Procedure Parameters Mapping

### Parameter to ACH Table Field Mapping

| Stored Procedure Parameter | Spanish Name | English Field Source | Table | Field | Notes |
|---------------------------|--------------|---------------------|-------|-------|-------|
| `GN_SECUENCIACONVENIO` | Secuencia Convenio | Trace Sequence Number | `ACH_ENTRY_DETAIL` | `TRACE_SEQUENCE_NUMBER` | Extract from TRACE_NUMBER (last 7 digits) or use TRACE_SEQUENCE_NUMBER if available |
| `GN_CODIGOCLIENTE` | Código Cliente | Client ID | `ACH_FILES` | `CLIENT_ID` | Direct mapping from ACH_FILES table |
| `GN_AGENCIACTAORIGEN` | Agencia Cuenta Origen | Origin Agency | `ACH_BATCH_HEADER` | `ORIGINATING_DFI_ID` | First 3 digits of ORIGINATING_DFI_ID (routing number prefix) |
| `GN_SUBCTAORIGEN` | Subcuenta Origen | Origin Sub-account | `ACH_ENTRY_DETAIL` | `DFI_ACCOUNT_NUMBER` | Parse from account number or default to 0 |
| `GV_APLCTAORIGEN` | Aplicación Cuenta Origen | ACH Class | `ACH_BATCH_HEADER` | `STANDARD_ENTRY_CLASS_CODE` | Direct mapping (e.g., 'PPD', 'CCD', 'TEL') |
| `GN_CTAORIGEN` | Cuenta Origen | Origin Account | `ACH_ENTRY_DETAIL` | `DFI_ACCOUNT_NUMBER` | Direct mapping |
| `GN_EMPCTAORIGEN` | Empresa Cuenta Origen | Company ID | `ACH_BATCH_HEADER` | `COMPANY_IDENTIFICATION` | Direct mapping |
| `GN_ABABCORECIBIDOR` | ABA Banco Receptor | Receiver Routing (ABA) | `ACH_ENTRY_DETAIL` | `RECEIVING_DFI_ID` | Combine RECEIVING_DFI_ID + CHECK_DIGIT (8 digits total) |
| `GV_CTABCORECIBIDOR` | Cuenta Banco Receptor | Receiver Account | `ACH_ENTRY_DETAIL` | `DFI_ACCOUNT_NUMBER` | Direct mapping |
| `GN_PRODBCORECIBIDOR` | Producto Banco Receptor | Transaction Code | `ACH_ENTRY_DETAIL` | `TRANSACTION_CODE` | Direct mapping (e.g., '22' for Checking) |
| `GV_CUENTAINSTITUCION` | Cuenta Institución | Company Name | `ACH_BATCH_HEADER` | `COMPANY_NAME` | Direct mapping |
| `GV_IDRECIBIDOR` | ID Receptor | Receiver ID | `ACH_ENTRY_DETAIL` | `INDIVIDUAL_ID_NUMBER` | Direct mapping |
| `GV_NOMBRERECIBIDOR` | Nombre Receptor | Receiver Name | `ACH_ENTRY_DETAIL` | `INDIVIDUAL_NAME` | Direct mapping |
| `GV_REFERENCIA` | Referencia | Reference | `ACH_FILE_HEADER` | `REFERENCE_CODE` | Direct mapping |
| `GV_DESCPAGO` | Descripción Pago | Payment Description | `ACH_BATCH_HEADER` | `COMPANY_ENTRY_DESCRIPTION` | Direct mapping |
| `GN_MONTOOPERACION` | Monto Operación | Amount | `ACH_ENTRY_DETAIL` | `AMOUNT_DECIMAL` | Use decimal amount (converted from cents) |

## Table Relationships

### Primary Table: ACH_ENTRY_DETAIL (Record Type 6)
- This is the main source table for most parameters
- Each row represents one payment transaction

### Join Relationships:
1. **ACH_ENTRY_DETAIL → ACH_FILES**
   - Join: `ACH_ENTRY_DETAIL.FILE_ID = ACH_FILES.FILE_ID`
   - Purpose: Get CLIENT_ID

2. **ACH_ENTRY_DETAIL → ACH_BATCH_HEADER**
   - Join: `ACH_ENTRY_DETAIL.FILE_ID = ACH_BATCH_HEADER.FILE_ID`
   - Join: `ACH_ENTRY_DETAIL.BATCH_NUMBER = ACH_BATCH_HEADER.BATCH_NUMBER`
   - Purpose: Get batch-level information (Company Name, Standard Entry Class, Company ID, etc.)

3. **ACH_ENTRY_DETAIL → ACH_FILE_HEADER**
   - Join: `ACH_ENTRY_DETAIL.FILE_ID = ACH_FILE_HEADER.FILE_ID`
   - Purpose: Get file-level information (Reference Code)
   - Note: There should be only one file header per file

## Query Structure Plan

### Base Query Structure

```sql
SELECT
    -- Trace Sequence Number (GN_SECUENCIACONVENIO)
    ed.TRACE_SEQUENCE_NUMBER AS trace_sequence_number,  -- GN_SECUENCIACONVENIO
    
    -- Client ID (GN_CODIGOCLIENTE)
    af.CLIENT_ID AS client_id,  -- GN_CODIGOCLIENTE
    
    -- Origin Agency (GN_AGENCIACTAORIGEN)
    SUBSTR(bh.ORIGINATING_DFI_ID, 1, 3) AS origin_agency,  -- GN_AGENCIACTAORIGEN
    
    -- Origin Sub-account (GN_SUBCTAORIGEN)
    -- May need parsing logic or default to 0
    0 AS origin_sub_account,  -- GN_SUBCTAORIGEN (default, may need parsing)
    
    -- ACH Class (GV_APLCTAORIGEN)
    bh.STANDARD_ENTRY_CLASS_CODE AS ach_class,  -- GV_APLCTAORIGEN
    
    -- Origin Account (GN_CTAORIGEN)
    ed.DFI_ACCOUNT_NUMBER AS origin_account,  -- GN_CTAORIGEN
    
    -- Company ID (GN_EMPCTAORIGEN)
    bh.COMPANY_IDENTIFICATION AS company_id,  -- GN_EMPCTAORIGEN
    
    -- Receiver Routing/ABA (GN_ABABCORECIBIDOR)
    ed.RECEIVING_DFI_ID || ed.CHECK_DIGIT AS receiver_routing_aba,  -- GN_ABABCORECIBIDOR
    
    -- Receiver Account (GV_CTABCORECIBIDOR)
    ed.DFI_ACCOUNT_NUMBER AS receiver_account,  -- GV_CTABCORECIBIDOR
    
    -- Transaction Code (GN_PRODBCORECIBIDOR)
    ed.TRANSACTION_CODE AS transaction_code,  -- GN_PRODBCORECIBIDOR
    
    -- Company Name (GV_CUENTAINSTITUCION)
    bh.COMPANY_NAME AS company_name,  -- GV_CUENTAINSTITUCION
    
    -- Receiver ID (GV_IDRECIBIDOR)
    ed.INDIVIDUAL_ID_NUMBER AS receiver_id,  -- GV_IDRECIBIDOR
    
    -- Receiver Name (GV_NOMBRERECIBIDOR)
    ed.INDIVIDUAL_NAME AS receiver_name,  -- GV_NOMBRERECIBIDOR
    
    -- Reference (GV_REFERENCIA)
    fh.REFERENCE_CODE AS reference_code,  -- GV_REFERENCIA
    
    -- Payment Description (GV_DESCPAGO)
    bh.COMPANY_ENTRY_DESCRIPTION AS payment_description,  -- GV_DESCPAGO
    
    -- Amount (GN_MONTOOPERACION)
    ed.AMOUNT_DECIMAL AS amount,  -- GN_MONTOOPERACION
    
    -- Additional fields for filtering/identification
    ed.ENTRY_DETAIL_ID,
    ed.FILE_ID,
    ed.BATCH_NUMBER,
    af.ORIGINAL_FILENAME

FROM
    ACH_ENTRY_DETAIL ed
    
    -- Join to ACH_FILES for CLIENT_ID
    INNER JOIN ACH_FILES af
        ON ed.FILE_ID = af.FILE_ID
    
    -- Join to ACH_BATCH_HEADER for batch-level data
    INNER JOIN ACH_BATCH_HEADER bh
        ON ed.FILE_ID = bh.FILE_ID
        AND ed.BATCH_NUMBER = bh.BATCH_NUMBER
    
    -- Join to ACH_FILE_HEADER for file-level data
    INNER JOIN ACH_FILE_HEADER fh
        ON ed.FILE_ID = fh.FILE_ID

WHERE
    -- Filter conditions (to be determined based on requirements)
    ed.RECORD_TYPE_CODE = '6'  -- Only Entry Detail records
    -- Add additional filters as needed (e.g., by FILE_ID, CLIENT_ID, date range, etc.)
```

## Data Transformations Required

### 1. Trace Sequence Number (GN_SECUENCIACONVENIO)
- **Source**: `ACH_ENTRY_DETAIL.TRACE_NUMBER` or `TRACE_SEQUENCE_NUMBER`
- **Transformation**: 
  - If `TRACE_SEQUENCE_NUMBER` exists, use it directly
  - Otherwise, extract last 7 digits from `TRACE_NUMBER`
  - Convert to NUMBER
- **Example**: `TRACE_NUMBER = '021000020000001'` → Extract `'0000001'` → Convert to `1`

### 2. Origin Agency (GN_AGENCIACTAORIGEN)
- **Source**: `ACH_BATCH_HEADER.ORIGINATING_DFI_ID`
- **Transformation**: Extract first 3 digits (Federal Reserve routing prefix)
- **Example**: `ORIGINATING_DFI_ID = '02100002'` → Extract `'021'` → Convert to `101` (may need lookup table)

### 3. Origin Sub-account (GN_SUBCTAORIGEN)
- **Source**: `ACH_ENTRY_DETAIL.DFI_ACCOUNT_NUMBER` or derived
- **Transformation**: 
  - May need to parse account number structure
  - Default to 0 if not available
  - May require business logic based on account number format

### 4. Receiver Routing/ABA (GN_ABABCORECIBIDOR)
- **Source**: `ACH_ENTRY_DETAIL.RECEIVING_DFI_ID` + `CHECK_DIGIT`
- **Transformation**: Concatenate 8-digit routing number
- **Example**: `RECEIVING_DFI_ID = '02100002'` + `CHECK_DIGIT = '1'` → `'021000021'`

### 5. Amount (GN_MONTOOPERACION)
- **Source**: `ACH_ENTRY_DETAIL.AMOUNT_DECIMAL`
- **Transformation**: Use decimal amount directly (already converted from cents)
- **Example**: `AMOUNT = 150025` (cents) → `AMOUNT_DECIMAL = 1500.25`

## Query Considerations

### 1. Filtering Options
- By `FILE_ID`: Process specific ACH file
- By `CLIENT_ID`: Process all entries for a specific client
- By date range: Filter by `CREATED_DATE` or `EFFECTIVE_ENTRY_DATE`
- By processing status: Filter by `ACH_FILES.PROCESSING_STATUS`
- By batch number: Process specific batch

### 2. Data Quality Checks
- Ensure all required fields are NOT NULL
- Validate transaction codes are valid (22, 23, 24, etc.)
- Validate standard entry class codes (PPD, CCD, TEL, etc.)
- Check for missing relationships (orphaned entry details)

### 3. Performance Optimization
- Use indexes on join columns:
  - `ACH_ENTRY_DETAIL.FILE_ID`
  - `ACH_ENTRY_DETAIL.BATCH_NUMBER`
  - `ACH_BATCH_HEADER.FILE_ID, BATCH_NUMBER`
  - `ACH_FILE_HEADER.FILE_ID`
- Consider filtering early in WHERE clause
- May need to process in batches if large volumes

### 4. Error Handling
- Handle NULL values with COALESCE or NVL
- Validate data types before conversion
- Log records that fail validation
- Consider creating a staging table for records to be processed

## Sample Query with Spanish Aliases

```sql
SELECT
    -- English field names with Spanish aliases
    ed.TRACE_SEQUENCE_NUMBER AS trace_sequence_number,  -- GN_SECUENCIACONVENIO
    af.CLIENT_ID AS client_id,  -- GN_CODIGOCLIENTE
    SUBSTR(bh.ORIGINATING_DFI_ID, 1, 3) AS origin_agency,  -- GN_AGENCIACTAORIGEN
    NVL(0, 0) AS origin_sub_account,  -- GN_SUBCTAORIGEN
    bh.STANDARD_ENTRY_CLASS_CODE AS ach_class,  -- GV_APLCTAORIGEN
    ed.DFI_ACCOUNT_NUMBER AS origin_account,  -- GN_CTAORIGEN
    bh.COMPANY_IDENTIFICATION AS company_id,  -- GN_EMPCTAORIGEN
    ed.RECEIVING_DFI_ID || ed.CHECK_DIGIT AS receiver_routing_aba,  -- GN_ABABCORECIBIDOR
    ed.DFI_ACCOUNT_NUMBER AS receiver_account,  -- GV_CTABCORECIBIDOR
    ed.TRANSACTION_CODE AS transaction_code,  -- GN_PRODBCORECIBIDOR
    bh.COMPANY_NAME AS company_name,  -- GV_CUENTAINSTITUCION
    ed.INDIVIDUAL_ID_NUMBER AS receiver_id,  -- GV_IDRECIBIDOR
    ed.INDIVIDUAL_NAME AS receiver_name,  -- GV_NOMBRERECIBIDOR
    fh.REFERENCE_CODE AS reference_code,  -- GV_REFERENCIA
    bh.COMPANY_ENTRY_DESCRIPTION AS payment_description,  -- GV_DESCPAGO
    ed.AMOUNT_DECIMAL AS amount,  -- GN_MONTOOPERACION
    
    -- Spanish aliases for stored procedure parameters
    ed.TRACE_SEQUENCE_NUMBER AS GN_SECUENCIACONVENIO,
    af.CLIENT_ID AS GN_CODIGOCLIENTE,
    SUBSTR(bh.ORIGINATING_DFI_ID, 1, 3) AS GN_AGENCIACTAORIGEN,
    NVL(0, 0) AS GN_SUBCTAORIGEN,
    bh.STANDARD_ENTRY_CLASS_CODE AS GV_APLCTAORIGEN,
    ed.DFI_ACCOUNT_NUMBER AS GN_CTAORIGEN,
    bh.COMPANY_IDENTIFICATION AS GN_EMPCTAORIGEN,
    ed.RECEIVING_DFI_ID || ed.CHECK_DIGIT AS GN_ABABCORECIBIDOR,
    ed.DFI_ACCOUNT_NUMBER AS GV_CTABCORECIBIDOR,
    ed.TRANSACTION_CODE AS GN_PRODBCORECIBIDOR,
    bh.COMPANY_NAME AS GV_CUENTAINSTITUCION,
    ed.INDIVIDUAL_ID_NUMBER AS GV_IDRECIBIDOR,
    ed.INDIVIDUAL_NAME AS GV_NOMBRERECIBIDOR,
    fh.REFERENCE_CODE AS GV_REFERENCIA,
    bh.COMPANY_ENTRY_DESCRIPTION AS GV_DESCPAGO,
    ed.AMOUNT_DECIMAL AS GN_MONTOOPERACION

FROM
    ACH_ENTRY_DETAIL ed
    INNER JOIN ACH_FILES af ON ed.FILE_ID = af.FILE_ID
    INNER JOIN ACH_BATCH_HEADER bh 
        ON ed.FILE_ID = bh.FILE_ID 
        AND ed.BATCH_NUMBER = bh.BATCH_NUMBER
    INNER JOIN ACH_FILE_HEADER fh ON ed.FILE_ID = fh.FILE_ID

WHERE
    ed.RECORD_TYPE_CODE = '6'
    -- Add additional filters as needed
```

## Implementation Steps

1. **Verify Table Structures**
   - Confirm all required columns exist in each table
   - Verify data types match stored procedure parameter types
   - Check for NULL constraints

2. **Test Data Extraction**
   - Run query on sample data
   - Verify all fields are populated correctly
   - Check data transformations (amounts, routing numbers, etc.)

3. **Handle Edge Cases**
   - Missing batch headers (LEFT JOIN may be needed)
   - Missing file headers (LEFT JOIN may be needed)
   - NULL values in required fields
   - Invalid data formats

4. **Optimize Query Performance**
   - Add appropriate indexes
   - Use query hints if needed
   - Consider materialized views for frequently accessed data

5. **Create Stored Procedure Wrapper**
   - Loop through query results
   - Call `BE_K_INTERFAZ_ACH.BE_P_PROCESA_PAGO` for each row
   - Handle errors and log results
   - Commit or rollback transactions appropriately

## Notes

- The query assumes one-to-one relationships where appropriate (e.g., one file header per file)
- Some fields may require additional parsing or lookup tables (e.g., routing number to agency conversion)
- The `GN_SUBCTAORIGEN` (origin sub-account) may need business logic to determine based on account number structure
- Consider adding validation checks before calling the stored procedure
- May need to handle multiple batches per file and multiple entries per batch

