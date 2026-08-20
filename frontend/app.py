import streamlit as st
import os
import tempfile
import time
import uuid

# Backend imports
from database.db import init_db
from backend.ingestion.file_validator import validate_file
from backend.ingestion.extractor import extract_file
from backend.parsing.segmenter import segment_resume
from backend.parsing.field_parser import parse_fields
from backend.validation.evidence_validator import validate_profile
from backend.identity.duplicate_detector import detect_duplicate
from backend.identity.version_manager import add_resume_version, compare_versions
from backend.parsing.jd_parser import parse_jd
from backend.analysis.skill_analyzer import analyze_skill
from backend.analysis.experience_analyzer import analyze_experience
from backend.scoring.scorer import calculate_score
from backend.scoring.ranker import rank_candidates
from backend.decisions.decision_manager import (
    get_candidate_decision,
    record_decision,
    get_candidates_by_decision
)
from backend.models.schemas import (
    DuplicateStatus, ExtractionStatus, FieldStatus, DecisionValue, ScoreMatchStatus, RequirementCategory, CandidateRankingInput
)

st.set_page_config(page_title="EvidenceHire", page_icon="📄", layout="wide")

# Initialize state
if "candidates_db" not in st.session_state:
    st.session_state.candidates_db = []
if "versions_db" not in st.session_state:
    st.session_state.versions_db = []
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = []
if "jd_requirements" not in st.session_state:
    st.session_state.jd_requirements = []
if "ranked_candidates" not in st.session_state:
    st.session_state.ranked_candidates = []

def init():
    init_db()

def get_status_icon(status: str) -> str:
    mapping = {
        "FOUND": "🟢",
        "NOT_FOUND": "🔴",
        "AMBIGUOUS": "🟡",
        "MATCHED": "✓",
        "PARTIAL": "~",
        "MISSING": "✗",
        "HIGH_MATCH": "✓",
        "SKILL_GAP": "✗",
        "PENDING": "⏳",
        "ACCEPTED": "✅",
        "REJECTED": "❌"
    }
    return mapping.get(status, "🔹")

def page_dashboard():
    st.title("Dashboard")
    
    total_candidates = len(st.session_state.candidates_db)
    accepted = len(get_candidates_by_decision(DecisionValue.ACCEPTED))
    rejected = len(get_candidates_by_decision(DecisionValue.REJECTED))
    pending = total_candidates - accepted - rejected
    
    # Duplicates can be inferred from versions > 1
    duplicates = sum(1 for c in st.session_state.candidates_db if len([v for v in st.session_state.versions_db if v.candidate_id == c]) > 1)
    
    st.markdown("### Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Candidates", total_candidates)
    with col2:
        st.metric("Pending Review", max(0, pending))
    with col3:
        st.metric("Accepted", accepted)
    with col4:
        st.metric("Rejected", rejected)
    with col5:
        st.metric("Duplicate Uploads", duplicates)
        
    st.markdown("---")
    if total_candidates == 0:
        st.info("No candidates yet. Upload a resume to begin screening.")

def run_analysis_pipeline(resume_files, jd_file):
    temp_dir = tempfile.mkdtemp()
    
    # 1. JD Parsing
    jd_reqs = []
    if jd_file is not None:
        jd_path = os.path.join(temp_dir, "jd.txt")
        with open(jd_path, "wb") as f:
            f.write(jd_file.getvalue())
        with open(jd_path, "r") as f:
            jd_text = f.read()
        jd_reqs = parse_jd(jd_text)
        st.session_state.jd_requirements = jd_reqs
    else:
        jd_reqs = st.session_state.jd_requirements

    results = []
    ranking_inputs = []

    for file_obj in resume_files:
        path = os.path.join(temp_dir, file_obj.name)
        with open(path, "wb") as f:
            f.write(file_obj.getvalue())
            
        is_valid, ext, err = validate_file(path)
        if not is_valid:
            results.append({"filename": file_obj.name, "valid": False, "error": err, "ext": ext})
            continue
            
        ext_res = extract_file(path)
        if ext_res.status != ExtractionStatus.SUCCESS:
            results.append({"filename": file_obj.name, "valid": False, "error": ext_res.error_message, "ext": ext})
            continue
            
        sections = segment_resume(ext_res.raw_text)
        fields = parse_fields(sections)
        validations = validate_profile(fields, ext_res.raw_text, sections)
        valid_fields = [f for f, v in zip(fields, validations) if v.is_valid]
        
        dup_res = detect_duplicate(path, ext_res.raw_text, valid_fields, st.session_state.candidates_db)
        
        if dup_res.status == DuplicateStatus.EXACT_DUPLICATE:
            results.append({
                "filename": file_obj.name, 
                "valid": True,
                "ext": ext,
                "duplicate": True, 
                "duplicate_status": dup_res.status, 
                "message": "⚠ ALREADY IT EXIST",
                "candidate_id": dup_res.existing_candidate_id
            })
            continue
            
        candidate_id = ""
        is_new_candidate = False
        if dup_res.status == DuplicateStatus.SAME_CANDIDATE and dup_res.existing_candidate_id:
            candidate_id = dup_res.existing_candidate_id
        else:
            candidate_id = "C" + str(uuid.uuid4())[:8].upper()
            st.session_state.candidates_db.append(candidate_id)
            is_new_candidate = True
            
        new_version = add_resume_version(
            candidate_id, 
            "upload-" + str(uuid.uuid4()), 
            dup_res.content_hash, 
            valid_fields, 
            st.session_state.versions_db
        )
        
        name_field = next((f for f in valid_fields if f.field_id == "name"), None)
        candidate_name = name_field.value if name_field and name_field.status == FieldStatus.FOUND else "Unknown Candidate"
        
        skill_res = []
        exp_res = []
        skills_field = next((f for f in valid_fields if f.field_id.lower() == "skills"), None)
        exp_field = next((f for f in valid_fields if f.field_id.lower() == "experience"), None)
        exp_text = exp_field.evidence if exp_field and exp_field.status == FieldStatus.FOUND else ""
        
        for req in jd_reqs:
            if req.category == RequirementCategory.SKILL:
                skill_res.append(analyze_skill(req, skills_field))
            elif req.category == RequirementCategory.EXPERIENCE:
                exp_res.append(analyze_experience(req, exp_text))
        
        score_res = calculate_score(candidate_id, jd_reqs, valid_fields, skill_res, exp_res)
        
        r_input = CandidateRankingInput(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            resume_version=new_version.version_number,
            is_current=new_version.is_current,
            score_result=score_res
        )
        ranking_inputs.append(r_input)
        
        results.append({
            "filename": file_obj.name,
            "valid": True,
            "ext": ext,
            "duplicate": False,
            "duplicate_status": dup_res.status,
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "version": new_version,
            "valid_fields": valid_fields,
            "score_result": score_res,
            "skill_res": skill_res,
            "exp_res": exp_res
        })
        
    st.session_state.analysis_results = results
    
    if ranking_inputs:
        st.session_state.ranked_candidates = rank_candidates(ranking_inputs)

def page_resume_screening():
    st.title("Resume Screening")
    st.markdown("Upload resumes and job description")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Resume Upload")
        resume_files = st.file_uploader("Drag & Drop Resume (PDF / DOCX)", type=["pdf", "docx"], accept_multiple_files=True)
        
    with col2:
        st.subheader("Job Description")
        jd_file = st.file_uploader("Upload JD (TXT)", type=["txt"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("ANALYZE RESUMES", type="primary", use_container_width=True):
        if resume_files and (jd_file or st.session_state.jd_requirements):
            with st.status("Analyzing resumes...", expanded=True) as status:
                st.write("✓ File Validation")
                st.write("✓ Extraction")
                st.write("✓ Section Parsing")
                st.write("✓ Evidence Validation")
                st.write("✓ Duplicate Detection")
                st.write("✓ Candidate Analysis")
                st.write("✓ JD Matching")
                st.write("✓ Scoring")
                run_analysis_pipeline(resume_files, jd_file)
                status.update(label="Analysis complete!", state="complete", expanded=False)
        else:
            st.warning("Please upload both resumes and a Job Description.")
            
    if st.session_state.analysis_results:
        st.markdown("---")
        st.header("Analysis Results")
            
        for res in st.session_state.analysis_results:
            st.markdown(f"### File: {res['filename']}")
            
            # Error / Validation States
            if not res['valid']:
                if "no extractable text layer" in res['error']:
                    st.error(f"✗ UNKNOWN — No extractable text layer detected.")
                else:
                    st.error(f"✗ Unsupported file or error: {res['error']}")
                continue
                
            # Duplicate Warning
            if res.get('duplicate'):
                st.error(f"**⚠ ALREADY IT EXIST**\n\nThis resume already exists. Existing Candidate ID: {res['candidate_id']}")
                continue
            elif res['duplicate_status'] == DuplicateStatus.SAME_CANDIDATE:
                st.info(f"**Same Candidate Detected**\n\nResume Version: v{res['version'].version_number}")
            elif res['duplicate_status'] == DuplicateStatus.POSSIBLE_SAME_CANDIDATE:
                st.warning("Possible existing candidate detected based on identity signals.")
                
            # Candidate Header
            st.markdown("---")
            v = res['version']
            score = res['score_result']
            decision = get_candidate_decision(res['candidate_id'], v.resume_version_id)
            decision_val = decision.decision.value
            
            hcol1, hcol2, hcol3 = st.columns([2, 1, 1])
            with hcol1:
                st.subheader(res['candidate_name'])
                st.caption(f"Candidate ID: {res['candidate_id']} | Version: v{v.version_number}")
            with hcol2:
                st.metric("Fit Score", f"{score.fit_score:.1f} / 100")
            with hcol3:
                st.metric("Confidence", f"{score.confidence_score:.1f} / 100")
                
            st.markdown(f"**Decision:** {get_status_icon(decision_val)} {decision_val}")
            
            # Decision Buttons
            dcol1, dcol2, dcol3 = st.columns([1, 1, 4])
            with dcol1:
                if st.button("ACCEPT", type="primary", key=f"accept_{res['candidate_id']}_{v.resume_version_id}"):
                    record_decision(res['candidate_id'], v.resume_version_id, DecisionValue.ACCEPTED, st.session_state.candidates_db, [v_obj.resume_version_id for v_obj in st.session_state.versions_db])
                    st.rerun()
            with dcol2:
                if st.button("REJECT", key=f"reject_{res['candidate_id']}_{v.resume_version_id}"):
                    record_decision(res['candidate_id'], v.resume_version_id, DecisionValue.REJECTED, st.session_state.candidates_db, [v_obj.resume_version_id for v_obj in st.session_state.versions_db])
                    st.rerun()
                    
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Candidate Profile
            st.markdown("### Candidate Profile")
            pcol1, pcol2 = st.columns(2)
            
            personal_cats = ["Personal"]
            edu_cats = ["Education", "Certifications"]
            exp_cats = ["Experience"]
            
            with pcol1:
                st.markdown("**PERSONAL**")
                for f in res['valid_fields']:
                    if f.category in personal_cats:
                        st.markdown(f"**{f.field_id.title()}:** {f.value if f.status == FieldStatus.FOUND else get_status_icon(f.status.value) + ' ' + f.status.value}")
                        
            with pcol2:
                st.markdown("**EDUCATION & EXPERIENCE**")
                for f in res['valid_fields']:
                    if f.category in edu_cats + exp_cats:
                        st.markdown(f"**{f.field_id.title()}:** {f.value if f.status == FieldStatus.FOUND else get_status_icon(f.status.value) + ' ' + f.status.value}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Match Summary
            st.markdown("### Match Summary")
            high_matches, partials, gaps, missing = [], [], [], []
            for sr in score.requirement_results:
                if sr.status == ScoreMatchStatus.MATCHED: high_matches.append(sr)
                elif sr.status == ScoreMatchStatus.PARTIAL: partials.append(sr)
                elif sr.status == ScoreMatchStatus.MISSING: 
                    if sr.requirement.category == RequirementCategory.SKILL: gaps.append(sr)
                    else: missing.append(sr)
                    
            scol1, scol2, scol3, scol4 = st.columns(4)
            scol1.metric("High Matches", len(high_matches))
            scol2.metric("Partial", len(partials))
            scol3.metric("Skill Gaps", len(gaps))
            scol4.metric("Missing", len(missing))
            
            # Skills Display
            sk1, sk2, sk3 = st.columns(3)
            with sk1:
                st.markdown("#### HIGH MATCHES")
                for hm in [h for h in high_matches if h.requirement.category == RequirementCategory.SKILL]:
                    st.markdown(f"✓ {hm.requirement.requirement_text}")
            with sk2:
                st.markdown("#### PARTIAL MATCHES")
                for pm in [p for p in partials if p.requirement.category == RequirementCategory.SKILL]:
                    st.markdown(f"~ {pm.requirement.requirement_text}")
            with sk3:
                st.markdown("#### SKILL GAPS")
                for gm in gaps:
                    st.markdown(f"✗ {gm.requirement.requirement_text}")
                    
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Experience Match
            exp_res_items = res['exp_res']
            if exp_res_items:
                st.markdown("### Experience Match")
                for er in exp_res_items:
                    st.markdown(f"**Required:** {er.required_experience.requirement_text}")
                    st.markdown(f"**Candidate:** {er.candidate_experience_years:.1f} years")
                    st.markdown(f"**Status:** {get_status_icon(er.status.value)} {er.status.value}")
                    if er.evidence:
                        st.info(f'"{er.evidence}"')
                    st.markdown("<br>", unsafe_allow_html=True)
            
            # JD Requirements Table
            st.markdown("### JD Requirements")
            req_data = []
            for sr in score.requirement_results:
                req_data.append({
                    "Requirement": sr.requirement.requirement_text,
                    "Status": sr.status.value,
                    "Evidence": sr.evidence_ref if sr.evidence_ref else sr.explanation
                })
            st.dataframe(req_data, use_container_width=True)
            
            # Evidence Viewer
            st.markdown("### Evidence Viewer")
            for f in res['valid_fields']:
                if f.status == FieldStatus.FOUND:
                    with st.expander(f"{f.field_id.title()} - {get_status_icon('FOUND')} FOUND"):
                        st.markdown(f"**Value:** {f.value}")
                        st.markdown(f"**Evidence:**\n\n> {f.evidence}")
                        st.markdown(f"**Source Section:** {f.source_section}")
                        
            st.markdown("---")

def page_candidates():
    st.title("Ranked Candidates")
    if not st.session_state.ranked_candidates:
        st.info("No candidates available. Please run analysis first.")
        return
        
    for rc in st.session_state.ranked_candidates:
        versions = sorted([v for v in st.session_state.versions_db if v.candidate_id == rc.candidate_id], key=lambda x: x.version_number)
        current_v = versions[-1] if versions else None
        
        decision = get_candidate_decision(rc.candidate_id, current_v.resume_version_id if current_v else "").decision.value
        
        with st.container(border=True):
            rcol1, rcol2, rcol3 = st.columns([3, 1, 1])
            with rcol1:
                st.markdown(f"### #{rc.rank} {rc.candidate_name}")
                st.caption(f"Candidate ID: {rc.candidate_id} | Resume v{rc.resume_version}")
                st.markdown(f"**Decision:** {get_status_icon(decision)} {decision}")
            with rcol2:
                st.metric("Fit Score", f"{rc.fit_score:.1f}")
            with rcol3:
                st.metric("Confidence", f"{rc.confidence_score:.1f}")

def page_accepted():
    st.title("Accepted Candidates")
    accepted = get_candidates_by_decision(DecisionValue.ACCEPTED)
    if not accepted:
        st.info("No accepted candidates yet.")
        return
        
    for a in accepted:
        with st.container(border=True):
            st.markdown(f"#### Candidate ID: {a.candidate_id}")
            st.markdown(f"**Resume Version:** {a.resume_version_id}")
            st.markdown(f"**Decision:** ✅ {a.decision.value}")
            st.caption(f"Decided at: {a.decided_at}")

def page_rejected():
    st.title("Rejected Candidates")
    rejected = get_candidates_by_decision(DecisionValue.REJECTED)
    if not rejected:
        st.info("No rejected candidates yet.")
        return
        
    for r in rejected:
        with st.container(border=True):
            st.markdown(f"#### Candidate ID: {r.candidate_id}")
            st.markdown(f"**Resume Version:** {r.resume_version_id}")
            st.markdown(f"**Decision:** ❌ {r.decision.value}")
            st.caption(f"Decided at: {r.decided_at}")

def page_resume_history():
    st.title("Resume History")
    cands = set(v.candidate_id for v in st.session_state.versions_db)
    if not cands:
        st.info("No history available. Upload resumes to track version history.")
        return
        
    for c in cands:
        st.markdown(f"### Candidate: {c}")
        cand_versions = sorted([v for v in st.session_state.versions_db if v.candidate_id == c], key=lambda x: x.version_number)
        
        for v in cand_versions:
            st.markdown(f"**v{v.version_number}** {'(Current)' if v.is_current else ''}")
            
        if len(cand_versions) >= 2:
            comp = compare_versions(cand_versions[-2], cand_versions[-1])
            if comp.added or comp.removed or comp.changed:
                with st.expander(f"Changes from v{cand_versions[-2].version_number} to v{cand_versions[-1].version_number}"):
                    if comp.added:
                        st.markdown("**ADDED**")
                        for f in comp.added: st.markdown(f"+ {f.field_id}: {f.value}")
                    if comp.removed:
                        st.markdown("**REMOVED**")
                        for f in comp.removed: st.markdown(f"- {f.field_id}: {f.value}")
                    if comp.changed:
                        st.markdown("**CHANGED**")
                        for c_obj in comp.changed: st.markdown(f"~ {c_obj['old'].field_id}: {c_obj['old'].value} → {c_obj['new'].value}")
        st.markdown("---")

def main():
    init()
    
    st.sidebar.title("Navigation")
    pages = {
        "🏠 Dashboard": page_dashboard,
        "📄 Resume Screening": page_resume_screening,
        "👥 Candidates": page_candidates,
        "✅ Accepted Candidates": page_accepted,
        "❌ Rejected Candidates": page_rejected,
        "🕒 Resume History": page_resume_history
    }
    
    selection = st.sidebar.radio("Go to", list(pages.keys()), label_visibility="collapsed")
    
    # Run selected page
    pages[selection]()

if __name__ == "__main__":
    main()
