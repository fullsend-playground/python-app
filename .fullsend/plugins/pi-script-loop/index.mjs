import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mkdirSync, readFileSync, writeFileSync, writeSync } from 'node:fs';

// This is lifecycle code, not a model-requested tool call.
export default function (pi) {
  let started = false;
  const pluginDir = dirname(fileURLToPath(import.meta.url));
  pi.on('session_start', () => {
    if (started) return;
    started = true;
    const outputDir = process.env.FULLSEND_OUTPUT_DIR || process.env.SCRIPT_LOOP_OUTPUT_DIR || '/sandbox/workspace/output';
    mkdirSync(outputDir, { recursive: true });
    try {
      const result = spawnSync('bash', [join(pluginDir, 'run-loop.sh')], {
        env: { ...process.env, SCRIPT_LOOP_OUTPUT_DIR: outputDir },
        stdio: ['ignore', 'ignore', 'inherit'],
        timeout: 660_000,
      });
      if (result.error) throw result.error;
      if (result.status !== 0) throw new Error(`Bash loop exited ${result.status}`);
      // Fullsend's current Pi parser requires an assistant message + agent_end.
      // These are SYNTHETIC script-completion records, not a model response.
      // Consequently its num_turns includes one adapter record, despite zero
      // parent inference calls. Preserve this provenance when sharing metrics.
      const output = JSON.parse(readFileSync(join(outputDir, 'agent-result.json'), 'utf8'));
      const message = {
        role: 'assistant', model: 'script-loop-completion-adapter',
        provider: 'script-loop', api: 'script', stopReason: 'stop',
        content: [{ type: 'text', text: `[Synthetic script completion; no parent LLM call] ${output.summary}` }],
        usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0,
          totalTokens: 0, cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } },
        timestamp: Date.now(), synthetic: true,
      };
      writeSync(1, JSON.stringify({ type: 'message_end', message, synthetic: true }) + '\n');
      writeSync(1, JSON.stringify({ type: 'agent_end', messages: [message], synthetic: true }) + '\n');
      // Exit before Pi can send the parent's prompt to any model.
      process.exit(0);
    } catch (error) {
      writeFileSync(join(outputDir, 'agent-result.json'), JSON.stringify({
        status: 'error', summary: error.message, comment: '',
      }) + '\n');
      console.error(`[start-script] ${error.message}`);
      process.exit(1);
    }
  });
}
