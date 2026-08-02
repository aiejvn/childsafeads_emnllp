"""Package a baseline's submission into a self-contained, competition-ready zip.

Validates the submission with starting_kit/check_submission.py, then bundles just
enough of the repo for a reviewer to `pip install -r requirements.txt` and reproduce
it: the baseline script(s), starting_kit/ helpers, the label taxonomy + target split,
requirements.txt, and the submission itself (renamed to the competition-standard
`submission.jsonl`).

Usage (from repo root):
    python package_submission.py --method gpt
    python package_submission.py --method agentic_rag --run-log runs/run_20260801_210444_agentic_rag_full_gpt-5.4.log

Writes to runs/submissions/<method>_<timestamp>.zip.
"""
import argparse
import glob
import os
import subprocess
import sys
import zipfile
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))

# Files needed to reproduce each method, relative to ROOT. baseline_agentic_rag.py
# imports baseline_gpt.py directly and oj-eval's retrieval loop (flowchart.py /
# globals.py -- the only two oj-eval modules it touches; see their own imports).
METHOD_FILES = {
    "gpt": ["src/baseline_gpt.py"],
    "agentic_rag": [
        "src/baseline_gpt.py",
        "src/baseline_agentic_rag.py",
        "oj-eval/src/flowchart.py",
        "oj-eval/src/globals.py",
    ],
}
COMMON_FILES = [
    "starting_kit/check_submission.py",
    "starting_kit/load_data.py",
    "requirements.txt",
]

RUN_COMMAND = {
    "gpt": "python src/baseline_gpt.py {data_file}",
    "agentic_rag": "python src/baseline_agentic_rag.py {data_file}",
}


def default_submission_path(method: str) -> str:
    return os.path.join(ROOT, f"submission_{method}.jsonl")


def latest_run_log(method: str) -> str | None:
    pattern = {
        "gpt": "runs/run_*_full_*.log",
        "agentic_rag": "runs/run_*_agentic_rag_full_*.log",
    }[method]
    matches = sorted(glob.glob(os.path.join(ROOT, pattern)))
    return matches[-1] if matches else None


def validate_submission(submission: str, data_file: str) -> None:
    checker = os.path.join(ROOT, "starting_kit", "check_submission.py")
    result = subprocess.run([sys.executable, checker, submission, data_file])
    if result.returncode != 0:
        raise SystemExit(f"{submission} failed validation -- fix it before packaging")


def build_readme(method: str, data_file: str, submission: str, run_log: str | None) -> str:
    data_rel = os.path.relpath(data_file, ROOT)
    included = "\n".join(f"- `{f}`" for f in METHOD_FILES[method] + COMMON_FILES)
    log_note = f"\n- `{os.path.basename(run_log)}` -- the run log this submission reproduces" if run_log else ""
    return f"""# {method} baseline -- reproduction package

Run (from the folder this zip was extracted into):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export OPENAI_API_KEY=...   # or a .env file; agentic_rag also needs OJ_API_KEY

{RUN_COMMAND[method].format(data_file=data_rel)}
```

`submission.jsonl` in this zip is the predictions being submitted; validate it any time with:

```bash
python starting_kit/check_submission.py submission.jsonl {data_rel}
```

Included:
{included}
- `{data_rel}` -- target split used to produce this submission
- `public_data_dev/labels_taxonomy.md` -- label taxonomy (read by the baseline's system prompt)
- `submission.jsonl` -- the predictions being submitted{log_note}

Folder structure is preserved as in the source repo since the scripts import across
`src/`, `starting_kit/`, and (for agentic_rag) `oj-eval/src/` via paths relative to
their own location.
"""


def package(method: str, submission: str, data_file: str, run_log: str | None, out_dir: str) -> str:
    validate_submission(submission, data_file)

    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = os.path.join(out_dir, f"{method}_{timestamp}.zip")

    taxonomy = os.path.join(ROOT, "public_data_dev", "labels_taxonomy.md")
    data_rel = os.path.relpath(data_file, ROOT)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in METHOD_FILES[method] + COMMON_FILES:
            zf.write(os.path.join(ROOT, rel), rel)
        zf.write(taxonomy, os.path.relpath(taxonomy, ROOT))
        zf.write(data_file, data_rel)
        zf.write(submission, "submission.jsonl")
        if run_log:
            zf.write(run_log, os.path.join("runs", os.path.basename(run_log)))
        zf.writestr("README.md", build_readme(method, data_file, submission, run_log))

    return zip_path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--method", required=True, choices=sorted(METHOD_FILES))
    ap.add_argument("--submission", help="defaults to submission_<method>.jsonl at repo root")
    ap.add_argument("--data-file", default=os.path.join("public_data_dev", "dev.jsonl"),
                     help="target split the submission was predicted on (default: %(default)s)")
    ap.add_argument("--run-log", help="run log to include for reference; auto-detected if omitted")
    ap.add_argument("--out-dir", default=os.path.join("runs", "submissions"))
    args = ap.parse_args()

    submission = args.submission or default_submission_path(args.method)
    if not os.path.isfile(submission):
        raise SystemExit(f"{submission} not found -- run src/baseline_{args.method}.py first")
    data_file = os.path.abspath(args.data_file)
    run_log = args.run_log or latest_run_log(args.method)

    zip_path = package(args.method, submission, data_file, run_log, args.out_dir)
    print(f"wrote {zip_path}")


if __name__ == "__main__":
    main()
