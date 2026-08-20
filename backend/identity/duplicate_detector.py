import hashlib
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from backend.models.schemas import CandidateField, FieldStatus, DuplicateStatus, DuplicateResult

@dataclass
class ExistingCandidate:
    candidate_id: str
    file_hash: str
    content_hash: str
    fields: List[CandidateField]

def calculate_file_hash(file_path: str) -> str:
    """Calculates SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return ""

def calculate_content_hash(raw_text: str) -> str:
    """Calculates a deterministic normalized content hash."""
    if not raw_text:
        return ""
    # Normalize: lowercase, remove all non-alphanumeric chars (or just normalize whitespace)
    # The prompt says: trimming unnecessary whitespace; normalizing repeated whitespace; normalizing line endings; consistent casing
    normalized = re.sub(r'\s+', ' ', raw_text).strip().lower()
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def _get_field_value(fields: List[CandidateField], field_id: str) -> Optional[str]:
    for f in fields:
        if f.field_id == field_id and f.status == FieldStatus.FOUND and f.value:
            return f.value.strip().lower()
    return None

def detect_duplicate(
    file_path: str,
    raw_text: str,
    parsed_fields: List[CandidateField],
    existing_candidates: List[ExistingCandidate]
) -> DuplicateResult:
    """Detects if the uploaded resume is a duplicate or belongs to an existing candidate."""
    
    file_hash = calculate_file_hash(file_path)
    content_hash = calculate_content_hash(raw_text)
    
    # Extract identity signals from parsed_fields
    name = _get_field_value(parsed_fields, "FULL-NAME")
    email = _get_field_value(parsed_fields, "EMAIL")
    phone = _get_field_value(parsed_fields, "PHONE")
    linkedin = _get_field_value(parsed_fields, "LINKEDIN-PORTFOLIO")
    institution = _get_field_value(parsed_fields, "INSTITUTION")
    job = _get_field_value(parsed_fields, "MOST-RECENT-JOB")
    
    for candidate in existing_candidates:
        # 1. EXACT_DUPLICATE
        if file_hash and candidate.file_hash == file_hash:
            return DuplicateResult(
                status=DuplicateStatus.EXACT_DUPLICATE,
                message="Already it exist",
                existing_candidate_id=candidate.candidate_id,
                file_hash=file_hash,
                content_hash=content_hash
            )
            
        # 2. SAME CONTENT, DIFFERENT FILE -> SAME_CANDIDATE
        if content_hash and candidate.content_hash == content_hash:
            return DuplicateResult(
                status=DuplicateStatus.SAME_CANDIDATE,
                message="Same content found with a different file.",
                existing_candidate_id=candidate.candidate_id,
                file_hash=file_hash,
                content_hash=content_hash
            )
            
        # 3. Check Identity Signals
        c_name = _get_field_value(candidate.fields, "FULL-NAME")
        c_email = _get_field_value(candidate.fields, "EMAIL")
        c_phone = _get_field_value(candidate.fields, "PHONE")
        c_linkedin = _get_field_value(candidate.fields, "LINKEDIN-PORTFOLIO")
        c_inst = _get_field_value(candidate.fields, "INSTITUTION")
        c_job = _get_field_value(candidate.fields, "MOST-RECENT-JOB")
        
        # Strong match: Email, Phone, or LinkedIn matches
        strong_match = False
        if email and c_email and email == c_email:
            strong_match = True
        elif phone and c_phone and phone == c_phone:
            strong_match = True
        elif linkedin and c_linkedin and linkedin == c_linkedin:
            strong_match = True
            
        if strong_match:
            # If strong match but name is totally different, it's possible same candidate (e.g. name change or shared email)
            if name and c_name and name != c_name:
                return DuplicateResult(
                    status=DuplicateStatus.POSSIBLE_SAME_CANDIDATE,
                    message="Strong identity signal matched but name differs.",
                    existing_candidate_id=candidate.candidate_id,
                    file_hash=file_hash,
                    content_hash=content_hash
                )
            return DuplicateResult(
                status=DuplicateStatus.SAME_CANDIDATE,
                message="Strong identity signal matched.",
                existing_candidate_id=candidate.candidate_id,
                file_hash=file_hash,
                content_hash=content_hash
            )
            
        # Weak match: Name + Institution OR Name + Job
        if name and c_name and name == c_name:
            if (institution and c_inst and institution == c_inst) or (job and c_job and job == c_job):
                return DuplicateResult(
                    status=DuplicateStatus.POSSIBLE_SAME_CANDIDATE,
                    message="Name and supporting weak signal matched.",
                    existing_candidate_id=candidate.candidate_id,
                    file_hash=file_hash,
                    content_hash=content_hash
                )
                
    # No matches found
    return DuplicateResult(
        status=DuplicateStatus.NEW_CANDIDATE,
        message="New candidate detected.",
        existing_candidate_id=None,
        file_hash=file_hash,
        content_hash=content_hash
    )
