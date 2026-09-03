#!/usr/bin/env bash
set -euo pipefail

# This script runs on the trusted runner, before the agent sandbox exists.
source_url="https://raw.githubusercontent.com/fullsend-playground/python-app/main/README.md"
# Write beside the harness configuration. Full Send's agent_input mechanism
# copies this runner-created directory into the sandbox after the pre-script
# ends.
config_dir="${FULLSEND_DIR:-$(dirname "${BASH_SOURCE[0]}")/..}"
if [[ "${config_dir}" != /* ]]; then
  config_dir="${PWD}/${config_dir}"
fi
config_dir="$(cd "${config_dir}" && pwd)"
output_file="${config_dir}/explore-prefetch-input-d64642a/proof.json"
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
print("PREFETCH_PAYLOAD " + json.dumps(payload, separators=(",", ":")))
PY
