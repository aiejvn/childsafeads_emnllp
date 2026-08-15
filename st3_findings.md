# ST3 Label Pattern Analysis

Analysis of `public_data_dev/train.jsonl` (2353 rows) + `dev.jsonl` (504 rows), grepping/filtering by `labels.st3` to find structural and semantic patterns behind each compliance-risk flag. Motivated by ST3 being the priority optimization target (st1/st2 regressions are tolerated if st3 improves).

**st3 label counts (train, 2353 rows, multi-label so totals exceed 100%):**

| label | train count |
|---|---|
| misleading_claim | 1277 |
| inadequate_disclosure | 611 |
| no_flag | 529 |
| undisclosed_advertising | 352 |
| direct_exhortation | 304 |
| age_restricted_or_prohibited_product | 59 |
| hfss_food_marketing | 40 |
| insufficient_context | 15 |

Labels below are grouped by how learnable/clean each one turned out to be.

---

## Tier 1: Near-deterministic structural patterns

### `insufficient_context` (22 total across train+dev)

Every single instance has a degenerate/near-empty transcript segment — `[Music]`, `[Applause]`, filler words, single short phrases, or a literally empty string. Not a property of the product/brand/ad at all: it's an artifact of the sliding-window transcript sampler landing on a window with no real speech/ad content. Effectively an "abstain, no signal in this window" bucket rather than a substantive taxonomy category.

**Implication:** transcript length/emptiness is likely a stronger feature for this label than semantic understanding. Its historically ~0.000 F1 across many training runs may trace to this — there's little textual signal to learn beyond "is this segment near-empty."

### `undisclosed_advertising` (426 total)

- 100% deterministic one-directional gate on `video_context.official_disclosure`: **0/1565 (0%)** of `official_disclosure="true"` rows ever carry this flag.
- But `official_disclosure="false"` is necessary, not sufficient — only **418/1256 (33%)** of false-disclosure rows get it; the rest mostly get `inadequate_disclosure` instead.
- The split within `official_disclosure="false"` tracks in-transcript disclosure language (sponsor/ad/partnered/#ad regex): `inadequate_disclosure` rows contain such language ~59–76% of the time (some disclosure present, judged insufficient); `undisclosed_advertising` rows contain it only **2.9%** of the time (near-zero in-transcript disclosure).
- Taxonomy split: *some* spoken disclosure but inadequate → `inadequate_disclosure`; *zero* spoken disclosure → `undisclosed_advertising`.
- Co-occurs heavily with `misleading_claim` (188×) and `direct_exhortation` (71×).
- Skews toward st2 `creator_community`/`fashion`/`apps` and st1 `physical_goods`/`digital_content_or_services` — classic influencer sponsorship categories (discount codes, affiliate links, app partnerships).

---

## Tier 2: Diffuse but category/semantically informed

### `misleading_claim` (1537 combined, 53.8% of all rows — the dominant st3 flag)

No sharp structural rule, but strongly category-concentrated:

- st2 well above base rate (53.8%): health **84.3%** (269/319), financial **76.1%** (118/155), physical_services **71.9%** (105/146).
- st2 well below base rate: toys **25.9%** (22/85), creator_community **31.0%** (98/316), fashion **42.9%** (136/317).
- Sample quotes: *"the first ingredient proven to target senescent cells"*, *"20 times stronger than over-the-counter retinols"*.
- Weak lexical tells: "guarantee/promise" language **5x** more common (10.1% vs 2.1%), numeric/comparative claims ("20 times stronger") **4x** more common, superlatives ("best," "#1") at 26.7% vs 17.2%.
- Longer transcripts: mean 257.8 words vs 181.2 for non-flagged (more talk time → more room for embellished claims).
- 99.6% of flagged rows have grounding `st3_evidence` — annotators grounded this in specific quotes.
- 50.0% stand alone; when paired, mostly with `inadequate_disclosure` (28.0%).
- No correlation with `official_disclosure` or product_page presence — driven by claim content/category, not disclosure metadata.

### `inadequate_disclosure` (729 combined)

Unlike `undisclosed_advertising`, **not** gated by `official_disclosure` — appears with both `official_disclosure="true"` (36.8%) and `"false"` (61.3%). Among all `official_disclosure="true"` rows, 35.4% still get this flag vs 64.6% getting `no_flag` — a real judgment call, not a structural gate.

Key structural signal — **spoken vs. written disclosure**:
- ~50% of its `st3_evidence` quotes come from `video_context.description` only (written boilerplate like affiliate/promo-code blocks), not the spoken `transcript.text`.
- Restricted to `official_disclosure="true"` rows, spoken sponsor-language rate is **47.8%** for `inadequate_disclosure` vs **71.3%** for `no_flag` (23.5pp gap).
- Disclosure position also skews slightly later in the segment for `inadequate_disclosure` (median relative offset 0.14) vs `no_flag` (0.11).

Heavy co-occurrence with `misleading_claim` (59.0%); essentially mutually exclusive with `undisclosed_advertising` (0.1% overlap) — the two are complementary "disclosure absent entirely" vs "disclosure exists but insufficient/unspoken/buried" categories. No sharp st1/st2 concentration.

### `no_flag` (656 — the "clean" class)

- Confirmed to **never** co-occur with another st3 flag (0 exceptions in 656 rows) — internally consistent labeling.
- Disclosure hygiene is necessary but not sufficient: combining `official_disclosure="true"` AND spoken sponsor-language present gives a **6.5x lift** in no_flag rate (32.8% vs 5.1% when both absent) — but even in that "both present" bucket, **58.1%** still get `misleading_claim`. Proper disclosure alone doesn't make claims non-misleading.
- Product category matters a lot: education (30.3%) and apps (28.1%) skew clean; health (8.8%), food (10.2%), gambling (0.0%) skew heavily toward violation flags.
- Transcript length and product_page presence are non-discriminative (100% of *all* rows have a product_page regardless of label).

### `direct_exhortation` (381 combined)

Diffuse CTA-intensity signal, **not** child-specific language — literal phrases like "ask your parents" appear **0 times** in positive evidence quotes. It's standard influencer CTA phrasing: imperative verb + link/code/offer (*"go to the link... to buy a Sona 2"*, *"use code callmechris at checkout"*).

- Rarely stands alone: only 19.2% solo; heavily co-occurs with `misleading_claim` (60.6%), `inadequate_disclosure` (26.0%), `undisclosed_advertising` (18.6%). Positive rows average 2.14 st3 flags vs 1.23 for negatives.
- No child-audience category concentration: toys only 3.4% vs 3.0% baseline; kid-keyword rate in title/description/channel name ~identical for positive (6.0%) vs negative (6.3%).
- Best quantitative signal is imperative-verb *density*, not a keyword: zero-imperative-verb rows are 4.5% of positives vs 20.3% of negatives.
- Single best lexical phrase ("get yours") gives only an 8x lift on a low base rate — not a clean rule. Any-phrase-hit rate: 73.0% positive vs 64.9% negative (modest lift only).
- Weak negative association with `official_disclosure`: false=50.1% positive vs 43.0% negative.

### `age_restricted_or_prohibited_product` (75 combined, rare)

Manually reviewed taxonomy of every instance:

| category | count |
|---|---|
| sports betting / fantasy sports | 16 |
| alcohol | 12 |
| sex toys / adult products | 11 |
| skin-gambling / trading sites (SkinsMonkey, CSGOFast) | 9 |
| energy drinks / high caffeine | 8 |
| THC/CBD/Delta-9 gummies | 5 |
| vaping / nicotine | 4 |
| age-gated games/content | 3 |
| weapons, ED medication, crypto | 1–2 each |

**Not redundant with st2** — only 29% of flagged rows come from st2 `gambling`/`gambling_adjacent`; the majority (71%) are alcohol/sex-toys/energy-drinks/THC that st2 buckets generically into `health`/`food`/`other`. This is a genuinely distinct signal the model has to learn separately, unlike `insufficient_context`.

Co-occurs with `misleading_claim` (52%), `inadequate_disclosure` (24%), `direct_exhortation` (23%), `undisclosed_advertising` (21%); 21% stand alone. No `official_disclosure` correlation (matches baseline rate of ~55%/44%).

---

## Tier 3: Likely noisy ground truth — low ceiling expected

### `hfss_food_marketing` (45 combined, rare)

Taxonomy:

| category | share |
|---|---|
| energy drinks / gaming-supplement brands (G Fuel, Gamer Supps) | ~49% |
| Japanese candy/snack subscription boxes (Tokyo Treat, Sakuraco, Bokksu) | ~40% |
| misc candy/soda | ~7% |

**st2=="food" is a weak predictor** — only 12.3% of 342 food rows get this flag; most food rows get `misleading_claim` instead (67.8%).

**No clean textual/brand discriminator found**, and evidence suggests genuine annotation inconsistency rather than a learnable pattern:
- The *same brands*, even near-identical templated ad copy from the *same channel*, appear on both sides. One channel reads the same "brought to you by Gamer Subs, flavor of the week" script across ~10 videos — only 1 is flagged.
- Several flagged G Fuel quotes explicitly say "zero sugar" / "sugar-free" / "keto," directly contradicting an HFSS (high fat/sugar/salt) rationale.

Co-occurrence: `misleading_claim` 37.8%, `direct_exhortation` 35.6%, `inadequate_disclosure` 28.9%, `undisclosed_advertising` 17.8%, `age_restricted_or_prohibited_product` 11.1%. Mild `official_disclosure=false` skew (57.8%).

**Implication:** if `hfss_food_marketing` F1 stays stuck low across many training runs/recipes, that may reflect a **data-quality ceiling** rather than a modeling deficiency — worth spot-checking a sample of model errors against raw labels before investing more tuning effort here.

---

## Summary for modeling decisions

- **Cheap heuristic features likely to help:** transcript emptiness (`insufficient_context`), `official_disclosure` + spoken-sponsor-language regex (`undisclosed_advertising`, `inadequate_disclosure`, `no_flag`).
- **Needs real semantic understanding, but category priors help:** `misleading_claim` (health/financial-heavy), `direct_exhortation` (imperative-density, not keyword), `age_restricted_or_prohibited_product` (genuinely distinct from st2, not derivable from it).
- **Don't over-invest tuning effort chasing:** `hfss_food_marketing` — likely has a low achievable ceiling due to inconsistent ground-truth labeling on near-identical ad copy.

---

## Context-rung separability (per label, per context level)

This repo trains/evaluates against 4 nested "context rungs" (`src/common/__init__.py`, `CONTEXT_CHOICES`), in increasing order of information:

1. **transcript** — `transcript.text` alone.
2. **no_product_page** — transcript + `video_context.title`/`description` + `official_disclosure`.
3. **st2_page** — rung 2 + product page text filtered to ST2 (category) vocabulary lines only.
4. **full** — rung 2 + the entire product page text.

For each remaining label (excluding the two solved dedicated-model cases below), we tested how well a small rung-scoped heuristic separates it from "not this label," using real precision/recall/F1 against gold labels (not just correlation) across train+dev combined. Headline finding: **more context is not uniformly better** — for 4 of the 6 labels tested, adding the product page rung actively *hurts* F1 (precision collapses faster than recall improves), and only one label (`misleading_claim`) genuinely needs it.

| label | rung 1 (transcript) | rung 2 (+description) | rung 3/4 (+page) | minimum sufficient rung |
|---|---|---|---|---|
| `misleading_claim` | F1=0.451 (P=0.755, R=0.321) — decent precision, misses ~68% of positives | +3.8% of evidence quotes live only in description — small gain | **F1=0.632** (P=0.651, R=0.614) — page nearly doubles recall; 8.5% of evidence quotes are page-only (ad implicitly repeats the page's own marketing copy, e.g. "world's #1 rated wallets") | **full (4)** — the one label where the page rung clearly earns its cost |
| `inadequate_disclosure` | F1=0.33; only 71.8% correctly split from sibling `undisclosed_advertising` | **F1=0.40**, ID-vs-UA split accuracy 79.9%; 23.3% of positives have disclosure language ONLY in the description (would be misrouted to `undisclosed_advertising` at rung 1) | **0% of evidence quotes ever match the product page** — page adds nothing measurable | **no_product_page (2)** |
| `no_flag` | F1=0.361 (lexical clean-check, better than the 23% base rate but weak) | F1=0.365 — lexical check barely moves, but this is the first rung where **st2 category becomes inferable**, and category is the strongest signal found (apps/education ~28-30% no_flag vs health/food/gambling 0-10%) | No signal — no_flag rate flat (21-23%) regardless of page-level claim language | **no_product_page (2)**, driven by category inference, not the lexical rule |
| `direct_exhortation` | F1=0.263 (CTA-verb density, threshold≥2); 99.5% of gold evidence quotes are transcript-only | F1=0.264 — a +0.001 no-op; description doesn't change what counts as evidence | F1=0.183 — **worse than transcript alone**; page urgency language is equally common (~5.5%) in positive and negative rows | **transcript (1)** — richer rungs add nothing |
| `age_restricted_or_prohibited_product` | **F1=0.485** (P=0.436, R=0.547) — best of any rung; only ~3% of positives are rescued by the page | F1=0.315 — recall +20pts but precision collapses 3x (generic alcohol/gambling-adjacent words in unrelated descriptions) | F1=0.273 — **worst of the three rungs**; +5pts recall not worth the precision cost. Same brand (e.g. "Lelo," "G Fuel") is gold-inconsistent across different videos regardless of rung | **transcript (1)** |
| `hfss_food_marketing` | F1=0.485 (brand-keyword heuristic) — modest, honest signal | F1=0.295 — description reuses brand names indiscriminately (boilerplate CTAs), precision collapses | **F1=0.0** — page nutrition-content signal (sugar-free/zero-sugar claims) actually trends *backwards* from the HFSS hypothesis (11.1% of flagged pages say "sugar-free" vs 1.1% of unflagged); zero pages of either class state actual sugar/fat/calorie numbers | **transcript (1)** — and even that is capped by the label's own noise (see above); no rung raises the ceiling |

**Already-solved labels, for reference (see `project_st3_classical_ml_ceiling.md` in memory for the dedicated models):**
- `undisclosed_advertising` needs rung 2 (transcript + description) — it's gated on `official_disclosure` (metadata, available at every rung) plus the ABSENCE of disclosure language in transcript OR description; the page rung is irrelevant.
- `insufficient_context` needs rung 2 as well — it requires BOTH the transcript AND the description to be thin/non-promotional (an empty transcript with a promo-heavy description gets a real flag instead, not this one).

**Practical implication:** rung 2 (`no_product_page`) is the sweet spot for 5 of 8 st3 labels (`undisclosed_advertising`, `insufficient_context`, `inadequate_disclosure`, `no_flag`, and roughly `direct_exhortation`/`age_restricted_or_prohibited_product`/`hfss_food_marketing` which do best at rung 1 and get *worse* with more text). Only `misleading_claim` benefits from paying for the full product-page rung. A model trained/served with `--context full` for every label (the current default in this repo's baselines) is spending most of its extra token budget on a rung that's neutral-to-harmful for 7 of 8 labels — a label-conditional or rung-2-default context choice is worth testing against the existing `--context full` baseline.
