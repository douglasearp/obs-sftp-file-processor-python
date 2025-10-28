"""ACH file line validation and processing."""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ACHRecordType(Enum):
    """ACH record types."""
    FILE_HEADER = "1"
    BATCH_HEADER = "5"
    ENTRY_DETAIL = "6"
    ADDENDA = "7"
    BATCH_CONTROL = "8"
    FILE_CONTROL = "9"


@dataclass
class ACHLineValidation:
    """ACH line validation result."""
    line_number: int
    line_content: str
    record_type: str
    is_valid: bool
    errors: List[str]


class ACHValidator:
    """ACH file line validator."""
    
    # ACH field positions and lengths based on NACHA specification
    FIELD_SPECS = {
        "1": {  # File Header Record
            "record_type": (0, 1),
            "priority_code": (1, 3),
            "immediate_destination": (3, 13),
            "immediate_origin": (13, 23),
            "file_creation_date": (23, 29),
            "file_creation_time": (29, 33),
            "file_id_modifier": (33, 34),
            "record_size": (34, 37),
            "blocking_factor": (37, 39),
            "format_code": (39, 40),
            "immediate_destination_name": (40, 63),
            "immediate_origin_name": (63, 86),
            "reference_code": (86, 94)
        },
        "5": {  # Batch Header Record
            "record_type": (0, 1),
            "service_class_code": (1, 4),
            "company_name": (4, 20),
            "company_discretionary_data": (20, 40),
            "company_identification": (40, 50),
            "standard_entry_class": (50, 53),
            "company_entry_description": (53, 63),
            "company_descriptive_date": (63, 69),
            "effective_entry_date": (69, 75),
            "settlement_date": (75, 78),
            "originator_status_code": (78, 79),
            "originating_dfi_id": (79, 87),
            "batch_number": (87, 94)
        },
        "6": {  # Entry Detail Record
            "record_type": (0, 1),
            "transaction_code": (1, 3),
            "receiving_dfi_id": (3, 11),
            "check_digit": (11, 12),
            "dfi_account_number": (12, 29),
            "amount": (29, 39),
            "individual_id": (39, 54),
            "individual_name": (54, 76),
            "discretionary_data": (76, 78),
            "addenda_indicator": (78, 79),
            "trace_number": (79, 94)
        },
        "7": {  # Addenda Record
            "record_type": (0, 1),
            "addenda_type_code": (1, 3),
            "payment_related_information": (3, 83),
            "addenda_sequence_number": (83, 87),
            "entry_detail_sequence_number": (87, 94)
        },
        "8": {  # Batch Control Record
            "record_type": (0, 1),
            "service_class_code": (1, 4),
            "entry_addenda_count": (4, 10),
            "entry_hash": (10, 20),
            "total_debit_entry_dollar_amount": (20, 32),
            "total_credit_entry_dollar_amount": (32, 44),
            "company_identification": (44, 54),
            "message_authentication_code": (54, 73),
            "reserved": (73, 79),
            "originating_dfi_id": (79, 87),
            "batch_number": (87, 94)
        },
        "9": {  # File Control Record
            "record_type": (0, 1),
            "batch_count": (1, 7),
            "block_count": (7, 13),
            "entry_addenda_count": (13, 21),
            "entry_hash": (21, 31),
            "total_debit_entry_dollar_amount": (31, 43),
            "total_credit_entry_dollar_amount": (43, 55),
            "reserved": (55, 94)
        }
    }
    
    @classmethod
    def validate_line(cls, line_number: int, line_content: str) -> ACHLineValidation:
        """Validate an ACH line."""
        errors = []
        
        # Basic length validation
        if len(line_content) != 94:
            errors.append(f"Line length must be 94 characters, got {len(line_content)}")
        
        # Get record type
        record_type = line_content[0:1] if len(line_content) > 0 else ""
        
        if record_type not in ["1", "5", "6", "7", "8", "9"]:
            errors.append(f"Invalid record type: {record_type}")
            return ACHLineValidation(line_number, line_content, record_type, False, errors)
        
        # Validate fields based on record type
        field_specs = cls.FIELD_SPECS.get(record_type, {})
        
        for field_name, (start, end) in field_specs.items():
            if end > len(line_content):
                errors.append(f"Field {field_name} extends beyond line length")
                continue
                
            field_value = line_content[start:end]
            
            # Field-specific validations
            if field_name == "record_type":
                if field_value != record_type:
                    errors.append(f"Record type mismatch: expected {record_type}, got {field_value}")
            
            elif field_name == "amount" and record_type == "6":
                # Amount validation for entry detail
                if not field_value.isdigit():
                    errors.append(f"Amount must be numeric: {field_value}")
                elif len(field_value) != 10:
                    errors.append(f"Amount must be 10 digits: {field_value}")
            
            elif field_name == "transaction_code" and record_type == "6":
                # Transaction code validation
                valid_codes = ["22", "23", "24", "27", "28", "29", "32", "33", "34", "37", "38", "39"]
                if field_value not in valid_codes:
                    errors.append(f"Invalid transaction code: {field_value}")
            
            elif field_name == "service_class_code" and record_type in ["5", "8"]:
                # Service class code validation
                valid_codes = ["200", "220", "225", "280", "285"]
                if field_value not in valid_codes:
                    errors.append(f"Invalid service class code: {field_value}")
            
            elif field_name == "standard_entry_class" and record_type == "5":
                # Standard entry class validation
                valid_codes = ["PPD", "CCD", "TEL", "WEB", "ARC", "BOC", "POP", "RCK"]
                if field_value not in valid_codes:
                    errors.append(f"Invalid standard entry class: {field_value}")
        
        # Additional validations
        if record_type == "6":  # Entry Detail
            # Check addenda indicator
            addenda_indicator = line_content[78:79] if len(line_content) > 78 else ""
            if addenda_indicator not in ["0", "1"]:
                errors.append(f"Invalid addenda indicator: {addenda_indicator}")
        
        is_valid = len(errors) == 0
        
        return ACHLineValidation(
            line_number=line_number,
            line_content=line_content,
            record_type=record_type,
            is_valid=is_valid,
            errors=errors
        )
    
    @classmethod
    def get_record_type_description(cls, record_type: str) -> str:
        """Get description for record type."""
        descriptions = {
            "1": "File Header Record",
            "5": "Batch Header Record", 
            "6": "Entry Detail Record",
            "7": "Addenda Record",
            "8": "Batch Control Record",
            "9": "File Control Record"
        }
        return descriptions.get(record_type, f"Unknown Record Type {record_type}")


def parse_ach_file_content(file_content: str) -> List[ACHLineValidation]:
    """Parse ACH file content and validate each line."""
    lines = file_content.split('\n')
    validations = []
    
    for i, line in enumerate(lines, 1):
        # Skip empty lines
        if not line.strip():
            continue
            
        # Remove carriage return if present
        line = line.rstrip('\r')
        
        validation = ACHValidator.validate_line(i, line)
        validations.append(validation)
    
    return validations
