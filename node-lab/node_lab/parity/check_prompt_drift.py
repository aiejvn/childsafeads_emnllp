"""Diff the Python prompt copies against the TypeScript sources.

Extracts each named template literal from the TS file, resolves its `${...}`
interpolations against the Python fragments, and compares byte-for-byte. Drift
is a one-command check rather than a guess.

Scope: SURVIVING prompts only. Constants belonging to dropped stages
(`REASONING_SUBAGENT_SYSTEM_PROMPT`, curation, requirement extraction,
citation repair) are not ported and are deliberately excluded — flagging them
would report permanent, expected drift.

Prompt *builders* are not covered here; their parity recipe (dump both sides
and diff the assembled string) is in the README.
"""

from __future__ import annotations

import difflib
import sys
from dataclasses import dataclass
from pathlib import Path

from ..prompts.reasoning_discipline import EVALUATIVE_ANCHORS, SYNTHESIS_FIDELITY
from ..prompts.reasoning_node import (
    REASONING_ANALYSIS_SYSTEM_PROMPT,
    REASONING_PREDICTION_SYSTEM_PROMPT,
)
from ..prompts.reflect_rationale import RATIONALE_REFLECTION_SYSTEM_PROMPT

REPO_ROOT = Path(__file__).resolve().parents[4]
RUNNERS = REPO_ROOT / "apps/backend/src/node-execution/runners"


@dataclass(frozen=True)
class PromptCheck:
    python_name: str
    python_value: str
    ts_path: Path
    #: The TS identifier, which is not always the exported name — the analysis
    #: prompt is declared as REASONING_SYNTHESIS_SYSTEM_PROMPT and re-exported
    #: under an alias.
    ts_name: str


CHECKS: list[PromptCheck] = [
    PromptCheck(
        "SYNTHESIS_FIDELITY",
        SYNTHESIS_FIDELITY,
        RUNNERS / "shared/reasoning-discipline.prompt.ts",
        "SYNTHESIS_FIDELITY",
    ),
    PromptCheck(
        "EVALUATIVE_ANCHORS",
        EVALUATIVE_ANCHORS,
        RUNNERS / "shared/reasoning-discipline.prompt.ts",
        "EVALUATIVE_ANCHORS",
    ),
    PromptCheck(
        "REASONING_ANALYSIS_SYSTEM_PROMPT",
        REASONING_ANALYSIS_SYSTEM_PROMPT,
        RUNNERS / "reasoning-node.prompts.ts",
        "REASONING_SYNTHESIS_SYSTEM_PROMPT",
    ),
    PromptCheck(
        "REASONING_PREDICTION_SYSTEM_PROMPT",
        REASONING_PREDICTION_SYSTEM_PROMPT,
        RUNNERS / "reasoning-node.prompts.ts",
        "REASONING_PREDICTION_SYSTEM_PROMPT",
    ),
    PromptCheck(
        "RATIONALE_REFLECTION_SYSTEM_PROMPT",
        RATIONALE_REFLECTION_SYSTEM_PROMPT,
        RUNNERS / "lib/reasoning-node/reflect-rationale.prompts.ts",
        "RATIONALE_REFLECTION_SYSTEM_PROMPT",
    ),
]

#: Values available to `${...}` interpolations inside a TS template literal.
INTERPOLATIONS: dict[str, str] = {
    "SYNTHESIS_FIDELITY": SYNTHESIS_FIDELITY,
    "EVALUATIVE_ANCHORS": EVALUATIVE_ANCHORS,
}


class ExtractionError(RuntimeError):
    pass


def extract_template_literal(source: str, name: str) -> str:
    """Return the raw body of ``const <name> = `...`;`` from TS source."""
    marker = f"{name} = `"
    start = source.find(marker)
    if start < 0:
        raise ExtractionError(f"`{name}` not found (or not a template literal)")
    i = start + len(marker)
    out: list[str] = []
    while i < len(source):
        ch = source[i]
        if ch == "\\":
            out.append(source[i : i + 2])
            i += 2
            continue
        if ch == "`":
            return "".join(out)
        out.append(ch)
        i += 1
    raise ExtractionError(f"unterminated template literal for `{name}`")


def resolve(raw: str) -> str:
    """Unescape a TS template literal and substitute its interpolations."""
    out: list[str] = []
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "\\" and i + 1 < len(raw):
            nxt = raw[i + 1]
            out.append(
                {"n": "\n", "r": "\r", "t": "\t"}.get(nxt, nxt)
            )
            i += 2
            continue
        if ch == "$" and raw.startswith("${", i):
            end = raw.find("}", i)
            if end < 0:
                raise ExtractionError("unterminated ${...} interpolation")
            key = raw[i + 2 : end].strip()
            if key not in INTERPOLATIONS:
                raise ExtractionError(
                    f"interpolation ${{{key}}} has no Python counterpart; add it "
                    "to INTERPOLATIONS or port the fragment"
                )
            out.append(INTERPOLATIONS[key])
            i = end + 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def check_all(*, verbose: bool = True) -> int:
    """Return the number of drifted prompts (0 == clean)."""
    drifted = 0
    for check in CHECKS:
        try:
            source = check.ts_path.read_text(encoding="utf-8")
            expected = resolve(extract_template_literal(source, check.ts_name))
        except (OSError, ExtractionError) as error:
            drifted += 1
            print(f"ERROR  {check.python_name}: {error}")
            continue

        if expected == check.python_value:
            if verbose:
                rel = check.ts_path.relative_to(REPO_ROOT)
                print(f"ok     {check.python_name}  <- {rel}::{check.ts_name}")
            continue

        drifted += 1
        print(f"DRIFT  {check.python_name}  <- {check.ts_path}::{check.ts_name}")
        diff = difflib.unified_diff(
            expected.splitlines(keepends=True),
            check.python_value.splitlines(keepends=True),
            fromfile="typescript",
            tofile="python",
            n=1,
        )
        sys.stdout.writelines(diff)
        print()

    print()
    print(
        f"{len(CHECKS) - drifted}/{len(CHECKS)} prompts match their TypeScript source."
    )
    return drifted


def main() -> int:
    return 1 if check_all() else 0


if __name__ == "__main__":
    raise SystemExit(main())
