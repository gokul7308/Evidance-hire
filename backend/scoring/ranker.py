from typing import List, Dict
from backend.models.schemas import CandidateRankingInput, RankedCandidate, ScoreMatchStatus, RequirementCategory

def rank_candidates(candidates: List[CandidateRankingInput]) -> List[RankedCandidate]:
    if not candidates:
        return []
        
    # 1. Filter to current/latest valid version per candidate
    # Group by candidate_id
    candidate_groups: Dict[str, List[CandidateRankingInput]] = {}
    for c in candidates:
        if c.candidate_id not in candidate_groups:
            candidate_groups[c.candidate_id] = []
        candidate_groups[c.candidate_id].append(c)
        
    latest_candidates = []
    for cid, versions in candidate_groups.items():
        current_versions = [v for v in versions if v.is_current]
        if current_versions:
            # Should normally only be one current version, take the one with highest version number just in case
            selected = max(current_versions, key=lambda x: x.resume_version)
        else:
            # If no current flagged version, take the highest version number
            selected = max(versions, key=lambda x: x.resume_version)
        latest_candidates.append(selected)
        
    # 2. Sort deterministically
    # Sort criteria: 
    # 1. Higher fit_score (descending) -> -x.fit_score
    # 2. Higher confidence_score (descending) -> -x.confidence_score
    # 3. Higher matched_count (descending) -> -x.matched_count
    # 4. Lower missing_count (ascending) -> x.missing_count
    # 5. Stable candidate_id (ascending) -> x.candidate_id
    
    sorted_candidates = sorted(
        latest_candidates,
        key=lambda x: (
            -x.score_result.fit_score,
            -x.score_result.confidence_score,
            -x.score_result.matched_count,
            x.score_result.missing_count,
            x.candidate_id
        )
    )
    
    # 3. Map to RankedCandidate
    ranked_results = []
    for rank_idx, c in enumerate(sorted_candidates, start=1):
        high_matches = []
        partial_matches = []
        skill_gaps = []
        experience_match = "MISSING" # Default if not evaluated
        
        # Populate display lists
        for req_res in c.score_result.requirement_results:
            req_text = req_res.requirement.requirement_text
            cat = req_res.requirement.category
            
            if cat == RequirementCategory.SKILL:
                if req_res.status == ScoreMatchStatus.MATCHED:
                    high_matches.append(req_text)
                elif req_res.status == ScoreMatchStatus.PARTIAL:
                    partial_matches.append(req_text)
                elif req_res.status == ScoreMatchStatus.MISSING:
                    skill_gaps.append(req_text)
            elif cat == RequirementCategory.EXPERIENCE:
                experience_match = req_res.status.value
                
        ranked_results.append(RankedCandidate(
            rank=rank_idx,
            candidate_id=c.candidate_id,
            candidate_name=c.candidate_name,
            resume_version=c.resume_version,
            fit_score=c.score_result.fit_score,
            confidence_score=c.score_result.confidence_score,
            matched_count=c.score_result.matched_count,
            partial_count=c.score_result.partial_count,
            missing_count=c.score_result.missing_count,
            high_matches=high_matches,
            partial_matches=partial_matches,
            skill_gaps=skill_gaps,
            experience_match=experience_match
        ))
        
    return ranked_results
