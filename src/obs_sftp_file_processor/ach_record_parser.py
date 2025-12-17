"""ACH record parser to extract records from file content."""

from typing import List, Dict, Any, Optional
from .ach_validator import ACHValidator
from .ach_record_models import (
    AchFileHeaderCreate,
    AchBatchHeaderCreate,
    AchEntryDetailCreate,
    AchAddendaCreate,
    AchBatchControlCreate,
    AchFileControlCreate
)


class ACHRecordParser:
    """Parser for ACH file records."""
    
    @staticmethod
    def parse_file_content(file_content: str) -> Dict[str, List[Any]]:
        """Parse ACH file content and extract records by type.
        
        Returns a dictionary with keys:
        - 'file_headers': List of AchFileHeaderCreate
        - 'batch_headers': List of AchBatchHeaderCreate
        - 'entry_details': List of AchEntryDetailCreate
        - 'addendas': List of AchAddendaCreate
        - 'batch_controls': List of AchBatchControlCreate
        - 'file_controls': List of AchFileControlCreate
        """
        lines = file_content.split('\n')
        records = {
            'file_headers': [],
            'batch_headers': [],
            'entry_details': [],
            'addendas': [],
            'batch_controls': [],
            'file_controls': []
        }
        
        current_batch_number = None
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
            
            # Remove carriage return if present
            line = line.rstrip('\r')
            
            # Ensure line is 94 characters (pad or truncate if needed)
            if len(line) < 94:
                line = line.ljust(94)
            elif len(line) > 94:
                line = line[:94]
            
            # Get record type
            record_type = line[0:1] if len(line) > 0 else ""
            
            if record_type == "1":
                # File Header Record
                record = ACHRecordParser._parse_file_header(line)
                if record:
                    records['file_headers'].append(record)
            
            elif record_type == "5":
                # Batch Header Record
                record = ACHRecordParser._parse_batch_header(line)
                if record:
                    records['batch_headers'].append(record)
                    # Update current batch number
                    if record.batch_number:
                        current_batch_number = record.batch_number
            
            elif record_type == "6":
                # Entry Detail Record
                record = ACHRecordParser._parse_entry_detail(line, current_batch_number)
                if record:
                    records['entry_details'].append(record)
            
            elif record_type == "7":
                # Addenda Record
                record = ACHRecordParser._parse_addenda(line, current_batch_number)
                if record:
                    records['addendas'].append(record)
            
            elif record_type == "8":
                # Batch Control Record
                record = ACHRecordParser._parse_batch_control(line, current_batch_number)
                if record:
                    records['batch_controls'].append(record)
            
            elif record_type == "9":
                # File Control Record
                record = ACHRecordParser._parse_file_control(line)
                if record:
                    records['file_controls'].append(record)
        
        return records
    
    @staticmethod
    def _parse_file_header(line: str) -> Optional[AchFileHeaderCreate]:
        """Parse File Header Record (Type 1)."""
        if len(line) < 94:
            return None
        
        try:
            return AchFileHeaderCreate(
                file_id=0,  # Will be set when inserting
                record_type_code=line[0:1] if len(line) > 0 else "1",
                priority_code=line[1:3].strip() if len(line) >= 3 else None,
                immediate_destination=line[3:13].strip() if len(line) >= 13 else None,
                immediate_origin=line[13:23].strip() if len(line) >= 23 else None,
                file_creation_date=line[23:29].strip() if len(line) >= 29 else None,
                file_creation_time=line[29:33].strip() if len(line) >= 33 else None,
                file_id_modifier=line[33:34].strip() if len(line) >= 34 else None,
                record_size=line[34:37].strip() if len(line) >= 37 else "094",
                blocking_factor=line[37:39].strip() if len(line) >= 39 else "10",
                format_code=line[39:40].strip() if len(line) >= 40 else "1",
                immediate_dest_name=line[40:63].strip() if len(line) >= 63 else None,
                immediate_origin_name=line[63:86].strip() if len(line) >= 86 else None,
                reference_code=line[86:94].strip() if len(line) >= 94 else None,
                raw_record=line[:94]
            )
        except Exception:
            return None
    
    @staticmethod
    def _parse_batch_header(line: str) -> Optional[AchBatchHeaderCreate]:
        """Parse Batch Header Record (Type 5)."""
        if len(line) < 94:
            return None
        
        try:
            batch_number_str = line[87:94].strip() if len(line) >= 94 else "0"
            batch_number = int(batch_number_str) if batch_number_str.isdigit() else 0
            
            return AchBatchHeaderCreate(
                file_id=0,  # Will be set when inserting
                batch_number=batch_number,
                record_type_code=line[0:1] if len(line) > 0 else "5",
                service_class_code=line[1:4].strip() if len(line) >= 4 else None,
                company_name=line[4:20].strip() if len(line) >= 20 else None,
                company_discretionary_data=line[20:40].strip() if len(line) >= 40 else None,
                company_identification=line[40:50].strip() if len(line) >= 50 else None,
                standard_entry_class_code=line[50:53].strip() if len(line) >= 53 else None,
                company_entry_description=line[53:63].strip() if len(line) >= 63 else None,
                company_descriptive_date=line[63:69].strip() if len(line) >= 69 else None,
                effective_entry_date=line[69:75].strip() if len(line) >= 75 else None,
                settlement_date=line[75:78].strip() if len(line) >= 78 else None,
                originator_status_code=line[78:79].strip() if len(line) >= 79 else None,
                originating_dfi_id=line[79:87].strip() if len(line) >= 87 else None,
                raw_record=line[:94]
            )
        except Exception:
            return None
    
    @staticmethod
    def _parse_entry_detail(line: str, batch_number: Optional[int] = None) -> Optional[AchEntryDetailCreate]:
        """Parse Entry Detail Record (Type 6)."""
        if len(line) < 94:
            return None
        
        try:
            # Extract amount
            amount_str = line[29:39].strip() if len(line) >= 39 else "0"
            amount = int(amount_str) if amount_str.isdigit() else 0
            amount_decimal = amount / 100.0 if amount > 0 else 0.0
            
            # Extract trace number and sequence
            trace_number = line[79:94].strip() if len(line) >= 94 else None
            trace_sequence = None
            if trace_number and len(trace_number) >= 7:
                try:
                    trace_sequence = int(trace_number[-7:])
                except ValueError:
                    pass
            
            return AchEntryDetailCreate(
                file_id=0,  # Will be set when inserting
                batch_number=batch_number or 0,
                record_type_code=line[0:1] if len(line) > 0 else "6",
                transaction_code=line[1:3].strip() if len(line) >= 3 else None,
                receiving_dfi_id=line[3:11].strip() if len(line) >= 11 else None,
                check_digit=line[11:12].strip() if len(line) >= 12 else None,
                dfi_account_number=line[12:29].strip() if len(line) >= 29 else None,
                amount=amount,
                amount_decimal=amount_decimal,
                individual_id_number=line[39:54].strip() if len(line) >= 54 else None,
                individual_name=line[54:76].strip() if len(line) >= 76 else None,
                discretionary_data=line[76:78].strip() if len(line) >= 78 else None,
                addenda_record_indicator=line[78:79].strip() if len(line) >= 79 else "0",
                trace_number=trace_number,
                trace_sequence_number=trace_sequence,
                raw_record=line[:94]
            )
        except Exception:
            return None
    
    @staticmethod
    def _parse_addenda(line: str, batch_number: Optional[int] = None) -> Optional[AchAddendaCreate]:
        """Parse Addenda Record (Type 7)."""
        if len(line) < 94:
            return None
        
        try:
            addenda_seq_str = line[83:87].strip() if len(line) >= 87 else None
            addenda_seq = int(addenda_seq_str) if addenda_seq_str and addenda_seq_str.isdigit() else None
            
            entry_detail_seq_str = line[87:94].strip() if len(line) >= 94 else None
            entry_detail_seq = int(entry_detail_seq_str) if entry_detail_seq_str and entry_detail_seq_str.isdigit() else None
            
            return AchAddendaCreate(
                file_id=0,  # Will be set when inserting
                entry_detail_id=None,  # Will be linked later if needed
                batch_number=batch_number or 0,
                record_type_code=line[0:1] if len(line) > 0 else "7",
                addenda_type_code=line[1:3].strip() if len(line) >= 3 else None,
                payment_related_info=line[3:83].strip() if len(line) >= 83 else None,
                addenda_sequence_number=addenda_seq,
                entry_detail_sequence_num=entry_detail_seq,
                raw_record=line[:94]
            )
        except Exception:
            return None
    
    @staticmethod
    def _parse_batch_control(line: str, batch_number: Optional[int] = None) -> Optional[AchBatchControlCreate]:
        """Parse Batch Control Record (Type 8)."""
        if len(line) < 94:
            return None
        
        try:
            batch_num_str = line[87:94].strip() if len(line) >= 94 else "0"
            batch_num = int(batch_num_str) if batch_num_str.isdigit() else (batch_number or 0)
            
            entry_addenda_count_str = line[4:10].strip() if len(line) >= 10 else "0"
            entry_addenda_count = int(entry_addenda_count_str) if entry_addenda_count_str.isdigit() else None
            
            debit_amount_str = line[20:32].strip() if len(line) >= 32 else "0"
            debit_amount = int(debit_amount_str) if debit_amount_str.isdigit() else 0
            debit_decimal = debit_amount / 100.0 if debit_amount > 0 else 0.0
            
            credit_amount_str = line[32:44].strip() if len(line) >= 44 else "0"
            credit_amount = int(credit_amount_str) if credit_amount_str.isdigit() else 0
            credit_decimal = credit_amount / 100.0 if credit_amount > 0 else 0.0
            
            return AchBatchControlCreate(
                file_id=0,  # Will be set when inserting
                batch_number=batch_num,
                record_type_code=line[0:1] if len(line) > 0 else "8",
                service_class_code=line[1:4].strip() if len(line) >= 4 else None,
                entry_addenda_count=entry_addenda_count,
                entry_hash=line[10:20].strip() if len(line) >= 20 else None,
                total_debit_amount=debit_amount,
                total_debit_amount_decimal=debit_decimal,
                total_credit_amount=credit_amount,
                total_credit_amount_decimal=credit_decimal,
                company_identification=line[44:54].strip() if len(line) >= 54 else None,
                message_auth_code=line[54:73].strip() if len(line) >= 73 else None,
                reserved=line[73:79].strip() if len(line) >= 79 else None,
                originating_dfi_id=line[79:87].strip() if len(line) >= 87 else None,
                raw_record=line[:94]
            )
        except Exception:
            return None
    
    @staticmethod
    def _parse_file_control(line: str) -> Optional[AchFileControlCreate]:
        """Parse File Control Record (Type 9)."""
        if len(line) < 94:
            return None
        
        try:
            batch_count_str = line[1:7].strip() if len(line) >= 7 else None
            batch_count = int(batch_count_str) if batch_count_str and batch_count_str.isdigit() else None
            
            block_count_str = line[7:13].strip() if len(line) >= 13 else None
            block_count = int(block_count_str) if block_count_str and block_count_str.isdigit() else None
            
            entry_addenda_count_str = line[13:21].strip() if len(line) >= 21 else None
            entry_addenda_count = int(entry_addenda_count_str) if entry_addenda_count_str and entry_addenda_count_str.isdigit() else None
            
            debit_amount_str = line[31:43].strip() if len(line) >= 43 else "0"
            debit_amount = int(debit_amount_str) if debit_amount_str.isdigit() else 0
            debit_decimal = debit_amount / 100.0 if debit_amount > 0 else 0.0
            
            credit_amount_str = line[43:55].strip() if len(line) >= 55 else "0"
            credit_amount = int(credit_amount_str) if credit_amount_str.isdigit() else 0
            credit_decimal = credit_amount / 100.0 if credit_amount > 0 else 0.0
            
            return AchFileControlCreate(
                file_id=0,  # Will be set when inserting
                record_type_code=line[0:1] if len(line) > 0 else "9",
                batch_count=batch_count,
                block_count=block_count,
                entry_addenda_count=entry_addenda_count,
                entry_hash=line[21:31].strip() if len(line) >= 31 else None,
                total_debit_amount=debit_amount,
                total_debit_amount_decimal=debit_decimal,
                total_credit_amount=credit_amount,
                total_credit_amount_decimal=credit_decimal,
                reserved=line[55:94].strip() if len(line) >= 94 else None,
                raw_record=line[:94]
            )
        except Exception:
            return None

