#!/usr/bin/env bash
set -euo pipefail

test_dir="$(mktemp -d)"
trap 'rm -rf "${test_dir}"' EXIT

FULLSEND_PREFETCH_DIR="${test_dir}" \
  .fullsend/scripts/pre-explore.sh

test -s "${test_dir}/explore-prefetch.json"
python3 - "${test_dir}/explore-prefetch.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
assert data["source_url"].startswith("https://raw.githubusercontent.com/")
assert data["fetched_heading"]
assert data["fetched_bytes"] > 0
print("PASS: pre-script fetched data and wrote explore-prefetch.json")
print(json.dumps(data, indent=2))
PY
