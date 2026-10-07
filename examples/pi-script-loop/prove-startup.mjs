import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, realpathSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const example = dirname(fileURLToPath(import.meta.url));
const root = join(example, '../..');
const piBin = process.env.PI_BIN;
if (!piBin) throw new Error('Set PI_BIN to a Pi 0.99.2 executable');
let packageDir = dirname(realpathSync(piBin));
while (!existsSync(join(packageDir, 'package.json')) && dirname(packageDir) !== packageDir) packageDir = dirname(packageDir);
const piVersion = JSON.parse(readFileSync(join(packageDir, 'package.json'), 'utf8')).version;
assert.equal(piVersion, '0.99.2');
const checks = [];
for (const [index, mode] of ['proof', 'proof', 'invalid'].entries()) {
  const dir = mkdtempSync(join(tmpdir(), 'fullsend-start-script-proof-'));
  mkdirSync(join(dir, 'config'));
  mkdirSync(join(dir, 'output'));
  const run = spawnSync(piBin, [
    '--print', '--mode', 'json', '--no-approve', '--no-extensions', '--no-skills',
    '--no-tools', '-e', join(root, '.fullsend/plugins/pi-script-guard/index.mjs'),
    '-e', join(root, '.fullsend/plugins/pi-script-loop'),
    'The parent model must never receive this prompt.',
  ], { encoding: 'utf8', timeout: 30_000, cwd: dir,
    env: { ...process.env, PI_CODING_AGENT_DIR: join(dir, 'config'),
      ANTHROPIC_API_KEY: 'proof-placeholder-never-sent',
      SCRIPT_LOOP_MODE: mode, SCRIPT_LOOP_OUTPUT_DIR: join(dir, 'output') },
  });
  assert.ifError(run.error);
  assert.equal(run.status, mode === 'proof' ? 0 : 1, run.stderr);
  // Only explicitly synthetic completion records may be emitted.
  const events = run.stdout.trim() ? run.stdout.trim().split('\n').map(JSON.parse) : [];
  assert.equal(events.length, mode === 'proof' ? 2 : 0);
  for (const event of events) assert.equal(event.synthetic, true);
  if (events.length) {
    assert.equal(events[0].message.synthetic, true);
    assert.equal(events[0].message.model, 'script-loop-completion-adapter');
    assert.equal(events[0].message.usage.totalTokens, 0);
  }
  const result = JSON.parse(readFileSync(join(dir, 'output/agent-result.json'), 'utf8'));
  assert.equal(result.status, mode === 'proof' ? 'ok' : 'error');
  if (mode === 'proof') {
    const validate = spawnSync(join(root, '.fullsend/scripts/validate-pi-script-loop.sh'), [],
      { cwd: dir, encoding: 'utf8', env: { ...process.env, FULLSEND_OUTPUT_SCHEMA: join(root, '.fullsend/schemas/pi-script-loop-result.schema.json') } });
    assert.equal(validate.status, 0, validate.stderr);
    checks.push({ startup: index + 1, mode, exitCode: run.status,
      trace: readFileSync(join(dir, 'output/loop-trace.txt'), 'utf8').trim().split('\n'),
      parentModelEvents: 0, syntheticCompletionRecords: events.length, validation: validate.stdout.trim() });
  } else {
    checks.push({ startup: index + 1, mode, exitCode: run.status,
      parentModelEvents: 0, result });
  }
}
// Positive control: the watchdog must fire when the startup-script plugin is absent.
const controlDir = mkdtempSync(join(tmpdir(), 'fullsend-parent-control-'));
mkdirSync(join(controlDir, 'config'));
const control = spawnSync(piBin, [
  '--print', '--mode', 'json', '--no-approve', '--no-extensions', '--no-skills',
  '--no-tools', '-e', join(root, '.fullsend/plugins/pi-script-guard/index.mjs'), 'Test watchdog.',
], { encoding: 'utf8', timeout: 30_000, cwd: controlDir,
  env: { ...process.env, PI_CODING_AGENT_DIR: join(controlDir, 'config'),
    ANTHROPIC_API_KEY: 'proof-placeholder-never-sent' },
});
assert.ifError(control.error);
assert.equal(control.status, 99, control.stderr);
checks.push({ control: 'startup plugin absent', exitCode: 99, watchdog: 'parent agent attempt blocked before model call' });
const proof = { piVersion, scope: 'Actual Pi lifecycle, local process; model calls mocked; not a Fullsend/OpenShell sandbox test', checks };
writeFileSync(join(example, 'startup-proof.json'), JSON.stringify(proof, null, 2) + '\n');
console.log('PASS: two independent Pi startups ran every Bash step; failure exited 1; no parent model events.');
