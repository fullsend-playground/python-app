#!/usr/bin/env bash
set -euo pipefail

# This script runs on the trusted runner, before the agent sandbox exists.
source_url="https://raw.githubusercontent.com/fullsend-playground/python-app/main/README.md"
# Use a unique runner-temp filename shared with the harness host_files entry.
# RUNNER_TEMP and GITHUB_RUN_ID are provided by GitHub Actions, so each run
# gets a fresh handoff file and cannot accidentally mount stale data.
runner_temp="${RUNNER_TEMP:-${TMPDIR:-/tmp}}"
run_id="${GITHUB_RUN_ID:-local}"
output_file="${runner_temp}/fullsend-prefetch-${run_id}.json"
prefetch_dir="$(dirname "${output_file}")"
mkdir -p "${prefetch_dir}"

echo "PREFETCH_PATH ${output_file}"

raw_file="$(mktemp)"
trap 'rm -f "${raw_file}"' EXIT

curl --fail --silent --show-error --location --max-time 20 \
  "${source_url}" -o "${raw_file}"

python3 - "${raw_file}" "${output_file}" "${source_url}" <<'PY'
import json
import pathlib
import sys

raw_path, output_path, source_url = sys.argv[1:]
text = pathlib.Path(raw_path).read_text(encoding="utf-8")
heading = next(
    (line.removeprefix("#").strip() for line in text.splitlines() if line.startswith("#")),
    "(no heading)",
)
payload = {
    "source_url": source_url,
    "fetched_heading": heading,
    "fetched_bytes": len(text.encode("utf-8")),
}
pathlib.Path(output_path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"PREFETCH_READY source={source_url} heading={heading!r} bytes={payload['fetched_bytes']}")
PY
