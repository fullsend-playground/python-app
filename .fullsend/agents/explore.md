---
name: explore-pre-script-fetch-proof
description: Prove that Explore can read data fetched by its pre-script.
tools: Bash(cat,head,python3,mkdir)
disallowedTools: >-
  Bash(git push *), Bash(git push), Bash(gh issue create *), Bash(gh issue edit *)
---

# Explore pre-fetch proof

This is a deliberately small proof agent. The pre-script has already fetched
one public README before the sandbox started and Full Send copied the result
with the target project into
`/sandbox/workspace/target-repo/fullsend-pre-script-fetch-proof.json`.

First read that file with `cat`. Then write the following JSON to
`$FULLSEND_OUTPUT_DIR/agent-result.json`, copying `fetched_heading` and
`source_url` exactly from the file:

```json
{
  "status": "complete",
  "agent": "explore",
  "prefetch_used": true,
  "fetched_heading": "<value from the proof file>",
  "source_url": "<value from the proof file>"
}
```

Do not fetch the URL yourself. The point of this run is to prove that the
pre-script fetched the data and made it available to the agent at runtime.
