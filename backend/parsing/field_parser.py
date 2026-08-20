import re
from typing import List, Dict, Optional
from backend.models.schemas import Section, CandidateField, FieldStatus

# Deterministic Regex Patterns
EMAIL_RE = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
PHONE_RE = re.compile(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}')
LINKEDIN_RE = re.compile(r'linkedin\.com/in/[\w-]+', re.IGNORECASE)
YEAR_RE = re.compile(r'\b(19\d{2}|20\d{2})\b')
DEGREE_RE = re.compile(r'\b(B\.?E\.?|B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?A\.?|Ph\.?D\.?|Bachelor[s]?|Master[s]?|Doctorate)(?!\w)', re.IGNORECASE)
INSTITUTION_RE = re.compile(r'\b([A-Za-z ]+(?:University|College|Institute|School|Academy))\b', re.IGNORECASE)

def _get_section(sections: List[Section], section_id: str) -> Optional[Section]:
    for sec in sections:
        if sec.section_id == section_id:
            return sec
    return None

def extract_name(contact_sec: Optional[Section]) -> CandidateField:
    field_id = "FULL-NAME"
    category = "Personal"
    if not contact_sec or not contact_sec.text.strip():
        return CandidateField(field_id, category, FieldStatus.NOT_FOUND)
        
    lines = [line.strip() for line in contact_sec.text.split('\n') if line.strip()]
    if not lines:
        return CandidateField(field_id, category, FieldStatus.NOT_FOUND)
    
    # Deterministic assumption: The first non-empty line of the contact section is the name.
    # To avoid ambiguous cases, if it matches an email or phone, it's not a name.
    first_line = lines[0]
    if EMAIL_RE.search(first_line) or PHONE_RE.search(first_line):
        return CandidateField(field_id, category, FieldStatus.NOT_FOUND)
        
    return CandidateField(field_id, category, FieldStatus.FOUND, first_line, first_line, contact_sec.section_id)

def extract_regex_field(contact_sec: Optional[Section], field_id: str, pattern: re.Pattern, category: str) -> CandidateField:
    if not contact_sec or not contact_sec.text.strip():
        return CandidateField(field_id, category, FieldStatus.NOT_FOUND)
        
    matches = list(set(pattern.findall(contact_sec.text)))
    if not matches:
        return CandidateField(field_id, category, FieldStatus.NOT_FOUND)
    if len(matches) > 1:
        # If multiple different emails/phones exist, it's ambiguous based on deterministic rules
        return CandidateField(field_id, category, FieldStatus.AMBIGUOUS)
        
    match_str = matches[0] if isinstance(matches[0], str) else matches[0][0]
    # For institution, the regex group extraction might just give the word "University".
    # To get the full match we just use search instead.
    
    # Let's do a finditer for the exact evidence match
    all_matches = list(pattern.finditer(contact_sec.text))
    # Deduplicate by match string
    unique_matches = {m.group(0).strip() for m in all_matches}
    
    if len(unique_matches) > 1:
        return CandidateField(field_id, category, FieldStatus.AMBIGUOUS)
        
    if not unique_matches:
        return CandidateField(field_id, category, FieldStatus.NOT_FOUND)
        
    val = list(unique_matches)[0]
    return CandidateField(field_id, category, FieldStatus.FOUND, val, val, contact_sec.section_id)

def extract_education_fields(edu_sec: Optional[Section]) -> List[CandidateField]:
    fields = []
    
    # 5. HIGHEST-DEGREE
    fields.append(extract_regex_field(edu_sec, "HIGHEST-DEGREE", DEGREE_RE, "Education"))
    # 6. INSTITUTION
    fields.append(extract_regex_field(edu_sec, "INSTITUTION", INSTITUTION_RE, "Education"))
    # 7. GRADUATION-YEAR
    fields.append(extract_regex_field(edu_sec, "GRADUATION-YEAR", YEAR_RE, "Education"))
    
    return fields

def extract_most_recent_job(exp_sec: Optional[Section]) -> CandidateField:
    field_id = "MOST-RECENT-JOB"
    category = "Experience"
    if not exp_sec or not exp_sec.text.strip():
        return CandidateField(field_id, category, FieldStatus.NOT_FOUND)
        
    lines = [line.strip() for line in exp_sec.text.split('\n') if line.strip()]
    if not lines:
        return CandidateField(field_id, category, FieldStatus.NOT_FOUND)
        
    first_line = lines[0]
    return CandidateField(field_id, category, FieldStatus.FOUND, first_line, first_line, exp_sec.section_id)

def extract_location(contact_sec: Optional[Section]) -> CandidateField:
    # A highly simplified deterministic location parser: look for common state/country abbreviations or "City, State"
    # To avoid guessing, we will just look for exactly a "City, State" format line.
    field_id = "LOCATION"
    category = "Personal"
    if not contact_sec or not contact_sec.text.strip():
        return CandidateField(field_id, category, FieldStatus.NOT_FOUND)
        
    location_re = re.compile(r'\b([A-Z][a-zA-Z\s]+,\s*[A-Z]{2})\b')
    return extract_regex_field(contact_sec, field_id, location_re, category)

def extract_section_raw(sec: Optional[Section], field_id: str, category: str) -> CandidateField:
    if not sec or not sec.text.strip():
        return CandidateField(field_id, category, FieldStatus.NOT_FOUND)
        
    return CandidateField(field_id, category, FieldStatus.FOUND, sec.text.strip(), sec.text.strip(), sec.section_id)

def parse_fields(sections: List[Section]) -> List[CandidateField]:
    """Deterministically extracts candidate fields from segmented resume sections."""
    fields = []
    
    contact_sec = _get_section(sections, "CONTACT")
    edu_sec = _get_section(sections, "EDUCATION")
    exp_sec = _get_section(sections, "EXPERIENCE")
    skills_sec = _get_section(sections, "SKILLS")
    cert_sec = _get_section(sections, "CERTIFICATIONS")
    proj_sec = _get_section(sections, "PROJECTS")
    
    # 1. FULL-NAME
    fields.append(extract_name(contact_sec))
    # 2. EMAIL
    fields.append(extract_regex_field(contact_sec, "EMAIL", EMAIL_RE, "Personal"))
    # 3. PHONE
    fields.append(extract_regex_field(contact_sec, "PHONE", PHONE_RE, "Personal"))
    # 4. LINKEDIN-PORTFOLIO
    fields.append(extract_regex_field(contact_sec, "LINKEDIN-PORTFOLIO", LINKEDIN_RE, "Personal"))
    
    # 5, 6, 7 (Education)
    fields.extend(extract_education_fields(edu_sec))
    
    # 8. MOST-RECENT-JOB
    fields.append(extract_most_recent_job(exp_sec))
    
    # 9. LOCATION
    fields.append(extract_location(contact_sec))
    
    # 10. SKILLS-LIST
    fields.append(extract_section_raw(skills_sec, "SKILLS-LIST", "Skills"))
    
    # 11. CERTIFICATIONS
    fields.append(extract_section_raw(cert_sec, "CERTIFICATIONS", "Certifications"))
    
    # 12. PROJECTS
    fields.append(extract_section_raw(proj_sec, "PROJECTS", "Projects"))
    
    return fields
