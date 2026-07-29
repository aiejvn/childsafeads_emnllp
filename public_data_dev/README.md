# ChildSafeAds v1.0 — Dataset Release

The first benchmark to unite three tasks over influencer advertising that reaches minors: identifying what is promoted, categorising it, and assessing its compliance with EU law. Built on community-verified sponsorship data and framed as a real-world system-design problem. NLLP @ EMNLP 2026.

## The Task

Imagine you work at an authority responsible for monitoring commercial content that reaches minors on video platforms. How would you build the monitoring system, and what can it achieve at each level of data access and cost? Each instance is one sponsored segment (community-verified via SponsorBlock) paired with the product page its description links to. Systems predict, per instance:

- **ST1 — commercial type** (single label)
- **ST2 — product category** (multi-label)
- **ST3 — compliance risk flags** (multi-label, legally grounded)

Full label definitions, severity tiers, and the Tier-2 bonus track: `labels_taxonomy.md`. Per-flag legal grounding in machine-readable form: `legal_provisions.json` (citations and notes on what each provision requires, not statutory text; resolvable against EUR-Lex if you want to retrieve more).

## Data Access Levels

The core of the task is a design question: what can a monitoring system achieve, and at what cost, depending on how much data it collects? To make that concrete, every instance groups its fields into four levels ordered by collection cost. A system that only reads the transcript uses a single field; a system that also fetches video metadata adds the next field; and so on. We ask teams to report what their system achieves at each level, so the community learns where the accuracy-versus-cost sweet spot lies.

| Level | Field | Contents | Collection cost |
|-------|-------|----------|-----------------|
| 1 | `transcript` | segment transcript text + start/end seconds | Lowest. Already in the release; scales to the whole platform. |
| 2 | `video_context` | videoID, title, description, `official_disclosure` (YouTube's "Includes paid promotion" label: `"true"` / `"false"` / `""` unknown) | One metadata API call per video. |
| 3 | `channel_context` | channelID, channel name | One channel lookup. |
| 4 | `product_page` | raw + resolved URL, page title, extracted page text | Requires crawling the outbound link; in the wild, some pages are dead (4xx) or block automated access. |
| Bonus | — | Destination data (shops, terms of service, apps) is **not** distributed. Teams who want to design richer systems can collect it themselves starting from `resolved_url` (see the Tier-2 bonus track in `labels_taxonomy.md`). | Highest, and that trade-off is exactly the point. |

## Files and Splits

| File | Instances | Labels |
|------|-----------|--------|
| `train.jsonl` | 2,353 | yes |
| `dev.jsonl` | 504 | yes |
| `test.jsonl` | 503 | **withheld** (evaluation phase) |

Splits are **channel-disjoint**: no channel appears in more than one split. Channels were curated to plausibly reach a significant teen audience: an automated classifier over channel descriptions, video titles, and metadata, followed by a human-validated exclusion pass. This curation is not guaranteed to be correct for every channel, but it means systems do **not** need to assess audience themselves; "child-facing" is a dataset-level property to take as given.

## Labels Block (train/dev)

```json
"labels": {
  "st1": "digital_content_or_services",
  "st2": ["apps", "gambling_adjacent"],
  "st3": ["undisclosed_advertising"],
  "st3_evidence": [{"flag": "undisclosed_advertising", "quote": "verbatim span from this instance's text"}]
}
```

Labels are automatically annotated, with human validation and legal calibration. Each `st3_evidence` quote is verbatim from that instance's own transcript, description, or product page (quotes that could not be matched against the source are omitted, so a flag may carry no evidence entry). Some compliance flags remain under legal review and may be refined in a point release; a set of human-annotated calibration examples will be released with the evaluation phase.

## Evaluation

The task has two complementary evaluation tracks.

**Quantitative (automated, on CodaBench).** Macro-F1 for each sub-task, reported at the fine-grained level and, for ST3, at the family level (disclosure / content / product) given class imbalance. This produces the live leaderboard.

**Qualitative (the system design report).** Because the research question is not only *whether* the labels can be predicted but *how a monitoring system should be built*, we highly encourage every team to submit a short **system design report** alongside their predictions. This does not need to be a full paper: a concise document recording your design decisions and the trade-offs you weighed is enough, covering how much data you used and why, the cost and generalisability of your approach, your model and compute choices, and what accuracy each added data level bought. Legal grounding is not scored on the leaderboard, so if you retrieved legal material beyond the citations we ship, or reported the provisions behind your predictions, the report is where that belongs, and we are genuinely interested in whether it helped.

Submission format and the CodaBench link ship can be found on the competition page.

## Licence and Use

The dataset derives from the **SponsorBlock** database (https://sponsor.ajay.app/database), which is licensed **CC BY-NC-SA 4.0**. Under that licence's share-alike term, the derived labels, instance structure, and resolved page text in this release are distributed under the same **CC BY-NC-SA 4.0** (attribution to SponsorBlock, non-commercial, share-alike).

Video-derived fields (transcripts, titles, descriptions, metadata) are provided for research use under the task's data-use agreement; participants must comply with the YouTube Terms of Service and must not attempt to re-identify or contact creators. Resolved page text is extracted from third-party commercial websites for research use only. The dataset must not be used to train systems for purposes other than this shared task's research aims without separate permission.

## Citation

TBD (task description paper to follow).
