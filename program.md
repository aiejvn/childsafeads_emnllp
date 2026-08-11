# autoresearch

This is an experiment to have the LLM do its own research.

## Setup

To set up a new experiment, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar5`). The branch `autoresearch/<tag>` must not already exist — this is a fresh run.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current master.
3. **Read the in-scope files**: The repo is small. Read these files for full context:
   - `README.md` — repository context.
   - `src/common, oj-eval, public_data_dev, starting_kit`— fixed constants, data prep, tokenizer, dataloader, evaluation. Do not modify.
   - `src/lora, src/last_layer` — the files you modify. Model architecture, optimizer, training loop.
4. **Verify data exists**: Check that `public_data_dev` contains a `train.jsonl`, `dev.jsonl`, `labels_taxonomy.md`, `legal_provisions.md`. Also ensure `emnllp-dialog-flow-dialog-flow.json` exists.
5. **Initialize results.tsv**: Create `results.tsv` with just the header row. The baseline will be recorded after the first run.
6. **Confirm and go**: Confirm setup looks good.

Once you get confirmation, kick off the experimentation.

## Experimentation

Each experiment runs on a single GPU. The training script runs for a **fixed epoch budget of 10 epochs**. Read the docs of the training scripts to understand how they work.

**What you CAN do:**
- Modify any files in `src/` that are NOT fixed constants. Everything is fair game: model architecture, optimizer, hyperparameters, training loop, batch size, model size, etc.

**What you CANNOT do:**
- Modify the fixed constants files mentioned above. It is read-only. It contains the fixed evaluation, data loading, tokenizer, and training constants (time budget, sequence length, etc).
- Install new packages or add dependencies. You can only use what's already in `requirements_no_version.txt`. If you need a new package, stop and ask me
- Modify the evaluation harness. Evaluating predict on `dev.jsonl`is the ground truth harness.

**The goal is simple: get highest mean macro F1 without explicitly tuning on the dev set.** Since the epoch budget is fixed, you don't need to worry about training time — it's always 20 epochs. Everything is fair game: change the architecture, the optimizer, the hyperparameters, the batch size, the model size. The only constraint is that the code runs without crashing and finishes within the time budget.

**VRAM** is a soft constraint. Anything below OOM errors are acceptable.

**Simplicity criterion**: All else being equal, simpler is better. A small improvement that adds ugly complexity is not worth it. Conversely, removing something and getting equal or better results is a great outcome — that's a simplification win. When evaluating whether to keep a change, weigh the complexity cost against the improvement magnitude. A 0.001 mean macro F1 improvement that adds 20 lines of hacky code? Probably not worth it. A 0.001 mean macro F1 improvement from deleting code? Definitely keep. An improvement of ~0 but much simpler code? Keep.

**The first run**: Your very first run should always be to establish the baseline, so you will run the training script as is.

## Output format

Once the script finishes it prints a summary like this:

```
2026-08-04 20:21:19,531 | INFO | MainThread | epoch 200 dev metrics: st1_macro_f1=0.613, st2_macro_f1=0.611, st3_macro_f1=0.397, st3_family_macro_f1=0.557, mean_macro_f1=0.540
2026-08-04 20:21:19,714 | INFO | MainThread | saved final epoch adapter to runs/lora_roberta/last (best dev mean_macro_f1=0.571)
```

```
grep "^mean_macro_f1:" run.log
```

## Logging results

When an experiment is done, log it to `results.tsv` (tab-separated, NOT comma-separated — commas break in descriptions).

The TSV has a header row and 9 columns:

```
commit	mean_macro_f1  st1_macro_f1   st2_macro_f1   st3_macro_f1   st3_family_macro_f1	model 	status	description
```

1. git commit hash (short, 7 chars)
2. macro f1 KPIs — use -1 for crashes
3. model used, if any
4. status: `keep`, `discard`, or `crash`
5. short text description of what this experiment tried


## The experiment loop

The experiment runs on a dedicated branch (e.g. `kw/autoresearch` or `autoresearch/mar5-gpu0`).

LOOP FOREVER:

1. Look at the git state: the current branch/commit we're on
2. Tune train scripts with an experimental idea by directly hacking the code.
3. git commit
4. Run the experiment: `uv run train.py > run.log 2>&1` (redirect everything — do NOT use tee or let output flood your context)
5. Read out the results: `grep "^val_bpb:\|^peak_vram_mb:" run.log`
6. If the grep output is empty, the run crashed. Run `tail -n 50 run.log` to read the Python stack trace and attempt a fix. If you can't get things to work after more than a few attempts, give up.
7. Record the results in the tsv (NOTE: do not commit the results.tsv file, leave it untracked by git)
8. If val_bpb improved (lower), you "advance" the branch, keeping the git commit
9. If val_bpb is equal or worse, you git reset back to where you started

The idea is that you are a completely autonomous researcher trying things out. If they work, keep. If they don't, discard. And you're advancing the branch so that you can iterate. If you feel like you're getting stuck in some way, you can rewind but you should probably do this very very sparingly (if ever).

**Timeout**: Each experiment should take ~5 minutes total (+ a few seconds for startup and eval overhead). If a run exceeds 10 minutes, kill it and treat it as a failure (discard and revert).

**Crashes**: If a run crashes (OOM, or a bug, or etc.), use your judgment: If it's something dumb and easy to fix (e.g. a typo, a missing import), fix it and re-run. If the idea itself is fundamentally broken, just skip it, log "crash" as the status in the tsv, and move on.

**NEVER STOP**: Once the experiment loop has begun (after the initial setup), do NOT pause to ask the human if you should continue. Do NOT ask "should I keep going?" or "is this a good stopping point?". The human might be asleep, or gone from a computer and expects you to continue working *indefinitely* until you are manually stopped. You are autonomous. If you run out of ideas, think harder — read papers referenced in the code, re-read the in-scope files for new angles, try combining previous near-misses, try more radical architectural changes. The loop runs until the human interrupts you, period.

As an example use case, a user might leave you running while they sleep. If each experiment takes you ~5 minutes then you can run approx 12/hour, for a total of about 100 over the duration of the average human sleep. The user then wakes up to experimental results, all completed by you while they slept!