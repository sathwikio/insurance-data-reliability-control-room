// Jev decision layer — isolated from the Python/PySpark pipeline.
//
// Reads the deterministic pipeline state from data/jev_input.json, asks Jev
// (typesafe-ai/jev via the Vercel AI SDK evaluation API) one bounded choice
// question per run, and writes data/jev_decisions.json.
//
// Jev never computes metrics; it only selects one of the four allowed
// decisions. Confidence is the native probability the API returns for the
// chosen option (null when the API returns no distribution).
//
// Run: NODE_OPTIONS="--require ./dns-shim.cjs" node evaluate.mjs

import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { experimental_evaluate as evaluate } from 'ai';

const HERE = dirname(fileURLToPath(import.meta.url));
const INPUT_PATH = join(HERE, '..', 'data', 'jev_input.json');
const OUTPUT_PATH = join(HERE, '..', 'data', 'jev_decisions.json');

const MODEL_ID = 'typesafe-ai/jev';

const DECISION_QUESTION = {
  type: 'choice',
  instructions:
    'Decide the operational decision for this data pipeline run using only its measured state.',
  criteria: {
    HEALTHY: 'normal pipeline operation',
    WATCH: 'a small anomaly needs observation',
    INVESTIGATE: 'a material anomaly needs review',
    BLOCK: 'a severe condition makes downstream data unsafe',
  },
};

const ALLOWED = Object.keys(DECISION_QUESTION.criteria);

async function main() {
  const runs = JSON.parse(readFileSync(INPUT_PATH, 'utf8'));
  const decisions = [];

  for (const run of runs) {
    const { answers } = await evaluate({
      model: MODEL_ID,
      state: run, // deterministic pipeline state only — no metrics computed here
      questions: { decision: DECISION_QUESTION },
    });

    const answer = answers.decision;
    if (answer.type !== 'choice' || !ALLOWED.includes(answer.choice)) {
      throw new Error(`unexpected answer for ${run.run_id}: ${JSON.stringify(answer)}`);
    }
    decisions.push({
      run_id: run.run_id,
      decision: answer.choice,
      confidence: answer.probabilities ? answer.probabilities[answer.choice] : null,
    });
    process.stderr.write(`${run.run_id} -> ${answer.choice}\n`);
  }

  writeFileSync(OUTPUT_PATH, JSON.stringify(decisions, null, 2));
  console.log(`wrote ${decisions.length} decisions to ${OUTPUT_PATH}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
