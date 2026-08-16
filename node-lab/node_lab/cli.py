"""argparse entry point: `python -m node_lab {run,list,check-prompts}`."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .backend_client import BackendClient
from .documents import DocumentResolver
from .flow import AmbiguousNodeError, NodeNotFoundError, load_flow
from .llm import DEFAULT_MODEL, MODEL_REGISTRY, UTILITY_MODEL, LLMClient
from .reasoning.runner import RunDeps, RunOptions, run_node
from .types import NodeType, PriorAnswer


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


# ============================================
# list
# ============================================


def cmd_list(args: argparse.Namespace) -> int:
    flow = load_flow(args.flow)
    print(f"{flow.name}  ({len(flow.nodes)} nodes, {len(flow.edges)} edges)")
    print()

    counts: dict[str, int] = {}
    for node in flow.nodes:
        counts[node.type] = counts.get(node.type, 0) + 1
    print("  " + ", ".join(f"{n} {t}" for t, n in sorted(counts.items())))
    print()

    for node in flow.nodes:
        targets = [e.target for e in flow.outgoing(node.id)]
        line = f"  {node.type:<10} {node.id}  {node.label}"
        print(line)
        if node.type == NodeType.REASONING.value:
            config = node.reasoning_config()
            bits = [f"dataType={config.data_type.value}"]
            if config.custom_enum_values:
                bits.append(f"enum={len(config.custom_enum_values)}")
            if config.annotations:
                bits.append(f"annotations={len(config.annotations)}")
            if config.child_node_ids:
                bits.append(f"childNodeIds={len(config.child_node_ids)}")
            vsc = config.vector_search_config
            if vsc is not None:
                scopes = ",".join(vsc.document_scopes or []) or "none"
                bits.append(f"rag={'on' if vsc.enabled else 'off'}({scopes})")
            print(f"             {' '.join(bits)}")
        if targets:
            # Edges are informational: node-lab executes them only under
            # `--children graph`, and only one hop.
            print(f"             -> {', '.join(targets)}")
    return 0


# ============================================
# check-prompts
# ============================================


def cmd_check_prompts(_args: argparse.Namespace) -> int:
    from .parity.check_prompt_drift import check_all

    return 1 if check_all() else 0


# ============================================
# run
# ============================================


def _load_answers(path: Path | None) -> dict[str, PriorAnswer]:
    """Seed prior answers so a mid-flow node can run without its ancestors.

    Accepts either the full `{id: {label, prediction, rationale?}}` shape or
    the shorthand `{id: "prediction"}`.
    """
    if path is None:
        return {}
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    out: dict[str, PriorAnswer] = {}
    for node_id, value in raw.items():
        if isinstance(value, str):
            out[node_id] = PriorAnswer(label=node_id, prediction=value)
        else:
            out[node_id] = PriorAnswer.model_validate(value)
    return out


async def _run(args: argparse.Namespace) -> int:
    flow = load_flow(args.flow)
    try:
        node = flow.resolve(args.node)
    except (NodeNotFoundError, AmbiguousNodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if node.type != NodeType.REASONING.value:
        print(
            f"error: node {node.id} is a `{node.type}` node. Only reasoning "
            "runners are ported.",
            file=sys.stderr,
        )
        return 2

    options = RunOptions(
        model=args.model,
        answer_model=args.answer_model,
        reflect=args.reflect,
        rag=args.rag,
        children=args.children,
        rag_fixture=Path(args.rag_fixture) if args.rag_fixture else None,
        text_dir=Path(args.text_dir) if args.text_dir else None,
        cache_dir=Path(args.cache_dir),
    )

    def on_progress(message: str) -> None:
        if not args.quiet:
            print(f"  · {message}", file=sys.stderr)

    prior = _load_answers(Path(args.answers) if args.answers else None)

    # `--message` is repeatable free text about the matter. It has no
    # production analogue in the distilled node (the conversation layer is not
    # ported), so it is injected as a prior answer keyed `user_message`, which
    # is exactly how <Conversation_Facts> renders it.
    for index, message in enumerate(args.message or []):
        prior[f"user_message_{index}"] = PriorAnswer(
            label="User message", prediction=message
        )

    async with BackendClient() as backend:
        resolver = DocumentResolver(
            backend=backend,
            cache_dir=Path(args.cache_dir),
            text_dir=options.text_dir,
        )
        llm = LLMClient(structured_mode=args.structured_output)
        deps = RunDeps(
            flow=flow,
            llm=llm,
            backend=backend,
            resolver=resolver,
            options=options,
            on_progress=on_progress,
        )
        transcript = await run_node(node, prior, deps)

    transcript["run"] = {
        "flow": str(args.flow),
        "flowName": flow.name,
        "model": args.model,
        "answerModel": args.answer_model,
        "children": args.children,
        "rag": args.rag,
        "reflect": args.reflect,
        "startedAt": datetime.now(timezone.utc).isoformat(),
    }

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"{stamp}-{node.id}.json"
    out_path.write_text(
        json.dumps(transcript, indent=2, ensure_ascii=False, default=_fallback),
        encoding="utf-8",
    )

    _print_summary(transcript, out_path)
    return 0


def _fallback(value: Any) -> Any:
    return str(value)


def _print_summary(transcript: dict[str, Any], out_path: Path) -> None:
    node = transcript["node"]
    print()
    print(f"{node['label']}  ({node['id']})")
    analysis = transcript["analysis"]
    print(
        f"  analysis: {len(analysis['rationale'])} chars, {analysis['steps']} step(s)"
        + ("  [HIT STEP CAP]" if analysis["hitStepCap"] else "")
    )
    rag_calls = transcript["ragCalls"]
    if rag_calls:
        for call in rag_calls:
            suppressed = len(call["suppressedFileIds"])
            note = f", {suppressed} suppressed" if suppressed else ""
            print(f"  rag: {len(call['hits'])} hit(s){note}  “{call['query']}”")
    reflection = transcript.get("reflection")
    if reflection:
        print(
            f"  reflection: {reflection['passes']} pass(es), "
            f"{len(reflection['findings'])} finding(s), "
            f"revised={reflection['revised']}"
        )
    for candidate in transcript["answers"]:
        print(f"  answer: {candidate['probability']:.2f}  {candidate['prediction']!r}")
    usage = transcript["tokenUsage"]
    print(f"  tokens: in={usage['input_tokens']} out={usage['output_tokens']}")
    if transcript["childResults"]:
        print(f"  children: {len(transcript['childResults'])}")
    print()
    print(f"  -> {out_path}")


def cmd_run(args: argparse.Namespace) -> int:
    return asyncio.run(_run(args))


# ============================================
# parser
# ============================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="node_lab",
        description="Run one OpenJustice reasoning node (plus its children) "
        "against raw LLM APIs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run one reasoning node")
    run.add_argument("--flow", required=True, help="dialog flow export JSON")
    run.add_argument("--node", required=True, help="node id or label")
    run.add_argument(
        "--message",
        action="append",
        default=[],
        help="matter facts, repeatable; rendered into <Conversation_Facts>",
    )
    run.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        choices=sorted(MODEL_REGISTRY),
        help=f"analysis + reflection model (default: {DEFAULT_MODEL})",
    )
    run.add_argument(
        "--answer-model",
        default=UTILITY_MODEL,
        choices=sorted(MODEL_REGISTRY),
        help=f"prediction model (default: {UTILITY_MODEL}, mirroring UTILITY_MODEL)",
    )
    run.add_argument(
        "--children",
        default="inline",
        choices=["inline", "graph", "both", "none"],
        help="inline = config.childNodeIds; graph = every outgoing edge, one hop",
    )
    run.add_argument("--answers", help="JSON file of prior answers to seed")
    run.add_argument(
        "--rag",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="expose the rag_search tool (--no-rag withholds it entirely)",
    )
    run.add_argument(
        "--reflect",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="run the self-reflection pass",
    )
    run.add_argument("--rag-fixture", help="replay recorded RAG hits from a JSON file")
    run.add_argument("--text-dir", help="local <fileId>.txt overrides for documents")
    run.add_argument("--cache-dir", default=".cache", help="fetched document text cache")
    run.add_argument("--out", default="out", help="transcript output directory")
    run.add_argument(
        "--structured-output",
        default="auto",
        choices=["auto", "native", "tool"],
        help="how the final object is produced; auto falls back to a "
        "schema-shaped tool if the SDK rejects provider-native output",
    )
    run.add_argument("--quiet", action="store_true", help="suppress progress lines")
    run.set_defaults(func=cmd_run)

    listing = sub.add_parser("list", help="list nodes, types, labels, edges")
    listing.add_argument("--flow", required=True)
    listing.set_defaults(func=cmd_list)

    check = sub.add_parser(
        "check-prompts", help="diff the Python prompt copies against the TS sources"
    )
    check.set_defaults(func=cmd_check_prompts)

    return parser


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
