import re
from typing import List, Dict, Optional
from backend.models.schemas import (
    JDRequirement, CandidateField, SkillGapResult, ExperienceResult, 
    RequirementCategory, Importance, ScoreMatchStatus, RequirementScore, 
    ScoreResult, MatchStatus, ExperienceStatus, FieldStatus
)

def _get_category_fields(fields: List[CandidateField], category: RequirementCategory) -> List[CandidateField]:
    # Map JD RequirementCategory to CandidateField categories
    mapping = {
        RequirementCategory.EDUCATION: ["Education"],
        RequirementCategory.CERTIFICATION: ["Certifications"],
        RequirementCategory.LOCATION: ["Personal"], # Location is often in personal info
        RequirementCategory.OTHER: ["Skills", "Experience", "Education", "Personal", "Certifications"] # Search everywhere
    }
    target_cats = mapping.get(category, [])
    return [f for f in fields if f.category in target_cats and f.status != FieldStatus.NOT_FOUND]

def _check_basic_match(req: JDRequirement, fields: List[CandidateField]) -> RequirementScore:
    relevant_fields = _get_category_fields(fields, req.category)
    
    if not relevant_fields:
        return RequirementScore(
            requirement=req,
            status=ScoreMatchStatus.MISSING,
            explanation=f"No validated candidate fields found for {req.category.value}.",
            evidence_ref=None,
            confidence=100.0
        )
        
    escaped_req = re.escape(req.requirement_text.lower())
    
    # Very basic substring matching for education, location, etc.
    # We do not hallucinate, we check for explicit presence.
    # To avoid part-word matching (e.g. matching "in" to "India"), we can use word boundaries if appropriate,
    # but requirement_text could be a long phrase. Let's just use substring match for non-skill categories.
    # Or better, just check if all words > 3 chars in the requirement exist in the candidate field.
    req_words = [w.lower() for w in req.requirement_text.split() if len(w) > 3]
    if not req_words:
        # Fallback to exact substring
        req_words = [req.requirement_text.lower()]
        
    best_match_field = None
    best_evidence = None
    all_words_found = False
    
    for field in relevant_fields:
        if not field.value and not field.evidence:
            continue
            
        text_to_search = f"{field.value or ''} {field.evidence or ''}".lower()
        
        # Check if all key words are in the text
        if all(w in text_to_search for w in req_words):
            all_words_found = True
            best_match_field = field
            best_evidence = field.evidence or field.value
            break
            
    if all_words_found:
        conf = 100.0
        if best_match_field and best_match_field.status == FieldStatus.AMBIGUOUS:
            conf = 50.0
        return RequirementScore(
            requirement=req,
            status=ScoreMatchStatus.MATCHED,
            explanation=f"Candidate profile contains evidence supporting {req.category.value} requirement.",
            evidence_ref=best_evidence,
            confidence=conf
        )
        
    return RequirementScore(
        requirement=req,
        status=ScoreMatchStatus.MISSING,
        explanation=f"No validated evidence found for requirement: {req.requirement_text}",
        evidence_ref=None,
        confidence=100.0
    )


def calculate_score(
    candidate_id: Optional[str],
    jd_requirements: List[JDRequirement],
    candidate_fields: List[CandidateField],
    skill_results: List[SkillGapResult],
    experience_results: List[ExperienceResult]
) -> ScoreResult:
    
    # Weighting Formula:
    # REQUIRED = 2 points
    # PREFERRED = 1 point
    # MATCHED = 100% of points, PARTIAL = 50% of points, MISSING = 0%
    
    req_scores = []
    
    total_possible = 0.0
    total_earned = 0.0
    
    matched_count = 0
    partial_count = 0
    missing_count = 0
    
    skill_map = {res.requirement.requirement_id: res for res in skill_results}
    exp_map = {res.required_experience.requirement_id: res for res in experience_results}
    
    for req in jd_requirements:
        weight = 2.0 if req.importance == Importance.REQUIRED else 1.0
        total_possible += weight
        
        req_score = None
        
        if req.category == RequirementCategory.SKILL:
            sr = skill_map.get(req.requirement_id)
            if sr:
                status = ScoreMatchStatus.MISSING
                if sr.match_status == MatchStatus.HIGH_MATCH:
                    status = ScoreMatchStatus.MATCHED
                elif sr.match_status == MatchStatus.PARTIAL_MATCH:
                    status = ScoreMatchStatus.PARTIAL
                    
                conf = 100.0
                if status == ScoreMatchStatus.MATCHED and not sr.candidate_evidence:
                    # Missing evidence for a match implies bad validation, reduce confidence
                    conf = 50.0
                
                req_score = RequirementScore(
                    requirement=req,
                    status=status,
                    explanation=sr.explanation,
                    evidence_ref=sr.candidate_evidence,
                    confidence=conf
                )
        
        elif req.category == RequirementCategory.EXPERIENCE:
            er = exp_map.get(req.requirement_id)
            if er:
                status = ScoreMatchStatus.MISSING
                conf = 100.0
                
                if er.status == ExperienceStatus.MATCHED:
                    status = ScoreMatchStatus.MATCHED
                elif er.status == ExperienceStatus.PARTIAL:
                    status = ScoreMatchStatus.PARTIAL
                elif er.status == ExperienceStatus.UNKNOWN:
                    status = ScoreMatchStatus.MISSING
                    conf = 0.0 # We have no idea, so confidence in the MISSING score is 0
                    
                req_score = RequirementScore(
                    requirement=req,
                    status=status,
                    explanation=er.explanation,
                    evidence_ref=er.evidence,
                    confidence=conf
                )
                
        # If not skill or exp, or missing from maps, evaluate basically
        if not req_score:
            req_score = _check_basic_match(req, candidate_fields)
            
        # Tally scores
        if req_score.status == ScoreMatchStatus.MATCHED:
            total_earned += weight
            matched_count += 1
        elif req_score.status == ScoreMatchStatus.PARTIAL:
            total_earned += (weight * 0.5)
            partial_count += 1
        else:
            missing_count += 1
            
        req_scores.append(req_score)
        
    fit_score = (total_earned / total_possible * 100.0) if total_possible > 0 else 0.0
    
    total_conf = sum(rs.confidence for rs in req_scores)
    confidence_score = (total_conf / len(req_scores)) if req_scores else 100.0
    
    return ScoreResult(
        candidate_id=candidate_id,
        fit_score=round(fit_score, 2),
        confidence_score=round(confidence_score, 2),
        matched_count=matched_count,
        partial_count=partial_count,
        missing_count=missing_count,
        requirement_results=req_scores,
        explanation=f"Candidate earned {total_earned} out of {total_possible} weighted points."
    )
