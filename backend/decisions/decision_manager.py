import time
import uuid
from typing import List, Optional
from database.db import get_connection, init_db
from backend.models.schemas import DecisionValue, HumanDecision

def get_candidate_decision(candidate_id: str, resume_version_id: str) -> HumanDecision:
    """
    Retrieves the latest decision for a specific candidate and resume version.
    Returns PENDING if no decision exists.
    """
    # Ensure DB is initialized
    init_db()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM decisions WHERE candidate_id = ? AND resume_version_id = ? ORDER BY decided_at DESC LIMIT 1",
            (candidate_id, resume_version_id)
        )
        row = cursor.fetchone()
        
        if row:
            return HumanDecision(
                decision_id=row["decision_id"],
                candidate_id=row["candidate_id"],
                resume_version_id=row["resume_version_id"],
                decision=DecisionValue(row["decision"]),
                decided_at=row["decided_at"]
            )
            
    # Default is PENDING if not found
    return HumanDecision(
        decision_id="pending-" + str(uuid.uuid4()),
        candidate_id=candidate_id,
        resume_version_id=resume_version_id,
        decision=DecisionValue.PENDING,
        decided_at=time.time()
    )

def record_decision(
    candidate_id: str, 
    resume_version_id: str, 
    decision: DecisionValue,
    valid_candidate_ids: List[str],
    valid_version_ids: List[str]
) -> HumanDecision:
    """
    Records a human decision. Validates candidate and version exist.
    """
    if candidate_id not in valid_candidate_ids:
        raise ValueError(f"Invalid candidate: {candidate_id}")
        
    if resume_version_id not in valid_version_ids:
        raise ValueError(f"Invalid resume version: {resume_version_id}")
        
    # Idempotency check: if the latest decision is exactly the same, return it without duplicating
    latest = get_candidate_decision(candidate_id, resume_version_id)
    if latest.decision == decision:
        return latest
        
    decision_id = str(uuid.uuid4())
    decided_at = time.time()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO decisions (decision_id, candidate_id, resume_version_id, decision, decided_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (decision_id, candidate_id, resume_version_id, decision.value, decided_at)
        )
        conn.commit()
        
    return HumanDecision(
        decision_id=decision_id,
        candidate_id=candidate_id,
        resume_version_id=resume_version_id,
        decision=decision,
        decided_at=decided_at
    )

def get_candidates_by_decision(decision: DecisionValue) -> List[HumanDecision]:
    """
    Retrieves a list of decisions matching the specified value (ACCEPTED/REJECTED).
    Only returns the LATEST decision for each candidate/version pair if there are multiple.
    """
    init_db()
    results = []
    with get_connection() as conn:
        cursor = conn.cursor()
        # Use a subquery to get the latest decision per candidate and version
        cursor.execute(
            """
            SELECT d1.*
            FROM decisions d1
            INNER JOIN (
                SELECT candidate_id, resume_version_id, MAX(decided_at) as max_time
                FROM decisions
                GROUP BY candidate_id, resume_version_id
            ) d2 ON d1.candidate_id = d2.candidate_id 
                 AND d1.resume_version_id = d2.resume_version_id 
                 AND d1.decided_at = d2.max_time
            WHERE d1.decision = ?
            ORDER BY d1.decided_at DESC
            """,
            (decision.value,)
        )
        for row in cursor.fetchall():
            results.append(HumanDecision(
                decision_id=row["decision_id"],
                candidate_id=row["candidate_id"],
                resume_version_id=row["resume_version_id"],
                decision=DecisionValue(row["decision"]),
                decided_at=row["decided_at"]
            ))
            
    return results

def get_decision_history(candidate_id: str, resume_version_id: str) -> List[HumanDecision]:
    """
    Retrieves the full decision history for a candidate/version pair.
    """
    init_db()
    results = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM decisions WHERE candidate_id = ? AND resume_version_id = ? ORDER BY decided_at ASC",
            (candidate_id, resume_version_id)
        )
        for row in cursor.fetchall():
            results.append(HumanDecision(
                decision_id=row["decision_id"],
                candidate_id=row["candidate_id"],
                resume_version_id=row["resume_version_id"],
                decision=DecisionValue(row["decision"]),
                decided_at=row["decided_at"]
            ))
    return results
