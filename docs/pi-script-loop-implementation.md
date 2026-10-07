# Pi script-loop implementation and verification

Verified on 2026-10-07 against Fullsend main `bf5f4a62a846c2dbba81c80f9215e96be2738fcb`. This report accompanies
the runnable [example](../examples/pi-script-loop/README.md) and its
[live evidence](evidence/pi-script-loop/live-2026-10-07.json).

## Outcome

The Python playground now has a registered Pi example in which Bash owns a
three-step loop inside a real OpenShell sandbox. The live verification made
**three actual Haiku child calls**, made **zero parent model calls**, exited
successfully, and passed host-side schema and trace validation. The final
verified run recorded **$0.008311** in child model usage.

The motivating comparison is [Fullsend PR #7947](https://github.com/fullsend-ai/fullsend/pull/7947).
This proves the bounded Pi capability without a new harness `entrypoint:`
schema. It does not prove that the broader custom-entrypoint ADR's public
invocation contract, runtime independence, or agentless provisioning goals
are redundant. The example uses an internal dispatcher and a clearly labelled
synthetic completion adapter, whose telemetry limitations are recorded below.

## Audited baseline

- Python-app starting main: `ce6d8ffc67f5bb7b0d37efe3c32126cf87c49cb5`.
- Fullsend source and reusable dispatch: `bf5f4a62a846c2dbba81c80f9215e96be2738fcb`.
- Latest published stable release at the audit: `v0.45.0`; this example uses
  the newer audited main commit, rather than claiming that release contains
  every current-main change.
- Registered upstream agents: `56b9aa3a2a5b02d0000d1bd3f8df2fd65560a294`.
- OpenShell: `0.1.2`. Pi: `0.99.2`.
- Sandbox: `ghcr.io/fullsend-ai/fullsend-sandbox@sha256:f8255971fec8a72a60adb20f501e55098f237e699dc829f0894647c0de2a19c2` — the image recommended by the
  current generator, verified with the real sandbox run.

Pins are maintained in [versions.json](../examples/pi-script-loop/versions.json).
The shim's immutable workflow SHA also selects the matching CLI through
upstream's `job.workflow_sha` default. No older `fullsend_version` override
is passed. Local proof checks the binary's stamped source version.

## Changes recorded

1. Cloned the public playground and prepared the change on
   `feat/pi-script-loop-proof`, leaving its main checkout history intact.
2. Audited repository configuration, workflow contract, registered sources,
   and the presence of existing inference configuration. Secret values and
   private infrastructure identifiers were not copied into this report.
3. Rendered the current managed shim template with the audited SHA. This
   removes the obsolete installation-mode input, forwards the current optional
   inputs/secrets, routes slash commands as upstream now requires, and includes
   the current effective-permission handling for custom GitHub roles.
4. Updated the existing triage source using `fullsend agent update`, preserving
   its integrity hash and adding the CLI-generated remote dependency lock.
5. Migrated the existing pre-fetch demo to the built-in `vertex-ai` provider,
   removed stale reserved-name provider/profile copies, added the generated
   sandbox policy, and moved its command to `/fs-prefetch-demo` to match the
   current shim's routing filter. Removed an obsolete vendored-CLI note; no
   old binary was present in the repository.
6. Used `fullsend agent new pi-script-loop --runtime pi --model haiku` as the
   starting point. Added the trusted startup plugin, independent parent guard,
   and ordered Bash loop. Kept the generated registration, role, trigger,
   policy, credential delivery, model settings, and result-validation layout.
7. Removed unnecessary providers and the generated posting script. The
   example declares only Vertex, requests read privilege, and allows one
   iteration. It consumes no issue/PR body as a model prompt. Children have
   no built-in tools; prompts are generic and bounded.
8. Added a schema plus validation of complete step traces and live child
   usage. Added a reproducible real-sandbox runner, which stores raw data in
   a private temporary directory and exports only whitelisted evidence fields.
9. Added a credential-free CI lifecycle check using the pinned Pi npm package
   and lockfile, with dependency install scripts disabled. The workflow uses
   normal `pull_request`, minimal permissions, pinned actions, and a checkout
   without persisted Git credentials. It receives no model secrets.
10. Added README links, documentation coverage, sanitized proof records,
    explicit compatibility caveats, and ignored local caches/dependencies,
    private env files, and raw output directories.

## Verification and evidence boundaries

- Application tests: eight passed.
- Existing pre-fetch test: passed.
- Ruff checks and formatting: passed.
- Node and Bash syntax: passed.
- GitHub workflow validation with actionlint 1.7.12: passed; external
  shellcheck was disabled, with shell syntax and execution checked separately.
- Actual pinned Pi lifecycle: two startup successes, an intentional invalid-
  mode failure, and a positive guard control passed. See
  [startup evidence](evidence/pi-script-loop/startup-2026-10-07.json).
- Fullsend's current harness loader, generated-resource checks, plugin-tree
  validation, and CEL evaluation: passed for the local configurations. The
  new trigger matched its command, rejected unrelated commands, and rejected
  fork PRs. These are local routing checks, not hosted authorization evidence.
- Real Fullsend/OpenShell mock proof: two independent successes and one
  expected invalid-mode failure. See
  [sandbox evidence](evidence/pi-script-loop/proof-2026-10-07.json).
- Real Fullsend/OpenShell live proof: three successful Haiku calls in Bash
  order, zero parent inference, agent exit 0, validation passed. Evidence
  records child token usage, response lengths/hashes, exact versions, and
  implementation fingerprints; it does not publish raw responses or logs.
- Fresh locked npm install: passed. Plugin trees contain no symlinks and
  the npm lockfile resolves packages through the public npm registry.

The invalid mode was deliberately supplied to test failure propagation. Its
failure is expected and does not undermine the valid live run. The CI startup
check is model-free and does not itself prove OpenShell provisioning or live
inference; those have separate recorded sandbox evidence.

## Public-repository precautions

Credentials and raw logs were kept outside the repository. The inference
configuration already provisioned for the playground was preserved; no mint
deployment, repository secret, or inference identity was changed. Generated
evidence contains fixed schema fields, public source refs, numeric usage,
response hashes, and result states. Model output text and arbitrary exception
messages are not exported. The [public-safety scan](evidence/pi-script-loop/public-safety-2026-10-07.json)
records zero gitleaks findings and zero matches against the existing credential
values; it publishes only counts and tool versions, without finding values.

The registered command uses Fullsend's existing default-branch configuration
and platform authorization. A same-repo PR or issue can be used after merge by
an authorized maintainer. The example contains no forge-write operations;
Fullsend may still produce its normal platform status notifications in hosted
runs. The lifecycle CI job does not receive inference credentials and does
not upload raw artifacts.

## Completion, upgrade, and publication limits

The current Pi parser expects an assistant message and terminal event. The
plugin emits an explicitly synthetic, zero-token script-completion record.
It is not an LLM response. Fullsend reports one parent turn and can count
that adapter as a fourth request; the actual child-call records number three
and their cost sums to the recorded run cost. This limitation is preserved
in the evidence instead of being hidden.

Startup is deterministic once the extension is valid, loaded, and reaches
`session_start`. Provisioning and authentication can fail. One iteration
prevents validation replay within a run, but CI retries can start another
whole run. This is not an exactly-once guarantee across invocations.

The example was published in [python-app PR #49](https://github.com/fullsend-playground/python-app/pull/49)
with explicit commit/push permission. Its first hosted lifecycle run exposed
setuptools discovering both `app.py` and `test_app.py` as application modules.
The package now declares `app` explicitly and uses an explicit build backend;
a clean editable installation was added to the verification. Hosted CI results
remain separate from the recorded live sandbox evidence. After merge, the
committed example and automatic startup check make the proof maintainable;
the live command remains an explicit, billable operation.

To upgrade: review the new Fullsend docs and internal child-dispatch contract,
render the matching shim, update `versions.json` and agent/image pins, update
the Pi npm lock if needed, rerun startup and real sandbox tests, and record new
sanitized evidence. The internal API and completion stream are compatibility
workarounds tied to the audited revisions.

## Documentation coverage

All 251 Markdown documents in the audited Fullsend tree were inventoried and
scanned for implementation topics. Task-relevant sections of the configuration,
harness, authoring, Pi, local-run, trigger, workflow, sandbox, and shell guides
were reviewed against the actual source. This is not a claim of a line-by-line
semantic reading of every historical ADR. The
[coverage inventory](evidence/pi-script-loop/documentation-coverage.json)
records every path, source digest, and review level.

Key current sources:

- [Config reference](https://github.com/fullsend-ai/fullsend/blob/bf5f4a62a846c2dbba81c80f9215e96be2738fcb/docs/reference/config-reference.md)
- [Harness reference](https://github.com/fullsend-ai/fullsend/blob/bf5f4a62a846c2dbba81c80f9215e96be2738fcb/docs/reference/harness-reference.md)
- [Agent generator and update commands](https://github.com/fullsend-ai/fullsend/blob/bf5f4a62a846c2dbba81c80f9215e96be2738fcb/docs/cli/agent.md)
- [Custom agents and built-in provider migration](https://github.com/fullsend-ai/fullsend/blob/bf5f4a62a846c2dbba81c80f9215e96be2738fcb/docs/guides/user/bring-your-own-agent.md)
- [Pi extensions and child calls](https://github.com/fullsend-ai/fullsend/blob/bf5f4a62a846c2dbba81c80f9215e96be2738fcb/docs/runtimes/pi.md)
- [Running Fullsend locally](https://github.com/fullsend-ai/fullsend/blob/bf5f4a62a846c2dbba81c80f9215e96be2738fcb/docs/guides/user/running-agents-locally.md)
- [CEL trigger and authorization contract](https://github.com/fullsend-ai/fullsend/blob/bf5f4a62a846c2dbba81c80f9215e96be2738fcb/docs/guides/user/cel-triggers-reference.md)
- [Workflow contracts](https://github.com/fullsend-ai/fullsend/blob/bf5f4a62a846c2dbba81c80f9215e96be2738fcb/docs/contributing/workflow-contracts.md)
- [Current managed shim template](https://github.com/fullsend-ai/fullsend/blob/bf5f4a62a846c2dbba81c80f9215e96be2738fcb/internal/scaffold/fullsend-repo/templates/shim-per-repo.yaml)
- [Current Pi child dispatcher](https://github.com/fullsend-ai/fullsend/blob/bf5f4a62a846c2dbba81c80f9215e96be2738fcb/internal/runtime/pi_extension/fullsend-agent.js)
