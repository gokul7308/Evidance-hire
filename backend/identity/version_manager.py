import time
from typing import List, Dict
from backend.models.schemas import CandidateField, FieldStatus, ResumeVersion, VersionComparison

def add_resume_version(
    candidate_id: str,
    upload_id: str,
    content_hash: str,
    fields: List[CandidateField],
    existing_versions: List[ResumeVersion]
) -> ResumeVersion:
    """
    Creates a new resume version for the candidate.
    Sets all existing versions' is_current to False.
    """
    # Filter versions for this specific candidate
    cand_versions = [v for v in existing_versions if v.candidate_id == candidate_id]
    
    next_version_num = 1
    if cand_versions:
        next_version_num = max(v.version_number for v in cand_versions) + 1
        
        # Mark all old versions as not current
        for v in cand_versions:
            v.is_current = False
            
    new_version = ResumeVersion(
        resume_version_id=f"{candidate_id}-v{next_version_num}",
        candidate_id=candidate_id,
        upload_id=upload_id,
        version_number=next_version_num,
        content_hash=content_hash,
        created_at=time.time(),
        is_current=True,
        fields=fields
    )
    
    existing_versions.append(new_version)
    return new_version

def compare_versions(v_old: ResumeVersion, v_new: ResumeVersion) -> VersionComparison:
    """
    Deterministically compares two resume versions to find added, removed, changed, and unchanged fields.
    """
    comparison = VersionComparison()
    
    old_fields_map = {f.field_id: f for f in v_old.fields}
    new_fields_map = {f.field_id: f for f in v_new.fields}
    
    all_field_ids = set(old_fields_map.keys()).union(set(new_fields_map.keys()))
    
    for f_id in all_field_ids:
        f_old = old_fields_map.get(f_id)
        f_new = new_fields_map.get(f_id)
        
        old_is_present = f_old and f_old.status == FieldStatus.FOUND and f_old.value
        new_is_present = f_new and f_new.status == FieldStatus.FOUND and f_new.value
        
        if not old_is_present and new_is_present:
            comparison.added.append(f_new)
        elif old_is_present and not new_is_present:
            comparison.removed.append(f_old)
        elif old_is_present and new_is_present:
            # Check if values or evidence changed
            # Note: We consider a change only if the actual value or evidence string changed
            # (ignoring minor whitespace differences if they were already normalized, but here we do exact match)
            if f_old.value != f_new.value or f_old.evidence != f_new.evidence:
                comparison.changed.append({"old": f_old, "new": f_new})
            else:
                comparison.unchanged.append(f_new)
        else:
            # Both not present or ambiguous
            # Can be considered unchanged in their absence, but typically we only record actual fields
            # We will put them in unchanged for completeness, since they didn't 'change'
            if f_new:
                comparison.unchanged.append(f_new)
            elif f_old:
                comparison.unchanged.append(f_old)
                
    # Sort for deterministic output
    comparison.added.sort(key=lambda x: x.field_id)
    comparison.removed.sort(key=lambda x: x.field_id)
    comparison.changed.sort(key=lambda x: x["new"].field_id)
    comparison.unchanged.sort(key=lambda x: x.field_id)
    
    return comparison
