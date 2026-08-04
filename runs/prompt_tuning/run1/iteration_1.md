# Iteration 1

**Batch**: `runs/prompt_tuning/run1/batch_iter1.jsonl` (n=10), same file for before/after.

Instance IDs: UCN-JYa0sNXJ0osjqO--Dzcw_LhE7Pos43y8_931e1366, UCd21m0AHf4Vx88Znty7v4Cw_a7NgJJnSmFI_4fc96499, UCCqEeDAUf4Mg0GgEN658tkA_rrKVM7gI7zY_17ada26e, UCB_qr75-ydFVKSF9Dmo6izg_1Uc68hBXOrs_67f0ddda, UCFPElAbES8GHfBZrDrGbSLQ_7pcwHjS_iqM_63e0eb35, UCrEUTzd1W__Y5Sb5vSbuZ5g_6QyJmhuQZKw_a82ee5e2, UCqwmtYeuSTET9rSd7dNR_XQ_wx-KOYvc9GA_da901e4c, UC4G10tk3AHFuyMIuD3rHOBA_AXU40tVIxT4_9eab2229, UCtuLEGI-JkI6VFCW-5ZYtbw_xxZhHxBNn5Y_6912414b, UCfbnTUxUech4P1XgYUwYuKA_Ib_lBfhO-qE_68043743

## Metrics

| | st1 | st2 | st3 | st3_family | mean |
|---|---|---|---|---|---|
| before (prompt_v0) | 0.530 | 0.767 | 0.256 | 0.617 | 0.517 |
| after (prompt_v1)  | 0.908 | 0.729 | 0.900 | 0.911 | 0.845 |

9/10 instances had errors before; 7/10 after (st2 error count similar, but st1/st3 errors dropped sharply).

## Error summary read (before)

`error_summary_iter1_before.md` showed 7/9 st3 errors, matching the prior manual-analysis pattern
exactly:
- `misleading_claim` missing 5x (e.g. "world's greatest phone mount", "30% more breathability and
  reduces hip pressure by 20%", "without slowing your internet speeds down whatsoever" -- all
  specific/quantified/absolute performance claims the model let through as ordinary ad copy).
- `undisclosed_advertising` predicted as extra 4x, substituting for `inadequate_disclosure` 2x --
  in each case the transcript had an explicit verbal "sponsor of this video X" / "today's sponsor
  X" mention that the model missed or discounted, apparently over-indexing on
  `OFFICIAL_DISCLOSURE: false` as if it were the only disclosure signal.
- 1 st1 confusion: `physical_services` (therapy via an app) -> `digital_content_or_services`.

## Rationale for the edit

Root cause for `misleading_claim`: the taxonomy explicitly says the model is not asked to verify
claims, only to *identify* claims of a certain kind (unsubstantiated/high-risk claims about
performance, results, characteristics, price). The model appeared to be implicitly requiring the
claim to *sound* like a lie rather than checking for the taxonomy's actual trigger conditions
(quantified stats, superlatives, absolute guarantees, health/fitness claims). Added an explicit
checklist of trigger patterns with concrete examples pulled from the observed misses.

Root cause for `undisclosed_advertising` vs `inadequate_disclosure`: the taxonomy defines
`undisclosed_advertising` as "not identified anywhere available to the viewer: not in the spoken
content, not in the description, and not via the platform's own paid-promotion label" -- i.e. it
requires checking *all three* channels. The model appears to have been anchoring on the
`OFFICIAL_DISCLOSURE` boolean field alone and ignoring verbal disclosures in the transcript. Added
an explicit search-all-channels procedure before allowing `undisclosed_advertising`, plus the
correct downstream branch into `inadequate_disclosure` when a disclosure exists but is buried/
unclear.

Also added a physical_services vs. digital_content_or_services rule (human-performed test) since
this matches the dominant st1 confusion pattern from the prior 399-row manual analysis
(physical_goods/physical_services -> digital_content_or_services, ~31 cases), even though this
iteration only surfaced 1 instance of it -- treated as a supporting edit riding along with the two
well-evidenced fixes above, not the primary driver of this iteration's edit.

Deliberately did NOT act on the st2 `creator_community`/`other` under-use signal (missing 2x each)
this iteration -- the evidence was ambiguous (in one case `creator_community` appeared to be
triggered by an unrelated Patreon mention elsewhere in the video description, not the sponsored
product itself) and n=10 is too small to be confident about the actual trigger condition. Left for
a later iteration if the pattern persists in a fresh batch.

## Decision

**Accept.** mean_macro_f1 improved 0.517 -> 0.845 (tiebreak st3_macro_f1 0.256 -> 0.900, also
improved). Edit kept; snapshotted to `prompt_v1.txt`.
