"""Builds all three GreaseLM KG variants from a single script, so the legal/flow/none
ablation (decided earlier: build all three, ablate later) has one place to look:

  build_legal_kg()    -- from public_data_dev/legal_provisions.json: nodes for all 16
                          ST3 compliance flags (only the 8 in common.ST3_LABELS are ever
                          predicted; the rest still enrich the graph's neighborhood) plus
                          the family/severity/instrument concepts they're grounded in.
                          "instrument" = the EU legal act a flag cites (UCPD, AVMSD, DSA,
                          ...) -- a shared hub, so two flags become graph-neighbors
                          whenever they cite the same act, family, or severity; no
                          flag-to-flag edge is ever added directly. NOTE (flagged by the
                          user 2026-08-09, revisit after baseline results): this
                          flag->hub assignment is inherited as-is from
                          legal_provisions.json's existing family/severity/instruments
                          fields, not independently validated for GNN usefulness.

  build_flow_kg()      -- generic parser for a dialog-flow export (the shape
                          emnllp-dialog-flow-dialog-flow.json is in: "nodes" with
                          id/type/data.label/data.config, "edges" with
                          source/target/sourceHandle) into the shared schema. A switch
                          node's outgoing edges are its branches (relation
                          "branch:<compareValue>", or "branch:default" for the isDefault
                          fallback); everything else is relation "next".

  build_combined_kg() -- the flow graph as scaffold, legal graph merged in (a plain
                          union of both graphs' nodes/edges -- disjoint id namespaces,
                          flow ids are the export's own UUIDs, legal ids are
                          "<type>:<name>", so nothing collides), then bridged via
                          "assesses" edges from the flow's four compliance-relevant
                          reasoning nodes to the label nodes they assess:
                            Commercial Type      -> st1_label:*  (5,  own customEnumValues)
                            Product Categories   -> st2_label:*  (12, common.ST2_LABELS --
                                                     see note below)
                            Disclosure and Claims -> st3_flag:*  (5,  own customEnumValues)
                            Product Risk          -> st3_flag:*  (3,  own customEnumValues)
                          st1_label/st2_label nodes are minted fresh (legal_provisions.json
                          doesn't cover ST1/ST2); Disclosure/Product Risk point at
                          st3_flag nodes that already exist from build_legal_kg(), found
                          by label lookup, so st3_flag:no_flag ends up with an assesses
                          edge from *both* Disclosure and Claims and Product Risk --
                          intentional, not a bug: it makes no_flag a 2-hop bridge between
                          those two reasoning nodes on top of its housekeeping-family edge.
                          NOTE: Product Categories' own customEnumValues in the exported
                          flow is just ["null", "other"] (checked against flow_graph.json)
                          -- incomplete, so that one node's bridge targets come from
                          common.ST2_LABELS instead of its own field. Commercial Type's
                          own customEnumValues, in contrast, IS the complete 5-label set
                          (same values as common.ST1_LABELS, just different order) so it
                          does NOT need that fallback and is sourced from its own field
                          like Disclosure/Product Risk are.

Usage (from repo root):
    python src/greaselm/kg/build_kg.py                  # builds all three, writes all three JSONs
    python src/greaselm/kg/build_kg.py --mode legal      # just the legal-taxonomy graph
    python src/greaselm/kg/build_kg.py --mode flow       # just the flow graph
    python src/greaselm/kg/build_kg.py --mode combined   # flow + legal, merged (builds both first)
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))  # so `import greaselm`/`import common` resolve
from common import ST2_LABELS  # noqa: E402
from greaselm.graph_schema import KnowledgeGraph  # noqa: E402

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
LEGAL_PROVISIONS_PATH = os.path.join(REPO_ROOT, "public_data_dev", "legal_provisions.json")
FLOW_PATH = os.path.join(REPO_ROOT, "emnllp-dialog-flow-dialog-flow.json")
KG_DIR = os.path.dirname(__file__)


def build_legal_kg(legal_provisions_path: str = LEGAL_PROVISIONS_PATH) -> KnowledgeGraph:
    with open(legal_provisions_path, encoding="utf-8") as f:
        data = json.load(f)

    graph = KnowledgeGraph("legal_taxonomy")

    families = sorted({flag["family"] for flag in data["flags"].values()})
    for family in families:
        graph.add_node(f"family:{family}", "family", family)

    severities = sorted({flag["severity"] for flag in data["flags"].values() if flag["severity"] != "none"})
    for severity in severities:
        graph.add_node(f"severity:{severity}", "severity", severity)

    instruments = sorted({inst["instrument"] for flag in data["flags"].values() for inst in flag["instruments"]})
    for instrument in instruments:
        graph.add_node(f"instrument:{instrument}", "instrument", instrument)

    for flag_name, flag in data["flags"].items():
        node_id = f"st3_flag:{flag_name}"
        graph.add_node(
            node_id, "st3_flag", flag_name,
            code=flag["code"], tier=flag["tier"], scored=flag["scored"], severity=flag["severity"],
        )
        graph.add_edge(node_id, f"family:{flag['family']}", "in_family")
        if flag["severity"] != "none":
            graph.add_edge(node_id, f"severity:{flag['severity']}", "has_severity")
        for inst in flag["instruments"]:
            graph.add_edge(
                node_id, f"instrument:{inst['instrument']}", "grounded_in",
                provisions=inst["provisions"], note=inst["note"],
            )

    return graph


def build_flow_kg(flow_path: str = FLOW_PATH) -> KnowledgeGraph:
    with open(flow_path, encoding="utf-8") as f:
        data = json.load(f)

    graph = KnowledgeGraph(data.get("dialogFlow", {}).get("name", "flow"))

    switch_branches = {}  # node id -> {branchId: branch dict}, for switch nodes only
    for node in data["nodes"]:
        config = node["data"].get("config", {})
        meta = {}
        if "customEnumValues" in config:
            meta["customEnumValues"] = [v for v in config["customEnumValues"] if v != "null"]
        if "question" in config:
            meta["question"] = config["question"]
        graph.add_node(node["id"], node["type"], node["data"]["label"], **meta)
        if node["type"] == "switch":
            switch_branches[node["id"]] = {b["branchId"]: b for b in config["branches"]}

    for edge in data["edges"]:
        source, target = edge["source"], edge["target"]
        relation = "next"
        if source in switch_branches:
            branch = switch_branches[source][edge["sourceHandle"]]
            if branch["isDefault"] or not branch["conditions"]:
                relation = "branch:default"
            else:
                relation = "branch:" + branch["conditions"][0]["compareValue"]
        graph.add_edge(source, target, relation)

    return graph


def _find_reasoning_node(graph: KnowledgeGraph, label: str):
    for n in graph.nodes:
        if n.type == "reasoning" and n.label == label:
            return n
    raise ValueError(f"no reasoning node labeled {label!r} in graph {graph.name!r}")


def build_combined_kg(flow_graph: KnowledgeGraph = None, legal_graph: KnowledgeGraph = None) -> KnowledgeGraph:
    flow_graph = flow_graph or build_flow_kg()
    legal_graph = legal_graph or build_legal_kg()

    commercial_type = _find_reasoning_node(flow_graph, "Commercial Type")
    product_categories = _find_reasoning_node(flow_graph, "Product Categories")
    disclosure = _find_reasoning_node(flow_graph, "Disclosure and Claims")
    product_risk = _find_reasoning_node(flow_graph, "Product Risk")

    graph = flow_graph.merge(legal_graph, name="combined")

    # Commercial Type's own customEnumValues is the complete, correctly-ordered st1
    # label set (checked against common.ST1_LABELS) -- mint st1_label nodes from it
    # directly, same pattern as the two st3_flag bridges below.
    for label in commercial_type.meta.get("customEnumValues", []):
        graph.add_node(f"st1_label:{label}", "st1_label", label)
        graph.add_edge(commercial_type.id, f"st1_label:{label}", "assesses")

    # Product Categories' own customEnumValues is just ["other"] in this export
    # (incomplete) -- fall back to the canonical ST2_LABELS list instead.
    for label in ST2_LABELS:
        graph.add_node(f"st2_label:{label}", "st2_label", label)
        graph.add_edge(product_categories.id, f"st2_label:{label}", "assesses")

    # Disclosure and Claims / Product Risk: point at st3_flag nodes that already exist
    # from build_legal_kg(), found by label. st3_flag:no_flag gets an edge from BOTH
    # (each node's own customEnumValues includes it) -- intentional: it becomes a
    # 2-hop bridge between the two reasoning nodes.
    st3_flag_ids = {n.label: n.id for n in legal_graph.nodes if n.type == "st3_flag"}
    for reasoning_node in (disclosure, product_risk):
        for label in reasoning_node.meta.get("customEnumValues", []):
            if label in st3_flag_ids:
                graph.add_edge(reasoning_node.id, st3_flag_ids[label], "assesses")

    return graph


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["legal", "flow", "combined", "all"], default="all")
    args = ap.parse_args()

    legal_graph = build_legal_kg() if args.mode in ("legal", "combined", "all") else None
    flow_graph = build_flow_kg() if args.mode in ("flow", "combined", "all") else None

    to_write = {}
    if legal_graph is not None and args.mode in ("legal", "all"):
        to_write["legal_taxonomy_graph.json"] = legal_graph
    if flow_graph is not None and args.mode in ("flow", "all"):
        to_write["flow_graph.json"] = flow_graph
    if args.mode in ("combined", "all"):
        to_write["combined_graph.json"] = build_combined_kg(flow_graph or build_flow_kg(), legal_graph or build_legal_kg())

    for filename, graph in to_write.items():
        path = os.path.join(KG_DIR, filename)
        graph.save(path)
        print(f"[{filename}] wrote {len(graph.nodes)} nodes, {len(graph.edges)} edges")
        print(f"[{filename}] node types: {graph.node_types()}")
        print(f"[{filename}] relation types: {graph.relation_types()}")


if __name__ == "__main__":
    main()
