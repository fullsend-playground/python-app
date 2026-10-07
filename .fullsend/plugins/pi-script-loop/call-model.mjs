import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [step, outputDir] = process.argv.slice(2);
const manifestPath = process.env.FULLSEND_PI_MANIFEST;
const manifestSum = process.env.FULLSEND_PI_MANIFEST_SHA256;
if (!manifestPath || !manifestSum) throw new Error('Fullsend Pi launch context is missing');
const { loadManifest, createAgentTool } = await import(
  pathToFileURL(join(dirname(manifestPath), 'fullsend-agent.js')).href
);
const manifest = loadManifest(manifestPath);
if (!manifest.agent?.enabled) throw new Error('Agent provisioning is missing');

const prompts = {
  plan: 'Without inspecting files or running tools, give a generic three-point plan for documentation cleanup. Keep it under 120 words.',
  review: 'Without inspecting files or running tools, critique this plan and list two concrete improvements in under 120 words:\n',
  summarize: 'Without inspecting files or running tools, summarize the plan and critique in five sentences:\n',
};
if (!Object.hasOwn(prompts, step)) throw new Error('Unknown loop step');
let prompt = prompts[step];
if (step !== 'plan') prompt += readFileSync(join(outputDir, 'plan.txt'), 'utf8');
if (step === 'summarize') prompt += '\nCritique:\n' + readFileSync(join(outputDir, 'review.txt'), 'utf8');

// Reuse today's internal dispatcher, including child preflight and usage recording.
// This API is internal: this example is tied to the inspected main commit.
const tool = createAgentTool(manifest, { manifestPath, manifestSum });
try {
  const result = await tool.run({ model: 'haiku', description: `Bash ${step}`, prompt });
  if (result.isError || !result.text?.trim()) throw new Error(result.error || 'Empty model response');
  writeFileSync(join(outputDir, `${step}.txt`), result.text + '\n');
  writeFileSync(join(outputDir, `${step}-call.json`), JSON.stringify(result, null, 2) + '\n');
} finally {
  tool.shutdown();
}
