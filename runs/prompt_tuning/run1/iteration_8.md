# Iteration 8 (final loop iteration)

**Batch**: `runs/prompt_tuning/run1/batch_iter8.jsonl` (n=10), same file for before/after.

## Metrics

| | st1 | st2 | st3 | st3_family | mean |
|---|---|---|---|---|---|
| before (prompt_v4) | 1.000 | 0.528 | 0.088 | 0.154 | 0.539 |
| after (candidate edit) | 1.000 | 0.528 | 0.088 | 0.154 | 0.539 |

Byte-identical predictions before and after (`diff` on both the full submission jsonl and the
error jsonl showed zero differences across all 10 instances).

## Error summary read (before)

`error_summary_iter8_before.md`: st3 collapsed to 0.088 -- the worst of any iteration. `no_flag`
missing 4/8 (the dominant pattern), with the model over-flagging `misleading_claim` (5x),
`direct_exhortation` (3x), and `inadequate_disclosure` (3x) on segments gold calls clean. This is
the third independent batch (after iterations 2 and 3) reproducing the misleading_claim
puffery-vs-fact confusion: "insane refresh speeds... costs that won't break the bank" (Pixio
monitors), "Crop Preserver ball deodorant is amazing" (Manscaped), "highquality in-network
doctors" (Zocdoc) -- all vague opinion/hype with no attached specific fact, all flagged anyway.

## Rationale for the edit

Reintroduced the puffery-vs-specific-fact distinction for misleading_claim (isolated to that one
bullet only, as in iteration 3's attempt), this time using verbatim phrases from this batch's false
positives ("insane refresh speeds", "won't break the bank", "high-quality") as explicit
NOT-misleading_claim examples, alongside the DO-flag side (specific/quantified/factual assertions).
Given three independent batches (2, 3, 8) now show this exact failure mode, and this is the last
scheduled loop iteration, this was judged worth one more attempt even knowing prior attempts were
reverted by unrelated st2/cross-tier noise.

## Result and decision

The re-run produced **exactly the same predictions** as the pre-edit run -- every st1/st2/st3 label
for all 10 instances matched exactly, despite the prompt text genuinely differing (confirmed via
diff against `prompt_v4.txt`). No caching layer was found in the codebase or environment
(`langchain_openai` has no cache configured, no `set_llm_cache` call, no on-disk HTTP cache); the
most likely explanation is that GPT-5.4 at temperature=0 landed on the same decision for each of
these 10 specific instances regardless of the added clarifying examples -- i.e. this batch's
particular over-flagging wasn't actually caused by the literal wording this edit targeted, so the
edit was a no-op here rather than a validated fix or a refuted one.

**Accept** per the plan's literal rule ("improved or unchanged -> keep the edit"): mean_macro_f1
0.539 == 0.539. Snapshotted to `prompt_v5.txt`. This is the prompt carried into final validation.

## Caveat for the final report

This iteration's accept is procedurally correct but empirically uninformative -- the edit neither
helped nor hurt on this batch, so it should not be read as confirmation the puffery/fact distinction
works. The n=100 final validation (comparing `prompt_v0` vs. the final tuned prompt on a much larger
fresh sample) is the number that actually matters; this note flags that one component of the final
prompt (the misleading_claim puffery clause) has three iterations of qualitative diagnosis behind it
but only inconclusive/reverted quantitative iteration-level evidence, and its real contribution can
only be read off the aggregate final-validation numbers, not attributed to this specific clause.
