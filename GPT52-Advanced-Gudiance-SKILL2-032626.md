SmartMed Review 4.3.1 — Updated Technical Specification (Streamlit on Hugging Face Spaces)
Document Version: 4.3.1
Date: 2026-03-26
Status: Updated Technical Specification (Design + Implementation Guidance; no code included)
System Name: SmartMed Review 4.3.1 (智慧醫材與 510(k) 審查指引/清單/技能生成工作站)
Deployment Target: Hugging Face Spaces (Streamlit)
Core Stack: Streamlit + agents.yaml + Multi-LLM routing (Gemini / OpenAI / Anthropic / Grok) + OCR (optional modules) + Artifact workspace + WOW Observability
Primary Update Focus (4.3.1): “Show results directly” UX, non-noisy optional validation, and prompt editing for every LLM feature, plus hardened Streamlit state synchronization to prevent “blank output” UI bugs.

1. Executive Summary
SmartMed Review 4.3.1 is an agentic regulatory workspace designed to support medical device regulatory authoring and review workflows, with a particular emphasis on 510(k) transformation workflows and review guidance generation. It preserves all capabilities introduced in SmartMed Review 4.2 and 4.3—WOW UI v2, multi-provider model routing, environment-first API key handling with UI fallback, agent-by-agent execution with editable prompts and outputs, AI Note Keeper with keyword highlighting and AI Magics, observability (WOW Indicator, Live Log, Dashboard), and agents.yaml driven orchestration.

Version 4.3.1 specifically addresses usability and logic issues discovered during practical testing with “Sample A” inputs:

Results-first UX: Every stage (Organized Document A, Template Outline, Review Guidance B, SKILL.md C, Note Organizer, Note Magics, Agent Studio runs) must display LLM results directly, persistently, and immediately after generation.

Non-noisy validation: The app must not block users or “spam” warnings such as:

Table count mismatch: expected 5, got 0
Entity count mismatch: expected 20, got 0 These checks are redefined as optional validation that is:
Off by default
Never triggers warnings on empty outputs
Does not prevent any downstream steps
Treated as advisory telemetry rather than an “error state”
Prompt editability everywhere: Users can modify system prompts and user prompt templates for each LLM feature in the app (not only in Agent Studio), including the 510(k) pipeline stages and Note Keeper actions.

Streamlit state hardening: The specification formalizes a reliable pattern for synchronizing Streamlit widget state with generated outputs to prevent common “blank output” bugs caused by widget-key persistence overriding updated session values.

This version is optimized for real-world iterative drafting workflows: generate → view → edit → chain, without surprise blocking or validation noise.

2. Product Goals and Non-Goals
2.1 Goals
Human-in-the-loop by design: users control each stage with explicit model selection, prompt edits, and output edits.
Reliability of display: generated outputs must always be visible after a successful run, across reruns and tab switches.
Minimal friction: validation is supportive, not intrusive; the user’s primary experience is the content output.
Security-first API key behavior: environment keys take precedence; UI fallback is session-only; keys never displayed or logged.
Provider-agnostic generation: consistent UI across OpenAI/Gemini/Anthropic/Grok.
2.2 Non-Goals
No server-side persistence database is required (session-only by default).
No enterprise RBAC, audit trails, or multi-tenant data isolation.
No claim of regulatory authority; outputs are drafting aids, not final determinations.
No mandatory formatting compliance enforcement (the system can recommend, not enforce).
3. User Personas and Key Journeys
3.1 Personas
Regulatory Affairs author: needs structured documents and guidance drafts quickly; must preserve original facts.
Reviewer / QA: needs repeatable checklists and traceability mapping; wants transparency and reproducibility.
Technical maintainer: needs simple HF deployment with secrets management and stable workflows without brittle UI state issues.
3.2 Primary User Journey (510(k) Guidance Builder)
Paste input document (summary, reviewer note, or guidance) in TXT/Markdown.
Configure model, max tokens, temperature; edit prompt for Step A.
Generate Organized Document (A); immediately view and edit results.
Provide template: default / pasted / described. Edit prompt for template normalization.
Generate Template Outline; view and edit.
Edit prompt for Step B; generate Review Guidance (B); view and edit.
Edit prompt for Step C; generate SKILL.md; view and edit.
Download any artifact; optionally save as named artifacts for reuse in Agent Studio.
3.3 Secondary Journey (AI Note Keeper)
Paste messy notes (TXT/Markdown).
Edit prompts and generate organized note with coral-highlighted keywords.
Apply AI Magics with model selection and prompt editing per magic.
Download results or store as artifacts.
4. System Architecture (High-Level)
4.1 Components
A. Streamlit UI Layer

Sidebar: global settings (theme, language, painter style + jackpot), provider key readiness and UI fallback, default model parameters, agents.yaml override.
Main tabs: Dashboard, Live Log, 510(k) Guidance Builder, Agent Studio, AI Note Keeper.
Persistent top status panel: WOW indicator showing current run state.
B. Session State Layer
All user inputs, outputs, prompts, and artifacts are stored in st.session_state. No persistence is assumed beyond the session runtime.

C. LLM Integration Layer
A unified request interface routes calls by selected model/provider:

OpenAI: chat completions endpoint
Gemini: generateContent endpoint
Anthropic: messages endpoint
Grok/xAI: OpenAI-compatible chat completions endpoint
D. Orchestration Layer (agents.yaml)

Agents define default system prompts and user prompt templates.
The app supports a fallback built-in agent set if YAML is missing.
Users can override agent definitions via sidebar upload/paste.
E. Observability Layer

Structured run events appended to Live Log.
Runs summarized for Dashboard timeline and model/provider mix.
5. WOW UI v2 (Preserved)
5.1 Global UI Controls
Theme: Light / Dark
Language: English / Traditional Chinese (繁體中文) for UI labels and messages
Painter Style Presets (20): aesthetic theme tokens applied across the entire app
Jackpot: random style selection; optional session lock to prevent reroll on rerun
5.2 Design Tokens
Background gradients and panel translucency
Accent colors and coral highlight for keywords
Rounded UI elements and consistent spacing
Accessibility considerations: readable contrast, consistent typography
6. Observability: WOW Indicator, Live Log, Dashboard (Preserved + Strengthened)
6.1 WOW Indicator (Run Status)
Displays whether a run is active or idle.
Shows current run_id.
Must never leak sensitive data.
6.2 Live Log (Structured Events)
Events include:

timestamp (UTC)
run_id
module (510k, note_keeper, agent_studio, skill, artifacts, keys, system)
severity (info/warn/error)
event_type (run_started, preflight, exception, run_ended, artifact_saved, constraint_warning)
human-readable message (with best-effort redaction)
extra metadata (model, provider, runtime parameters, optional summary metrics)
4.3.1 policy: validation warnings (if enabled) are recorded as warn-level events; otherwise, no warning events are emitted for constraints.

6.3 Dashboard (Session Analytics)
Run timeline table
Success/error counts
Model/provider usage mix
Artifact quick access preview
Intended to support rapid debugging: confirm that a run completed and produced output.
7. API Key Management (Environment-First, UI Fallback)
7.1 Priority Rules
Environment secrets from Hugging Face Space
Session-only keys entered via UI
7.2 UX Rules
If environment key exists: display “Managed by environment” (never display key)
If missing: show password input for UI entry; allow clearing the session key
Keys must never be logged; logs redact common token patterns.
7.3 Preflight Behavior
Before any LLM call:

Determine provider from model name.
If key missing: the run is blocked and an error is shown; a log event records the failure without secrets.
8. Model Selection and Parameters
8.1 Supported Model Set (UI Allowlist)
At minimum:

OpenAI: gpt-4o-mini, gpt-4.1-mini
Gemini: gemini-2.5-flash, gemini-2.5-flash-lite
Anthropic: claude-* models as configured (e.g., claude-3.5-sonnet, claude-3.5-haiku)
Grok/xAI: grok-4-fast-reasoning, grok-3-mini
8.2 Parameter Controls
Each LLM feature exposes:

model selector
max_tokens (default 12000 for long documents; smaller defaults allowed for template outline/magics)
temperature
4.3.1 note: token/length warnings are advisory only; the system does not block on length compliance.

9. Prompt Editing Everywhere (4.3.1 Core Requirement)
9.1 Scope of Prompt Editability
Users must be able to modify system and user prompt templates for:

510(k) Stage A: Organized Document generation
510(k) Template normalization (Template Outline)
510(k) Stage B: Review Guidance generation
510(k) Stage C: SKILL.md generation
AI Note Organizer
Each AI Magic (9 magics), individually
Agent Studio already supports prompt editing per agent
9.2 Prompt Override Storage
Prompt overrides are stored in session state and applied on subsequent runs. They are not persisted server-side. Recommended behaviors:

Clear default indicator (“overridden” badge) when a prompt differs from default.
Optional “reset to default” actions (implementation choice; recommended but not mandatory).
9.3 Prompt Safety
Prompts must not include API keys.
The app redacts potential secrets if pasted accidentally into prompt text.
10. Results-First Output Display (4.3.1 Core Requirement)
10.1 Display Principles
For every stage:

Show the LLM output directly as a persistent artifact view (not only inside a button press block).
Provide an editor (Markdown and/or Text) for user modifications.
Render a preview for Markdown output, but also keep raw text visible to avoid parser discrepancies.
10.2 Persistence Across Reruns
Streamlit reruns on every interaction, so output display must be:

derived from session state, not from transient local variables
resilient to widget-state overriding (see §13)
10.3 Editing and Chaining
After a user edits output:

The edited version becomes the effective output for downstream steps.
The raw output remains available for reference (either stored separately or accessible via artifacts/logs).
11. Optional Validation: Non-Noisy Constraints (4.3.1 Redefinition)
11.1 The Problem
Strict constraints (exact table counts, exact entity counts, word bands) are useful for quality control but frequently produce confusing warnings when:

output is empty (not yet generated)
output is partial due to token limits
model deviates from strict formatting
CJK content confounds word estimators
validators are heuristic and not semantically aware
11.2 The 4.3.1 Validation Policy
Validation is optional and off by default.
Validation does not prevent output display.
Validation must not show mismatch warnings when output is empty.
Validation warnings should be shown only when:
validation is enabled for that artifact, AND
output is non-empty, AND
mismatch exists
11.3 What Validation Measures (Heuristic)
When enabled, validation may compute:

Markdown pipe-table count (heuristic)
entity marker count (heuristic based on a pattern like - **Entity #N**)
word estimate and character count
4.3.1 guidance: character count is always displayed to mitigate CJK ambiguity; word estimates should be labeled as approximate.

11.4 User Experience
Validation is presented as:

a collapsed “Constraint Panel (optional)” expander
metrics shown as informational
warnings appear only if user enables validation
This ensures a “results-first” experience while still allowing strict users to validate output.

12. 510(k) Guidance Builder Module (A → Template → B → C)
12.1 Stage A — Organized Document (A)
Input: pasted 510(k) submission summary, review note, or guidance (TXT/MD).
Output: an organized Markdown document intended to preserve all original information while structuring content for review.

Key behaviors:

User can edit prompt, choose model, set max tokens/temperature.
The generated output is immediately shown, then stored as:
raw output (for provenance)
effective output (user-editable; used downstream)
Recommended output structure (default prompts):

structured headings (scope, device overview, intended use, technology, testing, labeling, manufacturing, open issues)
source-preservation strategy (appendix/verbatim anchors) when strict preservation is required
tables/entities may be requested by prompt, but the app does not require them unless validation is enabled.
12.2 Template Input Modes
Users choose one:

Default template: built-in DCB guidance template (Traditional Chinese)
Paste template: user provides a full template in TXT/MD
Describe template: user describes desired template structure and requirements
12.3 Template Outline Generation
The template outline step normalizes template inputs into an actionable outline that Stage B can follow. Users can:

edit prompt
edit the generated outline manually
12.4 Stage B — Review Guidance (B)
Transforms Organized Document + Template Outline into a 510(k) review guidance document. Requirements are template-driven. Typical output includes:

reviewer focus areas
evidence expectations
deficiency risks and decision triggers
review checklist (if the prompt requests it)
Again, strict table/entity constraints are prompt-driven and validated only optionally.

12.5 Stage C — SKILL.md Generation (Skill Creator Style)
Generates a SKILL.md describing a reusable “review skill” that can be used by an agent later to review a 510(k) submission consistently.

The skill should include:

pushy trigger description (“use whenever the user asks for 510(k) review, deficiency checks, completeness review…”)
step-by-step review workflow
output format templates (memo, deficiency list, checklist, traceability summary)
guardrails (no fabrication; cite submission sections)
2–3 realistic test prompts
Users can edit prompts and the resulting skill file in Markdown.

13. Streamlit State Management and Output Visibility (Bug Prevention Requirements)
13.1 Known Failure Mode: “Output Generated but Editor Shows Blank”
In Streamlit, widget state is keyed and persistent. If a text area is created with a key and later the app assigns a new value to a different session key, the widget may continue displaying the old (empty) state.

13.2 Specification Requirement: Stable Output Editor Pattern
For every editable output:

Maintain dedicated widget-state keys (e.g., effective_output__md_widget) separate from raw/effective storage keys.
Initialize widget state only when missing, derived from the latest effective output.
Avoid having both Markdown and Text tabs write back to the same session key on every rerun; adopt a single canonical source of edits (typically the Markdown widget), or define a clear reconciliation rule.
13.3 Persistent Output Rendering
Outputs must be rendered outside the “button click” block so they remain visible after reruns:

The UI should always show the latest effective output for each stage.
This ensures “show results directly” remains true even after the user changes a dropdown or edits a prompt.
13.4 Explicit Rerun After Generation (Recommended)
After successful generation:

Update effective output and widget state keys.
Trigger a rerun so UI rehydrates with the latest output in editors and previews.
This reduces the chance that the user sees stale outputs.

14. Agent Studio (Preserved)
14.1 Capabilities
Select an agent from loaded agents.yaml definitions.
Choose input source: paste or artifact.
Edit system prompt and user prompt template.
Choose model and parameters.
Run agent and show results immediately.
Edit output (effective output).
Save output as artifact with user-defined name.
14.2 Integration with 510(k) Builder
Outputs from 510(k) stages are saved as artifacts (e.g., 510k_organized_doc_A.md, 510k_review_guidance_B.md, SKILL.md), allowing Agent Studio to reuse them as inputs.

15. AI Note Keeper (Preserved + Prompt-Editable)
15.1 Note Organizer
User pastes note in TXT/MD.
Chooses model and parameters.
Edits organizer prompts.
Generates organized Markdown with coral-highlighted keywords.
Edits results and downloads.
15.2 AI Magics (9)
Each magic:

is model-selectable and parameterized
has its own prompt editor (system + user template)
runs on the effective note content
produces a Markdown output
is saved as an artifact if desired
16. Artifact Management
16.1 Artifact Types
Artifacts are named text blobs stored in session state:

510(k) outputs A/B
Template outline
SKILL.md
organized notes and magic outputs
agent studio outputs
16.2 Download Support
Download as .md and .txt for any major output.
Encourage users to download important content because HF Spaces may restart.
16.3 Provenance Metadata (Recommended)
Artifacts may include metadata:

model used
stage/module
timestamp
parameters This supports reproducibility and debugging.
17. Reliability and Error Handling
17.1 Expected Failures
Missing API key: preflight block and friendly message.
Provider rate limit or quota: show error from provider; log details.
Network timeouts: show failure; allow rerun or model/provider switch.
Partial outputs due to token limits: still display output; optionally suggest increasing tokens.
17.2 No-Silent-Failure Rule
If a run fails:

the error must be visible in the UI
a log event must be recorded with module, run_id, and exception message (redacted as needed)
18. Security, Privacy, and Compliance Considerations
18.1 Data Privacy Defaults
Session-only state; no persistent database.
User-initiated downloads only.
Document content is sent only to the chosen LLM provider at run time.
18.2 Key Safety
Environment keys never displayed.
UI keys stored only in session.
Best-effort redaction in logs and messages.
18.3 Responsible Output Guardrails (Prompt-Level)
Prompts should instruct models not to fabricate evidence or claims.
When uncertain: label assumptions and request verification.
Encourage traceability (anchors, citations) when appropriate.
19. Deployment on Hugging Face Spaces
19.1 Required Environment Secrets
OPENAI_API_KEY
GEMINI_API_KEY
ANTHROPIC_API_KEY
XAI_API_KEY
19.2 Optional Files
agents.yaml for custom agent definitions. If absent, built-in defaults must operate.
Optional skill reference documentation (display-only) if desired.
19.3 Operational Notes
Spaces restarts can clear session state; artifacts should be downloaded.
Logs are session-local unless exported.
20. Acceptance Criteria (4.3.1)
Results-first display: Output A/B/C, Template Outline, Note outputs, Magic outputs, and Agent Studio outputs remain visible after reruns and parameter changes.
Prompt editability everywhere: each LLM feature has editable system and user prompt fields.
Optional validation: constraint mismatch warnings are off by default and never appear on empty outputs.
No “only error message” UX: mismatch warnings (when enabled) appear in a dedicated optional panel and never suppress output editors.
Streamlit state reliability: the app avoids “blank editor despite output generated” failures via stable widget-state synchronization.
Security rules: environment keys never shown; UI keys session-only; logs redact secrets.
Multi-provider routing: supported models run successfully when keys are provided; errors are surfaced and logged.
Follow-up Questions (20)
Should optional validation be configurable as a global preference (apply to all stages) in addition to per-stage toggles?
Do you want a dedicated “viewer-only” mode that displays outputs without editors for stakeholder review/share screen sessions?
Should the app implement a “Reset editor from latest output” control to recover quickly if widget state drifts?
Do you want automatic artifact versioning (e.g., ..._v1, ..._v2) so reruns never overwrite prior outputs?
Should the system store prompt overrides with timestamps as a prompt history to support reproducibility and rollback?
Do you want a “prompt library export” (JSON/MD) to save all prompts used in a session without exporting document content?
Should the dashboard show per-run metrics like output character length and input character length to quickly validate that content was generated?
Do you want a structured “run bundle export” (zip: artifacts + prompts + logs) that is user-initiated and session-local?
Should the app support customizable provider base URLs (for proxies or enterprise gateways) via sidebar settings?
Do you want a formal “repair formatting” optional step that post-processes outputs to meet table/entity targets without changing meaning?
For Chinese-heavy documents, should length validation (when enabled) use character bands instead of word estimates automatically?
Do you want the app to detect and warn if the model output contains unintended HTML that might affect Markdown rendering?
Should template normalization be optional, allowing users to pass raw templates directly into Stage B for advanced use cases?
Do you want explicit “chain this output to next stage” buttons, or is implicit chaining via effective output sufficient?
Should the app include a built-in “diff viewer” (raw vs effective output) for audit-style traceability?
Do you want to enforce a consistent citation scheme (e.g., SRC-###) across stages even when constraints are not enabled?
Should the system include provider-specific guidance (recommended max tokens/temperature presets) based on the selected model?
Do you want “Note Magics” outputs to optionally update the main effective note automatically (overwrite), or remain separate artifacts only?
Should Live Log support advanced filtering by model/provider and the ability to click a run to open the exact stage with outputs loaded?
Do you want additional first-class 510(k) tools (e.g., Substantial Equivalence comparison matrix generator, deficiency letter drafting, RTA completeness checklist) with the same results-first and prompt-editable design?
