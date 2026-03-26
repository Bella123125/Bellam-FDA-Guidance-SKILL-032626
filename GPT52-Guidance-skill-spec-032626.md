# SmartMed Review 4.3 — Updated Technical Specification (Streamlit on Hugging Face Spaces)

**Document Version:** 4.3.0  
**Date:** 2026-03-26  
**Status:** Updated Technical Specification (design + implementation guidance; **no code included**)  
**System Name:** SmartMed Review 4.3 (智慧醫材與 510(k) 審查指引/清單/技能生成工作站)  
**Deployment Target:** Hugging Face Spaces (Streamlit)  
**Core Stack:** Streamlit + `agents.yaml` + multi-LLM routing (Gemini / OpenAI / Anthropic / Grok) + OCR toolchain + Markdown workspace  
**Primary Additions in 4.3:** 510(k) Submission → Organized Doc → Review Guidance Builder → Skill.md generator pipeline (while preserving all SmartMed Review 4.2 features)

---

## 1. Executive Summary

SmartMed Review 4.3 is an agentic regulatory workspace for medical device regulatory professionals and reviewers. It **preserves all original features** from SmartMed Review 4.2 (WOW UI v2, theme/language/painter styles, Live Log, WOW indicators, interactive dashboard, environment-first API key handling with UI fallback, agent-by-agent execution studio with editable prompts/outputs, multi-provider model selection, AI Note Keeper with coral-highlighted keywords and 9 AI Magics, OCR ingestion, and `agents.yaml` orchestration on Streamlit/Hugging Face Spaces).

Version **4.3** adds a specialized **510(k) Review Guidance Builder pipeline** designed for real reviewer workflows:

1) Users paste a **510(k) submission summary**, **review note**, or **510(k) review guidance** (TXT/Markdown). An agent transforms the content into an **organized Markdown document** that **preserves all original information** (no deletions), and adds:
- **Exactly 5 Markdown tables**
- **Exactly 20 extracted “entities” with context** (traceable to the source)
- Target length: **2000–3000 words** (with transparent counting caveats for mixed-language inputs)

2) Users then paste a **510(k) review guidance template** (or a template description) or choose the **default guidance template** (the provided PTCA DCB catheter review guidance template). An agent transforms the organized document into a **510(k) review guidance** document aligned to the chosen template, with:
- **Exactly 5 Markdown tables**
- **Exactly 20 entities with context** (carried forward and refreshed for reviewer relevance)
- A **review checklist** section (structured and action-oriented)
- Target length: **3000–4000 words**

3) Users then create a **skill description file (`skill.md` / `SKILL.md`)** for the “preview review guidance” using the provided **skill-creator** specification. The skill description is intended to be used by an agent later to review a full 510(k) submission. Users can edit the generated skill in Markdown.

Across all steps, SmartMed Review 4.3 enforces a strong **human-in-the-loop editing workflow**:
- Users can choose models, modify prompts and max tokens (default 12000), run agents one-by-one, and edit outputs before passing them to the next agent.
- Observability is first-class: all runs emit structured events to WOW Interactive Indicator, Live Log, and the interactive dashboard.

---

## 2. Scope and Feature Preservation (4.2 → 4.3)

### 2.1 Explicitly Preserved Features (No Regressions)
SmartMed Review 4.3 retains:

- **WOW UI v2**: Light/Dark themes, English/Traditional Chinese UI language toggle, **20 painter-inspired style presets**, and **Jackpot** style randomizer.
- **WOW Interactive Indicator** with Run Inspector drawer.
- **Live Log** with streaming run events, filters, search, export.
- **WOW Interactive Dashboard** with run timeline, model mix, token/cost estimates (best-effort), bottleneck analyzer, compliance monitor, artifact quick access.
- **API Key Management**: environment-first; UI key entry only when missing; never display environment keys; session-only storage of UI-entered keys.
- **Agent Studio**: agent-by-agent sequential execution; editable prompt and model; editable output as input to next agent; dual Markdown/Text views.
- **Model selection** across providers: `gpt-4o-mini`, `gpt-4.1-mini`, `gemini-2.5-flash`, `gemini-2.5-flash-lite` (added/ensured), Anthropic models (configurable list), `grok-4-fast-reasoning`, `grok-3-mini`.
- **AI Note Keeper**: paste TXT/MD → organized Markdown with coral keywords → edit and download; pinned prompt per note; 9 AI Magics.
- **PDF preview, page selection, OCR** (Python extraction/OCR + Gemini Vision OCR option) and the existing guidance structuring workflow.
- **`agents.yaml`** orchestration and skill panel rendering (`SKILL.md` display support).

### 2.2 New Capabilities in 4.3 (Additive)
- **510(k) Review Guidance Builder module** (two-stage transformation + checklist + entity extraction).
- **Skill.md Generator** based on the **skill-creator** description, producing a reusable “review skill” that later agents can invoke for consistent 510(k) submission review behavior.
- **Regulatory traceability layer** for preservation of original information via “source anchors,” coverage checks, and entity-to-source mapping.

---

## 3. Users, Primary Workflows, and Success Criteria

### 3.1 Target Users
- Regulatory Affairs professionals preparing 510(k) strategies and reviewer-ready guidance
- Reviewers conducting consistency checks and deficiency identification
- QA/Compliance professionals needing traceability and gap visibility
- Technical maintainers managing `agents.yaml`, providers, and deployment

### 3.2 Primary Workflow (New in 4.3): 510(k) Guidance Builder
**Workflow A — Organize (preserve all information):**
- Input: 510(k) submission summary / review note / guidance text (TXT/MD)
- Output: Organized Markdown doc (2000–3000 words), **5 tables**, **20 entities with context**, plus preservation appendix to ensure no information is lost.

**Workflow B — Convert to Review Guidance (template-driven):**
- Input: Organized doc from A + template (pasted or default)
- Output: 510(k) review guidance doc (3000–4000 words), **5 tables**, **20 entities**, plus a structured **review checklist** aligned to template sections.

**Workflow C — Create `SKILL.md` for future automated review:**
- Input: Preview review guidance from B + selected scope notes
- Output: A skill description file that an agent can use to review submissions consistently; editable in Markdown.

### 3.3 Success Criteria
- Users can **verify traceability** from organized doc and guidance back to source content.
- “Preserve all original information” holds in practice through measurable checks and explicit “source preservation” sections.
- The system reliably produces **exactly** the required number of tables and entities (with validation and guided regeneration if needed).
- Users can iteratively refine outcomes via prompt/model control and output editing between agents.
- Logs and dashboard provide enough detail to reproduce or debug results without exposing secrets.

---

## 4. High-Level Architecture (4.3)

### 4.1 Core Layers
**UI Layer (Streamlit)**
- Global settings (theme/language/style/Jackpot, provider readiness, defaults)
- Module navigation: Guidance OCR Workspace, Agent Studio, AI Note Keeper, **510(k) Guidance Builder**, Dashboard, Live Log
- Persistent status bar: WOW indicator + run controls + artifact shortcuts

**Session State Layer (ephemeral)**
- Input documents (pasted text, uploaded files)
- Extracted text and intermediate artifacts
- Prompts, parameter selections, pinned prompts
- Agent outputs (raw + edited “effective output”)
- Entities and tables metadata
- Run events for log/dashboard
- Session-only keys (if entered)

**Document Transformation Layer**
- Chunking, normalization, source anchoring (line numbers / chunk IDs)
- Structured extraction (entities, section map, checklist items)
- Markdown rendering with constraints (table count, length bands)

**LLM Routing Layer**
- Provider selection based on chosen model
- Preflight key validation and policy enforcement
- Unified request/response normalization for logging and artifact capture

**Agent Orchestration Layer (`agents.yaml`)**
- Defines agent steps, prompt templates, default models/params, and expected outputs
- Supports sequential, user-confirmed execution with editable prompts and outputs

### 4.2 Observability (Cross-cutting)
- Every run emits structured events:
  - preflight checks, request dispatch, partial completion (if supported), completion, warnings, constraint failures, exceptions
- Dashboard aggregates:
  - run timeline, per-model usage, constraint pass rates, bottlenecks, artifact quick access

---

## 5. WOW UI v2 Requirements (Retained)

### 5.1 Themes and Language
- Light/Dark theme toggle applies to all modules and embedded components.
- UI language toggle (English / Traditional Chinese) localizes labels, hints, errors, and run explanations.
- Generated content language remains controlled by prompts and module-level options.

### 5.2 20 Painter Styles + Jackpot
- 20 painter-inspired presets applied via design tokens (colors, accent gradients, panel effects).
- “Jackpot” randomly selects a style; users can lock style for session stability.
- Style influences visuals only; it must not affect generated regulatory content.

---

## 6. Security and API Key Handling (Retained)

### 6.1 Key Priority and Visibility Policy
1) Environment secrets (HF Space secrets)  
2) UI-entered keys (session-only)

Rules:
- If environment key exists, UI shows “Managed by environment” and provider readiness; **key is never displayed**.
- If missing, UI presents password field; value stored only in session state; never written to log or artifact.

### 6.2 Preflight Blocking
Before any LLM call:
- Determine provider from selected model.
- Verify key exists.
- If missing, block execution with:
  - localized explanation
  - recommended available models/providers
  - a Live Log preflight event with no sensitive content

---

## 7. Agent Studio (Retained + Used as Backbone of 4.3 Pipeline)

### 7.1 Stepwise Execution Contract
- Agents run **one-by-one** with explicit user confirmation.
- Before each agent:
  - user can modify prompt
  - choose model from allowlist
  - set `max_tokens` (default **12000**) and temperature (within allowed bounds)
- After each agent:
  - output appears in **Markdown view** and **Text view**
  - user can edit the output; edited version becomes **effective output**
  - the next agent consumes the effective output by default

### 7.2 Artifact Versioning (Session-local)
For each agent step:
- store raw output (read-only)
- store edited effective output (downstream input)
- store run metadata (model, parameters, estimated tokens, duration, status, constraint checks)

---

## 8. New Module: 510(k) Review Guidance Builder (4.3)

This module is implemented as a dedicated workflow tab backed by `agents.yaml` agents, and it integrates fully with Agent Studio controls, Live Log, and Dashboard.

### 8.1 Inputs (Supported)
**Document types users may paste (TXT/Markdown):**
- 510(k) submission summary (internal or vendor-provided)
- reviewer notes (gap notes, RTA notes, deficiency notes)
- existing 510(k) review guidance text

**Template inputs:**
- paste a full template (TXT/MD), or
- paste a “template description” (requirements, headings, required tables), or
- choose the **default PTCA DCB catheter review guidance template** (the provided Traditional Chinese template)

### 8.2 Output A: “Organized Document” (2000–3000 words)
**Goal:** create a reviewer-friendly organized document that **keeps all original information** while making it navigable and structured, plus adding tables and entity extraction without deleting source content.

**Hard constraints**
- Target length band: **2000–3000 words** (system reports length estimates; it does not hide uncertainty for CJK)
- Exactly **5 Markdown tables** in total
- Exactly **20 entities with context**
- Must **not remove** any original information:
  - If condensation is needed for readability, the full original content must be preserved in a dedicated section (see preservation strategy)

#### 8.2.1 Preservation Strategy (“Keep all original information”)
SmartMed Review 4.3 treats preservation as a first-class requirement, implemented through three mechanisms:

1) **Source Anchoring**
- On ingestion, the input is normalized and segmented into **source chunks** (e.g., by paragraph or heading).
- Each chunk receives a stable anchor ID (e.g., `SRC-001`, `SRC-002`).
- The organized document references these anchors in context notes and entity mappings.

2) **Dual-Layer Representation**
The organized output contains:
- **Structured layer**: reorganized sections, summaries, and reviewer framing
- **Preservation appendix**: a “Source Preservation Appendix” that includes the original content **verbatim**, organized by anchor IDs (or minimally normalized for whitespace), ensuring nothing is lost.

3) **Coverage Checks (Heuristic)**
After generation, the system runs non-LLM checks:
- Ensures the appendix exists and contains all anchors in order
- Ensures each anchor appears at least once in the appendix
- Flags potential loss if anchors are missing or empty

This design ensures reviewers can always locate original statements even if the structured layer reframes them.

#### 8.2.2 The 5 Required Tables (Organized Document)
Exactly five Markdown pipe tables must be produced. Their intended semantics are standardized to support downstream transformation:

**Table A1 — Document Map**
- Columns: Section, Source anchors covered, Purpose, Reviewer relevance

**Table A2 — Key Claims / Statements (Traceable)**
- Columns: Claim/statement, Source anchor(s), Confidence (High/Med/Low), Notes

**Table A3 — Evidence/Artifact Inventory (As Stated)**
- Columns: Mentioned test/report/document, What it supports, Source anchor(s), Gaps/unknowns  
- Rule: must only list evidence mentioned in source, clearly marking unknowns

**Table A4 — Risk / Deficiency Candidates**
- Columns: Potential gap, Why it matters, Source anchor(s), Suggested reviewer question

**Table A5 — Terminology & Abbreviation Index**
- Columns: Term, Definition/context (from source), Source anchor(s), Notes

#### 8.2.3 The 20 Entities with Context (Organized Document)
Entities are standardized objects extracted from the source, each with context and traceability:

- Exactly **20** entities appear in a dedicated “Entities with Context” section and are optionally referenced throughout.
- Each entity must include:
  - **Entity name**
  - **Entity type** (controlled vocabulary)
  - **Context snippet** (short quote or paraphrase with anchor reference)
  - **Why it matters for review** (reviewer framing)
  - **Source anchor(s)**

**Suggested controlled types (flexible but consistent):**
- Device, Indication for Use, Intended Use, Technological Characteristic, Material, Sterilization, Packaging, Shelf life, Biocompatibility, Bench Test, Software, Cybersecurity, Clinical Evidence, Predicate Device, Labeling/IFU, Manufacturing Process, Risk Control, Performance Claim, Standard/Guidance, Post-market plan

**Entity selection rule:** choose the 20 entities that maximize reviewer utility and coverage diversity, without inventing facts.

### 8.3 Output B: “510(k) Review Guidance” (3000–4000 words, Template-driven)
**Goal:** transform Output A into a template-aligned review guidance document usable by reviewers, preserving key information while producing structured expectations, decision points, and a checklist.

**Hard constraints**
- Target length band: **3000–4000 words**
- Exactly **5 Markdown tables**
- Exactly **20 entities with context** (can be the same entities refined or re-ranked, but still exactly 20)
- Must include a **Review Checklist** section with actionable items and evidence expectations
- Must follow the template headings/ordering as closely as possible (for pasted templates) or follow the described template intent (for template descriptions)

#### 8.3.1 Template Handling
Users choose one of:
1) **Default template**: the provided PTCA DCB catheter review guidance template (Traditional Chinese).  
2) **Pasted template**: user-pasted headings, formatting rules, and required sections.  
3) **Template description**: a textual description of what the guidance should contain and how it should be structured.

The system normalizes templates into a “Template Outline” artifact:
- headings hierarchy
- required sections
- table placement instructions (if any)
- checklist expectations
- language and tone expectations

#### 8.3.2 The 5 Required Tables (Review Guidance)
Exactly five Markdown pipe tables must be produced. Their recommended semantics align with reviewer needs and the default template style:

**Table B1 — Regulatory Pathway & Classification Snapshot**
- Columns: Jurisdiction/Framework, Classification, Review pathway, Notes/assumptions

**Table B2 — Submission Completeness / Expected Sections**
- Columns: Required element, What to look for, Common deficiency, Evidence/examples

**Table B3 — Standards & Test Expectations Traceability**
- Columns: Topic (e.g., biocompatibility), Expected standard/guidance, What reviewer checks, Notes

**Table B4 — Risk-to-Evidence Mapping**
- Columns: Risk area, Potential harm, Evidence type expected, Acceptance considerations

**Table B5 — Decision & Escalation Triggers**
- Columns: Trigger condition, Impact, Reviewer action, Escalation path

If the user template explicitly demands different tables, the system adapts table semantics while still producing exactly five tables total.

#### 8.3.3 Review Checklist (Required)
A dedicated checklist section must be included, designed for practical review execution:

- Organized by template headings (or by standard review domains if no explicit headings)
- Each checklist item includes:
  - what to verify
  - what evidence satisfies it
  - how to record findings (pass/fail/NA + comments)
  - typical red flags
  - references to relevant entities and source anchors (from Output A where applicable)

### 8.4 Editing and Output Management
For both Output A and B:
- Users can edit in **Markdown view** (rendered + source) or **Text view**.
- Edits create a new effective artifact version.
- Users can download `.md` and `.txt`.
- Users can pin prompts and re-run with modifications and different models.

---

## 9. New Module: Skill.md Generator for “Preview Review Guidance” (Skill-Creator Based)

### 9.1 Purpose
Generate a skill description file (`skill.md` or `SKILL.md`) that will later be used by an agent to review a 510(k) submission in a consistent, repeatable manner based on the newly created review guidance.

### 9.2 Inputs
- The generated **510(k) Review Guidance** (Output B), including:
  - checklist
  - entities
  - tables
  - reviewer decision triggers
- Optional user-provided constraints:
  - target product type
  - regulatory jurisdiction expectations
  - organization-specific tone and formatting norms

### 9.3 Output Requirements for `SKILL.md`
The generated skill must follow the skill structure guidelines (frontmatter + body), aligned with the provided **skill-creator** description:

- **Frontmatter**
  - `name`: stable identifier (configured by user or default naming convention)
  - `description`: “pushy” trigger guidance so it reliably triggers when users ask for 510(k) review, deficiency checks, completeness checks, or template-aligned review memos

- **Body**
  - When to use / when not to use
  - Required inputs (submission text, sections, device description, testing)
  - Step-by-step review workflow:
    - intake and scoping
    - completeness and consistency checks
    - claim-evidence mapping
    - deficiency drafting
    - risk-based prioritization
    - final review summary
  - Output format templates:
    - reviewer memo format
    - deficiency list format
    - checklist report format
  - Guardrails:
    - no fabrication of evidence
    - uncertainty labeling
    - cite where conclusions come from (submission section references)
  - Optional evaluation hooks:
    - suggested test prompts (2–3) for validating the skill performance
    - qualitative success criteria aligned with the tables/entities/checklist

### 9.4 Human Editing Loop
- The skill is presented in an editable Markdown editor.
- Users can adjust trigger conditions, output formats, and organizational preferences.
- The skill artifact is versioned session-locally and downloadable.

---

## 10. Constraints, Validation, and Regeneration (4.3)

### 10.1 Shared Constraint System (Both Outputs)
Each generated artifact includes an automated validation panel:

- **Length estimate**
  - Words estimate for English
  - Transparent note for Chinese/Japanese: show character count and approximate “word-equivalent” estimate
- **Table count**
  - Regex-based detection of Markdown pipe tables
  - Must equal exactly 5
- **Entity count**
  - Must equal exactly 20
  - Must include required fields and at least one source anchor per entity
- **Preservation checks (Output A only)**
  - Presence of “Source Preservation Appendix”
  - Coverage of all anchors

### 10.2 Failure Handling (No Silent Failures)
If constraints fail:
- Status becomes **Warning** (unless the run errored)
- UI provides:
  - an explanation of which constraint failed
  - a “Regenerate with constraint fix” action that inserts a targeted prompt hint (while preserving user customizations)
  - links to Live Log filtered to that run
- User may override and proceed, but the dashboard records the constraint failure for traceability.

---

## 11. Model Selection and Provider Policies (4.3)

### 11.1 Model Allowlist (Ensured)
- OpenAI: `gpt-4o-mini`, `gpt-4.1-mini`
- Gemini: `gemini-2.5-flash`, `gemini-2.5-flash-lite`
- Anthropic: configurable set of Claude models (deployment-time configuration)
- Grok: `grok-4-fast-reasoning`, `grok-3-mini`

### 11.2 Per-Step Model Choice
Each of the following steps exposes its own model selector (defaulting from global settings, but overridable):
- Organized Document generation (Output A)
- Review Guidance generation (Output B)
- Skill.md generation
- Any optional extraction helpers (template normalization, entity audit, checklist refinement)

### 11.3 Max Tokens Defaults
- Default `max_tokens`: **12000** (user-editable per agent)
- The system warns if `max_tokens` is likely insufficient based on input size and constraints (warning only, not blocking).

---

## 12. WOW Observability Integration (Applies to 4.3 Additions)

### 12.1 WOW Interactive Indicator
- Shows pipeline stage:
  - A1 Organize
  - B1 Template normalization
  - B2 Review guidance generation
  - C1 Skill.md generation
- Clicking opens Run Inspector with:
  - selected model/provider
  - prompt snapshot (safe to display)
  - constraint results (tables/entities/length)
  - artifact links
  - Live Log deep link

### 12.2 Live Log Event Requirements (510(k) Module)
Events must include:
- document_type (summary / review note / guidance / mixed)
- template_source (default / pasted / described)
- constraints expected vs achieved
- warnings (e.g., “table count mismatch”)
- any regeneration attempts (with attempt count)

### 12.3 Dashboard Widgets (Extended)
The dashboard gains module-specific views:
- “510(k) Builder runs” timeline filter
- Constraint pass-rate trend across regeneration attempts
- Artifact lineage graph: Input → Output A → Output B → Skill.md
- Model comparison: runs by model for Output A vs Output B

---

## 13. Data Handling, Privacy, and Compliance Posture

### 13.1 Data Persistence
- Default: session-only storage; Space restarts clear state.
- User-controlled downloads: `.md`, `.txt`, log exports.

### 13.2 Sensitive Content Handling
- Input content may include confidential product details.
- System behavior:
  - does not transmit data anywhere except chosen LLM providers during execution
  - does not store content server-side beyond session state
  - does not log document contents in Live Log beyond high-level metrics (sizes, status), except where users explicitly view artifacts in UI

### 13.3 Key Redaction
- API keys are never displayed.
- Logs must not contain secrets.
- Best-effort redaction for secret-like strings if present in prompts.

---

## 14. Deployment on Hugging Face Spaces (Streamlit + agents.yaml)

### 14.1 Required Configuration
- Streamlit app with modular tabs
- Default `agents.yaml` including:
  - 510(k) Organized Doc agent
  - Template normalizer agent
  - 510(k) Review Guidance agent
  - Skill.md generator agent (skill-creator style)
  - Optional constraint-fixer helper agent (prompt-only, no code)
- Provider secrets configured in Space settings:
  - `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY` (names may be mapped by configuration)

### 14.2 Operational Guardrails
- Rate limit guidance with user-facing retry suggestions.
- Provide safe defaults for temperature and max tokens.
- Provide document-size warnings for extremely long pasted content.

---

## 15. Acceptance Criteria (4.3)

1. All SmartMed Review 4.2 features remain functional and visually consistent under WOW UI v2.
2. Users can paste 510(k) summary/review note/guidance and generate **Organized Document** meeting:
   - 2000–3000 word target band (with visible estimate method)
   - exactly 5 Markdown tables
   - exactly 20 entities with context and source anchors
   - “Source Preservation Appendix” present and complete
3. Users can provide a template (pasted/described/default) and generate **510(k) Review Guidance** meeting:
   - 3000–4000 word target band
   - exactly 5 Markdown tables
   - exactly 20 entities with context
   - includes a structured review checklist
4. Users can edit Output A and Output B in Markdown/Text views and download as `.md`/`.txt`.
5. Users can choose models and modify prompts/parameters at each step; the system supports sequential agent execution and editable intermediate outputs.
6. Users can generate and edit a `SKILL.md` using the skill-creator approach; skill output includes trigger description and structured review workflow.
7. All runs are observable via WOW indicator, Live Log, and dashboard with constraint reporting and artifact lineage.
8. API key behavior follows environment-first policy; UI key input appears only when missing; no key is displayed or logged.

---

## 16. Follow-up Questions (20)

1. For “**keep all original information**,” should the system treat *any* paraphrase in the structured layer as acceptable so long as the verbatim text is preserved in the appendix, or must the structured layer also avoid paraphrasing entirely?
2. Should the **Source Preservation Appendix** preserve formatting exactly (including line breaks and bullet indentation), or is whitespace normalization acceptable as long as content is verbatim?
3. What is the preferred **anchor granularity**: paragraph-level, sentence-level, or heading+paragraph blocks (balancing traceability vs readability)?
4. For the **20 entities**, do you want a fixed distribution by type (e.g., at least 3 tests, 3 claims, 2 standards), or should entity selection be purely utility-based?
5. Should entities be allowed to reference **multiple anchors** (recommended for context), and is there a maximum number of anchors per entity you want to enforce?
6. For the **5 tables** in Output A and Output B, are the proposed table semantics acceptable as defaults, or do you require different standardized tables aligned to your internal review SOP?
7. If a user-provided template already contains tables, should the system **reproduce those exact tables** (counting toward the “exactly 5” total), or always generate new tables and keep template tables as plain text?
8. In the Review Guidance output, should the **review checklist** be a numbered list, a table, or a hybrid (noting that tables count toward the strict “5 tables” constraint)?
9. Do you want the checklist to include **pass/fail/NA fields** explicitly formatted for copy/paste into Excel, or keep it purely Markdown narrative?
10. Should the module support optional **jurisdiction modes** (FDA 510(k) vs TFDA vs EU MDR) that change the default headings and checklist emphasis?
11. When the user supplies only a “template description,” should the system generate a **template outline artifact** that the user can edit before the final guidance generation step?
12. For word count constraints in Traditional Chinese, do you want the UI to enforce **character count bands** instead (e.g., 3000–6000 chars) to reduce ambiguity?
13. Should the system include a **“diff view”** (raw vs edited) for Output A and B to improve review traceability and audit readiness?
14. Do you want Output A and B to include **explicit citations** (anchor references) inline throughout the document body, or only in entity/table sections to reduce clutter?
15. For the **model selector**, should certain steps default to different providers (e.g., Gemini for long-context, OpenAI for structured formatting), or keep one global default model unless overridden?
16. Should the system offer an optional **“format-hardening pass”** agent that only fixes table counts/entities/checklist structure without changing substantive content?
17. For the **Skill.md generation**, should the skill’s trigger description target only “510(k) submission review,” or also trigger on adjacent tasks like “draft deficiency letter,” “RTA check,” or “substantial equivalence analysis”?
18. Do you want the generated skill to mandate a **standard output package** (e.g., memo + deficiency list + checklist + risk summary) every time, or allow users to request only one of those outputs?
19. Should the Live Log and dashboard support a **downloadable run bundle** (zip of artifacts + logs + prompts) for internal archiving, while still remaining user-initiated and session-local?
20. Are there any specific **regulated content warnings** or disclaimers (company-standard language) that must appear in the UI and at the top of generated guidance/skill outputs?
