import re
from backend.models.schemas import JDRequirement, CandidateField, FieldStatus, SkillGapResult, MatchStatus

def analyze_skill(jd_req: JDRequirement, candidate_skills_field: CandidateField) -> SkillGapResult:
    req_text = jd_req.requirement_text.strip()
    jd_evidence = jd_req.evidence
    
    if not candidate_skills_field or candidate_skills_field.status != FieldStatus.FOUND or not candidate_skills_field.value:
        return SkillGapResult(
            requirement=jd_req,
            match_status=MatchStatus.SKILL_GAP,
            candidate_value=None,
            candidate_evidence=None,
            jd_evidence=jd_evidence,
            explanation="Candidate has no skills listed or skills section was not found."
        )
        
    cand_val = candidate_skills_field.value
    cand_ev = candidate_skills_field.evidence
    
    # Strictly deterministic match using word boundaries to avoid Java matching JavaScript
    # Escape the requirement text to be safe in regex
    escaped_req = re.escape(req_text)
    
    # We use \b for word boundaries. Note that if the req has punctuation, \b might act weirdly.
    # For now, simple \b match is standard.
    pattern = r'(?i)\b' + escaped_req + r'\b'
    
    if re.search(pattern, cand_val) or (cand_ev and re.search(pattern, cand_ev)):
        return SkillGapResult(
            requirement=jd_req,
            match_status=MatchStatus.HIGH_MATCH,
            candidate_value=cand_val,
            candidate_evidence=cand_ev,
            jd_evidence=jd_evidence,
            explanation=f"Exact skill '{req_text}' found in candidate skills."
        )
        
    # If we wanted deterministic partial match, we could check for substrings without word boundaries,
    # but the prompt warns: Java != JavaScript. So we strictly avoid that.
    # If the user wants a PARTIAL match, we would need an explicit alias dictionary. 
    # Since we shouldn't invent semantic relationships, we return SKILL_GAP.
    return SkillGapResult(
        requirement=jd_req,
        match_status=MatchStatus.SKILL_GAP,
        candidate_value=cand_val,
        candidate_evidence=cand_ev,
        jd_evidence=jd_evidence,
        explanation=f"Skill '{req_text}' not found in candidate skills."
    )
