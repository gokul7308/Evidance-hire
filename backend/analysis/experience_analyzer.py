import re
import datetime
from backend.models.schemas import JDRequirement, ExperienceResult, ExperienceStatus, CandidateField

def extract_required_years(req_text: str) -> float:
    match = re.search(r'(\d+)(?:\+| years?)', req_text)
    if match:
        return float(match.group(1))
    return 0.0

def extract_target_skill(req_text: str) -> str:
    # Remove generic words to find the target skill, e.g., "3+ years Python experience" -> "Python"
    # This is a basic deterministic heuristic.
    cleaned = re.sub(r'(?i)(\d+\+?\s*years?|of|experience|required|preferred|minimum|software|development)', '', req_text)
    cleaned = cleaned.strip()
    # Return the first meaningful word if it exists
    words = [w for w in cleaned.split() if len(w) > 1]
    if words:
        return words[0]
    return ""

def calculate_years_from_intervals(intervals: list) -> float:
    if not intervals:
        return 0.0
    intervals.sort()
    merged = []
    for interval in intervals:
        if not merged:
            merged.append(interval)
        else:
            prev_start, prev_end = merged[-1]
            if interval[0] <= prev_end:
                merged[-1] = (prev_start, max(prev_end, interval[1]))
            else:
                merged.append(interval)
    return float(sum(end - start for start, end in merged))

def analyze_experience(jd_req: JDRequirement, exp_section_text: str) -> ExperienceResult:
    req_text = jd_req.requirement_text
    jd_evidence = jd_req.evidence
    
    required_years = extract_required_years(req_text)
    target_skill = extract_target_skill(req_text)
    
    if not exp_section_text:
        return ExperienceResult(
            required_experience=jd_req,
            candidate_experience_years=0.0,
            status=ExperienceStatus.MISSING,
            evidence=None,
            explanation="No experience section text provided."
        )
        
    current_year = datetime.datetime.now().year
    
    # Simple block splitting (by double newline)
    blocks = re.split(r'\n\s*\n', exp_section_text)
    
    intervals = []
    matched_evidences = []
    
    for block in blocks:
        # Regex for YYYY - YYYY or YYYY - Present
        matches = re.finditer(r'(\d{4})\s*(?:-|to|–)\s*(\d{4}|Present|Current)', block, re.IGNORECASE)
        found_date = False
        
        for match in matches:
            start_year = int(match.group(1))
            end_str = match.group(2)
            if end_str.lower() in ['present', 'current']:
                end_year = current_year
            else:
                end_year = int(end_str)
                
            # Valid range check
            if start_year <= end_year and start_year > 1950 and end_year <= current_year + 5:
                # If a target skill is required, check if it is in this block
                if target_skill:
                    pattern = r'(?i)\b' + re.escape(target_skill) + r'\b'
                    if re.search(pattern, block):
                        intervals.append((start_year, end_year))
                        found_date = True
                else:
                    intervals.append((start_year, end_year))
                    found_date = True
                    
        if found_date:
            matched_evidences.append(block.strip())
            
    total_years = calculate_years_from_intervals(intervals)
    
    if total_years >= required_years and required_years > 0:
        status = ExperienceStatus.MATCHED
    elif total_years > 0 and total_years < required_years:
        status = ExperienceStatus.PARTIAL
    elif required_years == 0 and total_years > 0:
        status = ExperienceStatus.MATCHED
    elif not intervals:
        status = ExperienceStatus.MISSING
    else:
        status = ExperienceStatus.UNKNOWN
        
    return ExperienceResult(
        required_experience=jd_req,
        candidate_experience_years=total_years,
        status=status,
        evidence="\n\n".join(matched_evidences) if matched_evidences else None,
        explanation=f"Calculated {total_years} years. Required: {required_years} years."
    )
