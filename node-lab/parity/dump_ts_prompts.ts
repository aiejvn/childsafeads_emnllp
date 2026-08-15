/**
 * Dump the TypeScript prompt builders' output for byte-comparison against the
 * Python ports. Run from `apps/backend` so the `@/*` path alias resolves:
 *
 *   cd apps/backend
 *   node_modules/.bin/ts-node -T \
 *     --compiler-options '{"module":"commonjs","moduleResolution":"node","experimentalDecorators":true,"emitDecoratorMetadata":true,"target":"es2023","esModuleInterop":true}' \
 *     -r tsconfig-paths/register \
 *     ../../scripts/node-lab/parity/dump_ts_prompts.ts \
 *     --flow ../../scripts/<flow>.json --node "<label or id>" --out /tmp/ts
 *
 * The decorator options must be spelled out: this file sits outside the
 * backend tsconfig's `include`, so ts-node does not inherit them and the
 * NestJS controllers pulled in transitively fail to load under standard
 * (non-legacy) decorators.
 *
 * Then diff against the Python side:
 *
 *   python -m node_lab.parity.check_builder_parity \
 *     --flow scripts/<flow>.json --node "<label or id>" --ts-dir /tmp/ts
 *
 * Only the builders that survive the distillation are dumped
 * (`buildAnalysisMessage`, `buildPredictionMessage`). `formatAnnotationContextBlock`
 * is not exported from the TS module, so its parity is covered by the
 * function-for-function port and code review rather than a diff.
 */
import * as fs from "fs";
import * as path from "path";

import { FactDictionary } from "@/fact-dictionary";
import {
  buildAnalysisMessage,
  buildPredictionMessage,
} from "@/node-execution/runners/reasoning-node.prompts";

function arg(name: string, fallback?: string): string {
  const i = process.argv.indexOf(`--${name}`);
  if (i >= 0 && process.argv[i + 1]) return process.argv[i + 1];
  if (fallback !== undefined) return fallback;
  throw new Error(`missing --${name}`);
}

const flowPath = arg("flow");
const nodeRef = arg("node");
const outDir = arg("out", "/tmp/ts-prompts");

const flow = JSON.parse(fs.readFileSync(flowPath, "utf8"));
const node = flow.nodes.find(
  (n: any) => n.id === nodeRef || n.data?.label === nodeRef,
);
if (!node) throw new Error(`no node matching "${nodeRef}"`);
const cfg = node.data.config;

// An empty dictionary is the honest input: node-lab replaces the ContextPool
// with a plain answers dict, and the empty case is what a Phase-1 run sees.
const empty = new FactDictionary();

fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(
  path.join(outDir, "analysis.txt"),
  buildAnalysisMessage({
    question: cfg.question,
    instructions: cfg.instructions,
    factDictionary: empty,
    subAgentAnswers: [],
  }),
);
fs.writeFileSync(
  path.join(outDir, "prediction.txt"),
  buildPredictionMessage({
    config: cfg,
    factDictionary: empty,
    rationale: "## Facts\nx\n\n## Analysis\ny",
  }),
);

console.log(`wrote analysis.txt, prediction.txt to ${outDir}`);
