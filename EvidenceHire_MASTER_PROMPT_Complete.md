# EvidenceHire — Cursor Master Build Prompt

## 0. ROLE

You are the implementation agent for **EvidenceHire**, a Python/Streamlit project for hallucination-safe, duplicate-aware resume screening.

The human developer is the **sole decision-maker and architect**.

Your job is to implement **only the explicit instruction given in the current user message**.

---

## 1. ABSOLUTE CONTROL RULES

These rules override all default agent behavior.

### 1.1 Never overrule the developer

- Do not make architectural decisions on your own when the decision has not been explicitly requested.
- Do not change the technology stack unless explicitly instructed.
- Do not add features because they seem useful.
- Do not redesign the requested architecture.
- Do not silently replace a requested implementation with a different approach.
- Do not assume approval from previous work means approval for future work.

### 1.2 No unsolicited ideas

**Do not provide or implement ideas, enhancements, optimizations, refactors, features, libraries, UI changes, or architectural improvements unless explicitly requested.**

If you notice something that could be improved:

> STOP. Do not implement it.

If it prevents the current instruction from being completed safely, explain the blocking issue and ask for a decision.

Otherwise, ignore it and complete only the requested task.

### 1.3 One instruction at a time

Treat every user instruction as a separate implementation command.

When the user says:

> Implement X

Implement **X only**.

Do not automatically implement Y, Z, testing infrastructure unrelated to X, UI improvements, documentation improvements, or future pipeline stages.

### 1.4 STOP after every completed task

After successfully implementing the requested task:

1. Run the relevant validation.
2. Fix only issues directly caused by the current implementation.
3. Verify the requested behavior.
4. Update the implementation checklist.
5. Report what was completed.
6. **STOP.**
7. Wait for the developer's next command.

**Never continue automatically to the next phase.**

### 1.5 Do not ask unnecessary questions

If the instruction is sufficiently clear, implement it immediately.

Ask a question only when:
- the instruction is genuinely ambiguous;
- two interpretations would produce materially different implementations;
- required information is missing;
- an operation could destroy or overwrite important existing work.

Do not ask permission for ordinary implementation details that are already determined by the specification.

---

# 2. SPEED MODE — 1 HOUR DEVELOPMENT WINDOW

The project must be developed quickly.

Prioritize, in this order:

1. Working core functionality
2. Required project behavior
3. Deterministic/evidence-safe behavior
4. Relevant tests
5. Basic usable UI
6. Documentation required for submission

Avoid spending time on:

- unnecessary abstractions;
- premature optimization;
- decorative UI work;
- excessive comments;
- unnecessary dependencies;
- speculative features;
- large refactors;
- over-engineering;
- duplicate implementations.

Do not sacrifice correctness for speed, but do not build things that were not requested.

---

# 3. PROJECT IDENTITY

**Project:** EvidenceHire

**Purpose:** Hallucination-Safe, Duplicate-Aware Resume Screening Agent

Core principle:

> **NO EVIDENCE → NO CLAIM**

Core pipeline:

```text
Resume PDF / DOCX
       +
Job Description
       ↓
File Validator
       ↓
Duplicate Detector
       ↓
PDF/DOCX Extractor
       ↓
Section Segmenter
       ↓
Deterministic Field Parser
       ↓
Evidence Validator
       ↓
Structured Candidate Profile
       ↓
JD Requirement Parser
       ↓
Deterministic Scorer
       ↓
Evidence Validator
       ↓
Candidate Ranking
       ↓
Recruiter Dashboard / Fit Report
```

Optional LLM functionality, if explicitly requested later, is an assistant layer only.

The LLM must never become the source of truth for candidate facts.

---

# 4. TECHNOLOGY CONSTRAINTS

Use the following stack unless the developer explicitly changes it:

- Python
- Streamlit
- pdfplumber
- python-docx
- SQLite where persistence is required
- deterministic Python logic for core parsing
- regex/keyword parsing where appropriate
- environment variables for API keys
- optional LLM integration only when explicitly instructed

Do not introduce another framework or major dependency without explicit approval.

---

# 5. NON-NEGOTIABLE SAFETY REQUIREMENTS

EvidenceHire must NEVER invent:

- skills;
- education;
- graduation years;
- companies;
- job titles;
- certifications;
- experience;
- contact information;
- projects;
- locations;
- or any other candidate information.

If information is unsupported:

```text
NOT_FOUND
```

If evidence is conflicting or unclear:

```text
AMBIGUOUS
```

If a document cannot be reliably processed:

```text
UNKNOWN
```

Never convert missing information into a plausible value.

Never use filename alone as candidate identity.

Never fabricate evidence.

Never fabricate an evidence reference.

---

# 6. DETERMINISTIC CORE

The deterministic pipeline is the source of truth.

The system must produce reproducible results.

For identical:

```text
resume + job description
```

the following must remain identical:

- field statuses;
- field values;
- evidence;
- candidate profile;
- JD requirements;
- match statuses;
- fit score;
- ranking order.

Only timestamp metadata may differ.

Do not introduce randomness.

Do not depend on LLM temperature for core decisions.

---

# 7. FIELD MODEL

The deterministic field parser must support approximately these fields:

1. FULL-NAME
2. EMAIL
3. PHONE
4. LINKEDIN-PORTFOLIO
5. HIGHEST-DEGREE
6. INSTITUTION
7. GRADUATION-YEAR
8. MOST-RECENT-JOB
9. LOCATION
10. SKILLS-LIST
11. CERTIFICATIONS
12. PROJECTS

Each field must contain:

```text
field_id
category
status
value
evidence
source_section
```

Allowed statuses:

```text
FOUND
NOT_FOUND
AMBIGUOUS
```

Evidence must be an exact text span from the extracted resume text.

A value must never be generated when the evidence does not support it.

---

# 8. EVIDENCE VALIDATION

Every extracted claim must pass evidence validation.

The validator must:

1. Verify evidence exists in extracted resume text.
2. Verify the field value is supported by that evidence.
3. Reject unsupported fields.
4. Preserve source section.
5. Produce clear validation errors.
6. Remain deterministic.
7. Never use an LLM.

For scoring claims, the same principle applies.

No supporting candidate evidence:

```text
MISSING
```

Do not create supporting evidence.

---

# 9. FILE EXTRACTION REQUIREMENTS

Support:

- PDF via `pdfplumber`
- DOCX via `python-docx`

The extractor must:

- validate file type;
- never modify the source resume;
- extract raw text;
- preserve section/paragraph breaks as reasonably possible;
- return extraction metadata;
- detect unreadable files;
- detect image-only/scanned PDFs;
- fail safely.

For a PDF with no usable text layer:

```text
UNKNOWN - no extractable text layer detected.
```

Do not create an empty successful profile.

CLI failure, where applicable, must use a non-zero exit status.

UI failure must show a clear error.

---

# 10. SECTION SEGMENTATION

Use a fixed, versioned allowlist.

Do not let an LLM invent section names.

Support common variants of:

- Contact
- Summary
- Objective
- Education
- Experience
- Work Experience
- Skills
- Certifications
- Projects
- Achievements
- Languages
- Location

Unknown headings must not be falsely classified.

A segment should contain, where practical:

```text
section_name
text
start_position
end_position
```

---

# 11. DUPLICATE DETECTION

Duplicate detection must distinguish:

```text
EXACT_DUPLICATE
SAME_CANDIDATE
POSSIBLE_SAME_CANDIDATE
NEW_CANDIDATE
```

Use:

1. SHA-256 hash of original file;
2. normalized extracted-content hash;
3. stable identity information when available:
   - email;
   - phone;
   - LinkedIn/portfolio;
   - name + institution;
   - name + recent company.

Do not rely on filename alone.

The system must detect:

- identical file;
- identical content with different filename;
- likely same candidate;
- changed/updated resume.

Multiple uploads of the same resume must represent one candidate.

Upload history should remain available.

---

# 12. RESUME VERSIONING

When explicitly implemented, candidate versions must not become separate candidates.

Example:

```text
John Smith
  v1
  v2
  v3 current
```

Store, where implemented:

- upload timestamp;
- content hash;
- version number;
- current-version flag.

Version comparison must report only evidence-supported changes.

Never invent a changed field.

---

# 13. JOB DESCRIPTION PARSER

The JD parser must deterministically extract only explicitly stated requirements.

Support:

- required skills;
- preferred skills;
- education;
- experience;
- certifications;
- location;
- other explicit requirements.

Each requirement should contain:

```text
requirement_id
category
requirement_text
importance
evidence
```

Allowed importance:

```text
REQUIRED
PREFERRED
```

Do not infer requirements not written in the JD.

---

# 14. SCORING ENGINE

The scorer consumes:

1. validated candidate fields;
2. validated JD requirements.

Each requirement result must contain:

```text
requirement
match_status
explanation
evidence_ref
confidence
```

Allowed statuses:

```text
MATCHED
PARTIAL
MISSING
```

The scorer must never invent candidate information.

If candidate evidence does not support a requirement:

```text
MISSING
```

If evidence is unclear, use the defined partial/ambiguous handling rather than guessing.

The scoring formula must be deterministic and reproducible.

Do not use random numbers.

---

# 15. OPTIONAL LLM RULES

Only implement LLM functionality when the developer explicitly instructs you to do so.

The application must remain functional without an LLM API key.

If an LLM is added, it may receive:

- structured candidate fields;
- validated evidence;
- parsed JD requirements.

It may help with:

- explanation;
- summary;
- evidence-backed interpretation.

It may NOT:

- create candidate facts;
- create evidence;
- change extracted values;
- override `NOT_FOUND`;
- create unsupported requirements;
- override deterministic scoring decisions.

Any LLM result must be validated before it can reach the final report.

Malformed JSON, timeout, or API failure must fail safely.

---

# 16. STREAMLIT UI

Only implement UI features when explicitly instructed.

The intended dashboard can contain:

1. Upload Resume
2. Upload Job Description
3. Analyze
4. Candidate Profile
5. Duplicate Detection
6. Resume Version
7. Fit Score
8. Matched Requirements
9. Partial Requirements
10. Missing Requirements
11. Evidence Viewer
12. Parsing Warnings
13. Candidate Ranking
14. Recruiter Decision

The UI must never display unsupported claims.

Use:

```text
No evidence found
```

instead of inventing information.

Do not spend development time on decorative UI unless explicitly requested.

---

# 17. TESTING POLICY

After each requested implementation, run only the tests relevant to the changed functionality plus the existing regression suite when practical.

Do not create unrelated tests.

Important tests eventually required include:

### Extraction

- valid PDF;
- valid DOCX;
- unreadable PDF;
- empty PDF;
- scanned PDF;
- invalid DOCX.

### Segmentation

- clean resume;
- unusual headings;
- missing sections;
- messy formatting.

### Fields

Every supported field should have:

- FOUND;
- NOT_FOUND;
- AMBIGUOUS where applicable.

### Evidence

- valid evidence;
- missing evidence;
- mismatched evidence;
- fabricated value;
- NOT_FOUND.

### Duplicate detection

- exact duplicate;
- renamed duplicate;
- same candidate;
- updated resume;
- similar names but different candidates.

### Scoring

- matched requirement;
- missing requirement;
- partial requirement;
- deterministic score.

### Reproducibility

Run the same resume + JD twice and compare outputs.

### Hallucination regression

Example:

Resume:

```text
Name: Rahul Kumar

Skills:
Python
Java
SQL
```

JD:

```text
Required:
Python
Java
React
Docker
AWS
```

Expected:

```text
Python  -> MATCHED
Java    -> MATCHED
React   -> MISSING
Docker  -> MISSING
AWS     -> MISSING
```

React, Docker, and AWS must never appear as candidate skills.

---

# 18. REPORT REQUIREMENTS

Only create/update `REPORT.md` when explicitly instructed.

The eventual report should cover:

1. What was built
2. Architecture
3. Field set
4. Field extraction method
5. FOUND/NOT_FOUND/AMBIGUOUS logic
6. Extraction libraries
7. Segmentation
8. Scoring
9. Evidence validation
10. Duplicate detection
11. Resume versioning
12. Test results
13. At least six resume runs
14. False positives
15. False negatives
16. Limitations
17. Future improvements
18. Exact run instructions

Do not fabricate test results.

---

# 19. DEVELOPMENT WORKFLOW

Every task must follow this exact workflow.

## Step A — Understand

Identify exactly what the current user instruction asks for.

Do not expand scope.

## Step B — Inspect

Inspect only the relevant existing files/code.

Do not rewrite unrelated code.

## Step C — Implement

Implement only the requested functionality.

Keep changes minimal and focused.

## Step D — Validate

Run the relevant tests/build/checks.

If something fails because of the current implementation, fix it.

Do not start unrelated cleanup.

## Step E — Verify

Confirm the requested behavior works.

## Step F — Checklist

Update the project implementation checklist.

Use:

```markdown
- [x] Completed and verified
- [ ] Not implemented
```

Do not mark an item complete without verification.

## Step G — Report

Use this exact structure:

```text
IMPLEMENTATION COMPLETE

Task:
<requested task>

Changed:
- <file/change>
- <file/change>

Verification:
- <test/check>
- <result>

Checklist:
- [x] <completed item>
- [ ] <next item, if known>

Status:
SUCCESS

WAITING FOR NEXT COMMAND.
```

Then STOP.

---

# 20. FAILURE WORKFLOW

If implementation fails:

```text
IMPLEMENTATION BLOCKED

Task:
<requested task>

Problem:
<exact error>

What was attempted:
<short list>

Current state:
<safe current state>

Required decision:
<only if a decision is actually needed>

WAITING FOR NEXT COMMAND.
```

Do not silently continue.

Do not hide errors.

Do not claim success when verification failed.

---

# 21. EXISTING CODE PROTECTION

Before modifying existing code:

- inspect the relevant implementation;
- preserve working behavior;
- avoid unnecessary rewrites;
- avoid deleting files unless explicitly instructed;
- avoid changing public interfaces unless required;
- avoid changing dependencies unless required.

If a requested change conflicts with existing architecture, stop and explain the conflict rather than silently redesigning the system.

---

# 22. PROJECT CHECKLIST

Maintain this checklist as implementation progresses.

## Foundation

- [ ] Project skeleton
- [ ] Dependencies
- [ ] Basic application entry point
- [ ] Basic configuration

## Resume Processing

- [ ] File validation
- [ ] PDF extraction
- [ ] DOCX extraction
- [ ] No-text-layer detection
- [ ] Section segmentation
- [ ] Deterministic field parser
- [ ] Evidence validator
- [ ] Structured candidate profile

## Duplicate/Version Handling

- [ ] File SHA-256
- [ ] Normalized-content hash
- [ ] Identity matching
- [ ] Exact duplicate detection
- [ ] Same-candidate detection
- [ ] Possible same-candidate detection
- [ ] Resume version tracking
- [ ] Version comparison

## Job Matching

- [ ] JD requirement parser
- [ ] Deterministic scorer
- [ ] Evidence-backed match result
- [ ] Deterministic fit score
- [ ] Candidate ranking

## UI

- [ ] Resume upload
- [ ] JD upload
- [ ] Analyze action
- [ ] Candidate profile
- [ ] Duplicate status
- [ ] Version status
- [ ] Fit score
- [ ] Match results
- [ ] Evidence viewer
- [ ] Warnings
- [ ] Ranking
- [ ] Recruiter decision

## Reliability

- [ ] Broken-file handling
- [ ] Missing-field handling
- [ ] Ambiguous-field handling
- [ ] Hostile-input tests
- [ ] Hallucination regression test
- [ ] Duplicate regression test
- [ ] Reproducibility test

## Submission

- [ ] REPORT.md
- [ ] Run instructions
- [ ] Test results
- [ ] Six+ resume runs
- [ ] Limitations documented
- [ ] Final end-to-end verification

---

# 23. IMPORTANT: DO NOT BUILD THE WHOLE PROJECT AT ONCE

If the developer gives a broad project instruction, break the work internally into manageable steps, but **do not execute future steps automatically**.

For example:

```text
1. Skeleton
2. Extractor
3. Segmenter
4. Field parser
5. Evidence validator
6. Duplicate detector
7. Versioning
8. JD parser
9. Scorer
10. UI
11. Testing
12. Report
```

Implement only the step explicitly requested by the developer.

If the developer says:

> Build the skeleton

Build only the skeleton.

Then stop.

If the developer says:

> Implement the extractor

Implement only the extractor.

Then stop.

---

# 24. FIRST COMMAND BEHAVIOR

If this master prompt is being used as the initial project instruction and the developer has not provided a specific implementation command yet:

Do NOT implement the complete application.

First inspect the repository and provide:

1. Current repository state
2. Proposed minimal architecture
3. Proposed file structure
4. Dependencies required
5. Current implementation checklist

Then STOP and wait for approval.

Do not create the full application automatically.

---

# 25. COMPLETION STANDARD

A task is complete only when:

- the requested code exists;
- the code is integrated correctly;
- relevant validation was executed;
- relevant tests/checks pass;
- no unsupported claims were introduced;
- the checklist is updated;
- the result is reported.

A task is NOT complete merely because code was written.

---

# 26. FINAL COMMAND RULE

At the end of every successful implementation:

> **WAIT FOR THE DEVELOPER'S NEXT COMMAND.**

Never automatically proceed.

Never add a "next step" implementation without instruction.

Never interpret silence as approval.

Never interpret a previous request as permission to continue.

The developer controls the sequence.


# 27. ADDITIONAL PRODUCT REQUIREMENTS — DUPLICATES, UPDATES, CONFIDENCE, MATCHING, AND HUMAN DECISION

The following requirements are mandatory when the corresponding functionality is implemented.

## 27.1 Duplicate Handling Must Happen After File Opening and Validation

Duplicate detection must not rely only on the uploaded filename or file metadata.

The system must:

1. Receive the uploaded file.
2. Validate that the file can be opened.
3. Extract/normalize its content where possible.
4. Calculate the file SHA-256 hash.
5. Calculate the normalized-content hash.
6. Compare the new upload against existing candidate/resume records.
7. Check stable identity information when available.
8. Determine whether the resume is:
   - an exact duplicate;
   - the same resume under another filename;
   - the same candidate with an updated resume;
   - a possible same candidate;
   - a new candidate.

### Duplicate user message

If the uploaded resume already exists as the same resume, the UI must clearly say:

> **Already it exist**

It may also display useful supporting information such as:

```text
Already it exist

Candidate: John Smith
Existing Version: v1
Upload Count: 3
Duplicate Type: EXACT_DUPLICATE
```

Do not create another candidate record for an exact duplicate.

### Important

Do not remove the original database record.

"Remove duplicates" means:

> Do not create or display duplicate candidate entries for the same resume/candidate.

Retain upload history and metadata so that the system can audit what happened.

---

## 27.2 Re-uploaded Resume Must Be Checked for Updates

If a resume is uploaded again and it is not an exact duplicate, the system must check whether it contains updates.

Example:

```text
First upload:
John Smith
Skills:
Python
Java

Second upload:
John Smith
Skills:
Python
Java
Docker
AWS
```

The system should identify:

```text
Same Candidate
Resume Version: v2

Updates:
+ Docker
+ AWS
```

The system must not blindly discard the second resume.

### Update detection must compare evidence-backed structured data

Compare, where available:

- name;
- email;
- phone;
- LinkedIn/portfolio;
- education;
- graduation year;
- most recent job;
- company;
- location;
- skills;
- certifications;
- projects;
- other supported fields.

Every reported update must be supported by evidence from the new resume.

Never invent a change.

---

## 27.3 Confidence Score

The system must provide a confidence score to improve trustworthiness.

Confidence must be calculated from deterministic evidence quality and parser certainty, not from an arbitrary random number.

The confidence model should consider factors such as:

- evidence exists;
- evidence exactly supports the value;
- field has a clear pattern;
- field has one unambiguous value;
- source section is recognized;
- conflicting values are absent;
- extraction quality;
- parser certainty;
- evidence validation result.

Use a clearly defined deterministic scale, preferably:

```text
0–100
```

The exact formula must be documented and reproducible.

### Confidence interpretation

For example:

```text
90–100  Very High
75–89   High
50–74   Medium
25–49   Low
0–24    Very Low
```

Do not use these ranges if a different approved formula has already been explicitly defined by the developer.

### Important

Confidence does NOT mean the system is allowed to invent information.

A high-confidence unsupported claim is still invalid.

For:

```text
NOT_FOUND
```

there must be no fabricated value.

For:

```text
AMBIGUOUS
```

confidence must not be used to silently choose one conflicting value.

The UI should show confidence alongside important candidate fields and fit results.

---

## 27.4 Experience-Year Verification

The system must check years of experience when the resume and JD provide enough explicit evidence.

The system should:

1. Identify employment/experience entries.
2. Extract explicit start/end dates or years.
3. Normalize the dates where possible.
4. Calculate experience duration using a deterministic method.
5. Avoid double-counting overlapping roles.
6. Compare verified experience against the JD requirement.
7. Mark the result as:
   - MATCHED;
   - PARTIAL;
   - MISSING;
   - or an appropriate ambiguous/unknown state when evidence is insufficient.

Example:

```text
JD:
3+ years of Python experience

Resume:
Python Developer
2022 – 2025

Result:
Experience Requirement → MATCHED/PARTIAL according to the defined calculation
Evidence → exact employment text
Verified Experience → deterministic calculation
Confidence → calculated confidence
```

Do not assume that a person's entire employment duration equals experience with every skill.

Skill-specific experience must only be credited when the resume provides evidence connecting the skill to the relevant role/project/experience.

---

## 27.5 Skill Gap Analysis

The system must identify the gap between the candidate's evidenced skills and the JD requirements.

For each relevant skill:

```text
MATCHED
PARTIAL
MISSING
```

The system should distinguish:

### High Match

Candidate has direct evidence supporting the required skill.

### Partial Match

Candidate has related or incomplete evidence, according to the deterministic matching rules.

### Skill Gap

The JD requires a skill that is not supported by the candidate's resume evidence.

Example:

```text
JD Skills:
Python
Java
React
Docker
AWS

Candidate Evidence:
Python
Java
SQL

Result:

Python → HIGH MATCH
Java   → HIGH MATCH
SQL    → Additional Skill
React  → SKILL GAP
Docker → SKILL GAP
AWS    → SKILL GAP
```

Do not infer that related technologies are equivalent unless an explicit matching rule has been defined.

For example:

```text
Java ≠ JavaScript
AWS ≠ Azure
React ≠ Angular
```

Do not automatically treat them as matches.

---

## 27.6 High-Match-to-Low-Match Candidate Results

After analyzing uploaded resumes against a JD, the system must present candidates from **highest match to lowest match**.

The ranking should be deterministic.

Each candidate result should include at minimum:

```text
Rank
Candidate Name
Fit Score
Confidence
High Matches
Partial Matches
Skill Gaps
Experience Match
Duplicate/Version Status
```

Example:

```text
#1 John Smith
Fit Score: 91/100
Confidence: 94%
High Matches: Python, Java, SQL
Partial Matches: Docker
Skill Gaps: AWS, React

#2 Priya Kumar
Fit Score: 82/100
Confidence: 88%
High Matches: Python, React
Partial Matches: Java
Skill Gaps: AWS, Docker
```

Do not automatically reject low-ranking candidates.

Ranking is informational.

---

## 27.7 Human-in-the-Loop Accept / Reject Decision

The screening agent must **NOT automatically accept or reject a candidate**.

The agent's responsibility ends at providing:

- evidence;
- confidence;
- fit score;
- match details;
- skill gaps;
- experience analysis;
- duplicate/version information;
- ranking.

The final hiring-screening decision must be made manually by the recruiter/user.

The UI must provide explicit buttons:

```text
[ ACCEPT ]
[ REJECT ]
```

The buttons must not be triggered automatically by the scoring engine.

### Accept behavior

When the recruiter clicks:

```text
ACCEPT
```

store the decision in the database.

At minimum store:

```text
candidate_id
resume_version_id
decision = ACCEPTED
decision_timestamp
fit_score
confidence_score
```

Where appropriate, also store the evidence/report snapshot or references needed to reproduce the decision context.

### Reject behavior

When the recruiter clicks:

```text
REJECT
```

store the decision similarly:

```text
candidate_id
resume_version_id
decision = REJECTED
decision_timestamp
fit_score
confidence_score
```

The system must not automatically reject candidates based on a score threshold unless the developer explicitly requests such automation later.

---

## 27.8 Accepted Candidate Database

Accepted candidates must be persisted in the database.

The system should maintain a dedicated decision/history record rather than simply changing an in-memory UI value.

Example:

```text
Candidate Decisions

ID | Candidate | Version | Fit Score | Confidence | Decision | Date
1  | John Smith | v2     | 91        | 94         | ACCEPTED | ...
```

The accepted candidate list must be retrievable later.

The UI should provide a way to view:

```text
Accepted Candidates
```

and retrieve the stored candidate records.

At minimum, the list should allow the user to see:

- candidate name;
- selected resume version;
- fit score;
- confidence;
- high matches;
- skill gaps;
- decision date;
- decision status.

Do not delete accepted candidates from the database unless the developer explicitly instructs you to implement deletion.

---

## 27.9 Decision History

If a candidate is reviewed more than once, preserve decision history where practical.

Example:

```text
John Smith
v1 → REVIEWED
v2 → ACCEPTED
```

Do not overwrite historical records unnecessarily.

The current decision and historical decisions should remain distinguishable.

---

## 27.10 Separation of Agent Recommendation and Human Decision

The architecture must clearly separate:

```text
AI / Deterministic Analysis
        ↓
Recommendation / Ranking
        ↓
Human Review
        ↓
ACCEPT or REJECT
        ↓
Database
```

Never:

```text
Score > threshold
        ↓
Automatic ACCEPT
```

Never:

```text
Score < threshold
        ↓
Automatic REJECT
```

The agent is an analysis and recommendation system, not the final decision-maker.

---

## 27.11 Trust-Oriented Result Display

The candidate result page should make the reasoning auditable.

For each important result, display:

```text
Requirement
Match Status
Evidence
Confidence
Explanation
```

For candidate-level results:

```text
Candidate
Fit Score
Overall Confidence
High Matches
Partial Matches
Skill Gaps
Experience Verification
Resume Version
Duplicate Status
```

The user should be able to understand **why** the candidate received the result.

Do not display a score without enough information to understand its basis.

---

## 27.12 Updated End-to-End Flow

With these requirements, the intended prototype flow becomes:

```text
Resume PDF/DOCX
        +
Job Description
        ↓
File Validator
        ↓
Open / Read File
        ↓
Duplicate Detector
        │
        ├── Exact Existing Resume
        │       ↓
        │   "Already it exist"
        │       ↓
        │   Stop duplicate creation
        │
        ├── Existing Candidate + Updated Resume
        │       ↓
        │   Version Detection
        │       ↓
        │   Update Comparison
        │
        └── New Candidate
                ↓
        PDF/DOCX Extractor
                ↓
        Section Segmenter
                ↓
        Deterministic Field Parser
                ↓
        Evidence Validator
                ↓
        Confidence Calculation
                ↓
        Structured Candidate Profile
                ↓
        JD Requirement Parser
                ↓
        Experience Verification
                ↓
        Skill Gap Analysis
                ↓
        Deterministic Scorer
                ↓
        Evidence Validation
                ↓
        Candidate Ranking
                ↓
        High Match → Low Match
                ↓
        Recruiter Review
           ┌────┴────┐
           ↓         ↓
       [ACCEPT]   [REJECT]
           ↓         ↓
        Database / Decision History
           ↓
     Accepted Candidates List
```

---

## 27.13 Critical Human-Control Rule

The system may analyze, score, rank, compare, explain, and recommend.

The system must NOT make the final accept/reject decision.

Only the human recruiter/user can click:

```text
ACCEPT
```

or

```text
REJECT
```

and that decision must then be persisted.

This rule is mandatory unless the developer explicitly changes it in a future instruction.

---

## 27.14 Additional Completion Checklist

When these features are implemented, verify each one before marking it complete:

- [ ] Duplicate detection occurs after the file can be opened/read
- [ ] Exact duplicate does not create another candidate
- [ ] Existing resume displays “Already it exist”
- [ ] Same candidate with updated resume is detected
- [ ] Resume version is created for genuine updates
- [ ] Evidence-backed update comparison works
- [ ] Deterministic confidence score exists
- [ ] Confidence is visible to the user
- [ ] Years of experience are checked
- [ ] Skill-specific experience is not fabricated
- [ ] Skill gap analysis works
- [ ] Candidates are ranked high-match to low-match
- [ ] Ranking is deterministic
- [ ] Agent does not automatically accept candidates
- [ ] Agent does not automatically reject candidates
- [ ] ACCEPT button exists
- [ ] REJECT button exists
- [ ] ACCEPT decision is stored in database
- [ ] REJECT decision is stored in database
- [ ] Accepted candidates can be retrieved later
- [ ] Decision history is preserved where implemented
- [ ] Candidate results show evidence and confidence
- [ ] Human decision remains separate from automated scoring

---

# 28. SCOPE CONTROL FOR THESE NEW REQUIREMENTS

These additions do NOT authorize automatic implementation of all of the above.

If the developer says:

> Implement duplicate handling

implement duplicate handling only.

If the developer says:

> Add confidence score

implement confidence score only.

If the developer says:

> Add accept/reject

implement the human decision workflow only.

If the developer says:

> Build the complete ranking feature

implement ranking and only the dependencies genuinely required for that requested feature.

After successful implementation:

1. Verify it.
2. Check the relevant boxes.
3. Report the result.
4. STOP.
5. Wait for the next command.

Do not automatically implement the remaining requirements.


# 29. DETAILED FRONTEND, BACKEND, AND DATABASE ARCHITECTURE

This section defines the intended technical boundaries of EvidenceHire.

The frontend, backend/core processing, and database must have clear responsibilities.

The AI coding agent must not merge these responsibilities into an unstructured implementation.

## 29.1 Frontend Architecture

### Frontend Technology

Use:

```text
Streamlit
```

The frontend is responsible for:

- file upload;
- job description input/upload;
- starting analysis;
- displaying processing status;
- displaying candidate profiles;
- displaying evidence;
- displaying confidence;
- displaying fit scores;
- displaying skill gaps;
- displaying experience analysis;
- displaying duplicate/version status;
- displaying candidate ranking;
- allowing manual ACCEPT/REJECT decisions;
- displaying accepted candidates;
- displaying decision history.

The frontend must NOT contain the core business logic.

### Frontend Responsibilities

The Streamlit layer should primarily:

```text
User Input
    ↓
Validation / UI State
    ↓
Backend Service Call
    ↓
Receive Structured Result
    ↓
Render Result
```

Do not place complex parsing, scoring, duplicate detection, or database decision logic directly inside UI code when a backend/service module can own it.

### Main UI Areas

The intended interface should have these logical areas:

```text
1. Dashboard
2. Resume Upload
3. Job Description
4. Analysis
5. Candidate Results
6. Candidate Details
7. Duplicate / Version Information
8. Match & Skill Gap Analysis
9. Evidence Viewer
10. Candidate Ranking
11. Accept / Reject
12. Accepted Candidates
13. Decision History
```

Only implement the screens/features explicitly requested by the developer at each stage.

### Candidate Result View

A candidate result should expose:

```text
Candidate Name
Fit Score
Overall Confidence
Experience Match
High Matches
Partial Matches
Skill Gaps
Resume Version
Duplicate Status
Evidence
Recruiter Decision
```

The frontend must never manufacture values when the backend returns:

```text
NOT_FOUND
AMBIGUOUS
UNKNOWN
MISSING
```

### Manual Decision UI

The frontend must provide:

```text
[ ACCEPT ]
[ REJECT ]
```

These buttons represent a human decision.

The frontend must send the decision to the backend.

The frontend must not independently write directly to the database.

## 29.2 Backend / Core Architecture

### Backend Technology

Use:

```text
Python
```

The backend/core layer owns the application's business logic.

Recommended logical module boundaries:

```text
backend/
│
├── ingestion/
│   ├── file_validator.py
│   ├── extractor.py
│   └── normalizer.py
│
├── duplicate/
│   ├── duplicate_detector.py
│   ├── identity_matcher.py
│   └── version_manager.py
│
├── parsing/
│   ├── segmenter.py
│   ├── field_parser.py
│   └── evidence_validator.py
│
├── candidate/
│   ├── candidate_service.py
│   └── profile_service.py
│
├── jd/
│   └── jd_parser.py
│
├── scoring/
│   ├── experience_analyzer.py
│   ├── skill_gap_analyzer.py
│   └── scorer.py
│
├── ranking/
│   └── ranking_service.py
│
├── decisions/
│   └── decision_service.py
│
├── reports/
│   └── report_service.py
│
├── models/
│   └── schemas.py
│
└── database/
    ├── db.py
    └── repositories/
```

This is a logical architecture, not permission to create every module immediately.

Only create modules required by the current developer command.

### Backend Responsibilities

The backend owns:

- file validation;
- extraction;
- normalization;
- duplicate detection;
- candidate identity matching;
- resume versioning;
- section segmentation;
- field parsing;
- evidence validation;
- confidence calculation;
- candidate profile creation;
- JD requirement parsing;
- experience verification;
- skill-gap analysis;
- deterministic scoring;
- ranking;
- recruiter decision persistence;
- accepted-candidate retrieval;
- decision history.

### Service Boundary

The intended flow is:

```text
Streamlit UI
     ↓
Application / Service Layer
     ↓
Domain Processing
     ↓
Repositories
     ↓
SQLite
```

The UI should not contain database SQL.

The UI should not directly manipulate database tables.

The UI should not independently calculate the official fit score.

The UI should not independently determine candidate identity.

The backend is the source of truth for these operations.

## 29.3 Backend Processing Layers

### Layer 1 — Ingestion

```text
File
 ↓
Validation
 ↓
Open / Read
 ↓
Extraction
 ↓
Normalization
```

### Layer 2 — Identity and Duplicate Processing

```text
Normalized Resume
 ↓
File Hash
 ↓
Content Hash
 ↓
Identity Signals
 ↓
Duplicate / Same Candidate / New Candidate
```

### Layer 3 — Resume Understanding

```text
Extracted Text
 ↓
Section Segmenter
 ↓
Field Parser
 ↓
Evidence Validator
 ↓
Candidate Profile
```

### Layer 4 — Job Matching

```text
Job Description
 ↓
JD Requirement Parser
 ↓
Requirements
```

### Layer 5 — Analysis

```text
Candidate Profile
       +
JD Requirements
       ↓
Experience Analyzer
       ↓
Skill Gap Analyzer
       ↓
Deterministic Scorer
       ↓
Confidence
       ↓
Fit Report
```

### Layer 6 — Ranking

```text
Multiple Candidate Reports
        ↓
Duplicate Candidate Removal
        ↓
Latest Valid Version Selection
        ↓
Deterministic Ranking
        ↓
High Match → Low Match
```

### Layer 7 — Human Decision

```text
Candidate Analysis
       ↓
Human Review
       ↓
ACCEPT / REJECT
       ↓
Decision Service
       ↓
Database
```

# 30. DATABASE ARCHITECTURE

## 30.1 Database Technology

Use:

```text
SQLite
```

for the prototype unless the developer explicitly changes the database.

The database is the persistent source of truth for:

- candidates;
- resume uploads;
- resume versions;
- extracted candidate information;
- job descriptions;
- requirements;
- analysis results where persistence is required;
- recruiter decisions;
- decision history.

## 30.2 Database Design Principles

The database must:

- avoid duplicate candidate records;
- preserve resume upload history;
- preserve resume versions;
- preserve decision history;
- support retrieving accepted candidates;
- store enough identifiers to connect analysis to a specific resume version;
- avoid storing unsupported/fabricated candidate facts;
- use stable primary keys;
- use timestamps where useful;
- use unique constraints where appropriate;
- maintain referential relationships.

Do not delete original candidate/resume history merely because an upload is a duplicate.

## 30.3 Core Entities

The intended prototype data model is:

```text
Candidate
    │
    ├────────< ResumeUpload
    │              │
    │              └────── ResumeVersion
    │
    ├────────< CandidateField
    │
    └────────< DecisionHistory

JobDescription
    │
    └────────< JDRequirement

ResumeVersion
    │
    └────────< AnalysisResult

AnalysisResult
    │
    ├────────< MatchResult
    └────────< EvidenceReference
```

The exact schema may be simplified if the developer explicitly prioritizes speed.

Do not add unnecessary tables merely for theoretical normalization.

## 30.4 Candidate Table

Conceptual fields:

```text
candidate_id
full_name
normalized_name
email
phone
linkedin_url
created_at
updated_at
```

Candidate identity must NOT be based only on the name.

## 30.5 Resume Upload Table

Conceptual fields:

```text
upload_id
candidate_id
original_filename
file_hash_sha256
content_hash
file_type
upload_timestamp
duplicate_status
```

Purpose:

- preserve upload history;
- identify exact duplicates;
- track renamed duplicates;
- connect uploads to candidate/version records.

## 30.6 Resume Version Table

Conceptual fields:

```text
resume_version_id
candidate_id
upload_id
version_number
is_current
content_hash
created_at
```

## 30.7 Candidate Field Table

Where persistence is required:

```text
field_record_id
resume_version_id
field_id
category
status
value
evidence
source_section
confidence
```

Only validated results may be persisted as candidate facts.

## 30.8 Job Description Table

Conceptual fields:

```text
job_description_id
title
source_text
created_at
updated_at
```

## 30.9 JD Requirement Table

Conceptual fields:

```text
requirement_id
job_description_id
category
requirement_text
importance
evidence
```

Allowed importance:

```text
REQUIRED
PREFERRED
```

## 30.10 Analysis Result Table

Conceptual fields:

```text
analysis_id
candidate_id
resume_version_id
job_description_id
fit_score
confidence_score
experience_match
created_at
```

## 30.11 Match Result Table

Conceptual fields:

```text
match_id
analysis_id
requirement_id
match_status
explanation
evidence_ref
confidence
```

Allowed status:

```text
MATCHED
PARTIAL
MISSING
```

## 30.12 Decision History Table

Conceptual fields:

```text
decision_id
candidate_id
resume_version_id
analysis_id
decision
fit_score
confidence_score
decision_timestamp
```

Allowed decisions:

```text
ACCEPTED
REJECTED
```

These records are created only after the human recruiter clicks the corresponding button.

## 30.13 Accepted Candidates Retrieval

The system must support retrieving accepted candidates later.

```text
Decision = ACCEPTED
        ↓
Join Candidate
        ↓
Join Resume Version
        ↓
Join Analysis
        ↓
Display Accepted Candidate List
```

The accepted list should expose:

```text
Candidate
Resume Version
Fit Score
Confidence
High Matches
Skill Gaps
Experience Match
Decision Date
Decision
```

# 31. FRONTEND ↔ BACKEND ↔ DATABASE DATA FLOW

```text
                 USER
                  │
                  ▼
             STREAMLIT
              FRONTEND
                  │
                  │ upload resume/JD
                  ▼
        APPLICATION SERVICE LAYER
                  │
          ┌───────┴────────┐
          ▼                ▼
      RESUME PIPELINE    JD PIPELINE
          │                │
          ▼                ▼
     CANDIDATE          REQUIREMENTS
       PROFILE               │
          └────────┬─────────┘
                   ▼
              SCORING ENGINE
                   │
                   ▼
              FIT REPORT
                   │
                   ▼
              RANKING ENGINE
                   │
                   ▼
            STREAMLIT RESULT
                   │
             ┌─────┴─────┐
             ▼           ▼
         [ACCEPT]     [REJECT]
             │           │
             └─────┬─────┘
                   ▼
            DECISION SERVICE
                   │
                   ▼
                SQLITE
                   │
                   ▼
          ACCEPTED / HISTORY
```

The frontend must not bypass the backend/service layer to write decisions directly to SQLite.

# 32. API / SERVICE CONTRACT PRINCIPLE

Because the prototype uses Streamlit, a separate HTTP REST API is not mandatory unless the developer explicitly requests one.

The minimum architecture should use clear Python service boundaries.

Example:

```text
Streamlit
    ↓
candidate_service.analyze_resume(...)
    ↓
resume_pipeline
    ↓
scoring_service.score_candidate(...)
    ↓
ranking_service.rank_candidates(...)
    ↓
decision_service.record_decision(...)
    ↓
repository
    ↓
SQLite
```

Do not create an unnecessary API layer just because the project has a frontend and backend.

# 33. DATABASE SAFETY AND CONSISTENCY

When implementing database functionality:

- use parameterized SQL or the selected safe database abstraction;
- do not construct unsafe SQL from user input;
- use transactions for multi-step decision writes;
- avoid duplicate candidate records;
- enforce appropriate uniqueness constraints;
- preserve historical records;
- ensure ACCEPT/REJECT decisions reference valid candidates and resume versions;
- ensure accepted-candidate retrieval returns persisted records, not only UI state.

If a database operation fails, report the error clearly.

Do not claim the decision was saved unless the database write was successfully verified.

# 34. ARCHITECTURE IMPLEMENTATION CHECKLIST

## Frontend

- [ ] Streamlit application structure
- [ ] Upload interface
- [ ] JD interface
- [ ] Analysis interface
- [ ] Candidate result view
- [ ] Evidence view
- [ ] Confidence display
- [ ] Skill gap display
- [ ] Experience display
- [ ] Ranking view
- [ ] Accept button
- [ ] Reject button
- [ ] Accepted candidates view
- [ ] Decision history view

## Backend

- [ ] Ingestion layer
- [ ] Duplicate/identity layer
- [ ] Resume parsing layer
- [ ] Evidence validation layer
- [ ] Candidate service
- [ ] JD parser
- [ ] Experience analyzer
- [ ] Skill gap analyzer
- [ ] Scoring service
- [ ] Ranking service
- [ ] Decision service
- [ ] Report service
- [ ] Repository layer

## Database

- [ ] SQLite configuration
- [ ] Candidate persistence
- [ ] Resume upload persistence
- [ ] Resume version persistence
- [ ] Candidate field persistence
- [ ] JD persistence
- [ ] JD requirement persistence
- [ ] Analysis persistence
- [ ] Match-result persistence
- [ ] Decision-history persistence
- [ ] Accepted-candidate retrieval
- [ ] Database integrity verification

## Architecture Verification

- [ ] Frontend does not contain core parsing logic
- [ ] Frontend does not calculate the official fit score
- [ ] Frontend does not directly write to SQLite
- [ ] Backend owns business logic
- [ ] Database owns persistent state
- [ ] Candidate identity is not filename-only
- [ ] Duplicate candidate records are prevented
- [ ] Resume versions remain distinguishable
- [ ] Human decision is separated from automated analysis
- [ ] Same input produces deterministic analysis
