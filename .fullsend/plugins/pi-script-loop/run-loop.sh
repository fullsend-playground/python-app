#!/usr/bin/env bash
set -euo pipefail

plugin_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
output_dir=${SCRIPT_LOOP_OUTPUT_DIR:-/sandbox/workspace/output}
mode=${SCRIPT_LOOP_MODE:-live}
case "$mode" in proof|live) ;; *) echo "Invalid SCRIPT_LOOP_MODE" >&2; exit 2 ;; esac
mkdir -p -- "$output_dir"
trace_file="$output_dir/loop-trace.txt"
: > "$trace_file"
printf 'script_started\n' >> "$trace_file"

for step in plan review summarize; do
  printf 'call_started:%s\n' "$step" >> "$trace_file"
  if [[ "$mode" == proof ]]; then
    # Startup-order proof only. No model request or model credential is used.
    printf 'MOCK response for %s\n' "$step" > "$output_dir/$step.txt"
  else
    node "$plugin_dir/call-model.mjs" "$step" "$output_dir"
  fi
  printf 'call_completed:%s\n' "$step" >> "$trace_file"
done

printf 'script_completed\n' >> "$trace_file"
node --input-type=module - "$output_dir" "$mode" <<'JS'
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
const [outputDir, mode] = process.argv.slice(2);
writeFileSync(join(outputDir, 'agent-result.json'), JSON.stringify({
  status: 'ok', summary: `Bash completed three ${mode === 'proof' ? 'mock' : 'live model'} steps.`,
  comment: '', mode,
}) + '\n');
JS
