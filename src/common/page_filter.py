"""Shrink a scraped product page to the lines that bear on ST2 (product category).

The page is the most expensive rung of an instance -- a median 38% of full_context's
tokens, up to 92% -- and most of that spend is scrape noise: nav bars, breadcrumbs,
cookie banners, footer link lists. A `--context no_product_page` run drops the rung
outright; this is the middle option, keeping the lines that mention something the ST2
taxonomy talks about and discarding the rest.

Keywords come from two layers, kept separate so the split stays auditable:

  ST2_SEED_KEYWORDS   parsed out of public_data_dev/labels_taxonomy.md's ST2 table --
                      the label name plus the exemplars its own definition lists, so
                      this layer tracks the distributed taxonomy automatically.
  ST2_EXTRA_KEYWORDS  hand-added surface forms the definitions imply but never spell
                      out ("earbuds" for `hardware_electronics`, "mortgage" for
                      `financial`). Seeds alone are far too thin -- `financial`'s
                      definition contributes the single word "financial" -- so without
                      this layer the filter empties most pages.

This is a lexical heuristic, not a classifier. It is precision-blind by design: a line
is kept if it mentions any ST2 vocabulary at all, because dropping a line that turns out
to matter is unrecoverable while keeping a spurious one only costs tokens.

Usage (from the repo root):
    python src/common/page_filter.py                    # corpus stats: what it keeps/drops
    python src/common/page_filter.py --show 3           # before/after for 3 instances
"""
import argparse
import json
import os
import re

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
TAXONOMY_PATH = os.path.join(REPO_ROOT, "public_data_dev", "labels_taxonomy.md")

# Words the ST2 definitions use structurally rather than descriptively. "products" and
# "services" are dropped because `financial`'s definition ("Financial products and
# services") would otherwise match every commerce page on the web.
_DEFINITION_STOPWORDS = {
    "and", "or", "the", "of", "a", "an", "none", "above", "name", "you", "see", "all",
    "that", "with", "products", "product", "services", "service", "physical", "like",
    "mechanics", "markets", "consumer", "category", "other", "adjacent",
}

# Surface forms the taxonomy implies but does not enumerate. Multi-word entries are
# matched with flexible whitespace. Deliberately excludes bare words that collide across
# categories ("skin" -> skincare vs. game skins, "watch" -> a wristwatch vs. "watch this
# video"); the multi-word forms below carry those cases instead.
ST2_EXTRA_KEYWORDS = {
    "toys": ["toy", "plush", "doll", "puzzle", "lego", "board game", "playset",
             "action figure", "collectible", "figurine", "stuffed animal"],
    "food": ["snack", "drink", "beverage", "meal", "flavour", "flavor", "recipe",
             "nutrition", "calorie", "ingredient", "coffee", "tea", "candy", "chocolate",
             "cereal", "sauce", "energy drink", "protein bar", "meal kit", "gum"],
    "apps": ["app", "ios", "android", "download", "subscription", "software", "vpn",
             "streaming", "in-app", "app store", "play store", "web app", "mobile game"],
    "hardware_electronics": ["headphone", "earbud", "laptop", "monitor", "keyboard",
                             "speaker", "charger", "battery", "usb", "bluetooth",
                             "processor", "webcam", "microphone", "tablet", "smartphone",
                             "console", "graphics card", "hard drive", "smartwatch"],
    "fashion": ["clothing", "shirt", "tee", "hoodie", "jacket", "dress", "shoe",
                "sneaker", "boot", "sock", "fabric", "cotton", "outfit", "jewelry",
                "jewellery", "handbag", "sunglasses", "wristwatch", "size chart"],
    "health": ["supplement", "vitamin", "serum", "moisturizer", "moisturiser", "spf",
               "sunscreen", "collagen", "protein", "workout", "gym", "therapy",
               "probiotic", "skincare", "mental health", "sleep aid", "hair care"],
    "education": ["course", "lesson", "tutor", "curriculum", "classroom", "study",
                  "school", "university", "certificate", "training", "language learning",
                  "textbook", "study guide"],
    "financial": ["bank", "credit card", "debit card", "invest", "loan", "insurance",
                  "savings", "trading", "crypto", "stock", "mortgage", "brokerage",
                  "interest rate", "apr", "cashback", "portfolio"],
    "gambling": ["casino", "bet", "wager", "odds", "jackpot", "slot machine", "lottery",
                 "sportsbook", "roulette", "blackjack", "free spins"],
    "gambling_adjacent": ["loot box", "gacha", "mystery box", "battle pass", "skins",
                          "crate", "in-game currency", "randomised reward",
                          "randomized reward", "gems", "pity timer"],
    "creator_community": ["merch", "membership", "patreon", "subscriber", "fan club",
                          "exclusive content", "discord", "supporter tier", "ko-fi"],
}

_LONG_LINE_CHARS = 200  # above this a line is split further, on sentence boundaries
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _parse_seed_keywords(taxonomy_path: str = TAXONOMY_PATH) -> dict:
    """Label -> words drawn from its own row in the taxonomy's ST2 table."""
    with open(taxonomy_path, encoding="utf-8") as f:
        taxonomy = f.read()
    block = taxonomy.split("## ST2")[1].split("## ST3")[0]
    rows = re.findall(r"^\|\s*`([a-z0-9_]+)`\s*\|\s*(.+?)\s*\|\s*$", block, re.M)
    if not rows:
        raise ValueError(f"no ST2 label table found in {taxonomy_path}")
    seeds = {}
    for label, definition in rows:
        words = re.findall(r"[a-z][a-z0-9-]+", f"{label} {definition}".lower())
        seeds[label] = sorted({w for w in words if w not in _DEFINITION_STOPWORDS and len(w) > 2})
    return seeds


ST2_SEED_KEYWORDS = _parse_seed_keywords()


def _singular(word: str) -> str:
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("es") and len(word) > 3 and word[-3] in "sxzho":
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def _keyword_pattern(keywords) -> re.Pattern:
    """One alternation over every keyword, plural-tolerant, whitespace-flexible for
    multi-word entries. Longest-first so "energy drink" wins over "drink"."""
    parts = []
    for kw in sorted(set(keywords), key=len, reverse=True):
        words = [_singular(w) for w in kw.split()]
        stem = r"\s+".join(re.escape(w) for w in words)
        parts.append(rf"{stem}(?:e?s)?")
    return re.compile(rf"\b(?:{'|'.join(parts)})\b", re.I)


def st2_keywords() -> dict:
    """Label -> the full keyword list actually matched (both layers merged)."""
    return {label: sorted(set(seeds) | set(ST2_EXTRA_KEYWORDS.get(label, [])))
            for label, seeds in ST2_SEED_KEYWORDS.items()}


ST2_PATTERN = _keyword_pattern([kw for kws in st2_keywords().values() for kw in kws])
ST2_LABEL_PATTERNS = {label: _keyword_pattern(kws) for label, kws in st2_keywords().items()}


def split_units(text: str) -> list:
    """Scraped pages are line-oriented (nav items, bullets, table cells one per line),
    so lines are the filtering unit -- but a prose paragraph arrives as one long line,
    and keeping all of it because one clause matched would defeat the point. Long lines
    are therefore split again on sentence boundaries."""
    units = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if len(line) > _LONG_LINE_CHARS:
            units.extend(s.strip() for s in _SENTENCE_SPLIT.split(line) if s.strip())
        else:
            units.append(line)
    return units


def st2_relevant_page(text: str, max_chars: int = None) -> str:
    """The page reduced to units mentioning ST2 vocabulary, in original order, with
    exact duplicates dropped (scrape noise repeats the same nav strings). Returns "" when
    nothing matches -- the caller decides what an empty page means."""
    kept, seen = [], set()
    for unit in split_units(text):
        if not ST2_PATTERN.search(unit) or unit in seen:
            continue
        seen.add(unit)
        kept.append(unit)
        if max_chars and sum(len(k) + 1 for k in kept) >= max_chars:
            break
    return "\n".join(kept)


def matched_labels(text: str) -> set:
    """Which ST2 labels have vocabulary present in `text`. Diagnostic only -- this is a
    keyword lexicon, not a predictor, and it is not wired into any model path. On its
    own it scores 0.379 ST2 macro-F1 over train, which is what "carries signal but is
    not a classifier" looks like."""
    return {label for label, pattern in ST2_LABEL_PATTERNS.items() if pattern.search(text)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("split", nargs="?", default="public_data_dev/train.jsonl")
    ap.add_argument("--show", type=int, default=0, help="print before/after for N instances")
    ap.add_argument("--max-chars", type=int, default=None)
    args = ap.parse_args()

    with open(args.split, encoding="utf-8") as f:
        instances = [json.loads(line) for line in f if line.strip()]

    kws = st2_keywords()
    print(f"{sum(len(v) for v in kws.values())} keywords over {len(kws)} labels "
          f"({sum(len(v) for v in ST2_SEED_KEYWORDS.values())} from the taxonomy, "
          f"{sum(len(v) for v in ST2_EXTRA_KEYWORDS.values())} curated)")

    before = after = emptied = 0
    for inst in instances:
        page = inst["product_page"].get("text") or ""
        filtered = st2_relevant_page(page, args.max_chars)
        before += len(page)
        after += len(filtered)
        emptied += not filtered.strip()
    print(f"{len(instances):,} pages: {before:,} -> {after:,} chars "
          f"({100 * after / before:.0f}% kept), {emptied:,} reduced to nothing")

    for inst in instances[: args.show]:
        page = inst["product_page"].get("text") or ""
        filtered = st2_relevant_page(page, args.max_chars)
        print(f"\n{'=' * 70}\n{inst['product_page']['page_title'][:64]!r}  gold st2={inst['labels']['st2']}")
        print(f"  {len(page):,} -> {len(filtered):,} chars")
        for line in filtered.splitlines()[:6]:
            print(f"  | {line[:100]}")


if __name__ == "__main__":
    main()
