// The workflow belongs to Bash. Fail rather than let the parent LLM take over.
export default function (pi) {
  pi.on('before_agent_start', () => {
    console.error('[forbid-parent-model] Parent model turn attempted; refusing it.');
    process.exit(99);
  });
}
