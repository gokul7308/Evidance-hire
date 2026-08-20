EvidenceHire

Hallucination-Safe, Duplicate-Aware Resume Screening Agent

EvidenceHire is an evidence-backed resume screening prototype designed to analyze resumes against job descriptions while preventing unsupported candidate claims.

The core principle is:

NO EVIDENCE → NO CLAIM

The system extracts candidate information deterministically, validates every claim against resume evidence, identifies duplicate and updated resumes, analyzes experience and skill gaps, ranks candidates by fit, and leaves the final Accept/Reject decision to a human recruiter.

⸻

🚀 Key Features

📄 Resume Processing

* PDF resume support
* DOCX resume support
* File validation
* Corrupted-file handling
* Empty-file handling
* Scanned/image-only PDF detection
* Deterministic text extraction
* Source resume is never modified

🧩 Resume Section Segmentation

Recognizes controlled sections such as:

* Contact
* Summary
* Objective
* Education
* Experience
* Work Experience
* Skills
* Certifications
* Projects
* Achievements
* Languages
* Location

The section parser uses a fixed allowlist rather than allowing an LLM to invent section categories.

⸻

🛡️ Hallucination-Safe Candidate Parsing

EvidenceHire does not allow unsupported candidate information to become a claim.

Supported field categories include:

* Full Name
* Email
* Phone
* LinkedIn / Portfolio
* Highest Degree
* Institution
* Graduation Year
* Most Recent Job
* Location
* Skills
* Certifications
* Projects

Each extracted field contains:

field_id
category
status
value
evidence
source_section
confidence

Possible statuses:

FOUND
NOT_FOUND
AMBIGUOUS
UNKNOWN

Core rule

No Evidence
     ↓
No Claim

If information is missing, the system does not guess.

⸻

🔄 Duplicate Resume Detection

EvidenceHire does not rely on the filename alone.

It can use:

* SHA-256 file hash
* Normalized resume-content hash
* Email
* Phone
* LinkedIn / Portfolio
* Name + Institution
* Name + Recent Company

Duplicate states include:

EXACT_DUPLICATE
SAME_CANDIDATE
POSSIBLE_SAME_CANDIDATE
NEW_CANDIDATE

If an identical resume is uploaded again, the system should display:

Already it exist

The duplicate upload should not create another candidate.

Upload history is retained for traceability.

⸻

🔄 Resume Version Tracking

If an existing candidate uploads an updated resume, EvidenceHire checks for changes instead of blindly discarding the upload.

Example:

John Smith
v1
Python
Java
v2
Python
Java
Docker
AWS

The system can identify:

Same Candidate
Resume Version: v2
Updates:
+ Docker
+ AWS

Every reported update must be supported by evidence from the new resume.

⸻

🎯 Job Description Matching

EvidenceHire parses explicitly stated JD requirements such as:

* Required skills
* Preferred skills
* Education
* Experience
* Certifications
* Location
* Other explicit requirements

Requirements are represented with:

requirement_id
category
requirement_text
importance
evidence

Importance:

REQUIRED
PREFERRED

⸻

📊 Candidate Scoring

Candidates are evaluated using deterministic scoring.

Each requirement receives:

MATCHED
PARTIAL
MISSING

Every match result includes:

Requirement
Match Status
Explanation
Evidence Reference
Confidence

The same:

Resume + Job Description

must produce the same:

Field Results
Fit Score
Match Results
Ranking

⸻

🧠 Confidence Score

EvidenceHire provides a deterministic confidence score to improve transparency and trust.

The score uses factors such as:

* Evidence quality
* Parser certainty
* Extraction quality
* Recognized source section
* Conflicting information
* Evidence validation

Recommended scale:

0–100

Example interpretation:

90–100 → Very High
75–89  → High
50–74  → Medium
25–49  → Low
0–24   → Very Low

Confidence does not override missing evidence.

A high confidence score can never turn an unsupported claim into a valid claim.

⸻

💼 Experience Analysis

EvidenceHire checks explicit experience information from resumes.

It can analyze:

* Employment dates
* Start/end years
* Role duration
* Overlapping employment
* JD experience requirements
* Skill-specific experience evidence

The system must not assume that the entire duration of employment represents experience with every skill.

Example:

JD:
3+ years Python experience
Resume:
Python Developer
2022–2025
Result:
Experience Requirement → MATCHED

The calculation must be deterministic and evidence-backed.

⸻

🧠 Skill Gap Analysis

The system compares candidate skills against JD requirements.

Example:

JD:
Python
Java
React
Docker
AWS
Resume:
Python
Java
SQL

Result:

Python → HIGH MATCH
Java   → HIGH MATCH
React  → SKILL GAP
Docker → SKILL GAP
AWS    → SKILL GAP
SQL    → Additional Skill

EvidenceHire does not automatically treat related technologies as identical.

For example:

Java ≠ JavaScript
React ≠ Angular
AWS ≠ Azure

unless an explicit matching rule is defined.

⸻

🏆 Candidate Ranking

When multiple resumes are analyzed against a JD, candidates are ranked:

Highest Match
      ↓
      ↓
Lowest Match

Candidate results can include:

Rank
Candidate Name
Fit Score
Confidence
High Matches
Partial Matches
Skill Gaps
Experience Match
Resume Version
Duplicate Status

Important

Ranking is a recommendation.

It is not an automatic hiring decision.

⸻

👤 Human-in-the-Loop Decision

EvidenceHire does not automatically accept or reject candidates.

The recruiter makes the final decision.

The interface provides:

[ ACCEPT ]    [ REJECT ]

When a recruiter accepts or rejects a candidate, the decision is persisted.

Example:

Candidate
Resume Version
Fit Score
Confidence
Decision
Decision Timestamp

⸻

🗄️ Accepted Candidate Storage

Accepted candidates can be retrieved later.

Conceptually:

Accepted Candidates
Candidate      Version    Score    Confidence
------------------------------------------------
John Smith     v2         91       94%
Priya Kumar    v1         87       89%

The system also maintains decision history where implemented.

⸻

🏗️ Architecture

                         EVIDENCEHIRE
                              │
             ┌────────────────┴────────────────┐
             │                                 │
          RESUME                               JD
             │                                 │
             ▼                                 ▼
      File Validator                  JD Requirement Parser
             │
             ▼
      Duplicate Detector
             │
       ┌─────┼─────────┐
       │     │         │
     Exact Same      New
   Duplicate Candidate Candidate
       │     │         │
       └─────┴─────────┘
             │
             ▼
       PDF/DOCX Extractor
             │
             ▼
       Section Segmenter
             │
             ▼
    Deterministic Field Parser
             │
             ▼
       Evidence Validator
             │
             ▼
      Candidate Profile
             │
             └───────────────┐
                             ▼
                       JD Requirements
                             │
                             ▼
                    Experience Analyzer
                             │
                             ▼
                     Skill Gap Analyzer
                             │
                             ▼
                    Deterministic Scorer
                             │
                             ▼
                       Confidence
                             │
                             ▼
                    Candidate Ranking
                             │
                             ▼
                     Human Recruiter
                       ┌─────┴─────┐
                       ▼           ▼
                    ACCEPT       REJECT
                       │           │
                       └─────┬─────┘
                             ▼
                          SQLite
                             │
                   ┌─────────┴─────────┐
                   ▼                   ▼
             Accepted List       Decision History

⸻

🧱 Technology Stack

Layer	Technology
Frontend	Python + Streamlit
Backend	Python
Database	SQLite
PDF Processing	pdfplumber
DOCX Processing	python-docx
Parsing	Python Regex / Deterministic Rules
Optional AI	LLM/API
Configuration	Environment Variables

Why Python?

Python provides a single ecosystem for:

* document processing;
* text extraction;
* deterministic parsing;
* scoring;
* AI integration;
* database interaction;
* rapid prototype development.

Streamlit allows the frontend to be developed directly in Python, which reduces the complexity of maintaining a separate React/Angular frontend for the prototype.

⸻

📁 Planned Project Structure

EvidenceHire/
│
├── app.py
├── config.py
├── requirements.txt
├── .gitignore
│
├── backend/
│   ├── ingestion/
│   │   ├── file_validator.py
│   │   ├── extractor.py
│   │   └── normalizer.py
│   │
│   ├── duplicate/
│   │   ├── duplicate_detector.py
│   │   ├── identity_matcher.py
│   │   └── version_manager.py
│   │
│   ├── parsing/
│   │   ├── segmenter.py
│   │   ├── field_parser.py
│   │   └── evidence_validator.py
│   │
│   ├── candidate/
│   │   ├── candidate_service.py
│   │   └── profile_service.py
│   │
│   ├── jd/
│   │   └── jd_parser.py
│   │
│   ├── scoring/
│   │   ├── experience_analyzer.py
│   │   ├── skill_gap_analyzer.py
│   │   └── scorer.py
│   │
│   ├── ranking/
│   │   └── ranking_service.py
│   │
│   ├── decisions/
│   │   └── decision_service.py
│   │
│   ├── reports/
│   │   └── report_service.py
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   └── database/
│       ├── db.py
│       └── repositories/
│
├── tests/
│
└── README.md

The project is being developed incrementally. Not every planned module is necessarily implemented yet.

⸻

🗃️ Database Model

The prototype uses SQLite.

Core entities include:

Candidate
    │
    ├── ResumeUpload
    │       └── ResumeVersion
    │
    ├── CandidateField
    │
    └── DecisionHistory
JobDescription
    │
    └── JDRequirement
ResumeVersion
    │
    └── AnalysisResult
AnalysisResult
    ├── MatchResult
    └── EvidenceReference

This structure allows the system to preserve:

* candidates;
* uploads;
* resume versions;
* validated fields;
* job descriptions;
* requirements;
* analysis results;
* matching results;
* decisions;
* decision history.

⸻

🔐 Trust & Safety Principles

EvidenceHire follows several strict principles:

1. Evidence before claims

Evidence → Claim

Never:

Guess → Claim

2. Missing information remains missing

NOT_FOUND

instead of an invented value.

3. Ambiguous information remains ambiguous

AMBIGUOUS

instead of choosing a value without evidence.

4. Deterministic analysis

Same input should produce the same result.

5. Human final decision

The agent recommends.

The recruiter decides.

AI Analysis
     ↓
Ranking
     ↓
Human Review
     ↓
ACCEPT / REJECT

⸻

🧪 Testing Strategy

The project includes tests for:

Resume Processing

* Valid PDF
* Valid DOCX
* Unsupported files
* Missing files
* Empty files
* Corrupted PDF
* Corrupted DOCX
* No-text-layer PDF

Parsing

* Clean resumes
* Missing sections
* Unknown headings
* Messy formatting
* Multiple sections

Evidence

* Valid evidence
* Missing evidence
* Invalid evidence
* Unsupported values

Duplicate Detection

* Exact duplicate
* Renamed duplicate
* Same candidate
* Updated resume
* Similar names

Scoring

* Matched requirements
* Partial requirements
* Missing requirements
* Deterministic scoring

Hallucination Regression

Example:

Resume:
Python
Java
SQL
JD:
Python
Java
React
Docker
AWS

Expected:

Python → MATCHED
Java   → MATCHED
React  → MISSING
Docker → MISSING
AWS    → MISSING

The system must never claim:

React
Docker
AWS

as candidate skills.

⸻

🚧 Current Development Status

The project is being developed in controlled stages.

Foundation

* Project skeleton
* Dependencies
* Basic application entry point
* Basic configuration
* SQLite initialization

Resume Processing

* File validation
* PDF extraction
* DOCX extraction
* No-text-layer detection
* Extraction error handling
* Extraction tests

Upcoming

* Section segmentation
* Deterministic field parser
* Evidence validator
* Duplicate detection
* Resume versioning
* JD requirement parser
* Experience analysis
* Skill-gap analysis
* Confidence scoring
* Deterministic scoring
* Candidate ranking
* Human ACCEPT/REJECT
* Decision persistence
* Accepted candidate retrieval
* Streamlit dashboard
* Final end-to-end testing
* REPORT.md

⸻

⚙️ Installation

Clone the repository:

git clone <YOUR_REPOSITORY_URL>
cd EvidenceHire

Create a virtual environment:

python3 -m venv venv

Activate it:

macOS / Linux

source venv/bin/activate

Windows

venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

⸻

▶️ Running the Application

Once the Streamlit interface is implemented:

streamlit run frontend/app.py

The exact run command should follow the project’s current implementation and final requirements.txt.

⸻

🧪 Running Tests

Run the test suite using:

python -m unittest discover

For the current extraction tests:

PYTHONPATH=. python -m unittest tests/test_extraction.py

⸻

🔑 Environment Variables

If optional LLM functionality is enabled, API credentials must be supplied through environment variables.

Example:

export LLM_API_KEY="your-api-key"

Never hard-code API keys inside the source code.

⸻

🎯 Demo Flow

A typical demonstration:

1. Upload Resume
        ↓
2. Upload Job Description
        ↓
3. Analyze
        ↓
4. Extract Candidate Information
        ↓
5. Display Evidence
        ↓
6. Calculate Fit Score
        ↓
7. Show Confidence
        ↓
8. Show Experience Match
        ↓
9. Show Skill Gaps
        ↓
10. Rank Candidates
        ↓
11. Human Reviews Candidate
        ↓
12. ACCEPT / REJECT
        ↓
13. Store Decision

Duplicate demonstration

Upload:

John_Resume.pdf
John_Final.pdf
John_Resume_2.pdf

If the contents are identical:

Already it exist
Unique Candidates: 1
Duplicate Uploads: 2

Updated resume demonstration

Upload:

John_Resume_v2.pdf

Expected:

Same Candidate
Resume Version: v2
Updates:
+ Docker
+ AWS

⸻

🏆 Project Differentiator

Many resume-screening systems focus primarily on generating a candidate score.

EvidenceHire focuses on why the score can be trusted.

Its architecture separates:

Extraction
     ↓
Deterministic Parsing
     ↓
Evidence Validation
     ↓
Experience Verification
     ↓
Skill Gap Analysis
     ↓
Scoring
     ↓
Ranking
     ↓
Human Decision

The optional LLM is controlled rather than being the source of candidate facts.

⸻

👤 Human-in-the-Loop Philosophy

EvidenceHire does not replace the recruiter.

It provides:

Evidence
+
Confidence
+
Experience Analysis
+
Skill Gaps
+
Fit Score
+
Ranking

The recruiter makes the final decision:

          Candidate Analysis
                  │
           Human Review
            ┌─────┴─────┐
            ▼           ▼
         ACCEPT       REJECT

This keeps the final hiring-screening decision under human control.

⸻

📌 Project Status

EvidenceHire is currently an actively developed prototype.

The implementation is intentionally incremental and controlled. Features are implemented and verified one stage at a time rather than generating the entire application in a single step.

⸻

📄 License

Add the project’s chosen license here before public release.

⸻

Core Principle

NO EVIDENCE → NO CLAIM

EvidenceHire — Analyze with evidence. Decide with confidence.
