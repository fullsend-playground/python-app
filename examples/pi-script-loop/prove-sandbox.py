#!/usr/bin/env python3
"""Reproduce sandbox evidence; keep raw output private and export whitelisted fields."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

if not __debug__:
    raise SystemExit("Run proof checks without Python optimization")

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = Path(__file__).resolve().parent
VERSIONS = json.loads((EXAMPLE / "versions.json").read_text())
STEPS = ("plan", "review", "summarize")


def expected_trace():
    trace = ["script_started"]
    for step in STEPS:
        trace.extend([f"call_started:{step}", f"call_completed:{step}"])
    return trace + ["script_completed"]


def collect(output_root, log_path, mode, exit_code):
    paths = list(output_root.glob("*/metrics.json"))
    assert len(paths) == 1, "Expected one sandbox result"
    metrics = json.loads(paths[0].read_text())
    output = paths[0].parent / "iteration-1/output"
    result = json.loads((output / "agent-result.json").read_text())
    log = re.sub(r"\x1b\[[0-9;]*m", "", log_path.read_text())
    assert "extensions=pi-script-loop,pi-script-guard" in log, "Guards missing"
    record = {
        "mode": mode,
        "cli_exit": exit_code,
        "runtime": metrics["runtime"],
        "iterations": metrics["iterations"],
        "reported_turns": metrics["num_turns"],
        "cost_usd": metrics["total_cost_usd"],
        "parent_inference_guard_loaded": True,
    }
    assert record["runtime"] == "pi" and record["iterations"] == 1
    if mode == "invalid":
        assert exit_code != 0 and result["status"] == "error"
        assert "Agent exit code: 1" in log and "Validation: failed" in log
        record.update(agent_exit=1, validation="failed", child_model_calls=0)
        return record
    assert exit_code == 0 and result["status"] == "ok" and result["mode"] == mode
    assert "Agent exit code: 0" in log and "Validation: passed" in log
    trace = (output / "loop-trace.txt").read_text().strip().splitlines()
    assert trace == expected_trace()
    record.update(
        agent_exit=0,
        validation="passed",
        trace=trace,
        synthetic_completion_turns=1,
        parent_model_calls=0,
    )
    calls = []
    for step in STEPS:
        text = (output / f"{step}.txt").read_text()
        assert text.strip()
        if mode == "live":
            call = json.loads((output / f"{step}-call.json").read_text())
            assert not call["isError"] and call["stopReason"] == "stop"
            assert call["model"] == "anthropic-vertex/claude-haiku-4-5"
            assert call["usage"]["input"] > 0 and call["usage"]["output"] > 0
            # Export only known numeric usage values, never arbitrary returned text.
            usage = {
                key: call["usage"][key]
                for key in ("input", "output", "cacheRead", "cacheWrite", "cost")
            }
            assert all(
                isinstance(value, (int, float)) and math.isfinite(value) and value >= 0
                for value in usage.values()
            )
            calls.append(
                {
                    "step": step,
                    "model": call["model"],
                    "usage": usage,
                    "response_chars": len(text),
                    "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                }
            )
        else:
            assert text.strip() == f"MOCK response for {step}"
    record["child_model_calls"] = len(calls)
    if calls:
        assert (
            abs(sum(call["usage"]["cost"] for call in calls) - record["cost_usd"])
            < 1e-8
        )
        record["calls"] = calls
        record["reported_requests"] = metrics["per_model_usage"][
            "anthropic-vertex/claude-haiku-4-5"
        ]["requests"]
    else:
        assert record["cost_usd"] == 0
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fullsend", required=True, help="CLI built from versions.json's source commit"
    )
    parser.add_argument("--mode", choices=("proof", "live"), default="proof")
    parser.add_argument("--env-file", action="append", default=[])
    parser.add_argument(
        "--report", type=Path, required=True, help="Sanitized evidence JSON destination"
    )
    args = parser.parse_args()
    binary = shutil.which(args.fullsend) or str(Path(args.fullsend).resolve())
    version = subprocess.check_output([binary, "--version"], text=True)
    if VERSIONS["fullsend"] not in version:
        raise SystemExit(
            "CLI does not identify the pinned source commit; use the documented build command"
        )
    private = Path(tempfile.mkdtemp(prefix="python-app-pi-proof-"))
    reports = []
    modes = ["proof", "proof", "invalid"] if args.mode == "proof" else ["live"]
    for index, mode in enumerate(modes, 1):
        # A final private env file prevents user env files from changing the test mode.
        mode_file = private / f"mode-{index}.env"
        mode_file.write_text(f"SCRIPT_LOOP_MODE={mode}\n")
        mode_file.chmod(0o600)
        output = private / f"run-{index}"
        log = private / f"run-{index}.log"
        cmd = [
            binary,
            "run",
            "pi-script-loop",
            "--fullsend-dir",
            str(ROOT / ".fullsend"),
            "--target-repo",
            str(ROOT),
            "--output-dir",
            str(output),
            "--no-post-script",
        ]
        for file in [*args.env_file, str(mode_file)]:
            cmd.extend(["--env-file", str(Path(file).resolve())])
        with log.open("w") as stream:
            log.chmod(0o600)
            run = subprocess.run(
                cmd,
                env={**os.environ, "SCRIPT_LOOP_MODE": mode},
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=1000,
            )
        try:
            reports.append(collect(output, log, mode, run.returncode))
        except Exception:
            raise SystemExit(
                f"Proof failed; inspect private logs in {private}"
            ) from None
    implementation = {}
    for folder in (ROOT / ".fullsend", EXAMPLE):
        for path in sorted(folder.rglob("*")):
            if any(
                part
                in {".fullsend-cache", "cache", "env", "explore-prefetch-input-d64642a"}
                for part in path.parts
            ):
                continue
            if path.is_file() and (
                folder != EXAMPLE
                or path.name
                in {"versions.json", "prove-sandbox.py", "prove-startup.mjs"}
            ):
                if path.suffix in {".mjs", ".sh", ".yaml", ".json", ".md"}:
                    implementation[str(path.relative_to(ROOT))] = hashlib.sha256(
                        path.read_bytes()
                    ).hexdigest()
    report = {
        "versions": VERSIONS,
        "scope": "Actual Fullsend/OpenShell sandboxes",
        "checks": reports,
        "implementation_sha256": implementation,
        "accounting": "Each successful run includes one explicitly synthetic completion adapter turn. Model request counters may count that zero-token adapter; calls lists contain only actual child inference calls.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS: {args.mode} sandbox proof; sanitized report: {args.report}")
    print(f"Private raw logs and responses: {private}")


if __name__ == "__main__":
    main()
