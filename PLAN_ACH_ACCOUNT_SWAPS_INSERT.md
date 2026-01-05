# ACH_ACCOUNT_NUMBER_SWAPS INSERT Statement

## Table Structure

The `ACH_ACCOUNT_NUMBER_SWAPS` table has the following columns:

| Column Name | Null? | Type | Description |
|------------|-------|------|-------------|
| `SWAP_ID` | NOT NULL | NUMBER(38) | Primary key (auto-generated via RETURNING clause) |
| `ORIGINAL_DFI_ACCOUNT_NUMBER` | NULL | VARCHAR2(17) | Original DFI account number |
| `SWAP_ACCOUNT_NUMBER` | NULL | VARCHAR2(17) | Swapped/replacement account number |
| `SWAP_MEMO` | NOT NULL | VARCHAR2(255) | Memo/description for the swap |
| `CREATED_BY_USER` | NOT NULL | VARCHAR2(50) | User who created the record |
| `CREATED_DATE` | NOT NULL | TIMESTAMP(6) | Creation timestamp (auto-set to CURRENT_TIMESTAMP) |
| `UPDATED_BY_USER` | NULL | VARCHAR2(50) | User who last updated the record |
| `UPDATED_DATE` | NULL | TIMESTAMP(6) | Last update timestamp |

## INSERT Statement (As Implemented in Code)

### With Schema Prefix and Bind Variables

```sql
INSERT INTO {schema}.ACH_ACCOUNT_NUMBER_SWAPS (
    ORIGINAL_DFI_ACCOUNT_NUMBER,
    SWAP_ACCOUNT_NUMBER,
    SWAP_MEMO,
    CREATED_BY_USER,
    CREATED_DATE
) VALUES (
    :original_dfi_account_number,
    :swap_account_number,
    :swap_memo,
    :created_by_user,
    CURRENT_TIMESTAMP
) RETURNING SWAP_ID INTO :swap_id
```

**Note:** `{schema}` is replaced with the actual schema name from configuration (e.g., `OBS_SCHEMA`).

### Example with Actual Values

```sql
-- Example 1: Full swap with all fields
INSERT INTO OBS_SCHEMA.ACH_ACCOUNT_NUMBER_SWAPS (
    ORIGINAL_DFI_ACCOUNT_NUMBER,
    SWAP_ACCOUNT_NUMBER,
    SWAP_MEMO,
    CREATED_BY_USER,
    CREATED_DATE
) VALUES (
    '12345678901234567',
    '98765432109876543',
    'Account number swap for customer migration',
    'admin_user',
    CURRENT_TIMESTAMP
);

-- Example 2: Swap with NULL account numbers (memo-only swap)
INSERT INTO OBS_SCHEMA.ACH_ACCOUNT_NUMBER_SWAPS (
    ORIGINAL_DFI_ACCOUNT_NUMBER,
    SWAP_ACCOUNT_NUMBER,
    SWAP_MEMO,
    CREATED_BY_USER,
    CREATED_DATE
) VALUES (
    NULL,
    NULL,
    'General swap memo for tracking',
    'system_user',
    CURRENT_TIMESTAMP
);

-- Example 3: Swap with only original account number
INSERT INTO OBS_SCHEMA.ACH_ACCOUNT_NUMBER_SWAPS (
    ORIGINAL_DFI_ACCOUNT_NUMBER,
    SWAP_ACCOUNT_NUMBER,
    SWAP_MEMO,
    CREATED_BY_USER,
    CREATED_DATE
) VALUES (
    '11111111111111111',
    NULL,
    'Original account flagged for review',
    'review_user',
    CURRENT_TIMESTAMP
);
```

## Using RETURNING Clause (Oracle-Specific)

The implementation uses Oracle's `RETURNING` clause to get the generated `SWAP_ID`:

```sql
INSERT INTO OBS_SCHEMA.ACH_ACCOUNT_NUMBER_SWAPS (
    ORIGINAL_DFI_ACCOUNT_NUMBER,
    SWAP_ACCOUNT_NUMBER,
    SWAP_MEMO,
    CREATED_BY_USER,
    CREATED_DATE
) VALUES (
    :original_dfi_account_number,
    :swap_account_number,
    :swap_memo,
    :created_by_user,
    CURRENT_TIMESTAMP
) RETURNING SWAP_ID INTO :swap_id
```

This allows the application to immediately retrieve the auto-generated primary key value.

## Required Fields

- **`SWAP_MEMO`** - REQUIRED (NOT NULL) - Must always be provided
- **`CREATED_BY_USER`** - REQUIRED (NOT NULL) - Must always be provided
- **`CREATED_DATE`** - Auto-set to `CURRENT_TIMESTAMP` - Not provided in INSERT

## Optional Fields

- **`ORIGINAL_DFI_ACCOUNT_NUMBER`** - Optional (can be NULL)
- **`SWAP_ACCOUNT_NUMBER`** - Optional (can be NULL)
- **`UPDATED_BY_USER`** - Not set on INSERT (only on UPDATE)
- **`UPDATED_DATE`** - Not set on INSERT (only on UPDATE)

## Python Implementation

The INSERT is implemented in `oracle_service.py` in the `create_ach_account_swap()` method:

```python
def create_ach_account_swap(self, swap: AchAccountSwapCreate) -> int:
    """Create a new ACH_ACCOUNT_NUMBER_SWAPS record."""
    insert_sql = f"""
    INSERT INTO {self.config.db_schema}.ACH_ACCOUNT_NUMBER_SWAPS (
        ORIGINAL_DFI_ACCOUNT_NUMBER,
        SWAP_ACCOUNT_NUMBER,
        SWAP_MEMO,
        CREATED_BY_USER,
        CREATED_DATE
    ) VALUES (
        :original_dfi_account_number,
        :swap_account_number,
        :swap_memo,
        :created_by_user,
        CURRENT_TIMESTAMP
    ) RETURNING SWAP_ID INTO :swap_id
    """
    
    swap_id = cursor.var(int)
    cursor.execute(insert_sql, {
        'original_dfi_account_number': swap.original_dfi_account_number,
        'swap_account_number': swap.swap_account_number,
        'swap_memo': swap.swap_memo,
        'created_by_user': swap.created_by_user,
        'swap_id': swap_id
    })
    
    conn.commit()
    generated_id = swap_id.getvalue()[0]
    return generated_id
```

## API Usage

The INSERT is called via the API endpoint:

```bash
POST /api/oracle/ach-account-swaps
Content-Type: application/json

{
  "original_dfi_account_number": "12345678901234567",
  "swap_account_number": "98765432109876543",
  "swap_memo": "Account number swap for customer migration",
  "created_by_user": "admin_user"
}
```

## Notes

1. **Schema Prefix**: All queries use `{self.config.db_schema}.ACH_ACCOUNT_NUMBER_SWAPS` to ensure correct schema access
2. **Auto-Generated ID**: `SWAP_ID` is returned via the `RETURNING` clause
3. **Timestamp**: `CREATED_DATE` is automatically set to `CURRENT_TIMESTAMP`
4. **Nullable Fields**: Both account number fields can be NULL, but `SWAP_MEMO` and `CREATED_BY_USER` are required
5. **No Sequence**: The `SWAP_ID` appears to be generated by the database (possibly via a trigger or sequence), not explicitly in the INSERT

