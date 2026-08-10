"""Strip a dialog-flow export down to the content that carries task meaning.

The OpenJustice flow editor exports UI state alongside the flow itself: node UUIDs,
canvas x/y positions, measured widths and heights, selection flags, branch ids, CSS
classes, and the exporting user's OAuth id. In emnllp-dialog-flow-dialog-flow.json that
is 81% of the file -- 3,228 of its 4,003 Qwen3.5 tokens. It matters because the flow is
prepended to each instance as pre-context (`--df-path` in lora_train.py/lora_predict.py),
and `ClassificationDataset`/`GenerativeDataset` truncate to a fixed `--max-length`, so
every token of chrome displaces a token of segment text.

`flow_prompt_text()` renders the same flow as 943 tokens of questions, instructions,
answer sets, branch conditions and outcome templates -- 24% of the raw export -- with
UUIDs replaced by the node labels they stand for, which is also what makes the result
readable to a model.

This is the *text* consumer of the export. src/greaselm/kg/build_kg.py's
`build_flow_kg()` is the *graph* consumer, parsing the same file into the KnowledgeGraph
schema for GreaseLM. The two agree on how a switch node's branches become relations
("branch:<compareValue>", "branch:default" for the isDefault fallback), so the flow
reads the same whichever way it is loaded.

Usage (from the repo root):
    python src/common/dialog_flow.py                  # prompt-ready text
    python src/common/dialog_flow.py --format json    # the stripped structure
    python src/common/dialog_flow.py --stats          # what was dropped, and how much
"""
import argparse
import json
import os
import re

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
FLOW_PATH = os.path.join(REPO_ROOT, "emnllp-dialog-flow-dialog-flow.json")

# Editor chrome, dropped wherever it appears. Anything NOT listed here is kept, so a
# semantic field added by a future export survives by default instead of being silently
# lost -- the failure mode we want is a slightly longer prompt, not a missing rule.
NODE_CHROME = {
    "position", "measured", "selectable", "selected", "draggable", "dragging",
    "width", "height", "style", "className", "zIndex", "parentId", "handles",
}
# A switch branch's id/branchId/color go the same way, dropped by the reshape in
# strip_flow() rather than by name.
# Export provenance. exportedByUserId is a live Google OAuth subject id -- it must not
# reach a prompt, a training set, or a paper appendix.
EXPORT_CHROME = {"version", "exportedAt", "exportedByUserId"}

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(label: str, taken: set) -> str:
    """Readable stand-in for a node UUID. Collisions get a numeric suffix so the id
    stays unique and edges keep resolving."""
    base = _SLUG_RE.sub("_", label.strip().lower()).strip("_") or "node"
    slug, n = base, 2
    while slug in taken:
        slug, n = f"{base}_{n}", n + 1
    taken.add(slug)
    return slug


def _remap(value, id2slug: dict):
    """Recursively replace any node UUID with its slug. Applied to whole config
    subtrees, so id-bearing fields (childNodeIds, sourceNodeId, targetNodeId, ...) are
    rewritten without this module needing to know each one by name."""
    if isinstance(value, str):
        return id2slug.get(value, value)
    if isinstance(value, list):
        return [_remap(v, id2slug) for v in value]
    if isinstance(value, dict):
        return {k: _remap(v, id2slug) for k, v in value.items()}
    return value


def _prune(value):
    """Drop empty strings/lists/dicts at every depth. This export carries a fair number
    ("prompt": "", "annotations": [], a nested "customEnumValues": []) and they would
    otherwise survive as noise in both the stripped JSON and the prompt."""
    if isinstance(value, dict):
        return {k: _prune(v) for k, v in value.items() if v not in ("", [], {}, None)}
    if isinstance(value, list):
        return [_prune(v) for v in value]
    return value


def _keep(config: dict, id2slug: dict) -> dict:
    """Config with ids remapped and empty values pruned."""
    return _prune(_remap(config, id2slug))


def strip_flow(export: dict) -> dict:
    """Editor export -> {"name", "nodes", "edges"}, chrome removed and UUIDs replaced by
    label slugs. Switch branches are reshaped to {"when"|"default", "target"}; every
    other config field is passed through by `_keep`."""
    nodes_in = export.get("nodes", [])
    taken = set()
    id2slug = {n["id"]: _slug(n.get("data", {}).get("label", n["type"]), taken) for n in nodes_in}

    nodes, switch_branches = [], {}
    for node in nodes_in:
        data = node.get("data", {})
        config = _keep(data.get("config", {}), id2slug)

        out = {"id": id2slug[node["id"]], "type": node["type"], "label": data.get("label", "")}
        # A reasoning node's answer set is its customEnumValues minus the "null"
        # placeholder the editor seeds every enum with; renamed to "answers" because
        # that is what it means once the editor is out of the picture.
        if "customEnumValues" in config:
            answers = [v for v in config.pop("customEnumValues") if v != "null"]
            if answers:
                out["answers"] = answers
        if "branches" in config:
            branches = []
            for br in config.pop("branches"):
                shaped = {"target": br.get("targetNodeId")}
                if br.get("isDefault") or not br.get("conditions"):
                    shaped["default"] = True
                else:
                    cond = br["conditions"][0]  # the editor only ever emits one per branch
                    shaped["when"] = {
                        "node": cond.get("sourceNodeId"),
                        "operator": cond.get("operator", "=="),
                        "value": cond.get("compareValue"),
                    }
                branches.append(shaped)
            out["branches"] = branches
            switch_branches[node["id"]] = {b["branchId"]: b for b in data["config"]["branches"]}
        out.update(config)
        # data.prompt sits beside data.config rather than inside it; empty in the
        # current export, kept when a future one fills it in.
        if data.get("prompt"):
            out["prompt"] = _remap(data["prompt"], id2slug)
        nodes.append(out)

    edges = []
    for edge in export.get("edges", []):
        source, relation = edge["source"], "next"
        if source in switch_branches:
            branch = switch_branches[source].get(edge.get("sourceHandle"))
            if branch is None:
                relation = "branch:?"
            elif branch.get("isDefault") or not branch.get("conditions"):
                relation = "branch:default"
            else:
                relation = "branch:" + str(branch["conditions"][0].get("compareValue"))
        edges.append({"source": id2slug[source], "target": id2slug[edge["target"]], "relation": relation})

    return {"name": export.get("dialogFlow", {}).get("name", "flow"), "nodes": nodes, "edges": edges}


def load_flow(path: str = FLOW_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return strip_flow(json.load(f))


def flow_to_text(flow: dict) -> str:
    """Render a stripped flow as compact plain text. Node references are printed as
    labels rather than slugs -- the model reads "Assessability", not "assessability" --
    while the underlying dict keeps slugs so it stays programmatically addressable."""
    label = {n["id"]: n["label"] or n["id"] for n in flow["nodes"]}
    out_edges = {}
    for e in flow["edges"]:
        out_edges.setdefault(e["source"], []).append(e)

    lines = [f"DIALOG FLOW: {flow['name']}", ""]
    for node in flow["nodes"]:
        lines.append(f"[{node['type']}] {node['label']}")

        for fact in node.get("factDefinitions", []):
            spec = ", ".join(x for x in (fact.get("dataType"), "required" if fact.get("required") else "") if x)
            lines.append(f"  {fact.get('label', 'fact')} ({spec}): {fact.get('instructions', '')}".rstrip())
        if node.get("question"):
            lines.append(f"  Q: {node['question']}")
        if node.get("answers"):
            lines.append(f"  A: {' | '.join(node['answers'])}")
        if node.get("instructions"):
            lines.append(f"  How: {node['instructions']}")
        if node.get("prompt"):
            lines.append(f"  Prompt: {node['prompt']}")
        if node.get("template"):
            kind = node.get("responseType", "response")
            body = "\n".join(f"    {ln}" for ln in node["template"].strip().splitlines())
            lines += [f"  Respond ({kind}):", body]

        for br in node.get("branches", []):
            target = label.get(br.get("target"), br.get("target"))
            if br.get("default"):
                lines.append(f"  else -> {target}")
            else:
                w = br["when"]
                lines.append(f"  if {label.get(w['node'], w['node'])} {w['operator']} {w['value']} -> {target}")
        # A switch node's flow is already stated by its branches; printing its edges too
        # would say the same thing a second time.
        if not node.get("branches"):
            for e in out_edges.get(node["id"], []):
                lines.append(f"  -> {label.get(e['target'], e['target'])}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def flow_prompt_text(path: str = FLOW_PATH) -> str:
    """The drop-in for `json.dumps(json.load(f), separators=(",", ":"))` at the
    --df-path call sites in lora_train.py / lora_predict.py."""
    return flow_to_text(load_flow(path))


def df_pre_context(path: str, lean: bool = True) -> str:
    """The dialog flow as prompt pre-context: stripped and rendered when `lean`, or the
    raw compact JSON dump the --df-path call sites used before this module existed.

    The raw form is kept only so `--lean-prompt` has an honest ablation counterpart --
    it costs 4,003 Qwen3.5 tokens against 943 for the same content, and at the encoder
    path's --max-length 512 it does not fit at all."""
    if lean:
        return flow_prompt_text(path)
    with open(path, encoding="utf-8") as f:
        return json.dumps(json.load(f), separators=(",", ":"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("flow", nargs="?", default=FLOW_PATH, help=f"dialog-flow export (default: {FLOW_PATH})")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--stats", action="store_true", help="report what stripping removed instead of the flow")
    ap.add_argument("--out", help="write to this path instead of stdout")
    args = ap.parse_args()

    with open(args.flow, encoding="utf-8") as f:
        export = json.load(f)
    flow = strip_flow(export)
    text = flow_to_text(flow)

    if args.stats:
        raw = json.dumps(export, separators=(",", ":"))
        stripped = json.dumps(flow, separators=(",", ":"))
        present = sorted(EXPORT_CHROME & set(export)) + sorted(
            {k for n in export.get("nodes", []) for k in n} & NODE_CHROME
        )
        rendered = "\n".join(
            f"  {name:<22} {len(s):>7,} chars  {100 * len(s) / len(raw):>5.1f}%"
            for name, s in (("raw export", raw), ("stripped json", stripped), ("rendered text", text))
        )
        print(f"{args.flow}\n{rendered}")
        print(f"  {len(flow['nodes'])} nodes, {len(flow['edges'])} edges")
        print(f"  chrome dropped: {', '.join(present)}")
        return

    payload = json.dumps(flow, indent=2) + "\n" if args.format == "json" else text
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload)
        print(f"wrote {len(payload):,} chars to {args.out}")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
