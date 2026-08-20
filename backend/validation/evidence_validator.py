import re
from typing import List
from backend.models.schemas import CandidateField, FieldStatus, Section, ValidationResult

def normalize_text(text: str) -> str:
    """Normalizes whitespace to allow deterministic space variations."""
    if not text:
        return ""
    # Replace any sequence of whitespace with a single space and strip
    return re.sub(r'\s+', ' ', text).strip()

def validate_field(field: CandidateField, raw_text: str, sections: List[Section]) -> ValidationResult:
    """
    Deterministically validates a parsed CandidateField against the extracted resume text and sections.
    """
    if field.status == FieldStatus.NOT_FOUND:
        return ValidationResult(
            field_id=field.field_id,
            status=field.status,
            value=None,
            evidence=None,
            source_section=None,
            is_valid=True,
            validation_message="Field correctly identified as NOT_FOUND."
        )
        
    if field.status == FieldStatus.AMBIGUOUS:
        return ValidationResult(
            field_id=field.field_id,
            status=field.status,
            value=field.value,
            evidence=field.evidence,
            source_section=field.source_section,
            is_valid=True,
            validation_message="Field correctly preserved as AMBIGUOUS."
        )

    # Status must be FOUND
    if not field.evidence:
        return ValidationResult(
            field_id=field.field_id,
            status=field.status,
            value=field.value,
            evidence=field.evidence,
            source_section=field.source_section,
            is_valid=False,
            validation_message="No evidence provided for the claim."
        )
        
    if not field.value:
        return ValidationResult(
            field_id=field.field_id,
            status=field.status,
            value=field.value,
            evidence=field.evidence,
            source_section=field.source_section,
            is_valid=False,
            validation_message="No value provided for the claim."
        )

    # 1. Does evidence exist in the raw resume text?
    norm_evidence = normalize_text(field.evidence)
    norm_raw = normalize_text(raw_text)
    
    if norm_evidence not in norm_raw:
        return ValidationResult(
            field_id=field.field_id,
            status=field.status,
            value=field.value,
            evidence=field.evidence,
            source_section=field.source_section,
            is_valid=False,
            validation_message="Evidence not found in the extracted resume text."
        )
        
    # 2. Does evidence support the value?
    norm_value = normalize_text(field.value)
    if norm_value not in norm_evidence:
        return ValidationResult(
            field_id=field.field_id,
            status=field.status,
            value=field.value,
            evidence=field.evidence,
            source_section=field.source_section,
            is_valid=False,
            validation_message="Value is not supported by the provided evidence."
        )
        
    # 3. Source section validation
    if field.source_section:
        section_found = False
        section_text_norm = ""
        for sec in sections:
            if sec.section_id == field.source_section:
                section_found = True
                section_text_norm = normalize_text(sec.text)
                break
                
        if not section_found:
            return ValidationResult(
                field_id=field.field_id,
                status=field.status,
                value=field.value,
                evidence=field.evidence,
                source_section=field.source_section,
                is_valid=False,
                validation_message="Source section not found in segmented resume."
            )
            
        if norm_evidence not in section_text_norm:
            return ValidationResult(
                field_id=field.field_id,
                status=field.status,
                value=field.value,
                evidence=field.evidence,
                source_section=field.source_section,
                is_valid=False,
                validation_message="Evidence not found in the specified source section."
            )
            
    return ValidationResult(
        field_id=field.field_id,
        status=field.status,
        value=field.value,
        evidence=field.evidence,
        source_section=field.source_section,
        is_valid=True,
        validation_message="Valid evidence."
    )

def validate_profile(fields: List[CandidateField], raw_text: str, sections: List[Section]) -> List[ValidationResult]:
    return [validate_field(field, raw_text, sections) for field in fields]
