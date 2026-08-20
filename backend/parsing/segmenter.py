import re
from typing import List
from backend.models.schemas import Section

# Fixed section allowlist mapping
# Maps a normalized version of the heading to a canonical section_id
SECTION_MAPPING = {
    "contact": "CONTACT",
    
    "summary": "SUMMARY",
    "professional summary": "SUMMARY",
    "career summary": "SUMMARY",
    "objective": "OBJECTIVE",
    
    "education": "EDUCATION",
    "educational background": "EDUCATION",
    "academic background": "EDUCATION",
    
    "experience": "EXPERIENCE",
    "work experience": "EXPERIENCE",
    "professional experience": "EXPERIENCE",
    "employment history": "EXPERIENCE",
    
    "skills": "SKILLS",
    "technical skills": "SKILLS",
    "core skills": "SKILLS",
    "technical skills & tools": "SKILLS",
    "technical skills and tools": "SKILLS",
    
    "projects": "PROJECTS",
    "academic projects": "PROJECTS",
    "personal projects": "PROJECTS",
    "technical projects": "PROJECTS",
    
    "certifications": "CERTIFICATIONS",
    "certifications & licenses": "CERTIFICATIONS",
    "certifications and licenses": "CERTIFICATIONS",
    
    "achievements": "ACHIEVEMENTS",
    "awards & achievements": "ACHIEVEMENTS",
    "awards and achievements": "ACHIEVEMENTS",
    
    "languages": "LANGUAGES",
    "location": "LOCATION"
}

def clean_heading(text: str) -> str:
    """Normalize a potential heading to compare against our allowlist."""
    # Remove leading/trailing whitespace, newlines, and trailing colons
    cleaned = text.strip().lower()
    if cleaned.endswith(':'):
        cleaned = cleaned[:-1].strip()
    return cleaned

def segment_resume(text: str) -> List[Section]:
    """
    Deterministically segments extracted resume text into recognized sections.
    """
    sections = []
    
    if not text or not text.strip():
        return sections
        
    lines = text.split('\n')
    
    current_section_id = "CONTACT"
    current_section_name = "Contact"
    current_heading_text = ""
    current_start_line = 0
    
    # Contact section is typically at the top before any specific heading
    # We will accumulate lines until we hit a known heading.
    
    for i, line in enumerate(lines):
        cleaned_line = clean_heading(line)
        
        # Check if the line is a known heading
        if cleaned_line in SECTION_MAPPING:
            # We found a new section heading, so finalize the previous section
            
            # The text for the previous section goes from current_start_line to i
            section_content_lines = lines[current_start_line:i]
            section_text = "\n".join(section_content_lines).strip()
            
            if section_text or current_heading_text:
                # Calculate start/end positions based on character indices
                # Note: this is a simplistic index calculation; depending on exact needs, 
                # we might just store line numbers or precise char offsets of the original text.
                start_pos = 0 # Not doing exact char offsets for this simple implementation
                end_pos = 0
                
                sections.append(Section(
                    section_name=current_section_name,
                    section_id=current_section_id,
                    text=section_text,
                    start_position=current_start_line,
                    end_position=i,
                    heading_text=current_heading_text
                ))
            
            # Start the new section
            current_section_id = SECTION_MAPPING[cleaned_line]
            current_section_name = current_section_id.title() # e.g., "Experience"
            current_heading_text = line.strip()
            current_start_line = i + 1 # The content starts after the heading line
            
    # Finalize the last section
    section_content_lines = lines[current_start_line:]
    section_text = "\n".join(section_content_lines).strip()
    
    if section_text or current_heading_text:
        sections.append(Section(
            section_name=current_section_name,
            section_id=current_section_id,
            text=section_text,
            start_position=current_start_line,
            end_position=len(lines),
            heading_text=current_heading_text
        ))
        
    return sections
