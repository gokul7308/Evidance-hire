from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

class ExtractionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"

@dataclass
class ExtractionResult:
    status: ExtractionStatus
    file_type: str
    raw_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

@dataclass
class Section:
    section_name: str
    section_id: str
    text: str
    start_position: int
    end_position: int
    heading_text: str

class FieldStatus(str, Enum):
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"

@dataclass
class CandidateField:
    field_id: str
    category: str
    status: FieldStatus
    value: Optional[str] = None
    evidence: Optional[str] = None
    source_section: Optional[str] = None

@dataclass
class ValidationResult:
    field_id: str
    status: FieldStatus
    value: Optional[str]
    evidence: Optional[str]
    source_section: Optional[str]
    is_valid: bool
    validation_message: str

class DuplicateStatus(str, Enum):
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    SAME_CANDIDATE = "SAME_CANDIDATE"
    POSSIBLE_SAME_CANDIDATE = "POSSIBLE_SAME_CANDIDATE"
    NEW_CANDIDATE = "NEW_CANDIDATE"

@dataclass
class DuplicateResult:
    status: DuplicateStatus
    message: str
    existing_candidate_id: Optional[str] = None
    file_hash: str = ""
    content_hash: str = ""

@dataclass
class ResumeVersion:
    resume_version_id: str
    candidate_id: str
    upload_id: str
    version_number: int
    content_hash: str
    created_at: float
    is_current: bool
    fields: List[CandidateField] = field(default_factory=list)

@dataclass
class VersionComparison:
    added: List[CandidateField] = field(default_factory=list)
    removed: List[CandidateField] = field(default_factory=list)
    changed: List[Dict[str, CandidateField]] = field(default_factory=list)  # e.g. [{"old": f1, "new": f2}]
    unchanged: List[CandidateField] = field(default_factory=list)

class RequirementCategory(str, Enum):
    SKILL = "SKILL"
    EDUCATION = "EDUCATION"
    EXPERIENCE = "EXPERIENCE"
    CERTIFICATION = "CERTIFICATION"
    LOCATION = "LOCATION"
    OTHER = "OTHER"

class Importance(str, Enum):
    REQUIRED = "REQUIRED"
    PREFERRED = "PREFERRED"

@dataclass
class JDRequirement:
    requirement_id: str
    category: RequirementCategory
    requirement_text: str
    importance: Importance
    evidence: str
    source_line: int

class MatchStatus(str, Enum):
    HIGH_MATCH = "HIGH_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    SKILL_GAP = "SKILL_GAP"

class ExperienceStatus(str, Enum):
    MATCHED = "MATCHED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"

@dataclass
class SkillGapResult:
    requirement: JDRequirement
    match_status: MatchStatus
    candidate_value: Optional[str]
    candidate_evidence: Optional[str]
    jd_evidence: str
    explanation: str

@dataclass
class ExperienceResult:
    required_experience: JDRequirement
    candidate_experience_years: float
    status: ExperienceStatus
    evidence: Optional[str]
    explanation: str
