#!/usr/bin/env bash
set -euo pipefail

# This script runs on the trusted runner, before the agent sandbox exists.
source_url="https://raw.githubusercontent.com/fullsend-playground/python-app/main/README.md"
# Keep the handoff file beside the checked-out Full Send configuration. The
# harness copies this file after the pre-script finishes, so the sandbox gets
# the exact file produced by this run rather than a shared /tmp filename.
config_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
prefetch_dir="${FULLSEND_PREFETCH_DIR:-${config_dir}}"
output_file="${prefetch_dir}/explore-prefetch.json"
mkdir -p "${prefetch_dir}"

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
