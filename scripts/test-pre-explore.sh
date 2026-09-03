#!/usr/bin/env bash
set -euo pipefail

test_dir="$(mktemp -d)"
trap 'rm -rf "${test_dir}"' EXIT
mkdir -p "${test_dir}/target-repo"

TARGET_REPO_DIR="${test_dir}/target-repo" \
  .fullsend/scripts/pre-explore.sh

test -s "${test_dir}/target-repo/fullsend-pre-script-fetch-proof.json"
python3 - "${test_dir}/target-repo/fullsend-pre-script-fetch-proof.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
assert data["source_url"].startswith("https://raw.githubusercontent.com/")
assert data["fetched_heading"]
assert data["fetched_bytes"] > 0
print("PASS: pre-script fetched data into the target repo")
print(json.dumps(data, indent=2))
PY
