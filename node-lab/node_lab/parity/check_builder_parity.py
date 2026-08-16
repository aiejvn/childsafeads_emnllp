"""Diff the Python prompt *builders* against the TypeScript builders.

`check_prompt_drift` covers the prompt constants; this covers the assembled
strings, which is what actually reaches the model. Two steps, because the TS
side needs Node:

  1. dump the TS side (see ../../parity/dump_ts_prompts.ts for the command)
  2. `python -m node_lab.parity.check_builder_parity --flow ... --node ...
      --ts-dir /tmp/ts`

Exits non-zero on any difference.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

from ..flow import load_flow
from ..prompts.reasoning_node import build_analysis_message, build_prediction_message

#: The fixed rationale the TS dump uses; must match dump_ts_prompts.ts.
FIXED_RATIONALE = "## Facts\nx\n\n## Analysis\ny"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_builder_parity")
    parser.add_argument("--flow", required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument("--ts-dir", required=True, help="output dir of the TS dump")
    args = parser.parse_args(argv)

    flow = load_flow(args.flow)
    config = flow.resolve(args.node).reasoning_config()

    produced = {
        "analysis.txt": build_analysis_message(
            question=config.question,
            instructions=config.instructions,
            prior_answers={},
        ),
        "prediction.txt": build_prediction_message(
            config=config, prior_answers={}, rationale=FIXED_RATIONALE
        ),
    }

    ts_dir = Path(args.ts_dir)
    failures = 0
    for name, python_value in produced.items():
        ts_file = ts_dir / name
        if not ts_file.exists():
            print(f"ERROR  {name}: {ts_file} not found — run the TS dump first")
            failures += 1
            continue
        expected = ts_file.read_text(encoding="utf-8")
        if expected == python_value:
            print(f"ok     {name}")
            continue
        failures += 1
        print(f"DRIFT  {name}")
        sys.stdout.writelines(
            difflib.unified_diff(
                expected.splitlines(keepends=True),
                python_value.splitlines(keepends=True),
                fromfile=f"typescript/{name}",
                tofile=f"python/{name}",
                n=1,
            )
        )

    print()
    print(f"{len(produced) - failures}/{len(produced)} builders match.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
