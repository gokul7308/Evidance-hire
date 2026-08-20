import re
from typing import List
from backend.models.schemas import JDRequirement, RequirementCategory, Importance

def parse_jd(raw_text: str) -> List[JDRequirement]:
    requirements = []
    
    # State tracking
    current_importance = Importance.REQUIRED  # Default to required unless specified
    current_category_context = None
    
    lines = raw_text.split('\n')
    
    for i, line in enumerate(lines):
        original_line = line
        line = line.strip()
        
        if not line:
            continue
            
        # Check for context switches (headers)
        lower_line = line.lower()
        
        # Importance headers
        if re.search(r'^(required|requirements|must have|minimum qualifications):?$', lower_line):
            current_importance = Importance.REQUIRED
            continue
        elif re.search(r'^(preferred|nice to have|plus|preferred qualifications):?$', lower_line):
            current_importance = Importance.PREFERRED
            continue
            
        # Category headers
        if re.search(r'^(skills|required skills|preferred skills):?$', lower_line):
            current_category_context = RequirementCategory.SKILL
            if 'preferred' in lower_line:
                current_importance = Importance.PREFERRED
            elif 'required' in lower_line:
                current_importance = Importance.REQUIRED
            continue
        elif re.search(r'^(location):?$', lower_line):
            current_category_context = RequirementCategory.LOCATION
            continue
            
        # Clean bullet points for actual processing
        clean_line = re.sub(r'^[-•*]\s*', '', line)
        
        # Determine inline importance
        line_importance = current_importance
        if re.search(r'(?i)\b(preferred|nice to have|plus)\b', clean_line):
            line_importance = Importance.PREFERRED
        elif re.search(r'(?i)\b(required|must have|mandatory)\b', clean_line):
            line_importance = Importance.REQUIRED
            
        # Determine Category
        category = RequirementCategory.OTHER
        if re.search(r'(?i)\b(degree|bachelor|master|ph\.d|phd|b\.s\.|m\.s\.)\b', clean_line):
            category = RequirementCategory.EDUCATION
        elif re.search(r'(?i)\b(years of .*experience|experience with|minimum .* years)\b', clean_line):
            category = RequirementCategory.EXPERIENCE
        elif re.search(r'(?i)\b(certified|certification|certificate)\b', clean_line):
            category = RequirementCategory.CERTIFICATION
        elif re.search(r'(?i)\b(location|remote|relocate|located|based in|work in)\b', clean_line):
            category = RequirementCategory.LOCATION
        else:
            # If no explicit category matched, check if we are in a Skills context
            if current_category_context == RequirementCategory.SKILL:
                category = RequirementCategory.SKILL
            else:
                # If it's a short bullet, maybe it's a skill. But to be safe and strictly follow "explicit",
                # if it doesn't match and we're not in a skills block, it's OTHER or SKILL.
                # Let's say if it's very short (<= 3 words), it's likely a SKILL listing.
                words = clean_line.split()
                if len(words) <= 3:
                    category = RequirementCategory.SKILL
                else:
                    category = RequirementCategory.OTHER
                    
        # Extract specific text (e.g., removing "Experience with") to get the actual requirement if possible
        req_text = clean_line
        
        # We store the exact line as evidence.
        req_id = f"REQ-{len(requirements) + 1}"
        
        requirements.append(
            JDRequirement(
                requirement_id=req_id,
                category=category,
                requirement_text=req_text,
                importance=line_importance,
                evidence=original_line.strip(),
                source_line=i + 1
            )
        )
        
    return requirements
