# Deterministic Bash orchestration with Pi

This registered example demonstrates Bash owning a three-step loop inside a
Fullsend sandbox. The `session_start` extension invokes `run-loop.sh` before
Pi starts a parent agent turn. Bash calls Haiku for plan, review, and summary,
passing earlier answers to later steps. The independent guard exits 99 if a
parent agent turn is attempted. The parent prompt is never sent to an LLM.

The example uses existing harness `plugins:` and `Agent` provisioning, not a
new `entrypoint:` field. Registration was created with `fullsend agent new`.
The agent's only declared tool is `Agent`, so children have no built-in tools.
The script uses Fullsend's current internal child dispatcher, including its
manifest/provider integrity checks and child usage recording. That JavaScript
API is internal; this example intentionally pins the Fullsend source revision.

## Execution path and trust

`fullsend run → OpenShell sandbox → Pi session_start → Bash → three child Pi calls → validation`

The harness and extension are trusted repository configuration. This does not
turn arbitrary untrusted Bash into a model tool protected by PreToolUse hooks:
the orchestrator runs as extension code inside the sandbox. The child dispatcher
provisions Fullsend's usual child hook adapter. Sandbox filesystem and provider
egress policy remain in effect. No repository modifications, GitHub writes,
pre-script, or post-script are part of this example.

## Local startup check: no model calls

```bash
python3 -m pip install -e '.[dev]'
npm ci --prefix examples/pi-script-loop --ignore-scripts --no-audit --no-fund
make test-pi-script-loop
```

This runs actual Pi 0.99.2 twice with mocked model responses. It checks complete
traces, output schema, a deliberately invalid mode, and a positive watchdog
control with the startup plugin absent. CI runs this check without model
credentials. It is lifecycle evidence; it is not an OpenShell sandbox test.

## Build the pinned Fullsend CLI

Read `versions.json` for the audited source revisions and image digest. Use the
same CLI source as the shim. After cloning Fullsend, check out that exact commit:

```bash
FULLSEND_PROOF_REF=$(python3 -c 'import json; print(json.load(open("examples/pi-script-loop/versions.json"))["fullsend"])')
git -C /absolute/path/to/fullsend fetch origin "$FULLSEND_PROOF_REF"
git -C /absolute/path/to/fullsend checkout --detach "$FULLSEND_PROOF_REF"
cd /absolute/path/to/fullsend
go build -ldflags "-X github.com/fullsend-ai/fullsend/internal/cli.version=$FULLSEND_PROOF_REF -X github.com/fullsend-ai/fullsend/internal/cli.commitSHA=$FULLSEND_PROOF_REF" -o /tmp/fullsend-pi-proof ./cmd/fullsend
```

Use a disposable Fullsend clone for this build so checking out the proof revision
does not disturb ongoing work. For a source archive without Git metadata add
`-buildvcs=false`. The proof runner rejects a CLI whose version does not identify
the recorded commit, preventing accidental verification with a stale binary.

## Real sandbox verification

Install the recorded OpenShell version, start its authenticated gateway, and
configure existing credentials according to Fullsend's local-run guide. The
runner needs `GH_TOKEN`, `ANTHROPIC_VERTEX_PROJECT_ID`, `CLOUD_ML_REGION`, and
`GOOGLE_APPLICATION_CREDENTIALS`; use private env files outside this repository.
Never put credential values in an issue, command comment, evidence file, or PR.

From this repository root:

```bash
python3 examples/pi-script-loop/prove-sandbox.py \
  --fullsend /tmp/fullsend-pi-proof --mode proof \
  --env-file /absolute/path/to/private-gcp.env \
  --env-file /absolute/path/to/private-github.env \
  --report docs/evidence/pi-script-loop/proof-local.json

python3 examples/pi-script-loop/prove-sandbox.py \
  --fullsend /tmp/fullsend-pi-proof --mode live \
  --env-file /absolute/path/to/private-gcp.env \
  --env-file /absolute/path/to/private-github.env \
  --report docs/evidence/pi-script-loop/live-local.json
```

The hosted harness declares literal `live` mode. This runner selects each test
mode in a private configuration copy without changing the repository harness.

`proof` runs two successful real sandboxes with mocked responses and one expected
invalid-mode failure. It still needs Fullsend's normal forge/Vertex preflight
credentials. `live` makes three real billable Haiku calls in one sandbox, checks
nonzero child token usage, ordered traces, schema, successful agent exit, and
host validation. Raw logs and responses stay in a private temporary directory;
the report exports only selected fields and response hashes. Review generated
reports before publication. Each invocation cleans up its sandbox normally.

## Running through Fullsend dispatch

After these files are merged into the repository's default branch, an authorized
maintainer can comment `/fs-pi-script-loop` on a repository issue or a same-repo
PR. Fullsend dispatch performs authorization and evaluates the generated CEL
trigger. This starts live mode and incurs model usage. The example does not
run on ordinary issue creation and excludes fork PRs. It needs no custom mint
role or extra per-agent workflow. Merge and hosted execution have not been
claimed by the local evidence report.

## Completion and telemetry limitation

Fullsend's current Pi parser requires an assistant message and terminal event.
The extension therefore emits explicitly **synthetic script-completion events**,
with zero tokens/cost, before exiting. This is an adapter record, not a model
answer. Fullsend's reported parent turns include it; request counters can report
four entries for three real child calls. Evidence separates actual child calls
from that adapter and reconciles recorded cost against child usage.

An invalid mode is an intentional negative test, not a failure of valid live
mode. One iteration prevents validation-driven replay within an invocation;
external workflow retries can still repeat the whole run. This is deterministic
startup sequencing, not exactly-once execution across runs.

## Relevance to the custom-entrypoint ADR

Existing Pi extensions already satisfy this bounded requirement: a script owns
the loop in the sandbox, makes model calls, and is launched without a parent
model decision. A new entrypoint schema is not a prerequisite for it. A first-
class entrypoint could still supply a public invocation contract, runtime
independence, agentless bootstrap, and cleaner completion/telemetry. This proof
does not establish that those additional goals are redundant.

See the [implementation report](../../docs/pi-script-loop-implementation.md)
for current pins, migration details, validation evidence, and source links.
