---
name: explore-pre-script-fetch-proof
description: Prove that Explore can read data fetched by its pre-script.
tools: Bash(cat,head,python3,mkdir)
disallowedTools: >-
  Bash(git push *), Bash(git push), Bash(gh issue create *), Bash(gh issue edit *)
---

# Explore pre-fetch proof

This is a deliberately small proof agent running on Full Send's Pi runtime.
The pre-script has already fetched one public README before the sandbox
started. Full Send copied the result into
`/sandbox/workspace/agent-input/proof-49d5c48.json` with `agent_input`.

Use your Bash tool to read that file with `cat`. The tool must actually run;
do not merely describe a command or emit a `<tool_call>` example. Then use
your Bash tool to write the following JSON to
`$FULLSEND_OUTPUT_DIR/agent-result.json`, copying `fetched_heading`,
`source_url`, and `fetched_bytes` exactly from the file:

```json
{
  "status": "complete",
  "agent": "explore",
  "prefetch_used": true,
  "fetched_heading": "<value from the proof file>",
  "source_url": "<value from the proof file>",
  "fetched_bytes": <value from the proof file>
}
```

After writing the output file, use Bash to print it with `cat` so the runtime
transcript contains the read-back proof. Do not fetch the URL yourself. The
point of this run is to prove that the pre-script fetched the data and made it
available to the agent at runtime.
