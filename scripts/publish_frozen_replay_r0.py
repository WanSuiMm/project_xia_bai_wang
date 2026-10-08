#!/usr/bin/env python3
"""Export or audit the sanitized public R0 Frozen replay snapshot.

The default command audits the existing public directory using only local
files.  ``--export`` creates that directory once from the frozen private run
receipts; it refuses to replace an existing export.  This script has no
provider client, network, or environment-variable reads.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = REPO_ROOT / "epistemic_boundary_mimicry" / "runs"
PUBLIC_PARENT = REPO_ROOT / "epistemic_boundary_mimicry" / "published_runs"
PUBLIC_DIR = PUBLIC_PARENT / "go_frozen_replay_r0_20261008"
PRIMARY_SOURCE = RUNS_ROOT / "opencode_go_20261007_frozen_replay_r0_84_02"
INITIAL_SOURCE = RUNS_ROOT / "opencode_go_20261007_frozen_replay_r0_84_01"
SUPPLEMENT_SOURCES = (
    ("supplement07", RUNS_ROOT / "opencode_go_20261007_frozen_replay_r0_supplement07_01"),
    ("supplement06", RUNS_ROOT / "opencode_go_20261007_frozen_replay_r0_supplement06_01"),
)
PUBLIC_SNAPSHOT_DATE = "2026-10-08"
PLANNED_PRIMARY = 84
EXPECTED_PROMPTS = 14
REPETITIONS = 3

PRIMARY_RECEIPT_FIELDS = frozenset(
    {
        "request_id",
        "transcript_id",
        "model",
        "condition",
        "replicate",
        "pair_id",
        "slot_order",
        "prompt_sha256",
        "status",
        "parse_status",
        "error_type",
        "http_status",
        "sent_utc",
        "captured_utc",
        "returned_model",
        "finish_reason",
        "usage",
        "elapsed_seconds",
        "visible_text",
        "parsed",
        "source_request_id",
        "failure_selected_supplement",
        "continuation_after_preserved_429",
        "refusal",
        "refusal_reason",
        "tool_calls",
        "tool_call",
        "tools_used",
        "tool_used",
        "tool_use",
    }
)
REQUIRED_RECEIPT_FIELDS = frozenset(
    {
        "request_id",
        "transcript_id",
        "model",
        "condition",
        "replicate",
        "prompt_sha256",
        "status",
        "parse_status",
        "returned_model",
        "finish_reason",
        "usage",
        "elapsed_seconds",
        "visible_text",
        "parsed",
    }
)
EXCLUDED_RECEIPT_FIELDS = frozenset(
    {
        "raw_response_path",
        "session_id_private",
        "headers",
        "request_headers",
        "response_headers",
        "host",
        "hostname",
        "pid",
        "process_id",
        "account_url",
        "private_account_url",
        "api_key",
        "api_token",
        "authorization",
        "credential",
        "credentials",
        "private_key",
    }
)
FORBIDDEN_PUBLIC_KEYS = frozenset(
    {
        "raw_response_path",
        "session_id_private",
        "headers",
        "request_headers",
        "response_headers",
        "host",
        "hostname",
        "pid",
        "process_id",
        "account_url",
        "private_account_url",
        "api_key",
        "api_token",
        "authorization",
        "credential",
        "credentials",
        "private_key",
    }
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class PublicationError(Exception):
    """Raised when an export or offline audit finds inconsistent evidence."""


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise PublicationError(message)


def _sha256_bytes(data: bytes) -> str:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        normalized = data
    else:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PublicationError(f"cannot read {label}: {type(exc).__name__}") from None


def _write_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _write_json_lf(path: Path, value: Any) -> None:
    _write_lf(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def _load_analyzer() -> Any:
    scripts = str(REPO_ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        import analyze_frozen_replay_r0  # type: ignore[import-not-found]
    except Exception as exc:
        raise PublicationError(f"cannot load the local replay analyzer: {type(exc).__name__}") from None
    return analyze_frozen_replay_r0


def _safe_relpath(value: Any, label: str) -> PurePosixPath:
    _need(isinstance(value, str) and value.strip(), f"{label} must be a relative path")
    normalized = value.replace("\\", "/")
    p = PurePosixPath(normalized)
    _need(not p.is_absolute() and ".." not in p.parts, f"{label} must stay inside the run directory")
    _need(not re.match(r"^[A-Za-z]:", normalized), f"{label} must not be a machine path")
    return p


def _assert_no_private_keys(value: Any, label: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str):
                normalized = key.strip().lower()
                _need(normalized not in FORBIDDEN_PUBLIC_KEYS, f"private field found in {label}")
            _assert_no_private_keys(child, label)
    elif isinstance(value, list):
        for child in value:
            _assert_no_private_keys(child, label)


def _assert_no_private_endpoint(value: Any) -> None:
    if not isinstance(value, dict):
        return
    endpoint = value.get("endpoint_base")
    if endpoint is None:
        return
    _need(isinstance(endpoint, str), "manifest endpoint_base has an invalid type")
    parsed = urlsplit(endpoint)
    _need(not parsed.username and not parsed.password, "manifest endpoint_base contains user information")
    _need(not parsed.query and not parsed.fragment, "manifest endpoint_base contains private URL components")
    path_lower = parsed.path.lower()
    _need(not any(part in path_lower for part in ("/account/", "/session/", "/workspace/")),
          "manifest endpoint_base looks account-specific")


def _freeze_hashes(run_dir: Path, freeze: dict[str, Any], label: str) -> dict[str, str]:
    hashes = freeze.get("hashes")
    _need(isinstance(hashes, dict), f"{label} freeze hashes are missing")
    copied: dict[str, str] = {}
    for rel, expected in hashes.items():
        p = _safe_relpath(rel, f"{label} freeze hash path")
        _need(isinstance(expected, str) and SHA256_RE.fullmatch(expected.lower()) is not None,
              f"{label} freeze hash has an invalid digest")
        actual_path = run_dir.joinpath(*p.parts)
        _need(actual_path.is_file(), f"{label} freeze input is missing")
        _need(_sha256_file(actual_path) == expected.lower(), f"{label} freeze input hash mismatch")
        copied[p.as_posix()] = expected.lower()
    return copied


def _safe_reference_hashes(freeze: dict[str, Any], label: str) -> dict[str, str]:
    refs = freeze.get("reference_hashes", {})
    _need(isinstance(refs, dict), f"{label} reference hashes are invalid")
    result: dict[str, str] = {}
    for key, digest in refs.items():
        _need(isinstance(key, str) and SAFE_ID_RE.fullmatch(key), f"{label} reference label is invalid")
        _need(isinstance(digest, str) and SHA256_RE.fullmatch(digest.lower()) is not None,
              f"{label} reference hash is invalid")
        result[key] = digest.lower()
    return dict(sorted(result.items()))


def _response_public_view(receipt: Any, label: str) -> dict[str, Any]:
    _need(isinstance(receipt, dict), f"{label} receipt must be an object")
    unknown = set(receipt) - PRIMARY_RECEIPT_FIELDS - EXCLUDED_RECEIPT_FIELDS
    _need(not unknown, f"{label} receipt has an unreviewed field")
    _need(REQUIRED_RECEIPT_FIELDS.issubset(receipt), f"{label} receipt is missing required fields")
    public = {key: receipt[key] for key in receipt if key in PRIMARY_RECEIPT_FIELDS}
    _assert_no_private_keys(public, label)
    return public


def _receipt_valid(analyzer: Any, run_dir: Path, request: dict[str, Any]) -> tuple[bool, str | None]:
    receipt_path = run_dir / "responses" / f"{request['request_id']}.json"
    observation, reason = analyzer._classify_receipt(receipt_path, request, run_dir / "dispatches")
    return observation is not None, reason


def _source_requests(manifest: dict[str, Any], label: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    requests = manifest.get("requests")
    _need(isinstance(requests, list), f"{label} request list is missing")
    by_id: dict[str, dict[str, Any]] = {}
    for request in requests:
        _need(isinstance(request, dict), f"{label} contains a non-object request")
        request_id = request.get("request_id")
        _need(isinstance(request_id, str) and SAFE_ID_RE.fullmatch(request_id), f"{label} has an unsafe request id")
        _need(request_id not in by_id, f"{label} contains a duplicate request id")
        by_id[request_id] = request
    return requests, by_id


def _dispatch_rows(run_dir: Path, requests_by_id: dict[str, dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    dispatch_dir = run_dir / "dispatches"
    _need(dispatch_dir.is_dir(), f"{label} dispatch directory is missing")
    rows: dict[str, dict[str, Any]] = {}
    files = sorted(path for path in dispatch_dir.glob("*.json") if path.is_file())
    for path in files:
        dispatch = _read_json(path, f"{label} dispatch receipt")
        _need(isinstance(dispatch, dict), f"{label} dispatch receipt must be an object")
        request_id = dispatch.get("request_id")
        _need(isinstance(request_id, str) and request_id in requests_by_id, f"{label} dispatch has an unknown request")
        _need(request_id not in rows, f"{label} contains a duplicate dispatch")
        request = requests_by_id[request_id]
        _need(dispatch.get("prompt_sha256") == request.get("prompt_sha256"), f"{label} dispatch prompt hash mismatch")
        safe = {key: dispatch[key] for key in ("request_id", "source_request_id", "prompt_sha256", "dispatched_utc") if key in dispatch}
        _need(set(safe) == {"request_id", "prompt_sha256", "dispatched_utc"} or set(safe) == {
            "request_id", "source_request_id", "prompt_sha256", "dispatched_utc"
        }, f"{label} dispatch receipt is incomplete")
        _assert_no_private_keys(safe, f"{label} dispatch receipt")
        rows[request_id] = safe
    return rows


def _prompt_inventory(run_dir: Path, manifest: dict[str, Any], label: str) -> tuple[list[Path], dict[str, str]]:
    prompt_root = run_dir / "prompts"
    files = sorted(path for path in prompt_root.rglob("*") if path.is_file())
    _need(len(files) == EXPECTED_PROMPTS, f"{label} must contain exactly 14 prompt files")
    hashes: dict[str, str] = {}
    for path in files:
        rel = path.relative_to(run_dir).as_posix()
        _safe_relpath(rel, f"{label} prompt path")
        hashes[rel] = _sha256_file(path)
    requests, _ = _source_requests(manifest, label)
    for request in requests:
        rel = _safe_relpath(request.get("prompt_path"), f"{label} request prompt_path").as_posix()
        _need(rel in hashes, f"{label} request prompt is not in the 14-file prompt bundle")
        _need(hashes[rel] == request.get("prompt_sha256"), f"{label} request prompt hash mismatch")
    return files, hashes


def _load_primary_analysis(analyzer: Any) -> tuple[dict[str, Any], dict[str, Any], str]:
    manifest = _read_json(PRIMARY_SOURCE / "manifest.json", "primary frozen manifest")
    _need(isinstance(manifest, dict), "primary manifest must be an object")
    _assert_no_private_keys(manifest, "primary manifest")
    _assert_no_private_endpoint(manifest)
    requests, requests_by_id = _source_requests(manifest, "primary run")
    _need(len(requests) == PLANNED_PRIMARY, "primary manifest must contain 84 request slots")
    _need(manifest.get("planned") == PLANNED_PRIMARY, "primary manifest planned count is not 84")
    _need(manifest.get("repetitions") == REPETITIONS, "primary manifest repetition count changed")

    status = _read_json(PRIMARY_SOURCE / "status.json", "primary status")
    _need(status.get("state") == "ALL_84_ATTEMPTED", "primary source is not the fixed 84-attempt snapshot")
    _need(status.get("planned") == PLANNED_PRIMARY and status.get("provider_requests") == PLANNED_PRIMARY,
          "primary source dispatch count does not match the 84-slot freeze")

    policy = manifest.get("failure_policy", {})
    _need(isinstance(policy, dict), "primary failure policy is invalid")
    _need(policy.get("semantic_retry") is False and policy.get("transport_retry") is False,
          "primary source retry policy is not frozen to no retry")
    _need(policy.get("unknown_inflight_no_resubmit") is True,
          "primary source does not preserve the no-resubmit rule for unknown in-flight requests")

    freeze = _read_json(PRIMARY_SOURCE / "freeze.json", "primary freeze record")
    _need(isinstance(freeze, dict), "primary freeze record must be an object")
    frozen_hashes = _freeze_hashes(PRIMARY_SOURCE, freeze, "primary")
    for required in ("manifest.json", "cohort.json", "prompt_modules.json"):
        _need(required in frozen_hashes, f"primary freeze record is missing {required}")

    prompt_files, _ = _prompt_inventory(PRIMARY_SOURCE, manifest, "primary run")
    _need(len(prompt_files) == EXPECTED_PROMPTS, "primary prompt inventory changed")

    response_dir = PRIMARY_SOURCE / "responses"
    response_files = {path.name for path in response_dir.glob("*.json") if path.is_file()}
    expected_response_files = {f"{request_id}.json" for request_id in requests_by_id}
    _need(response_files == expected_response_files, "primary response receipt set does not cover exactly 84 slots")
    dispatch_rows = _dispatch_rows(PRIMARY_SOURCE, requests_by_id, "primary run")
    _need(set(dispatch_rows) == set(requests_by_id), "primary dispatch ledger does not cover 84 unique requests")

    expected_analysis = analyzer.analyze_run(PRIMARY_SOURCE)
    source_analysis = _read_json(PRIMARY_SOURCE / "analysis.json", "primary frozen analysis")
    _need(expected_analysis == source_analysis, "primary frozen analysis is stale relative to its receipts")
    return manifest, expected_analysis, _sha256_file(PRIMARY_SOURCE / "freeze.json")


def _validate_initial_run() -> dict[str, Any]:
    status = _read_json(INITIAL_SOURCE / "status.json", "initial run status")
    _need(status.get("state") == "HALTED", "initial run must remain a halted record")
    dispatch_dir = INITIAL_SOURCE / "dispatches"
    response_dir = INITIAL_SOURCE / "responses"
    dispatch_files = sorted(p for p in dispatch_dir.glob("*.json") if p.is_file())
    response_files = sorted(p for p in response_dir.glob("*.json") if p.is_file())
    _need(len(dispatch_files) == 2 and len(response_files) == 2, "initial run must have exactly two recorded attempts")
    http_statuses: Counter[str] = Counter()
    model_answers = 0
    for path in response_files:
        receipt = _read_json(path, "initial run response receipt")
        _need(isinstance(receipt, dict), "initial run receipt must be an object")
        status_code = receipt.get("http_status")
        http_statuses[str(status_code)] += 1
        if (
            receipt.get("status") == "response_received"
            and receipt.get("parse_status") == "valid"
            and isinstance(receipt.get("returned_model"), str)
            and bool(receipt.get("visible_text"))
        ):
            model_answers += 1
    _need(http_statuses == Counter({"403": 2}), "initial run no longer matches the two-403 recovery record")
    _need(model_answers == 0, "initial run contains a model answer")
    return {
        "label": "initial run 01",
        "state": status.get("state"),
        "planned_slots": status.get("planned"),
        "dispatch_attempts": len(dispatch_files),
        "response_receipts": len(response_files),
        "http_status_counts": dict(sorted(http_statuses.items())),
        "valid_model_answers": model_answers,
        "remaining_slots": "not dispatched after HTTP 403",
        "source_manifest_sha256": _sha256_file(INITIAL_SOURCE / "manifest.json"),
        "source_freeze_sha256": _sha256_file(INITIAL_SOURCE / "freeze.json")
        if (INITIAL_SOURCE / "freeze.json").is_file()
        else None,
    }


def _supplement_request_view(request: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "request_id",
        "source_request_id",
        "model",
        "transcript_id",
        "condition",
        "replicate",
        "pair_id",
        "slot_order",
        "prompt_sha256",
        "wave",
    )
    public = {key: request[key] for key in fields if key in request}
    original_failure = request.get("original_failure")
    if isinstance(original_failure, dict):
        public["original_failure"] = {
            key: original_failure[key]
            for key in ("status", "parse_status", "finish_reason", "error_type")
            if key in original_failure
        }
    _need("request_id" in public and "source_request_id" in public, "supplement request lacks original-source mapping")
    _assert_no_private_keys(public, "supplement request")
    return public


def _supplement_status(analyzer: Any, primary_manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    _, primary_by_id = _source_requests(primary_manifest, "primary run")
    runs: list[dict[str, Any]] = []
    source_hash_info: dict[str, Any] = {}
    for order, (label, run_dir) in enumerate(SUPPLEMENT_SOURCES, start=1):
        manifest = _read_json(run_dir / "manifest.json", f"{label} manifest")
        status = _read_json(run_dir / "status.json", f"{label} status")
        freeze = _read_json(run_dir / "freeze.json", f"{label} freeze record")
        _need(isinstance(manifest, dict) and isinstance(status, dict) and isinstance(freeze, dict),
              f"{label} source metadata is invalid")
        request_list, requests_by_id = _source_requests(manifest, label)
        dispatches = _dispatch_rows(run_dir, requests_by_id, label)
        response_dir = run_dir / "responses"
        response_paths = {path.stem: path for path in response_dir.glob("*.json") if path.is_file()}
        _need(set(response_paths).issubset(set(requests_by_id)), f"{label} contains an unmapped receipt")

        public_requests: list[dict[str, Any]] = []
        receipt_status_counts: Counter[str] = Counter()
        valid_count = 0
        not_dispatched = 0
        dispatched_without_response = 0
        for request in request_list:
            view = _supplement_request_view(request)
            source_request_id = view["source_request_id"]
            _need(source_request_id in primary_by_id, f"{label} request maps outside the original 84-slot queue")
            primary_request = primary_by_id[source_request_id]
            for key in ("model", "transcript_id", "condition", "replicate", "pair_id", "slot_order", "prompt_sha256"):
                if key in view and key in primary_request:
                    _need(view[key] == primary_request[key], f"{label} request changes its original position or prompt")
            request_id = view["request_id"]
            dispatch = dispatches.get(request_id)
            receipt_path = response_paths.get(request_id)
            if receipt_path is not None:
                _need(dispatch is not None, f"{label} has a response without a dispatch record")
                receipt = _read_json(receipt_path, f"{label} response receipt")
                public_receipt = _response_public_view(receipt, f"{label} response receipt")
                _need(receipt.get("source_request_id") == source_request_id,
                      f"{label} response original-source mapping mismatch")
                _need(receipt.get("prompt_sha256") == view["prompt_sha256"],
                      f"{label} response prompt hash mismatch")
                _need(receipt.get("request_id") == request_id, f"{label} response request id mismatch")
                view["receipt"] = public_receipt
                view["slot_state"] = str(receipt.get("status"))
                receipt_status_counts[str(receipt.get("status"))] += 1
                observation, _reason = analyzer._classify_receipt(receipt_path, request, run_dir / "dispatches")
                view["analysis_valid"] = observation is not None
                if observation is not None:
                    valid_count += 1
            elif dispatch is not None:
                view["slot_state"] = "dispatched_no_response"
                view["analysis_valid"] = False
                view["outcome"] = "unknown; do not resubmit or infer a terminal status"
                dispatched_without_response += 1
            else:
                view["slot_state"] = "not_dispatched"
                view["analysis_valid"] = False
                not_dispatched += 1
            if dispatch is not None:
                view["dispatch"] = dispatch
            public_requests.append(view)

        state = status.get("state")
        if label == "supplement06":
            _need(state == "RUNNING", "supplement 06 source status snapshot changed")
            lock_present = any("lock" in path.name.lower() for path in run_dir.iterdir())
            _need(lock_present, "supplement 06 lock-file snapshot changed")
            derived_process_absent = {
                "value": True,
                "basis": "root-verified publication snapshot on 2026-10-08; process identifier omitted",
            }
            snapshot_state = "interrupted_incomplete"
        else:
            _need(state == "HALTED", "supplement 07 source status snapshot changed")
            lock_present = None
            derived_process_absent = None
            snapshot_state = "halted_incomplete"

        run_record = {
            "label": label,
            "selection_order": order,
            "source_status": state,
            "snapshot_state": snapshot_state,
            "status_halt_reason": status.get("halt_reason"),
            "planned_requests": status.get("planned"),
            "dispatch_count": len(dispatches),
            "response_receipt_count": len(response_paths),
            "valid_response_count": valid_count,
            "receipt_status_counts": dict(sorted(receipt_status_counts.items())),
            "dispatched_no_response_count": dispatched_without_response,
            "not_dispatched_count": not_dispatched,
            "lockfile_present_at_snapshot": lock_present,
            "derived_process_absent": derived_process_absent,
            "source_status_file_not_rewritten": True,
            "requests": public_requests,
        }
        runs.append(run_record)
        source_freeze_hashes = _freeze_hashes(run_dir, freeze, label)
        source_hash_info[label] = {
            "freeze_json_sha256": _sha256_file(run_dir / "freeze.json"),
            "freeze_hashes": source_freeze_hashes,
            "reference_hashes": _safe_reference_hashes(freeze, label),
        }

    all_rows = [row for run in runs for row in run["requests"]]
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        for row in run["requests"]:
            by_source[row["source_request_id"]].append({"run": run["label"], "row": row})
    selection: list[dict[str, Any]] = []
    for source_id in sorted(by_source):
        candidates = by_source[source_id]
        valid_candidates = [candidate for candidate in candidates if candidate["row"].get("analysis_valid")]
        if valid_candidates:
            first = valid_candidates[0]
            selection.append(
                {
                    "source_request_id": source_id,
                    "selected_supplement": first["run"],
                    "selected_request_id": first["row"]["request_id"],
                    "additional_valid_candidates": max(0, len(valid_candidates) - 1),
                }
            )

    supplement_status = {
        "schema_version": 1,
        "snapshot_date": PUBLIC_SNAPSHOT_DATE,
        "order_rule": "supplement07 precedes supplement06 for first-valid-per-original-position summaries",
        "runs": runs,
        "first_valid_per_original_position": selection,
        "selection_counts": {
            "valid_supplement_receipts": sum(run["valid_response_count"] for run in runs),
            "distinct_original_positions_with_valid_supplement": len(selection),
            "first_valid_selected": len(selection),
            "later_duplicate_valid_receipts_not_selected": sum(item["additional_valid_candidates"] for item in selection),
        },
    }
    _need(len(all_rows) == 13, "supplement manifests must preserve all 13 planned slots")
    return supplement_status, source_hash_info


def _reason_word_count_from_visible_text(text: Any) -> int | None:
    if not isinstance(text, str):
        return None
    stripped = text.strip()
    fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.IGNORECASE | re.DOTALL)
    try:
        parsed = json.loads(fenced)
    except json.JSONDecodeError:
        return None
    reason = parsed.get("reason") if isinstance(parsed, dict) else None
    return len(reason.split()) if isinstance(reason, str) else None


def _condition_summary(manifest: dict[str, Any], analysis: dict[str, Any], run_dir: Path, analyzer: Any) -> dict[str, Any]:
    requests, _ = _source_requests(manifest, "public primary run")
    weights = analysis["design"]["family_weights"]
    output: dict[str, Any] = {}
    for model, model_result in analysis["models"].items():
        output[model] = {}
        for condition, row in model_result["conditions"].items():
            valid_weight = 0.0
            valid_slots = 0
            for request in requests:
                if request["model"] != model or request["condition"] != condition:
                    continue
                valid, _reason = _receipt_valid(analyzer, run_dir, request)
                if valid:
                    valid_slots += 1
                    valid_weight += float(weights[request["transcript_id"]]) / REPETITIONS
            output[model][condition] = {
                "planned_requests": row["planned_requests"],
                "valid_requests": row["valid_requests"],
                "missing_requests": row["missing_requests"],
                "missing_reasons": row["missing_reasons"],
                "valid_family_equal_slot_weight": round(valid_weight, 12),
                "missing_family_equal_slot_weight": round(1.0 - valid_weight, 12),
                "valid_count_recomputed": valid_slots,
            }
            _need(valid_slots == row["valid_requests"], "primary valid-count summary disagrees with analysis")
    return output


def _first_valid_overlay_summary(
    manifest: dict[str, Any], analysis: dict[str, Any], run_dir: Path,
    supplement_status: dict[str, Any], analyzer: Any,
) -> dict[str, Any]:
    """Describe primary receipts plus the first valid supplement per missing slot."""
    requests, _ = _source_requests(manifest, "primary run")
    weights = analysis["design"]["family_weights"]
    selected_rows: dict[str, dict[str, Any]] = {}
    for selection in supplement_status.get("first_valid_per_original_position", []):
        source_id = selection["source_request_id"]
        selected_run = selection["selected_supplement"]
        selected_request_id = selection["selected_request_id"]
        for run in supplement_status["runs"]:
            if run["label"] != selected_run:
                continue
            for row in run["requests"]:
                if row["request_id"] == selected_request_id and row["analysis_valid"]:
                    selected_rows[source_id] = row
    output: dict[str, Any] = {}
    for model in analysis["design"]["models"]:
        output[model] = {}
        for condition in analysis["design"]["conditions"]:
            planned = [q for q in requests if q["model"] == model and q["condition"] == condition]
            valid_count = 0
            primary_valid_count = 0
            supplement_valid_count = 0
            valid_weight = 0.0
            observed = 0.0
            for request in planned:
                request_id = request["request_id"]
                valid, _reason = _receipt_valid(analyzer, run_dir, request)
                parsed: Any = None
                if valid:
                    primary_valid_count += 1
                    parsed = _read_json(run_dir / "responses" / f"{request_id}.json", "public primary receipt").get("parsed")
                else:
                    supplement = selected_rows.get(request_id)
                    if supplement is not None:
                        parsed = supplement["receipt"].get("parsed")
                        supplement_valid_count += 1
                if not isinstance(parsed, dict) or not isinstance(parsed.get("p_A"), (int, float)):
                    continue
                p_a = float(parsed["p_A"])
                _need(math.isfinite(p_a) and 0.0 <= p_a <= 1.0, "overlay probability is invalid")
                valid_count += 1
                slot_weight = float(weights[request["transcript_id"]]) / REPETITIONS
                valid_weight += slot_weight
                observed += slot_weight * (p_a - 0.5) ** 2
            missing_weight = max(0.0, 1.0 - valid_weight)
            output[model][condition] = {
                "planned_requests": len(planned),
                "valid_requests": valid_count,
                "missing_requests": len(planned) - valid_count,
                "primary_valid_requests": primary_valid_count,
                "first_valid_supplement_requests": supplement_valid_count,
                "valid_family_equal_slot_weight": round(valid_weight, 12),
                "missing_family_equal_slot_weight": round(missing_weight, 12),
                "observed_contribution": round(observed, 12),
                "completion_bounds": [round(observed, 12), round(observed + 0.25 * missing_weight, 12)],
            }
    return output


def _summary_json(
    run_dir: Path,
    manifest: dict[str, Any],
    analysis: dict[str, Any],
    supplement_status: dict[str, Any],
    initial_run: dict[str, Any],
    analyzer: Any,
) -> dict[str, Any]:
    primary_valid_ids: set[str] = set()
    primary_requests, _ = _source_requests(manifest, "public primary run")
    for request in primary_requests:
        valid, _reason = _receipt_valid(analyzer, run_dir, request)
        if valid:
            primary_valid_ids.add(request["request_id"])
    valid_supplement_source_ids = {
        row["source_request_id"]
        for run in supplement_status["runs"]
        for row in run["requests"]
        if row.get("analysis_valid")
    }
    distinct_valid_positions = len(primary_valid_ids | valid_supplement_source_ids)

    target_request = "EB05_D1_symmetric_frozen_glm-5.3_r3_blind"
    target_receipt = _read_json(run_dir / "responses" / f"{target_request}.json", "primary invalid receipt")
    reason_words = _reason_word_count_from_visible_text(target_receipt.get("visible_text"))
    _need(reason_words == 121, "the retained EB05 D1 r3 visible reply no longer has its recorded 121-word reason")

    condition_metrics = _condition_summary(manifest, analysis, run_dir, analyzer)
    overlay_metrics = _first_valid_overlay_summary(manifest, analysis, run_dir, supplement_status, analyzer)
    return {
        "schema_version": 1,
        "snapshot_date": PUBLIC_SNAPSHOT_DATE,
        "registered_primary_analysis": {
            "state": "ALL_84_ATTEMPTED",
            "planned_requests": PLANNED_PRIMARY,
            "attempted_requests": PLANNED_PRIMARY,
            "valid_responses": len(primary_valid_ids),
            "invalid_or_missing_requests": PLANNED_PRIMARY - len(primary_valid_ids),
            "by_model_condition": condition_metrics,
            "analysis": "analysis.json",
            "report": "RESULTS.md",
            "supplements_included": False,
        },
        "supplemental_cutoff": {
            "planned_slots": sum(run["planned_requests"] for run in supplement_status["runs"]),
            "dispatch_attempts": sum(run["dispatch_count"] for run in supplement_status["runs"]),
            "response_receipts": sum(run["response_receipt_count"] for run in supplement_status["runs"]),
            "valid_supplement_receipts": supplement_status["selection_counts"]["valid_supplement_receipts"],
            "distinct_valid_primary_positions_after_first_valid_selection": distinct_valid_positions,
            "distinct_positions_without_a_valid_answer": PLANNED_PRIMARY - distinct_valid_positions,
            "selection_rule": "Keep primary valid receipts. For every other original position, count the first valid supplement in supplement07-then-supplement06 order. This descriptive count does not alter analysis.json or RESULTS.md.",
            "first_valid_overlay_by_model_condition": overlay_metrics,
            "runs": [
                {
                    "label": run["label"],
                    "source_status": run["source_status"],
                    "snapshot_state": run["snapshot_state"],
                    "planned": run["planned_requests"],
                    "dispatched": run["dispatch_count"],
                    "responses": run["response_receipt_count"],
                    "valid": run["valid_response_count"],
                    "dispatched_no_response": run["dispatched_no_response_count"],
                    "not_dispatched": run["not_dispatched_count"],
                    "receipt_status_counts": run["receipt_status_counts"],
                }
                for run in supplement_status["runs"]
            ],
        },
        "initial_run_01": initial_run,
        "retained_primary_failure_detail": {
            "source_request_id": target_request,
            "receipt_status": target_receipt.get("status"),
            "parse_status": target_receipt.get("parse_status"),
            "finish_reason": target_receipt.get("finish_reason"),
            "visible_reason_word_count_after_stripping_json_fence": reason_words,
            "analyzer_reason_word_cap": 120,
            "interpretation": "The visible reply contains a fenced JSON object with a 121-word reason. The frozen parser status remains invalid_json_or_schema; the 120-word analyzer cap is exceeded as well.",
        },
        "scope_notes": [
            "Only visible provider text is stored; hidden reasoning is not part of these records.",
            "Billing for transport failures or dispatched requests without a response is unknown.",
            "The primary registered analysis remains the fixed 84-request analysis; no supplement is represented as completed.",
        ],
    }


def _provenance_json(
    primary_freeze_sha256: str,
    primary_freeze: dict[str, Any],
    primary_frozen_hashes: dict[str, str],
    supplement_source_hashes: dict[str, Any],
    recovery: dict[str, Any],
    initial_run: dict[str, Any],
) -> dict[str, Any]:
    safe_recovery = {
        "identical_manifest_except_creation_time": recovery.get("identical_manifest_except_creation_time"),
        "amendment_sha256": recovery.get("amendment_sha256"),
        "recovery_helper_sha256": recovery.get("recovery_helper_sha256"),
        "prior_dispatches": initial_run["dispatch_attempts"],
        "prior_valid_model_answers": initial_run["valid_model_answers"],
    }
    for key in ("amendment_sha256", "recovery_helper_sha256"):
        if safe_recovery.get(key) is not None:
            _need(isinstance(safe_recovery[key], str) and SHA256_RE.fullmatch(safe_recovery[key].lower()),
                  "recovery provenance contains an invalid hash")
            safe_recovery[key] = safe_recovery[key].lower()
    return {
        "schema_version": 1,
        "snapshot_date": PUBLIC_SNAPSHOT_DATE,
        "primary_freeze": {
            "source_label": "frozen primary run 02",
            "source_freeze_json_sha256": primary_freeze_sha256,
            "source_frozen_file_hashes": primary_frozen_hashes,
            "source_reference_hashes": _safe_reference_hashes(primary_freeze, "primary"),
            "experimental_requests_at_freeze": primary_freeze.get("experimental_requests_at_freeze"),
            "verification_at_export": "source freeze hashes matched; public audit later verifies the published files",
        },
        "initial_recovery": safe_recovery,
        "initial_run_01_source_hashes": {
            "manifest_sha256": initial_run["source_manifest_sha256"],
            "freeze_json_sha256": initial_run["source_freeze_sha256"],
        },
        "supplement_source_hashes": supplement_source_hashes,
        "source_locations_published": False,
        "credential_or_environment_reads": 0,
        "network_calls": 0,
        "model_calls": 0,
    }


def _primary_dispatch_ledger(
    source_dir: Path,
    public_dir: Path,
    manifest: dict[str, Any],
    analyzer: Any,
    initial_run: dict[str, Any],
    recovery: dict[str, Any],
) -> dict[str, Any]:
    requests, requests_by_id = _source_requests(manifest, "primary run")
    dispatches = _dispatch_rows(source_dir, requests_by_id, "primary run")
    rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    parse_counts: Counter[str] = Counter()
    valid_count = 0
    for request in requests:
        request_id = request["request_id"]
        receipt = _read_json(source_dir / "responses" / f"{request_id}.json", "primary response receipt")
        dispatch = dispatches[request_id]
        public_dispatch = {
            "request_id": request_id,
            "prompt_sha256": dispatch["prompt_sha256"],
            "dispatched_utc": dispatch["dispatched_utc"],
        }
        _write_json_lf(public_dir / "dispatches" / f"{request_id}.json", public_dispatch)
        valid, missing_reason = _receipt_valid(analyzer, source_dir, request)
        status_counts[str(receipt.get("status"))] += 1
        parse_counts[str(receipt.get("parse_status"))] += 1
        valid_count += int(valid)
        rows.append(
            {
                "request_id": request_id,
                "dispatch_count": 1,
                "dispatch_state": "sent_once",
                "dispatched_utc": dispatch["dispatched_utc"],
                "prompt_sha256": request["prompt_sha256"],
                "receipt_status": receipt.get("status"),
                "parse_status": receipt.get("parse_status"),
                "finish_reason": receipt.get("finish_reason"),
                "http_status": receipt.get("http_status"),
                "analysis_valid": valid,
                "analysis_exclusion_reason": missing_reason,
            }
        )
    policy = manifest.get("failure_policy", {})
    return {
        "schema_version": 1,
        "primary": {
            "source_state": "ALL_84_ATTEMPTED",
            "planned_requests": PLANNED_PRIMARY,
            "dispatch_receipts": len(dispatches),
            "unique_dispatched_requests": len(dispatches),
            "duplicate_dispatches": 0,
            "receipt_status_counts": dict(sorted(status_counts.items())),
            "parse_status_counts": dict(sorted(parse_counts.items())),
            "valid_responses": valid_count,
            "retry_policy": {
                "semantic_retry": policy.get("semantic_retry"),
                "transport_retry": policy.get("transport_retry"),
                "model_fallback": policy.get("model_fallback"),
                "unknown_inflight_no_resubmit": policy.get("unknown_inflight_no_resubmit"),
            },
            "attempts": rows,
        },
        "initial_run_01_recovery": {
            "dispatch_attempts": initial_run["dispatch_attempts"],
            "http_status_counts": initial_run["http_status_counts"],
            "valid_model_answers": initial_run["valid_model_answers"],
            "identical_manifest_except_creation_time": recovery.get("identical_manifest_except_creation_time"),
            "amendment_sha256": recovery.get("amendment_sha256"),
        },
        "supplemental_ledger": "supplemental_status.json",
        "primary_analysis_includes_supplements": False,
    }


def _copy_primary_payload(stage: Path, manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str], dict[str, Any]]:
    freeze = _read_json(PRIMARY_SOURCE / "freeze.json", "primary freeze record")
    frozen_hashes = _freeze_hashes(PRIMARY_SOURCE, freeze, "primary")
    for name in ("manifest.json", "cohort.json", "prompt_modules.json"):
        src = PRIMARY_SOURCE / name
        shutil.copyfile(src, stage / name)
    prompt_files, prompt_hashes = _prompt_inventory(PRIMARY_SOURCE, manifest, "primary run")
    for src in prompt_files:
        rel = src.relative_to(PRIMARY_SOURCE)
        (stage / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, stage / rel)

    requests, requests_by_id = _source_requests(manifest, "primary run")
    response_dir = PRIMARY_SOURCE / "responses"
    expected_files = {f"{request_id}.json" for request_id in requests_by_id}
    actual_files = {path.name for path in response_dir.glob("*.json") if path.is_file()}
    _need(actual_files == expected_files, "primary response receipts do not match the frozen 84 requests")
    for request in requests:
        request_id = request["request_id"]
        receipt = _read_json(response_dir / f"{request_id}.json", "primary response receipt")
        public = _response_public_view(receipt, "primary response receipt")
        _need(public["request_id"] == request_id, "primary response request id mismatch")
        _need(public["prompt_sha256"] == request["prompt_sha256"], "primary response prompt hash mismatch")
        _need(public["transcript_id"] == request["transcript_id"], "primary response transcript mapping mismatch")
        _need(public["model"] == request["model"], "primary response model mapping mismatch")
        _need(public["condition"] == request["condition"], "primary response condition mapping mismatch")
        _write_json_lf(stage / "responses" / f"{request_id}.json", public)

    recovery = _read_json(PRIMARY_SOURCE / "recovery.json", "primary recovery provenance")
    _need(isinstance(recovery, dict), "primary recovery provenance must be an object")
    return freeze, frozen_hashes, recovery


def _copy_supplement_receipts(stage: Path, supplement_status: dict[str, Any]) -> None:
    for run in supplement_status["runs"]:
        label = run["label"]
        source_dir = dict(SUPPLEMENT_SOURCES)[label]
        expected = {
            row["request_id"]
            for row in run["requests"]
            if isinstance(row.get("receipt"), dict)
        }
        written: set[str] = set()
        for row in run["requests"]:
            receipt = row.get("receipt")
            if not isinstance(receipt, dict):
                continue
            request_id = row["request_id"]
            _write_json_lf(stage / "supplements" / label / "responses" / f"{request_id}.json", receipt)
            written.add(request_id)
        _need(written == expected, f"{label} public response receipt copy is incomplete")


def _readme_text() -> str:
    return """# OpenCode Go R0 Frozen replay: public cutoff snapshot

This directory publishes the frozen primary queue and the incomplete recovery supplements as of 2026-10-08. The primary 84-slot analysis stays fixed; supplemental responses are reported separately and do not change its registered estimates.

## Reading route

1. [Delivery note](../../replay_r0/DELIVERY_20261008.md) and [frozen protocol/results](../../replay_r0/RESULTS_20261007.md).
2. [Primary analysis](analysis.json) and its [rendered report](RESULTS.md).
3. [Coverage, conditional counts, slot weights, and cutoff summary](summary.json).
4. [Supplement dispatch/status ledger and original-request mapping](supplemental_status.json), plus the [primary attempt ledger](dispatch_ledger.json).
5. [Frozen manifest](manifest.json), [cohort](cohort.json), [prompt modules](prompt_modules.json), the 14 exact prompts in `prompts/`, and all 84 allowlisted primary receipts in `responses/`.
6. [Source freeze/reference hashes](provenance.json) and [published-file SHA-256LF list](SHA256SUMS.txt).

## What the records show

The registered primary run attempted all 84 frozen slots and contains 77 valid responses. Its analyzer output is reproduced from these public records. The seven excluded slots remain visible with their original receipt statuses and exact visible text. In the original EB05 D1, GLM blind replicate 3, the retained visible reply contains a fenced JSON object with a 121-word reason; after removing the fence the JSON parses, but the frozen receipt remains `invalid_json_or_schema` and the analyzer's 120-word reason cap is exceeded.

Two later supplements add two distinct first-valid responses for originally invalid positions, yielding 79/84 distinct positions with a valid answer for descriptive cutoff accounting. Those supplement records remain outside `analysis.json` and `RESULTS.md`. Supplement 07 halted after two dispatches, including one HTTP 429. Supplement 06 has a source status of `RUNNING` but is published as an incomplete snapshot: the process was absent at the publication snapshot, a lock file remained, one dispatched slot has no response and is marked `dispatched_no_response` with unknown outcome, and three slots were not dispatched. This does not mark either supplement complete.

Only the provider-visible answer text is included; hidden reasoning is not stored. Billing for transport failures and dispatched requests without a response is unknown. The package contains no credentials, private account links, local machine paths, host identifiers, or process identifiers.

## Audit and dependencies

The exporter and offline auditor are [`scripts/publish_frozen_replay_r0.py`](../../../scripts/publish_frozen_replay_r0.py). From the repository root, run `python -X utf8 -B scripts/publish_frozen_replay_r0.py` to audit this directory. The check uses Python's standard library and the local `scripts/analyze_frozen_replay_r0.py`; it makes no network or model calls and does not require the private source run. `SHA256SUMS.txt` hashes each published file except itself after normalizing text line endings to LF.
"""


def _write_content_hashes(root: Path) -> None:
    files = sorted(path for path in root.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt")
    lines = [f"{_sha256_file(path)}  {path.relative_to(root).as_posix()}" for path in files]
    _write_lf(root / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def _audit_content_hashes(root: Path) -> int:
    sums_path = root / "SHA256SUMS.txt"
    _need(sums_path.is_file(), "SHA256SUMS.txt is missing")
    listed: dict[str, str] = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9._/-]+)", line)
        _need(match is not None, "SHA-256 list has an invalid line")
        digest, rel = match.groups()
        _safe_relpath(rel, "SHA-256 list path")
        _need(rel not in listed, "SHA-256 list contains a duplicate path")
        listed[rel] = digest
    actual = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file() and path != sums_path
    }
    _need(set(listed) == set(actual), "SHA-256 list does not cover exactly the public files")
    for rel, path in actual.items():
        _need(_sha256_file(path) == listed[rel], f"published file hash mismatch: {rel}")
    return len(actual)


def _audit_supplements(root: Path, primary_manifest: dict[str, Any], analyzer: Any) -> dict[str, Any]:
    status = _read_json(root / "supplemental_status.json", "public supplemental status")
    _need(isinstance(status, dict) and status.get("schema_version") == 1, "public supplemental status schema is invalid")
    _, primary_by_id = _source_requests(primary_manifest, "public primary run")
    expected_labels = [label for label, _ in SUPPLEMENT_SOURCES]
    runs = status.get("runs")
    _need(isinstance(runs, list) and [run.get("label") for run in runs] == expected_labels,
          "public supplement order or run list changed")
    valid_receipts = 0
    candidate_by_source: dict[str, list[tuple[str, str]]] = defaultdict(list)
    total_requests = 0
    for run in runs:
        label = run["label"]
        requests = run.get("requests")
        _need(isinstance(requests, list), f"public {label} request ledger is missing")
        total_requests += len(requests)
        request_ids: set[str] = set()
        expected_receipt_files: set[str] = set()
        dispatch_count = 0
        receipt_status_counts: Counter[str] = Counter()
        valid_count = 0
        no_response_count = 0
        unstarted_count = 0
        for row in requests:
            _need(isinstance(row, dict), f"public {label} request row is invalid")
            request_id = row.get("request_id")
            source_id = row.get("source_request_id")
            _need(isinstance(request_id, str) and SAFE_ID_RE.fullmatch(request_id), f"public {label} request id is invalid")
            _need(request_id not in request_ids, f"public {label} request id is duplicated")
            request_ids.add(request_id)
            _need(source_id in primary_by_id, f"public {label} source mapping is outside the frozen queue")
            source = primary_by_id[source_id]
            for key in ("model", "transcript_id", "condition", "replicate", "pair_id", "slot_order", "prompt_sha256"):
                if key in row and key in source:
                    _need(row[key] == source[key], f"public {label} source mapping changes the original position")
            dispatch = row.get("dispatch")
            receipt = row.get("receipt")
            slot_state = row.get("slot_state")
            if isinstance(dispatch, dict):
                dispatch_count += 1
                _need(dispatch.get("request_id") == request_id, f"public {label} dispatch request id mismatch")
                _need(dispatch.get("prompt_sha256") == row.get("prompt_sha256"), f"public {label} dispatch prompt hash mismatch")
            if isinstance(receipt, dict):
                expected_receipt_files.add(request_id + ".json")
                _assert_no_private_keys(receipt, f"public {label} receipt")
                _need(set(receipt).issubset(PRIMARY_RECEIPT_FIELDS), f"public {label} receipt contains a non-whitelisted field")
                _need(receipt.get("request_id") == request_id, f"public {label} receipt request id mismatch")
                _need(receipt.get("source_request_id") == source_id, f"public {label} receipt source mapping mismatch")
                _need(receipt.get("prompt_sha256") == row.get("prompt_sha256"), f"public {label} receipt prompt hash mismatch")
                _need(slot_state == str(receipt.get("status")), f"public {label} receipt status mismatch")
                receipt_status_counts[str(receipt.get("status"))] += 1
                receipt_path = root / "supplements" / label / "responses" / (request_id + ".json")
                disk_receipt = _read_json(receipt_path, f"public {label} receipt")
                _need(disk_receipt == receipt, f"public {label} receipt copy differs from its ledger")
                original_request_view = {
                    key: row[key]
                    for key in ("request_id", "transcript_id", "model", "condition", "replicate", "pair_id", "slot_order", "prompt_sha256")
                    if key in row
                }
                observation, _reason = analyzer._classify_receipt(receipt_path, original_request_view, None)
                is_valid = observation is not None
                _need(row.get("analysis_valid") is is_valid, f"public {label} validity marker disagrees with receipt")
                if is_valid:
                    valid_count += 1
                    candidate_by_source[source_id].append((label, request_id))
            elif isinstance(dispatch, dict):
                _need(slot_state == "dispatched_no_response", f"public {label} pending dispatch lost its unknown marker")
                _need(row.get("analysis_valid") is False, f"public {label} pending dispatch has a false valid marker")
                no_response_count += 1
            else:
                _need(slot_state == "not_dispatched", f"public {label} unstarted slot is misclassified")
                _need(row.get("analysis_valid") is False, f"public {label} unstarted slot has a false valid marker")
                unstarted_count += 1
        response_dir = root / "supplements" / label / "responses"
        actual_receipt_files = {path.name for path in response_dir.glob("*.json") if path.is_file()}
        _need(actual_receipt_files == expected_receipt_files, f"public {label} response files do not match the ledger")
        _need(run.get("dispatch_count") == dispatch_count, f"public {label} dispatch count disagrees with rows")
        _need(run.get("response_receipt_count") == len(expected_receipt_files), f"public {label} receipt count disagrees with rows")
        _need(run.get("valid_response_count") == valid_count, f"public {label} valid count disagrees with rows")
        _need(run.get("dispatched_no_response_count") == no_response_count, f"public {label} pending count disagrees with rows")
        _need(run.get("not_dispatched_count") == unstarted_count, f"public {label} unstarted count disagrees with rows")
        _need(run.get("receipt_status_counts") == dict(sorted(receipt_status_counts.items())),
              f"public {label} receipt status counts disagree with rows")
        if label == "supplement06":
            _need(run.get("source_status") == "RUNNING", "public supplement 06 lost its raw source status")
            _need(run.get("snapshot_state") == "interrupted_incomplete", "public supplement 06 is mislabeled complete")
            derived = run.get("derived_process_absent")
            _need(isinstance(derived, dict) and derived.get("value") is True,
                  "public supplement 06 omitted root-verified process-absence snapshot")
            _need(run.get("lockfile_present_at_snapshot") is True, "public supplement 06 lock snapshot is missing")
            _need(no_response_count == 1, "public supplement 06 must preserve one dispatched request without a response")
        if label == "supplement07":
            _need(run.get("source_status") == "HALTED" and run.get("snapshot_state") == "halted_incomplete",
                  "public supplement 07 is mislabeled complete")
            _need(receipt_status_counts.get("http_error") == 1, "public supplement 07 lost its HTTP error response")
    _need(total_requests == 13, "public supplement ledger must cover all 13 planned supplement slots")

    first_valid: list[dict[str, Any]] = []
    for source_id, candidates in sorted(candidate_by_source.items()):
        label, request_id = candidates[0]
        first_valid.append(
            {
                "source_request_id": source_id,
                "selected_supplement": label,
                "selected_request_id": request_id,
                "additional_valid_candidates": len(candidates) - 1,
            }
        )
    _need(status.get("first_valid_per_original_position") == first_valid,
          "public first-valid selection does not follow the recorded supplement order")
    selection_counts = status.get("selection_counts", {})
    _need(selection_counts.get("valid_supplement_receipts") == valid_receipts + sum(run.get("valid_response_count", 0) for run in runs) - valid_receipts,
          "public supplement valid count is inconsistent")
    _need(selection_counts.get("distinct_original_positions_with_valid_supplement") == len(first_valid),
          "public supplement distinct-position count is inconsistent")
    _need(selection_counts.get("first_valid_selected") == len(first_valid),
          "public first-valid selection count is inconsistent")
    return {
        "planned_slots": total_requests,
        "dispatch_attempts": sum(run["dispatch_count"] for run in runs),
        "response_receipts": sum(run["response_receipt_count"] for run in runs),
        "valid_response_count": sum(run["valid_response_count"] for run in runs),
        "distinct_valid_original_positions": len(first_valid),
        "dispatched_no_response": sum(run["dispatched_no_response_count"] for run in runs),
        "not_dispatched": sum(run["not_dispatched_count"] for run in runs),
    }


def _audit_source_comparison(root: Path, primary_manifest: dict[str, Any], analysis: dict[str, Any]) -> str:
    if not PRIMARY_SOURCE.is_dir():
        return "private source unavailable; public content and analyzer output verified"
    source_analysis = _read_json(PRIMARY_SOURCE / "analysis.json", "private primary analysis")
    _need(analysis == source_analysis, "public analysis differs from the private primary analysis")
    for name in ("manifest.json", "cohort.json", "prompt_modules.json"):
        _need((root / name).read_bytes() == (PRIMARY_SOURCE / name).read_bytes(),
              f"public {name} differs from the original frozen file")
    prompt_files, _ = _prompt_inventory(PRIMARY_SOURCE, primary_manifest, "private primary run")
    for source_path in prompt_files:
        rel = source_path.relative_to(PRIMARY_SOURCE)
        _need((root / rel).read_bytes() == source_path.read_bytes(), "a public prompt differs from its frozen source")
    _, source_by_id = _source_requests(primary_manifest, "private primary run")
    for request_id in source_by_id:
        source_receipt = _read_json(PRIMARY_SOURCE / "responses" / f"{request_id}.json", "private primary receipt")
        public_expected = _response_public_view(source_receipt, "private primary receipt")
        public_receipt = _read_json(root / "responses" / f"{request_id}.json", "public primary receipt")
        _need(public_receipt == public_expected, "a public primary receipt differs from its allowlisted source fields")
    supplement_status = _read_json(root / "supplemental_status.json", "public supplemental status")
    verified_supplements: list[str] = []
    for label, source_dir in SUPPLEMENT_SOURCES:
        if not source_dir.is_dir():
            continue
        source_manifest = _read_json(source_dir / "manifest.json", f"private {label} manifest")
        source_status = _read_json(source_dir / "status.json", f"private {label} status")
        _request_list, source_requests_by_id = _source_requests(source_manifest, f"private {label}")
        source_dispatches = _dispatch_rows(source_dir, source_requests_by_id, f"private {label}")
        public_run = next(run for run in supplement_status["runs"] if run["label"] == label)
        _need(public_run.get("source_status") == source_status.get("state"),
              f"public {label} source status differs from its frozen snapshot")
        _need(public_run.get("planned_requests") == source_status.get("planned"),
              f"public {label} planned count differs from its source status")
        for row in public_run["requests"]:
            request_id = row["request_id"]
            source_request = source_requests_by_id[request_id]
            _need(row.get("source_request_id") == source_request.get("source_request_id"),
                  f"public {label} original-source mapping differs from its source manifest")
            source_dispatch = source_dispatches.get(request_id)
            _need(row.get("dispatch") == source_dispatch,
                  f"public {label} dispatch record differs from its source")
            source_receipt_path = source_dir / "responses" / f"{request_id}.json"
            public_receipt = row.get("receipt")
            if source_receipt_path.is_file():
                source_receipt = _read_json(source_receipt_path, f"private {label} response receipt")
                expected_public_receipt = _response_public_view(source_receipt, f"private {label} response receipt")
                _need(public_receipt == expected_public_receipt,
                      f"public {label} response differs from its allowlisted source fields")
            else:
                expected_slot_state = "dispatched_no_response" if source_dispatch is not None else "not_dispatched"
                _need(public_receipt is None and row.get("slot_state") == expected_slot_state,
                      f"public {label} missing receipt state differs from its source dispatch ledger")
        if label == "supplement06":
            current_lock = any("lock" in path.name.lower() for path in source_dir.iterdir())
            _need(public_run.get("lockfile_present_at_snapshot") is current_lock,
                  "public supplement 06 lock snapshot differs from its source directory")
        verified_supplements.append(label)
    if INITIAL_SOURCE.is_dir():
        summary = _read_json(root / "summary.json", "public summary")
        _need(summary.get("initial_run_01") == _validate_initial_run(),
              "public initial recovery summary differs from its source receipts")
    suffix = ", supplements verified=" + ",".join(verified_supplements) if verified_supplements else ", supplements unavailable"
    return "private source comparison passed; only public allowlisted fields were compared" + suffix


def _audit_public(root: Path) -> dict[str, Any]:
    analyzer = _load_analyzer()
    hashed_files = _audit_content_hashes(root)
    manifest = _read_json(root / "manifest.json", "public primary manifest")
    cohort = _read_json(root / "cohort.json", "public cohort")
    prompt_modules = _read_json(root / "prompt_modules.json", "public prompt modules")
    _assert_no_private_keys(manifest, "public primary manifest")
    _assert_no_private_endpoint(manifest)
    _assert_no_private_keys(cohort, "public cohort")
    _assert_no_private_keys(prompt_modules, "public prompt modules")
    requests, requests_by_id = _source_requests(manifest, "public primary run")
    _need(len(requests) == PLANNED_PRIMARY, "public primary manifest must contain 84 slots")

    prompt_files = sorted(path for path in (root / "prompts").rglob("*") if path.is_file())
    _need(len(prompt_files) == EXPECTED_PROMPTS, "public prompt directory must contain exactly 14 files")
    prompt_hashes = {path.relative_to(root).as_posix(): _sha256_file(path) for path in prompt_files}
    for request in requests:
        rel = _safe_relpath(request.get("prompt_path"), "public request prompt_path").as_posix()
        _need(rel in prompt_hashes and prompt_hashes[rel] == request.get("prompt_sha256"),
              "public request prompt hash does not match the exact prompt file")

    response_dir = root / "responses"
    actual_receipts = {path.name for path in response_dir.glob("*.json") if path.is_file()}
    _need(actual_receipts == {f"{request_id}.json" for request_id in requests_by_id},
          "public primary receipt set must cover exactly the 84 manifest requests")
    dispatch_dir = root / "dispatches"
    dispatch_files = {path.name for path in dispatch_dir.glob("*.json") if path.is_file()}
    _need(dispatch_files == {f"{request_id}.json" for request_id in requests_by_id},
          "public primary dispatch ledger must cover exactly the 84 manifest requests")
    for request_id, request in requests_by_id.items():
        receipt = _read_json(response_dir / f"{request_id}.json", "public primary response receipt")
        _assert_no_private_keys(receipt, "public primary response receipt")
        _need(set(receipt).issubset(PRIMARY_RECEIPT_FIELDS), "public primary receipt contains a non-whitelisted field")
        _need(REQUIRED_RECEIPT_FIELDS.issubset(receipt), "public primary receipt omitted a required field")
        _need(receipt.get("request_id") == request_id, "public primary receipt request id mismatch")
        _need(receipt.get("prompt_sha256") == request.get("prompt_sha256"), "public primary receipt prompt hash mismatch")
        _need(receipt.get("transcript_id") == request.get("transcript_id"), "public primary receipt transcript mismatch")
        dispatch = _read_json(dispatch_dir / f"{request_id}.json", "public primary dispatch receipt")
        _assert_no_private_keys(dispatch, "public primary dispatch receipt")
        _need(dispatch.get("request_id") == request_id and dispatch.get("prompt_sha256") == request.get("prompt_sha256"),
              "public primary dispatch does not match its request")

    analysis = analyzer.analyze_run(root)
    stored_analysis = _read_json(root / "analysis.json", "public primary analysis")
    _need(analysis == stored_analysis, "public analysis.json does not reproduce from the public records")
    rendered = analyzer.render_results(analysis).replace("\r\n", "\n")
    stored_results = (root / "RESULTS.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    _need(rendered == stored_results, "public RESULTS.md is not the analyzer rendering of public analysis")

    supplement_counts = _audit_supplements(root, manifest, analyzer)
    summary = _read_json(root / "summary.json", "public summary")
    _assert_no_private_keys(summary, "public summary")
    _need(summary.get("registered_primary_analysis", {}).get("valid_responses") == 77,
          "public summary primary valid count changed")
    _need(summary.get("registered_primary_analysis", {}).get("supplements_included") is False,
          "public summary incorrectly folds supplements into the registered analysis")
    _need(summary.get("supplemental_cutoff", {}).get("distinct_valid_primary_positions_after_first_valid_selection") == 79,
          "public summary distinct-position cutoff count changed")
    _need(supplement_counts["distinct_valid_original_positions"] == 2,
          "supplement valid receipts no longer map to two distinct primary positions")
    expected_primary_condition_metrics = _condition_summary(manifest, analysis, root, analyzer)
    _need(summary.get("registered_primary_analysis", {}).get("by_model_condition") == expected_primary_condition_metrics,
          "public summary conditional primary counts or slot weights disagree with public analysis")
    expected_overlay = _first_valid_overlay_summary(manifest, analysis, root, _read_json(root / "supplemental_status.json", "public supplemental status"), analyzer)
    _need(summary.get("supplemental_cutoff", {}).get("first_valid_overlay_by_model_condition") == expected_overlay,
          "public first-valid overlay counts or weighted bounds disagree with public records")
    glm_blind_overlay = expected_overlay["glm-5.3"]["blind"]
    _need(glm_blind_overlay["valid_requests"] == 16, "public GLM blind first-valid overlay should cover 16 of 21 slots")
    _need(glm_blind_overlay["observed_contribution"] == 0.011041666667,
          "public GLM blind first-valid overlay observed contribution changed")
    _need(glm_blind_overlay["missing_family_equal_slot_weight"] == 0.222222222222,
          "public GLM blind first-valid overlay missing weight changed")
    _need(glm_blind_overlay["completion_bounds"] == [0.011041666667, 0.066597222222],
          "public GLM blind first-valid overlay completion bounds changed")
    ledger = _read_json(root / "dispatch_ledger.json", "public dispatch ledger")
    _assert_no_private_keys(ledger, "public dispatch ledger")
    _need(ledger.get("primary", {}).get("dispatch_receipts") == 84, "public primary attempt ledger is incomplete")
    _need(ledger.get("primary", {}).get("duplicate_dispatches") == 0, "public ledger reports a duplicate primary dispatch")
    provenance = _read_json(root / "provenance.json", "public provenance")
    _assert_no_private_keys(provenance, "public provenance")
    primary_freeze = provenance.get("primary_freeze", {})
    frozen_hashes = primary_freeze.get("source_frozen_file_hashes", {})
    for name in ("manifest.json", "cohort.json", "prompt_modules.json"):
        _need(frozen_hashes.get(name) == _sha256_file(root / name), f"public {name} does not match the original freeze hash")

    source_comparison = _audit_source_comparison(root, manifest, analysis)
    return {
        "hashed_files": hashed_files,
        "primary_requests": PLANNED_PRIMARY,
        "primary_valid": analysis["models"]["glm-5.3"]["conditions"]["blind"]["valid_requests"]
        + analysis["models"]["glm-5.3"]["conditions"]["informed"]["valid_requests"]
        + analysis["models"]["qwen3.8-max"]["conditions"]["blind"]["valid_requests"]
        + analysis["models"]["qwen3.8-max"]["conditions"]["informed"]["valid_requests"],
        "supplement": supplement_counts,
        "private_source_comparison": source_comparison,
    }


def _export(stage: Path) -> dict[str, Any]:
    analyzer = _load_analyzer()
    manifest, expected_analysis, primary_freeze_sha = _load_primary_analysis(analyzer)
    initial_run = _validate_initial_run()
    freeze, frozen_hashes, recovery = _copy_primary_payload(stage, manifest)
    supplement_status, supplement_source_hashes = _supplement_status(analyzer, manifest)
    _copy_supplement_receipts(stage, supplement_status)

    for run in supplement_status["runs"]:
        label = run["label"]
        source_dir = dict(SUPPLEMENT_SOURCES)[label]
        source_manifest = _read_json(source_dir / "manifest.json", f"{label} manifest")
        for row in run["requests"]:
            request_id = row["request_id"]
            public_request = {
                "request_id": request_id,
                "source_request_id": row["source_request_id"],
                "model": row.get("model"),
                "transcript_id": row.get("transcript_id"),
                "condition": row.get("condition"),
                "replicate": row.get("replicate"),
                "pair_id": row.get("pair_id"),
                "slot_order": row.get("slot_order"),
                "prompt_sha256": row.get("prompt_sha256"),
            }
            _need(public_request["prompt_sha256"] in {value for value in _prompt_inventory(PRIMARY_SOURCE, manifest, "primary run")[1].values()},
                  f"{label} request prompt hash is outside the exact 14-prompt bundle")
        del source_manifest

    source_analysis = _read_json(PRIMARY_SOURCE / "analysis.json", "primary frozen analysis")
    _need(expected_analysis == source_analysis, "primary analysis changed while the export was being built")
    _write_json_lf(stage / "analysis.json", expected_analysis)
    rendered = analyzer.render_results(expected_analysis).replace("\r\n", "\n")
    source_results = (PRIMARY_SOURCE / "RESULTS.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    _need(rendered == source_results, "public report rendering differs from the private primary report")
    _write_lf(stage / "RESULTS.md", rendered)
    _write_json_lf(stage / "supplemental_status.json", supplement_status)
    _write_json_lf(stage / "dispatch_ledger.json", _primary_dispatch_ledger(PRIMARY_SOURCE, stage, manifest, analyzer, initial_run, recovery))
    _write_json_lf(
        stage / "provenance.json",
        _provenance_json(primary_freeze_sha, freeze, frozen_hashes, supplement_source_hashes, recovery, initial_run),
    )
    _write_json_lf(stage / "summary.json", _summary_json(stage, manifest, expected_analysis, supplement_status, initial_run, analyzer))
    _write_lf(stage / "README.md", _readme_text())
    _write_content_hashes(stage)
    return _audit_public(stage)


def _export_once() -> dict[str, Any]:
    _need(not PUBLIC_DIR.exists(), "public export already exists; --export never overwrites")
    _need(PUBLIC_PARENT.is_dir(), "public_runs directory is missing")
    stage_path = Path(tempfile.mkdtemp(prefix=".go_frozen_replay_r0_20261008-", dir=PUBLIC_PARENT))
    try:
        result = _export(stage_path)
        _need(not PUBLIC_DIR.exists(), "public export appeared during creation; refusing to replace it")
        stage_path.rename(PUBLIC_DIR)
    except Exception:
        resolved_parent = PUBLIC_PARENT.resolve()
        resolved_stage = stage_path.resolve()
        _need(resolved_stage.parent == resolved_parent and stage_path.name.startswith(".go_frozen_replay_r0_20261008-"),
              "temporary export path failed its cleanup boundary check")
        if stage_path.exists():
            shutil.rmtree(stage_path)
        raise
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", action="store_true", help="create the public snapshot once; refuse overwrite")
    parser.add_argument("--audit", action="store_true", help="audit the existing public directory (the default)")
    args = parser.parse_args(argv)
    if args.export and args.audit:
        parser.error("choose either --export or --audit")
    try:
        if args.export:
            result = _export_once()
            print(
                "EXPORT_OK public snapshot created; "
                f"hashed_files={result['hashed_files']} primary_valid={result['primary_valid']}/84 "
                f"supplement_distinct_valid_positions={result['supplement']['distinct_valid_original_positions']} "
                f"private_source={result['private_source_comparison']}"
            )
        else:
            _need(PUBLIC_DIR.is_dir(), "public directory is missing; use --export once to create it")
            result = _audit_public(PUBLIC_DIR)
            print(
                "AUDIT_OK public snapshot verified; "
                f"hashed_files={result['hashed_files']} primary_valid={result['primary_valid']}/84 "
                f"supplement_valid={result['supplement']['valid_response_count']} "
                f"supplement_distinct_positions={result['supplement']['distinct_valid_original_positions']} "
                f"private_source={result['private_source_comparison']}"
            )
    except PublicationError as exc:
        print(f"publication error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"publication error: {type(exc).__name__}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
