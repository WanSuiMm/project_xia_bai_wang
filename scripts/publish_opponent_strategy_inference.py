"""Offline allowlisted export and public-only verification for the OSI48 cutoff."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "epistemic_boundary_mimicry"
SOURCE_RUNS = {
    "original": BASE / "runs/opencode_go_20261009_opponent_strategy_inference48_01",
    "recovery": BASE / "runs/opencode_go_20261009_opponent_strategy_inference48_02",
}
PUBLIC = BASE / "published_runs/go_opponent_strategy_inference48_cutoff_20261009"
STUDY_ID = "opponent_strategy_inference48_20261009"
TOTAL = 48
MANIFEST_KEYS = {
    "schema_version", "study_id", "created_utc", "planned_provider_requests", "randomization_seed",
    "configuration_by_model", "timeout_seconds", "max_concurrency", "requests", "source_artifacts",
    "format_exception", "retry_policy", "weighting",
}
STATUS_KEYS = {
    "state", "halt_reason", "planned", "provider_requests", "response_count", "valid", "strict_valid",
    "format_exception_count", "updated_utc",
}
DISPATCH_EXTRA = {"prompt_sha256", "dispatched_utc"}
PROMPT_RECEIPT_KEYS = {"request_id", "prompt_sha256", "created_utc"}
RESPONSE_KEYS = {
    "request_id", "model", "kind", "case_id", "simulation_condition", "bluffer_condition", "judge_condition",
    "prompt_sha256", "sent_utc", "status", "visible_text", "parsed", "parse_status", "returned_model", "usage",
    "finish_reason", "http_status", "error_type", "elapsed_seconds", "captured_utc", "completion_parsed",
    "completion_parse_status", "format_acceptance",
}
RESPONSE_OPTIONAL_KEYS = {"provider_error_category"}
SOURCE_RESPONSE_OPTIONAL_KEYS = RESPONSE_OPTIONAL_KEYS | {"error_type"}
FORBIDDEN_KEYS = {
    "authorization", "api_key", "x-api-key", "headers", "session_id", "session_ids", "account_id", "pid",
    "host", "absolute_path", "provenance_private", "reasoning_content", "hidden_reasoning", "raw_provider_body",
    "raw_body", "response_body", "error_message", "launch_receipt", "stdout_path", "stderr_path", "run_path",
    "private_key", "secret", "token",
}
SCAN_PATTERNS = {
    "credential": r"oc_sk_[A-Za-z0-9_-]+|\bsk-[A-Za-z0-9_-]{20,}|\bgh[pousr]_[A-Za-z0-9_]{20,}|\bxox[baprs]-[A-Za-z0-9-]{20,}|(?i:Bearer\s+)[A-Za-z0-9._-]{16,}",
    "machine_path": r"(?i)\b[A-Z]:[\\/]|/(?:Users|home|mnt/[a-z])/?",
    "private_session_url": r"https?://(?:arena\.ai/c/|chatgpt\.com/c/)",
    "ip_address": r"(?<![\w.])(?!(?:127\.0\.0\.1|0\.0\.0\.0))(?:\d{1,3}\.){3}\d{1,3}(?![\w.])",
}
MODULES = (
    "run_strategic_qualification", "run_counterfactual_source_boundary", "run_joint_epistemic_simulation",
    "run_joint_epistemic_supplement", "run_opponent_strategy_inference", "analyze_opponent_strategy_inference",
)


class PublicationError(RuntimeError):
    """Raised when a frozen source or public projection does not verify."""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise PublicationError(message)


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value.replace(b"\r\n", b"\n")).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(value)


def write_json(path: Path, value: Any) -> None:
    write_bytes(path, json_bytes(value))


def write_text(path: Path, value: str) -> None:
    write_bytes(path, value.encode("utf-8"))


def within(root: Path, relative: str) -> Path:
    result = (root / relative).resolve()
    result.relative_to(root.resolve())
    need(result != root.resolve(), "Expected a file path, not a directory root")
    return result


def exact_keys(value: Any, expected: set[str], where: str) -> dict[str, Any]:
    need(isinstance(value, dict) and set(value) == expected, f"{where} fields differ from the frozen schema")
    return value


def _safe_scan(path: Path) -> None:
    try:
        content = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PublicationError(f"Non-UTF8 public file: {path.name}") from exc
    for label, pattern in SCAN_PATTERNS.items():
        need(not re.search(pattern, content), f"Unsafe {label} in {path.name}")
    if path.suffix == ".json":
        value = json.loads(content)

        def visit(item: Any) -> None:
            if isinstance(item, dict):
                keys = {str(key).casefold() for key in item}
                need(not (keys & FORBIDDEN_KEYS), f"Unsafe metadata field in {path.name}")
                for child in item.values():
                    visit(child)
            elif isinstance(item, list):
                for child in item:
                    visit(child)

        visit(value)


def _load_stack(run: Path) -> tuple[dict[str, Any], Any, Any, Any]:
    """Load only the code snapshot bundled inside this run/package."""
    sys.dont_write_bytecode = True
    scripts = run / "inputs/scripts"
    need(scripts.is_dir(), f"Bundled frozen scripts are missing under {run.name}")
    prior = {name: sys.modules.pop(name, None) for name in MODULES}
    sys.path.insert(0, str(scripts))
    try:
        study = importlib.import_module("run_opponent_strategy_inference")
        analyzer = importlib.import_module("analyze_opponent_strategy_inference")
        return prior, study, analyzer, study.api
    except Exception:
        _release_stack(prior, scripts)
        raise


def _release_stack(prior: dict[str, Any], scripts: Path) -> None:
    try:
        sys.path.remove(str(scripts))
    except ValueError:
        pass
    for name in MODULES:
        sys.modules.pop(name, None)
        if prior.get(name) is not None:
            sys.modules[name] = prior[name]


def _source_checks(run: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest = exact_keys(read_json(run / "manifest.json"), MANIFEST_KEYS, f"{run.name} manifest")
    freeze = read_json(run / "freeze.json")
    status = exact_keys(read_json(run / "status.json"), STATUS_KEYS, f"{run.name} status")
    need(manifest["study_id"] == STUDY_ID and manifest["planned_provider_requests"] == TOTAL,
         f"{run.name} is not the frozen 48-slot study")
    need(freeze.get("experimental_requests_at_freeze") == 0 and isinstance(freeze.get("hashes"), dict),
         f"{run.name} freeze does not prove zero calls at freeze")
    for relative, digest in freeze["hashes"].items():
        need(isinstance(relative, str) and not Path(relative).is_absolute(), "Freeze has an unsafe file path")
        path = within(run, relative)
        need(path.is_file() and sha_file(path) == digest, f"Frozen file changed: {run.name}/{relative}")
    sources = manifest["source_artifacts"]
    need(isinstance(sources, dict) and sources, "Manifest source_artifacts must be a nonempty map")
    for relative, digest in sources.items():
        need(isinstance(relative, str) and not Path(relative).is_absolute()
             and "runs/" not in relative.replace("\\", "/").casefold(),
             "source_artifacts contains an absolute or private-run path")
        snapshot = within(run / "inputs", relative)
        need(snapshot.is_file() and sha_file(snapshot) == digest,
             f"Source snapshot hash mismatch: {run.name}/{relative}")
    need(status["planned"] == TOTAL, f"{run.name} status planned count changed")
    need((run / "analysis/summary.json").is_file(), f"{run.name} registered summary is missing")
    return manifest, freeze, status


def _copy_freeze(run: Path, target: Path, freeze: dict[str, Any]) -> None:
    for relative, digest in freeze["hashes"].items():
        source = within(run, relative)
        destination = within(target, relative)
        need(sha_file(source) == digest, f"Source changed during copy: {relative}")
        write_bytes(destination, source.read_bytes())
        need(sha_file(destination) == digest, f"Published frozen file hash mismatch: {relative}")


def _safe_response(source: Path, row: dict[str, Any], study: Any) -> dict[str, Any]:
    raw = read_json(source)
    source_required = RESPONSE_KEYS - SOURCE_RESPONSE_OPTIONAL_KEYS
    need(set(raw) <= RESPONSE_KEYS | RESPONSE_OPTIONAL_KEYS and source_required <= set(raw),
         f"Response fields fall outside the frozen schema in {source.name}")
    for key in ("request_id", "model", "kind", "case_id", "simulation_condition", "bluffer_condition", "judge_condition"):
        need(raw.get(key) == row[key], f"Response schedule binding differs for {source.stem}/{key}")
    need(raw.get("prompt_sha256") == sha_file(source.parents[1] / row["prompt_path"]),
         f"Response prompt binding differs for {source.stem}")
    visible = raw.get("visible_text")
    need(isinstance(visible, str), f"Final visible text is absent in {source.name}")
    if raw["status"] == "response_received" and raw.get("returned_model") == row["model"]:
        parsed, parse_status = study.api.parse_response(visible, raw.get("finish_reason"))
        completion, completion_status, acceptance = study.formatting.parse_completion(
            visible, raw.get("finish_reason"))
        need((raw.get("parsed"), raw.get("parse_status")) == (parsed, parse_status),
             f"Strict parse fields do not reproduce in {source.name}")
        need((raw.get("completion_parsed"), raw.get("completion_parse_status"), raw.get("format_acceptance"))
             == (completion, completion_status, acceptance), f"Completion parse fields do not reproduce in {source.name}")
    else:
        need(raw.get("parse_status") == "not_received" and raw.get("completion_parse_status") == "not_received",
             f"Non-response parse status is inconsistent in {source.name}")
        parsed, completion, parse_status, completion_status, acceptance = None, None, "not_received", "not_received", None
    usage = raw.get("usage", {})
    need(usage is None or isinstance(usage, dict), f"Usage field is not an object in {source.name}")
    if usage is None:
        usage = {}
    safe_usage = {key: value for key, value in usage.items()
                  if isinstance(value, (int, float)) and not isinstance(value, bool)}
    need(set(safe_usage) == set(usage), f"Non-numeric usage field in {source.name}")
    result = {key: raw[key] for key in (
        "request_id", "model", "kind", "case_id", "simulation_condition", "bluffer_condition", "judge_condition",
        "prompt_sha256", "sent_utc", "status")}
    result.update(visible_text=visible, parsed=parsed, parse_status=parse_status,
                  returned_model=raw.get("returned_model"), usage=safe_usage,
                  finish_reason=raw.get("finish_reason"), http_status=raw.get("http_status"),
                  error_type=raw.get("error_type"), elapsed_seconds=raw.get("elapsed_seconds"),
                  captured_utc=raw.get("captured_utc"), completion_parsed=completion,
                  completion_parse_status=completion_status, format_acceptance=acceptance)
    if "provider_error_category" in raw:
        result["provider_error_category"] = raw["provider_error_category"]
    return result


def _copy_attempts(run: Path, target: Path, manifest: dict[str, Any], study: Any,
                   label: str) -> dict[str, Any]:
    rows = {row["request_id"]: row for row in manifest["requests"]}
    expected_dispatch = set(manifest["requests"][0]) | DISPATCH_EXTRA
    receipt_sets: dict[str, set[str]] = {}
    hashes: dict[str, dict[str, dict[str, str]]] = {name: {"source": {}, "published": {}}
                                                   for name in ("responses", "dispatches", "prompt_receipts")}
    for folder in hashes:
        paths = sorted((run / folder).glob("*.json"))
        receipt_sets[folder] = {path.stem for path in paths}
        for path in paths:
            rid = path.stem
            need(rid in rows, f"{label}/{folder} has an unscheduled request")
            if folder == "responses":
                projection = _safe_response(path, rows[rid], study)
                destination = target / folder / path.name
                write_json(destination, projection)
            else:
                item = read_json(path)
                expected = expected_dispatch if folder == "dispatches" else PROMPT_RECEIPT_KEYS
                exact_keys(item, expected, f"{label}/{folder}/{rid}")
                if folder == "dispatches":
                    prompt_sha = sha_file(within(run, rows[rid]["prompt_path"]))
                    need(item == rows[rid] | {"prompt_sha256": prompt_sha,
                                               "dispatched_utc": item["dispatched_utc"]},
                         f"{label}/{rid} dispatch does not bind to its schedule")
                else:
                    need(item["request_id"] == rid and item["prompt_sha256"] ==
                         sha_file(within(run, rows[rid]["prompt_path"])),
                         f"{label}/{rid} prompt receipt does not bind to its prompt")
                destination = target / folder / path.name
                write_bytes(destination, path.read_bytes())
            hashes[folder]["source"][rid] = sha_file(path)
            hashes[folder]["published"][rid] = sha_file(destination)
    need(receipt_sets["responses"] == receipt_sets["dispatches"] == receipt_sets["prompt_receipts"],
         f"{label} response, dispatch, and prompt-receipt sets differ")
    return {"sets": {name: sorted(ids) for name, ids in receipt_sets.items()}, "hashes": hashes}


def _copy_run(run: Path, stage: Path, label: str) -> dict[str, Any]:
    manifest, freeze, status = _source_checks(run)
    dest = stage / label
    _copy_freeze(run, dest, freeze)
    write_bytes(dest / "freeze.json", (run / "freeze.json").read_bytes())
    write_bytes(dest / "status.json", (run / "status.json").read_bytes())
    write_bytes(dest / "analysis/summary.json", (run / "analysis/summary.json").read_bytes())
    prior, study, analyzer, _ = _load_stack(run)
    try:
        calculated = analyzer.analyze(run, write=False)
        registered = read_json(run / "analysis/summary.json")
        need(_comparison_summary(calculated) == _comparison_summary(registered),
             f"{label} source summary does not reproduce from its frozen files")
        attempts = _copy_attempts(run, dest, manifest, study, label)
    finally:
        _release_stack(prior, run / "inputs/scripts")
    return {"manifest": manifest, "freeze": freeze, "status": status,
            "summary": read_json(run / "analysis/summary.json"), "attempts": attempts}


def _comparison_summary(summary: dict[str, Any]) -> dict[str, Any]:
    result = dict(summary)
    result.pop("analysis_utc", None)
    return result


def _attempt_ledger(source: dict[str, dict[str, Any]], stage: Path,
                    receipt_hashes: dict[str, Any] | None = None) -> dict[str, Any]:
    attempts = []
    seen: set[str] = set()
    for label in ("original", "recovery"):
        manifest = source[label]["manifest"]
        for row in sorted(manifest["requests"], key=lambda item: item["schedule_index"]):
            rid = row["request_id"]
            response_path = stage / label / "responses" / f"{rid}.json"
            if not response_path.exists():
                continue
            rec = read_json(response_path)
            hash_data = source[label]["attempts"].get("hashes")
            if hash_data is None:
                need(receipt_hashes is not None and label in receipt_hashes,
                     f"{label} source receipt hash provenance is missing")
                hash_data = receipt_hashes[label]
            attempts.append({
                "batch": label, "request_id": rid, "schedule_index": row["schedule_index"],
                "attempt_number_for_slot": 1 + int(rid in seen), "is_repeated_slot": rid in seen,
                "status": rec["status"], "strict_parse_status": rec["parse_status"],
                "completion_parse_status": rec["completion_parse_status"], "http_status": rec["http_status"],
                "error_type": rec["error_type"], "provider_error_category": rec.get("provider_error_category"),
                "prompt_sha256": rec["prompt_sha256"],
                "receipt_path": f"{label}/responses/{rid}.json",
                "dispatch_path": f"{label}/dispatches/{rid}.json",
                "prompt_receipt_path": f"{label}/prompt_receipts/{rid}.json",
                "source_receipt_sha256_lf": hash_data["responses"]["source"][rid],
                "published_receipt_sha256_lf": hash_data["responses"]["published"][rid],
            })
            seen.add(rid)
    return {"schema_version": 1, "study_id": STUDY_ID, "attempts": attempts}


def _publication(source: dict[str, dict[str, Any]], package: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": 1, "study_id": STUDY_ID,
        "source_run_ids": {label: SOURCE_RUNS[label].name for label in source},
        "source_manifest_sha256_lf": {}, "published_manifest_sha256_lf": {},
        "source_freeze_sha256_lf": {}, "published_freeze_sha256_lf": {},
        "source_schedule_sha256_lf": {}, "published_schedule_sha256_lf": {},
        "configuration_sha256_lf": {}, "source_summary_sha256_lf": {},
        "source_artifacts": {}, "prompt_sha256_lf": {},
        "receipt_sha256_lf": {}, "visible_text_sha256_utf8": {},
    }
    for label, row in source.items():
        source_run, target = SOURCE_RUNS[label], package / label
        result["source_manifest_sha256_lf"][label] = sha_file(source_run / "manifest.json")
        result["published_manifest_sha256_lf"][label] = sha_file(target / "manifest.json")
        result["source_freeze_sha256_lf"][label] = sha_file(source_run / "freeze.json")
        result["published_freeze_sha256_lf"][label] = sha_file(target / "freeze.json")
        result["source_schedule_sha256_lf"][label] = sha_file(source_run / "schedule.json")
        result["published_schedule_sha256_lf"][label] = sha_file(target / "schedule.json")
        result["configuration_sha256_lf"][label] = sha_bytes(json_bytes(row["manifest"]["configuration_by_model"]))
        result["source_summary_sha256_lf"][label] = sha_file(source_run / "analysis/summary.json")
        result["source_artifacts"][label] = {
            "digests": row["manifest"]["source_artifacts"],
            "snapshot_paths": {key: f"{label}/inputs/{key}" for key in row["manifest"]["source_artifacts"]},
        }
        result["prompt_sha256_lf"][label] = {
            row_req["request_id"]: {
                "source": sha_file(within(source_run, row_req["prompt_path"])),
                "published": sha_file(within(target, row_req["prompt_path"])),
            }
            for row_req in row["manifest"]["requests"]
        }
        result["receipt_sha256_lf"][label] = row["attempts"]["hashes"]
        result["visible_text_sha256_utf8"][label] = {
            rid: sha_text(read_json(package / label / "responses" / f"{rid}.json")["visible_text"])
            for rid in row["attempts"]["sets"]["responses"]
        }
    return result


def _report(source: dict[str, dict[str, Any]], ledger: dict[str, Any], file_count: int) -> dict[str, Any]:
    original, recovery = (source[label]["summary"] for label in ("original", "recovery"))
    attempted = {attempt["request_id"] for attempt in ledger["attempts"]}
    schedule = {row["request_id"] for row in source["original"]["manifest"]["requests"]}
    cells = original["cells"] + recovery["cells"]
    return {
        "verification": "PASS", "study_id": STUDY_ID, "fixed_slots": TOTAL,
        "batches": {
            "original": {key: original[key] for key in
                         ("completion", "planned", "provider_requests", "responses_received", "valid", "strict_valid", "invalid", "missing")},
            "recovery": {key: recovery[key] for key in
                          ("completion", "planned", "provider_requests", "responses_received", "valid", "strict_valid", "invalid", "missing")},
        },
        "physical_attempts": len(ledger["attempts"]), "unique_slots_attempted": len(attempted),
        "unique_slots_never_attempted": len(schedule - attempted),
        "valid_recovery_responses": recovery["valid"], "complete_cells": sum(cell["complete"] for cell in cells),
        "aggregate_oracle_contrasts": None, "frozen_calls": {label: source[label]["freeze"]["experimental_requests_at_freeze"]
                                                               for label in source},
        "public_file_count": file_count,
    }


def _results_text(report: dict[str, Any], ledger: dict[str, Any]) -> str:
    original = report["batches"]["original"]
    recovery = report["batches"]["recovery"]
    return (
        "# OSI48 cutoff results\n\n"
        "The original batch stopped after one HTTP 403 response classified as a payment error. "
        "The separate recovery batch stopped after three attempts: two strict-valid Qwen responses and one "
        "invalid GLM provider response (HTTP 200, `ValueError`). The original failure remains in its own batch.\n\n"
        "| Batch | Planned | Attempts | Receipts | Valid | Invalid | Missing |\n"
        "|---|---:|---:|---:|---:|---:|---:|\n"
        f"| Original | {original['planned']} | {original['provider_requests']} | {original['responses_received']} | "
        f"{original['valid']} | {original['invalid']} | {original['missing']} |\n"
        f"| Recovery | {recovery['planned']} | {recovery['provider_requests']} | {recovery['responses_received']} | "
        f"{recovery['valid']} | {recovery['invalid']} | {recovery['missing']} |\n\n"
        f"Across both batches there were **{report['physical_attempts']} physical attempts** over "
        f"**{report['unique_slots_attempted']} unique slots**. The first recovery call repeated the original failed "
        f"slot; **{report['unique_slots_never_attempted']} of 48 slots were never attempted**. The two valid replies "
        "are both Qwen responses. No complete model-by-condition cell exists, so registered cell endpoints and "
        "aggregate oracle contrasts are undefined. Per-slot exact oracle values remain in each frozen schedule.\n\n"
        "This is an incomplete cutoff record, not a scientific all-or-nothing verdict. The offline analyzer keeps "
        "missing slots unweighted and returns null for incomplete cell aggregates. No paid calls or retries are made "
        "by export or verification. See [the attempt ledger](../attempt_ledger.json) and each batch's "
        "[registered summary](../original/analysis/summary.json) and [recovery summary](../recovery/analysis/summary.json).\n"
    )


def _readme_text() -> str:
    return (
        "# Opponent Strategy Inference OSI48 cutoff evidence\n\n"
        "This public package preserves the two frozen 48-slot batches, exact prompts, schedules and per-slot oracle "
        "values, source snapshots, dispatch and prompt receipts, and safe final-visible response fields. Provider raw "
        "bodies, private launch records, credentials, and hidden reasoning are not part of the response projection.\n\n"
        "Start with [cutoff results](analysis/RESULTS.md), then inspect the [attempt ledger](attempt_ledger.json) and "
        "the [original summary](original/analysis/summary.json) and [recovery summary](recovery/analysis/summary.json). "
        "The frozen source code and protocol inputs are under each batch's `inputs/` directory.\n\n"
        "The original run contains one HTTP 403/payment failure. The recovery run contains three receipts: two strict-valid "
        "Qwen responses and one invalid GLM provider response with HTTP 200 and `ValueError`. Across both batches there "
        "were four physical attempts, including one repeated slot, and 45 of 48 unique slots were never attempted. No "
        "complete cell or aggregate oracle contrast is available.\n\n"
        "Run `python -X utf8 -B scripts/publish_opponent_strategy_inference.py --verify` from the project root. "
        "Verification uses only the published package's frozen parser, analyzer, and inputs; it makes no provider request.\n"
    )


def _expected_files(package: Path, ledger: dict[str, Any]) -> set[str]:
    expected = {
        "README.md", "publication.json", "attempt_ledger.json", "analysis/RESULTS.md",
        "analysis/public_verification.json",
    }
    for label in ("original", "recovery"):
        freeze = read_json(package / f"{label}/freeze.json")
        expected |= {f"{label}/{relative}" for relative in freeze["hashes"]}
        expected |= {f"{label}/{path}" for path in ("freeze.json", "status.json", "analysis/summary.json")}
        for attempt in ledger["attempts"]:
            if attempt["batch"] == label:
                expected |= {attempt[key] for key in ("receipt_path", "dispatch_path", "prompt_receipt_path")}
    return expected


def _verify_run(package: Path, label: str) -> dict[str, Any]:
    run = package / label
    manifest, freeze, status = _source_checks(run)
    need(len(manifest["requests"]) == TOTAL and manifest["requests"] == read_json(run / "schedule.json"),
         f"{label} manifest and schedule differ")
    prior, study, analyzer, _ = _load_stack(run)
    try:
        need(manifest["requests"] == study.schedule(), f"{label} schedule/oracle reconstruction differs")
        need(manifest["configuration_by_model"] == study.api.configurations(),
             f"{label} API configuration differs from frozen configuration code")
        need(manifest["weighting"] == "equal selected stimulus, separately by model/coupling; not population weighting",
             f"{label} weighting rule changed")
        summary = analyzer.analyze(run, write=False)
        saved = read_json(run / "analysis/summary.json")
        need(_comparison_summary(summary) == _comparison_summary(saved),
             f"{label} public analyzer summary does not reproduce")
        need(summary["completion"] == "INCOMPLETE" and summary["unreceived_dispatches"] == 0,
             f"{label} cutoff state does not reproduce")
        need(all(not cell["complete"] and cell["posterior_mse"] is None and cell["history_delta"] is None
                 for cell in summary["cells"]), f"{label} has an unexpected complete scientific cell")
        need(all(not contrast["complete"] and contrast["interaction"] is None
                 and contrast["interaction_absolute_error"] is None for contrast in summary["contrasts"]),
             f"{label} has an unexpected aggregate oracle contrast")
        return {"manifest": manifest, "freeze": freeze, "status": status, "summary": saved,
                "attempts": _audit_package_attempts(run, manifest, study)}
    finally:
        _release_stack(prior, run / "inputs/scripts")


def _audit_package_attempts(run: Path, manifest: dict[str, Any], study: Any) -> dict[str, Any]:
    rows = {row["request_id"]: row for row in manifest["requests"]}
    sets: dict[str, set[str]] = {}
    for folder in ("responses", "dispatches", "prompt_receipts"):
        sets[folder] = {p.stem for p in (run / folder).glob("*.json")}
    need(sets["responses"] == sets["dispatches"] == sets["prompt_receipts"],
         f"{run.name} receipt sets do not match")
    for rid in sets["responses"]:
        _safe_scan(run / "responses" / f"{rid}.json")
        rec = read_json(run / "responses" / f"{rid}.json")
        need(set(rec) in (RESPONSE_KEYS, RESPONSE_KEYS | RESPONSE_OPTIONAL_KEYS),
             f"{run.name}/{rid} public response has an unexpected field set")
        projected = _safe_response(run / "responses" / f"{rid}.json", rows[rid], study)
        need(projected == rec, f"{run.name}/{rid} response projection is not stable")
    return {folder: sets[folder] for folder in sets}


def _verify_public(package: Path) -> dict[str, Any]:
    package = package.resolve()
    need(package.is_dir(), "Public OSI48 package is missing")
    freeze = read_json(package / "freeze.json")
    need(freeze.get("hash_convention") == "SHA256 with CRLF normalized to LF"
         and isinstance(freeze.get("hashes"), dict), "Unexpected package hash convention")
    for relative, digest in freeze["hashes"].items():
        path = within(package, relative)
        need(path.is_file() and sha_file(path) == digest, f"Public file hash mismatch: {relative}")
        _safe_scan(path)
    _safe_scan(package / "freeze.json")
    ledger = read_json(package / "attempt_ledger.json")
    need(ledger.get("study_id") == STUDY_ID and isinstance(ledger.get("attempts"), list),
         "Attempt ledger has an unexpected schema")
    expected = _expected_files(package, ledger) | {"freeze.json"}
    actual = {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()}
    need(actual == expected, f"Public file allowlist differs: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
    need(set(freeze["hashes"]) == expected - {"freeze.json"}, "Public freeze hash allowlist is incomplete")
    need((package / "README.md").read_text(encoding="utf-8") == _readme_text(), "Public README does not reproduce")

    source = {label: _verify_run(package, label) for label in ("original", "recovery")}
    publication = read_json(package / "publication.json")
    need(publication["study_id"] == STUDY_ID
         and publication["source_run_ids"] == {label: SOURCE_RUNS[label].name for label in source},
         "Publication study identity or source run identities differ")
    need(source["original"]["manifest"]["requests"] == source["recovery"]["manifest"]["requests"],
         "Recovery schedule differs from the original frozen schedule")
    need(source["original"]["status"]["provider_requests"] == 1
         and source["original"]["status"]["response_count"] == 1
         and source["original"]["status"]["halt_reason"] == "http_error",
         "Original cutoff does not preserve its single HTTP failure")
    need(source["recovery"]["status"]["provider_requests"] == 3
         and source["recovery"]["status"]["response_count"] == 3
         and source["recovery"]["status"]["halt_reason"] == "invalid_provider_response",
         "Recovery cutoff does not preserve its three attempts")
    original = source["original"]["summary"]
    recovery = source["recovery"]["summary"]
    need(original["valid"] == 0 and original["invalid"] == 1 and original["missing"] == 47,
         "Original analysis counts differ from the one-error cutoff")
    need(recovery["valid"] == 2 and recovery["strict_valid"] == 2 and recovery["invalid"] == 1
         and recovery["missing"] == 45, "Recovery analysis counts differ from the 3-attempt cutoff")

    original_ids = source["original"]["attempts"]["responses"]
    recovery_ids = source["recovery"]["attempts"]["responses"]
    need(len(original_ids) == 1 and len(recovery_ids) == 3 and original_ids <= recovery_ids,
         "Physical attempt sets do not preserve one original plus a three-attempt recovery")
    original_id = next(iter(original_ids))
    first = read_json(package / "original/responses" / f"{original_id}.json")
    need(first["status"] == "http_error" and first["http_status"] == 403
         and first.get("provider_error_category") == "payment",
         "Original HTTP 403/payment receipt is not preserved")
    recovery_receipts = [read_json(package / "recovery/responses" / f"{rid}.json") for rid in recovery_ids]
    invalid = [rec for rec in recovery_receipts if rec["status"] == "invalid_provider_response"]
    valid = [rec for rec in recovery_receipts if rec["status"] == "response_received"]
    need(len(invalid) == 1 and invalid[0]["model"] == "glm-5.3" and invalid[0]["http_status"] == 200
         and invalid[0]["error_type"] == "ValueError", "Recovery GLM provider failure is not preserved")
    need(len(valid) == 2 and all(rec["model"] == rec["returned_model"] == "qwen3.8-max"
                                 and rec["parse_status"] == "valid" for rec in valid),
         "Recovery does not preserve the two strict-valid Qwen replies")

    expected_ledger = _attempt_ledger(source, package, publication.get("receipt_sha256_lf"))
    need(ledger == expected_ledger, "Public attempt ledger does not reproduce")
    report = _report(source, ledger, len(actual))
    need(report["physical_attempts"] == 4 and report["unique_slots_attempted"] == 3
         and report["unique_slots_never_attempted"] == 45 and report["complete_cells"] == 0
         and report["aggregate_oracle_contrasts"] is None,
         "Cutoff summary differs from frozen attempt records")
    for label in ("original", "recovery"):
        for filename, source_hash_key, published_hash_key in (
            ("manifest.json", "source_manifest_sha256_lf", "published_manifest_sha256_lf"),
            ("freeze.json", "source_freeze_sha256_lf", "published_freeze_sha256_lf"),
            ("schedule.json", "source_schedule_sha256_lf", "published_schedule_sha256_lf"),
        ):
            digest = sha_file(package / label / filename)
            need(publication[source_hash_key][label] == publication[published_hash_key][label] == digest,
                 f"{label} {filename} provenance differs")
        need(publication["source_summary_sha256_lf"][label] == sha_file(package / label / "analysis/summary.json"),
             f"{label} source summary provenance differs")
        manifest = source[label]["manifest"]
        need(publication["configuration_sha256_lf"][label] ==
             sha_bytes(json_bytes(manifest["configuration_by_model"])),
             f"{label} configuration hash differs")
        artifact_record = publication["source_artifacts"][label]
        need(artifact_record["digests"] == manifest["source_artifacts"]
             and artifact_record["snapshot_paths"] == {
                 key: f"{label}/inputs/{key}" for key in manifest["source_artifacts"]},
             f"{label} source artifact snapshot map differs")
        expected_prompts = {
            row["request_id"]: {
                "source": sha_file(package / label / row["prompt_path"]),
                "published": sha_file(package / label / row["prompt_path"]),
            }
            for row in manifest["requests"]
        }
        need(publication["prompt_sha256_lf"][label] == expected_prompts,
             f"{label} exact prompt hash bindings differ")
        published_hashes = publication["receipt_sha256_lf"][label]
        for folder in ("responses", "dispatches", "prompt_receipts"):
            ids = source[label]["attempts"][folder]
            hash_pair = published_hashes[folder]
            need(set(hash_pair["source"]) == ids and set(hash_pair["published"]) == ids,
                 f"{label} {folder} source/published hash sets differ")
            need(all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in hash_pair["source"].values()),
                 f"{label} {folder} contains an invalid source receipt hash")
            actual_published = {
                rid: sha_file(package / label / folder / f"{rid}.json") for rid in ids
            }
            need(hash_pair["published"] == actual_published,
                 f"{label} {folder} published hash bindings differ")
        visible = {rid: sha_text(read_json(package / label / "responses" / f"{rid}.json")["visible_text"])
                   for rid in source[label]["attempts"]["responses"]}
        need(publication["visible_text_sha256_utf8"][label] == visible,
             f"{label} final-visible text hashes differ")
    need(read_json(package / "analysis/public_verification.json") == report,
         "Public verification report does not reproduce")
    need((package / "analysis/RESULTS.md").read_text(encoding="utf-8") == _results_text(report, ledger),
         "Public results text does not reproduce")
    return report


def export() -> dict[str, Any]:
    need(not PUBLIC.exists(), "Public OSI48 package already exists; export is write-once")
    need(all(path.is_dir() for path in SOURCE_RUNS.values()), "Frozen OSI48 source runs are unavailable")
    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="osi48_export_", dir=PUBLIC.parent) as temp:
        stage = Path(temp) / PUBLIC.name
        stage.mkdir()
        source = {label: _copy_run(path, stage, label) for label, path in SOURCE_RUNS.items()}
        ledger = _attempt_ledger(source, stage)
        write_json(stage / "attempt_ledger.json", ledger)
        write_json(stage / "publication.json", _publication(source, stage))
        write_text(stage / "README.md", _readme_text())
        # Include the two report files and the package freeze that follow.
        file_count = sum(1 for path in stage.rglob("*") if path.is_file()) + 3
        report = _report(source, ledger, file_count)
        write_text(stage / "analysis/RESULTS.md", _results_text(report, ledger))
        write_json(stage / "analysis/public_verification.json", report)
        hashes = {path.relative_to(stage).as_posix(): sha_file(path)
                  for path in sorted(stage.rglob("*")) if path.is_file()}
        write_json(stage / "freeze.json", {
            "hash_convention": "SHA256 with CRLF normalized to LF", "hashes": hashes,
        })
        need(not PUBLIC.exists(), "Public OSI48 package appeared during export; refusing replacement")
        stage.rename(PUBLIC)
    return _verify_public(PUBLIC)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--export", action="store_true", help="Create the public projection once from frozen local runs")
    modes.add_argument("--verify", action="store_true", help="Verify the published package without private inputs (default)")
    args = parser.parse_args()
    try:
        report = export() if args.export else _verify_public(PUBLIC)
    except (AssertionError, OSError, ValueError, KeyError, TypeError, PublicationError) as exc:
        parser.exit(1, f"publication error: {exc}\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
