#!/usr/bin/env bash
set -euo pipefail

test_dir="$(mktemp -d)"
trap 'rm -rf "${test_dir}"' EXIT
mkdir -p "${test_dir}/fullsend"

FULLSEND_DIR="${test_dir}/fullsend" \
  .fullsend/scripts/pre-explore.sh

test -s "${test_dir}/fullsend/explore-prefetch-input-d64642a/proof-49d5c48.json"
python3 - "${test_dir}/fullsend/explore-prefetch-input-d64642a/proof-49d5c48.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
assert data["source_url"].startswith("https://raw.githubusercontent.com/")
assert data["fetched_heading"]
assert data["fetched_bytes"] > 0
print("PASS: pre-script fetched data into the Full Send handoff directory")
print(json.dumps(data, indent=2))
PY
