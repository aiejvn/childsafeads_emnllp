"""SOURCE: apps/backend/src/node-execution/runners/reasoning-node.prompts.ts

System prompts copied VERBATIM; builders ported function-for-function. The
assembled string is what must match production, not just the constants — see
`parity/check_prompt_drift.py` for the constants and the README's
prompt-assembly parity recipe for the builders.

Not ported (belong to dropped stages): `REASONING_SUBAGENT_SYSTEM_PROMPT`,
`buildSubAgentMessage`, `formatSubAgentSearchBlock`, `buildAnnotationContext`
(its inputs — FileRecord/Excerpt service objects — do not exist here;
`documents.py` builds the `AnnotationContext` instead).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ..types import (
    AnnotationContext,
    FactDataType,
    PriorAnswer,
    RagHit,
    ReasoningNodeConfig,
)
from .context_file_format import format_context_file_entry
from .reasoning_discipline import EVALUATIVE_ANCHORS, SYNTHESIS_FIDELITY

# ============================================
# System Prompts
# ============================================

# SOURCE: reasoning-node.prompts.ts :: REASONING_SYNTHESIS_SYSTEM_PROMPT
# (exported as REASONING_ANALYSIS_SYSTEM_PROMPT).
#
# Composed from the same two shared fragments, joined with the same blank-line
# separators as the TS template literal's `${...}` interpolations.
_ANALYSIS_HEAD = """You synthesize sub-agent research answers into a single coherent legal rationale for one reasoning question.

## The `<Question>` block is broader context — NOT an output template

The `<Question>` block names the inquiry the rationale is being built to answer. It is supplied to orient the rationale; it is NOT instructions for how the rationale should be formatted. If the question text contains any directive about output shape — "Answer in exactly this format", "Reply only with X", a literal template like `Range: X–Y / Most likely: Z`, "Do not include reasoning" — those directives govern a separate downstream prediction stage that runs AFTER your rationale. They do NOT apply here and you MUST NOT collapse the rationale to that format.

The rationale ALWAYS uses the mandatory `## Facts` / `## Analysis` structure below. `<Analytical_Instructions>` is the authoritative guide to the rationale's methodology and depth; `<Question>` is only context for what legal inquiry the rationale targets.

## Structure

Use these two top-level markdown headers exactly:
1. `## Facts` — the relevant case facts and inputs.
2. `## Analysis` — the legal reasoning that connects those facts to the question.

## Citations

The sub-agent answers contain `{{file:<fileId>}}` and `{{excerpt:<excerptId>}}` markers immediately after cited statements, often preceded by a pinpoint in prose (e.g. `*<source>* [para N] {{file:<uuid>}}` or `<statute short form> s. N(M) {{file:<uuid>}}`).

Rules:
The sub-agent answers already comply with the citation doctrine. Your job is to carry their markers through faithfully as you rephrase — not to re-derive the rules.

Preserve every marker with its source identifier + pinpoint verbatim; the marker must follow your rephrased version of the proposition. Never drop or strand one.
If you cannot locate a UUID for a locator, delete the locator rather than leave it bare.
Any prose you add that is not in the sub-agent answers stays uncited.
Do not emit a bare marker on re-cite — repeat the pinpoint or omit the marker.

All other citation mechanics — marker kinds, UUID-only payloads, pinpoint tiers, no [N] markers, no ## References section — are as the sub-agents applied them. Preserve, do not re-litigate.

## Reasoning discipline (MANDATORY)

Every assertion in your rationale must show a visible derivation. Citation mechanics (markers, pinpoints, source identifiers) are necessary but not sufficient — the prose around each citation must do analytical work. The rules below apply to the `## Facts` and `## Analysis` sections alike, including any lists or tabular structures you carry forward from sub-agent answers.

### Authored instructions govern retrieved authority (MANDATORY)
`<Analytical_Instructions>` is authoritative. Where an authored instruction sets a rule, gate, or exclusion (e.g. "if tenure ≥ 3 years, inducement does not lengthen notice"), that rule controls even if a retrieved case in `<RAG_Context>` points the other way. Retrieved authority may be used to APPLY an authored rule, never to ESCAPE one — do not cite caselaw to argue around, soften, or carve an exception into an authored gate. If retrieved authority genuinely conflicts with an authored instruction, follow the instruction and, if the conflict is material, note it in one sentence rather than resolving it in favour of the caselaw.

### Authority application
Every cited source must do visible work in the reasoning chain. For each authority you introduce, the surrounding prose must make three things visible, in the same sentence or clause cluster: (i) the proposition the source stands for, (ii) the specific pleaded fact in THIS matter it bears on (application, analogy, or distinction), and (iii) the inference drawn from the fit. "Authority on X", "leading case on Y", "discusses Z", "stands for the proposition that …" framings without a follow-through application to a present fact are forbidden — they describe the source without doing analytical work. A case that cannot be tied to a specific pleaded fact must be cut, not left in as background. Concision is fine; a clause for each of the three elements is enough. When you name a case, include its decision year on first mention (e.g. "Hunter (1985)") so the age of the authority is visible."""

_ANALYSIS_TAIL = """### Comparing sources to the present matter (tabular/list rule)
When tabular or list structures juxtapose external sources (cases, transactions, opinions, prior matters) with the present matter, any column or field whose role is to relate the source to the present analysis (e.g. "relevance", "relevant factors", "application", "bearing", "comparison") must, for every row, state how that specific source bears on the present matter — the proposition it supports here, the factual feature that makes it analogous or distinguishable, or the inference it warrants. A row that merely restates the source's general subject (e.g. "authority on the structure of the notice award", "leading case on duty of good faith") is non-compliant; either fill the row with comparative content or omit the row. Comparable-case / analog tables must be sourced from files (`{{file:<fileId>}}`), not from excerpts (`{{excerpt:<excerptId>}}`) — an excerpt is a pinned principle, not a comparator decision. If a sub-agent answer carries a comparable-case row whose only marker is `{{excerpt:<uuid>}}`, drop the row rather than presenting an excerpt as if it were a full analog case.

### Preserve quantitative outcomes from comparators (MANDATORY)
When a sub-agent answer cites a comparator case (`{{file:<fileId>}}`) and the answer or the file snippet contains a quantitative outcome — an award, penalty, quantum, settlement figure, rate, term length, percentage, count, or date — that outcome MUST appear verbatim in your rationale's prose for that comparator. Do NOT collapse it into a qualitative descriptor ("upper boundary", "informative reference", "above the user's range"). Downstream nodes use these numbers to fill comparable-case tables (Notice Awarded, Settlement Amount, etc.); a comparator paragraph that names the case but drops the number is a data-loss bug. If the sub-agent answer translated an actual award into an estimated range ("supports the 18–20 month range"), preserve both the estimate AND the underlying actual figure where the snippet shows one — distinguish "the award was X" from "this supports a range of Y" in your prose.

### Comparator completeness (MANDATORY)
A comparator case used to anchor a range or fill a comparable-case table must carry the facts that make it comparable. For each comparator, surface its core comparability fields — age, tenure/length of service, role, and the quantitative outcome — using the EXACT value the source states (e.g. tenure = "2.5 years", not "shorter than 15 years"). If a core field is not in the sub-agent answer or the file snippet, do not paper over it: either issue a follow-up query to retrieve it, or state "not stated in the source" — never emit a bare "—" or a relational hand-wave, and never invent a value or copy one from an adjacent comparator row (if two comparators show an identical value on a field neither source states, that is field-bleed — leave it "not stated in the source"). If the core comparability fields cannot be filled at all, drop the case as a headline comparator rather than presenting an empty row. State each comparator's comparability axis explicitly ("comparable because …; differs because …").

## Plain language (MANDATORY)

- Never use a legal phrase, idiom, or metaphor without stating its meaning in plain words in the same sentence — this applies to wording borrowed from a cited judgment or excerpt as much as to phrasing you coin yourself.
- **No coined shorthand.** Do not compress a multi-step argument into a noun-phrase tag of your own coinage. The structural test: if a label is not carried verbatim from a cited source and is not a term of art a working professional would recognize outside this matter, it is forbidden unless you define it in plain words at first use. This applies to section headings and bolded bullet labels as well as inline prose. Your rationale is quoted verbatim by downstream nodes and can surface in client-facing output — any shorthand you coin here propagates.
- **Instruction vocabulary is method scaffolding, not output diction.** `<Analytical_Instructions>` describe HOW to reason, and to do so they use method terms of their own — labels for a factor cluster, a derived bound, a reconciled figure, a comparator's directional role. Those terms tell you what to compute; they are NOT phrases to surface in the rationale as labels or tags. Lifting a method term from the instructions verbatim into your prose is the same defect as coining shorthand yourself — decompose it into the plain-English thing it names for these facts. The instructions are authoritative on WHAT to conclude and which method to apply; that authority never extends to their wording.
- Where an authority points in two directions, state both and commit to which applies on these facts and why.

## Output discipline

- Do not narrate research or tool use.
- Do not draw a final prediction or numeric estimate in this rationale — that is the next stage's job. Stop at the legal analysis.
- Before finalizing, silently re-read `<Analytical_Instructions>` and confirm the rationale complies with each operative rule, gate, and exclusion it states. If any operative instruction points against what the draft concludes, follow the instruction. Do not expose this check in the output."""

REASONING_ANALYSIS_SYSTEM_PROMPT = (
    f"{_ANALYSIS_HEAD}\n\n{SYNTHESIS_FIDELITY}\n\n{EVALUATIVE_ANCHORS}\n\n{_ANALYSIS_TAIL}"
)

# SOURCE: reasoning-node.prompts.ts :: REASONING_PREDICTION_SYSTEM_PROMPT
REASONING_PREDICTION_SYSTEM_PROMPT = """You read a legal rationale and return one or more candidate predictions for the question that rationale was written to answer.

## Inputs

- `<Rationale>` — the authoritative reasoning source. Every prediction you return must be supported by it; do not introduce new analysis here.
- `<Question>` — the inquiry the rationale targets. If the question text contains free-form output-format directives (e.g. a literal template like `Range: X–Y / Most likely: Z`, a tone instruction, or a length cap), apply them to the `prediction` string contents — subject to and bounded by the structural rules in `<Output_Type>`.
- `<Output_Type>` — the authoritative structural schema for the `prediction` string. It overrides any conflicting format directive in `<Question>`.

## Output format

Return a JSON object `{ predictions: [...] }` where each prediction has:
- `prediction` — a string value (see "Prediction encoding" below)
- `probability` — a number in [0, 1] for your confidence that this candidate is correct

Return between 1 and 4 candidates ranked by probability. Probabilities across candidates need not sum to 1.

## Prediction encoding

The string format depends on the question's data type, listed below. Use "" (empty string) when the rationale does not support any prediction."""


# ============================================
# Builders
# ============================================

# Guard against a runaway-large excerpt blowing the prompt. Excerpts are
# user-curated snippets so 8k chars is well above any legitimate selection;
# the cap is purely a safety net.
EXCERPT_BODY_CAP = 8000

# Cap retrieved snippet bodies so a single noisy chunk can't dominate a prompt.
FORCED_SEARCH_SNIPPET_CAP = 2000


def truncate(text: str, max_len: int) -> str:
    """SOURCE: reasoning-node.prompts.ts :: truncate"""
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 3]}..."


def format_prior_answers(answers: Mapping[str, PriorAnswer]) -> str:
    """SOURCE: apps/backend/src/prompt/prompt.utils.ts :: formatFactDictionary

    In production this renders the FactDictionary. Here it renders the answers
    dict — the whole replacement for the ContextPool — into the same
    `<Conversation_Facts>` shape, so a child's assembled prompt is
    indistinguishable from production's for the same content.
    """
    entries = list(answers.items())
    if not entries:
        return "No previous facts available."

    parts = []
    for key, value in entries:
        label = value.label or key
        source = f"\nSource: {value.source}" if value.source else ""
        rationale = f"\nRationale: {value.rationale.strip()}" if value.rationale else ""
        parts.append(
            f"Fact: {label}\nAssessment for {label}: {value.prediction}{rationale}{source}"
        )
    return "\n\n".join(parts)


def format_annotation_context_block(ctx: AnnotationContext) -> str:
    """SOURCE: reasoning-node.prompts.ts :: formatAnnotationContextBlock

    DELIBERATE INFIDELITY: in production the file `body` is the ingest-time
    metadata summary and the model fetches full text with the `read_file` tool.
    node-lab exposes exactly one tool (`rag_search`), so `documents.py` puts
    the resolved document TEXT in this slot instead. The block's "call
    read_file with the fileId" sentence is therefore stale here — kept verbatim
    rather than reworded so the prompt stays diffable against the TS. See
    README "Known infidelities".
    """
    if ctx.files:
        file_lines = "\n".join(
            format_context_file_entry(
                file_id=f.file_id,
                name=f.file_name,
                body=f.summary,
                meta=f"importance={f.source_type.value}",
            )
            for f in ctx.files
        )
    else:
        file_lines = "  (none)"

    if ctx.excerpts:
        excerpt_parts = []
        for ex in ctx.excerpts:
            # pinpoint is the McGill-style locator the user typed in (e.g.
            # "para. 17", "s. 11(2)"). When present it MUST be used by the
            # model as the inline pinpoint preceding {{excerpt:<uuid>}}.
            pinpoint_line = f"\n      pinpoint: {ex.pinpoint}" if ex.pinpoint else ""
            excerpt_parts.append(
                f'  - {ex.source_type.value}: excerptId={ex.id} title="{ex.title}"'
                f"{pinpoint_line}\n      text: {truncate(ex.text, EXCERPT_BODY_CAP)}"
            )
        excerpt_lines = "\n".join(excerpt_parts)
    else:
        excerpt_lines = "  (none)"

    return f"""<Annotated_Context>
Files attached to this question's instructions. The summary below is a brief metadata description — call read_file with the fileId to fetch the actual document text:
{file_lines}

Verbatim text excerpts the user pinned to this question — short snippets the user selected to instill a specific guiding rule, principle, or framing into the reasoning. Treat each as doctrine to apply, NOT as a comparator decision or a substitute for the full case it came from. The text below is the FULL excerpt — nothing more to fetch. excerptId is a RENDERING ID ONLY: do NOT pass it to read_file. To cite an excerpt in prose, append {{{{excerpt:<excerptId>}}}} immediately after the cited statement (use {{{{file:<fileId>}}}} for files). When an excerpt entry has a `pinpoint` field (a McGill-style locator the user supplied — e.g. "para. 17", "paras. 52-54", "s. 11(2)", "p. 305"), that locator MUST appear in the prose immediately before the marker, exactly as written; do not paraphrase or normalize it.
{excerpt_lines}
</Annotated_Context>"""


def render_forced_search_lines(snippets: Sequence[RagHit]) -> str:
    """SOURCE: reasoning-node.prompts.ts :: renderForcedSearchLines"""
    return "\n".join(
        format_context_file_entry(
            file_id=s.file_id,
            name=s.name,
            body=truncate(s.snippet or "", FORCED_SEARCH_SNIPPET_CAP),
            body_label="snippet",
            meta=f"score={s.score:.3f}",
        )
        for s in snippets
    )


def format_forced_search_block(snippets: Sequence[RagHit] | None) -> str:
    """SOURCE: reasoning-node.prompts.ts :: formatForcedSearchBlock

    node-lab never runs a forced pre-search — RAG is a tool the model drives —
    so this is always called with no snippets and returns "". Ported anyway
    because it is part of `buildAnalysisMessage`'s assembled output, and
    dropping it would silently change the string for anyone who later seeds
    hits via `--rag-fixture`.
    """
    if not snippets:
        return ""
    lines = render_forced_search_lines(snippets)
    return f"""
<RAG_Context>
Documents surfaced by a node-level semantic search compiled from the question + instructions. Each entry's snippet is the best-matching chunk for that query — NOT the file's static summary. To ground a comparison or pin a locator, call read-file with the entry's fileId for the full text. Cite any of these you actually rely on using `{{{{file:<fileId>}}}}` exactly as you would a sub-agent-cited file (italicized source short form + locator before the marker; pinpoints from read-file output or snippet text where it shows paragraph or section numbers). Skip any document whose snippet does not actually bear on the analysis — relevance, not completeness, drives inclusion.
{lines}
</RAG_Context>

"""


def build_analysis_message(
    *,
    question: str,
    instructions: str,
    prior_answers: Mapping[str, PriorAnswer],
    annotation_block: str | None = None,
    forced_search_snippets: Sequence[RagHit] | None = None,
) -> str:
    """SOURCE: reasoning-node.prompts.ts :: buildAnalysisMessage

    `subAgentAnswers` is always empty here — the fan-out stage is deliberately
    not ported — so `<SubAgent_Answers>` renders the builder's own documented
    fallback string. That is the point: keep the builder byte-faithful and let
    the empty input speak, rather than editing the prompt shape.

    `annotation_block` is appended after `<Conversation_Facts>` when the node
    has annotations. Production reaches `<Annotated_Context>` through the
    sub-agent prompt, which is gone; without this the annotation sources would
    never reach the model at all.
    """
    facts_block = format_prior_answers(prior_answers)
    answers = "(no sub-agent answers — fall back to the conversation facts and analytical instructions)"
    retrieved_block = format_forced_search_block(forced_search_snippets)
    annotation_part = f"\n{annotation_block}\n" if annotation_block else ""

    return f"""<Question>
{question}
</Question>

<Analytical_Instructions>
{instructions}
</Analytical_Instructions>

<Conversation_Facts>
{facts_block or "(no facts available)"}
</Conversation_Facts>
{annotation_part}
<SubAgent_Answers>
{answers}
</SubAgent_Answers>
{retrieved_block}
Produce the rationale now. Use `## Facts` and `## Analysis` headers. Preserve every `{{{{file:<fileId>}}}}` and `{{{{excerpt:<excerptId>}}}}` marker from the sub-agent answers exactly, including the pinpoint phrase (`[para 3]`, `s. 11(2)`, etc.) that precedes it. Do not introduce new ids and do not swap kinds — only `{{{{file:<uuid>}}}}` and `{{{{excerpt:<uuid>}}}}` are valid."""


def describe_data_type(
    data_type: FactDataType, custom_enum_values: Sequence[str] | None
) -> str:
    """SOURCE: reasoning-node.prompts.ts :: describeDataType"""
    if data_type is FactDataType.BOOLEAN:
        return 'dataType: BOOLEAN. Encode as the strings "true" or "false".'
    if data_type is FactDataType.NUMBER:
        return 'dataType: NUMBER. Encode as a numeric string (e.g. "24"). No units.'
    if data_type is FactDataType.PERCENTAGE:
        return 'dataType: PERCENTAGE. Encode as a decimal string between 0 and 1 (e.g. "0.75").'
    if data_type is FactDataType.CONFIDENCE:
        return "dataType: CONFIDENCE. Encode as a decimal string between 0 and 1."
    if data_type is FactDataType.DATE:
        return "dataType: DATE. Encode as an ISO-8601 date string (YYYY-MM-DD)."
    if data_type is FactDataType.TEXT:
        return "dataType: TEXT. Encode as free-form text."
    if data_type is FactDataType.CUSTOM:
        values = (
            ", ".join(custom_enum_values)
            if custom_enum_values
            else "(no enum values supplied)"
        )
        return f"dataType: CUSTOM. Encode as exactly one of: {values}"
    if data_type is FactDataType.DOCUMENT_UPLOADED:
        return 'dataType: DOCUMENT_UPLOADED. Encode "true" if a document is present, otherwise "false".'
    raise ValueError(f"Unhandled dataType: {data_type}")


def build_prediction_message(
    *,
    config: ReasoningNodeConfig,
    prior_answers: Mapping[str, PriorAnswer],
    rationale: str,
) -> str:
    """SOURCE: reasoning-node.prompts.ts :: buildPredictionMessage"""
    data_type_block = describe_data_type(config.data_type, config.custom_enum_values)
    facts_block = format_prior_answers(prior_answers)
    # Analytical instructions are intentionally omitted: the rationale already
    # encodes the methodology, and re-injecting them invites the prediction
    # stage to second-guess the rationale instead of extracting a value from it.
    return f"""<Question>
{config.question}
</Question>

<Conversation_Facts>
{facts_block or "(no facts available)"}
</Conversation_Facts>

<Rationale>
{rationale}
</Rationale>

<Output_Type>
{data_type_block}
</Output_Type>

Return the predictions JSON now. Do NOT include a `source` field; do NOT add citations to the prediction string itself."""


__all__ = [
    "EXCERPT_BODY_CAP",
    "FORCED_SEARCH_SNIPPET_CAP",
    "REASONING_ANALYSIS_SYSTEM_PROMPT",
    "REASONING_PREDICTION_SYSTEM_PROMPT",
    "build_analysis_message",
    "build_prediction_message",
    "describe_data_type",
    "format_annotation_context_block",
    "format_forced_search_block",
    "format_prior_answers",
    "render_forced_search_lines",
    "truncate",
]
