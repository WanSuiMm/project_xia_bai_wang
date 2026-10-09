"""Offline allowlisted export and public-only verification for OSI48 completion."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "epistemic_boundary_mimicry"
RUNS = {
    "supplement01": BASE / "runs/opencode_go_20261009_opponent_strategy_inference48_supplement01",
    "tail02": BASE / "runs/opencode_go_20261010_opponent_strategy_inference48_tail02",
}
CUTOFF_SOURCE = BASE / "published_runs/go_opponent_strategy_inference48_cutoff_20261009"
PUBLIC = BASE / "published_runs/go_opponent_strategy_inference48_completion_20261010"
PUBLISHER = ROOT / "scripts/publish_opponent_strategy_inference.py"
STUDY_ID = "opponent_strategy_inference48_20261009"
TAIL_STUDY_ID = "opponent_strategy_inference48_tail_completion_20261010"
TAIL_IDS = ("OSI_GLM_PERSISTENT_H4_ONESA_R2", "OSI_GLM_PERSISTENT_H7_ONESA_R2")
BATCH_ORDER = ("original01", "recovery02", "supplement01", "tail02")
BATCH_DIR = {"original01": "cutoff/original", "recovery02": "cutoff/recovery",
             "supplement01": "supplement01", "tail02": "tail02"}
RUN_NAMES = {
    "original01": "opencode_go_20261009_opponent_strategy_inference48_01",
    "recovery02": "opencode_go_20261009_opponent_strategy_inference48_02",
    "supplement01": RUNS["supplement01"].name,
    "tail02": RUNS["tail02"].name,
}
SCAN_PATTERNS = {
    "credential": r"oc_sk_[A-Za-z0-9_-]+|\bsk-[A-Za-z0-9_-]{20,}|\bgh[pousr]_[A-Za-z0-9_]{20,}|\bxox[baprs]-[A-Za-z0-9-]{20,}|(?i:Bearer\s+)[A-Za-z0-9._-]{16,}",
    "machine_path": r"(?i)\b[A-Z]:[\\/]|/(?:Users|home|mnt/[a-z])/?",
    "private_session_url": r"https?://(?:arena\.ai/c/|chatgpt\.com/c/)",
    "ip_address": r"(?<![\w.])(?!(?:127\.0\.0\.1|0\.0\.0\.0))(?:\d{1,3}\.){3}\d{1,3}(?![\w.])",
}
FORBIDDEN_KEYS = {
    "authorization", "api_key", "x-api-key", "headers", "session_id", "session_ids",
    "account_id", "pid", "host", "absolute_path", "provenance_private", "reasoning_content",
    "hidden_reasoning", "raw_provider_body", "raw_body", "response_body", "provider_diagnostic",
    "error_message", "launch_receipt", "stdout_path", "stderr_path", "run_path", "private_key",
    "secret", "token",
}
RESPONSE_KEYS = {
    "request_id", "model", "kind", "case_id", "simulation_condition", "bluffer_condition",
    "judge_condition", "prompt_sha256", "sent_utc", "status", "visible_text", "parsed", "parse_status",
    "returned_model", "usage", "finish_reason", "http_status", "error_type", "provider_error_category",
    "elapsed_seconds", "captured_utc", "completion_parsed", "completion_parse_status", "format_acceptance",
    "requested_config",
}
DISPATCH_EXTRA = {"prompt_sha256", "dispatched_utc"}
PROMPT_RECEIPT_KEYS = {"request_id", "prompt_sha256", "created_utc"}


class PublicationError(RuntimeError):
    """Raised when frozen evidence or its public projection does not verify."""


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
    need(isinstance(value, dict) and set(value) == expected, f"{where} fields differ from the reviewed schema")
    return value


def _scan(path: Path) -> None:
    try:
        body = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PublicationError(f"Non-UTF8 public file: {path.name}") from exc
    for label, pattern in SCAN_PATTERNS.items():
        need(not re.search(pattern, body), f"Unsafe {label} in {path.name}")
    if path.suffix.lower() == ".json":
        value = json.loads(body)

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


def _load_publisher():
    spec = importlib.util.spec_from_file_location("_osi48_cutoff_publisher", PUBLISHER)
    need(spec is not None and spec.loader is not None, "Cutoff publisher helper is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_stack(publisher: Any, run: Path):
    return publisher._load_stack(run)


def _release_stack(publisher: Any, prior: dict[str, Any], run: Path) -> None:
    publisher._release_stack(prior, run / "inputs/scripts")


def _source_metadata(run: Path, label: str) -> dict[str, Any]:
    manifest = read_json(run / "manifest.json")
    schedule = read_json(run / "schedule.json")
    freeze = read_json(run / "freeze.json")
    status = read_json(run / "status.json")
    need(isinstance(manifest, dict) and isinstance(schedule, list), f"{label} manifest/schedule is malformed")
    need(manifest.get("requests") == schedule, f"{label} manifest and schedule differ")
    need(isinstance(freeze.get("hashes"), dict) and freeze.get("experimental_requests_at_freeze") == 0,
         f"{label} freeze does not prove a pre-call freeze")
    for relative, digest in freeze["hashes"].items():
        need(isinstance(relative, str) and not Path(relative).is_absolute(), f"{label} freeze path is unsafe")
        path = within(run, relative)
        need(path.is_file() and sha_file(path) == digest, f"{label} frozen file changed: {relative}")
    source_artifacts = manifest.get("source_artifacts", {})
    need(isinstance(source_artifacts, dict), f"{label} source_artifacts is malformed")
    for relative, digest in source_artifacts.items():
        need(isinstance(relative, str) and not Path(relative).is_absolute(), f"{label} source path is unsafe")
        snapshot = within(run / "inputs", relative)
        need(snapshot.is_file() and sha_file(snapshot) == digest, f"{label} source snapshot changed: {relative}")
    rows = {row.get("request_id"): row for row in schedule if isinstance(row, dict)}
    need(len(rows) == len(schedule) and None not in rows, f"{label} schedule request IDs are not unique")
    return {"manifest": manifest, "schedule": schedule, "freeze": freeze, "status": status, "rows": rows}


def _usage_projection(value: Any) -> dict[str, Any]:
    need(value is None or isinstance(value, dict), "Response usage must be an object")
    result: dict[str, Any] = {}
    for key, item in (value or {}).items():
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            result[key] = item
        elif isinstance(item, dict):
            nested = {name: number for name, number in item.items()
                      if isinstance(number, (int, float)) and not isinstance(number, bool)}
            if nested:
                result[key] = nested
    return result


def _project_response(source: Path, row: dict[str, Any], study: Any,
                      prompt_path: Path, requested_config: dict[str, Any] | None = None) -> dict[str, Any]:
    raw = read_json(source)
    need(isinstance(raw, dict) and set(raw) <= RESPONSE_KEYS | {"provider_diagnostic"},
         f"Unreviewed response fields in {source.name}")
    required = RESPONSE_KEYS - {"error_type", "provider_error_category", "requested_config"}
    need(required <= set(raw), f"Required response fields are missing in {source.name}")
    for key in ("request_id", "model", "kind", "case_id", "simulation_condition", "bluffer_condition", "judge_condition"):
        need(raw.get(key) == row[key], f"Response schedule binding differs for {source.stem}/{key}")
    prompt_digest = sha_file(prompt_path)
    need(raw.get("prompt_sha256") == prompt_digest, f"Response prompt binding differs for {source.stem}")
    visible = raw.get("visible_text")
    need(isinstance(visible, str), f"Final visible text is absent in {source.name}")
    parsed, parse_status = study.api.parse_response(visible, raw.get("finish_reason"))
    completion, completion_status, acceptance = study.formatting.parse_completion(visible, raw.get("finish_reason"))
    need((raw.get("parsed"), raw.get("parse_status")) == (parsed, parse_status),
         f"Strict parser fields do not reproduce in {source.name}")
    need((raw.get("completion_parsed"), raw.get("completion_parse_status"), raw.get("format_acceptance"))
         == (completion, completion_status, acceptance), f"Completion parser fields do not reproduce in {source.name}")
    need(raw.get("returned_model") is None or isinstance(raw.get("returned_model"), str),
         f"Returned model field is malformed in {source.name}")
    error_type = raw.get("error_type")
    need(error_type is None or (isinstance(error_type, str) and re.fullmatch(r"[A-Za-z0-9_.-]+", error_type)),
         f"Unsafe error type in {source.name}")
    safe = {key: raw.get(key) for key in (
        "request_id", "model", "kind", "case_id", "simulation_condition", "bluffer_condition", "judge_condition",
        "prompt_sha256", "sent_utc", "status", "visible_text", "parsed", "parse_status", "returned_model",
        "finish_reason", "http_status", "elapsed_seconds", "captured_utc", "completion_parsed",
        "completion_parse_status", "format_acceptance")}
    safe["usage"] = _usage_projection(raw.get("usage"))
    if "error_type" in raw:
        safe["error_type"] = error_type
    if "provider_error_category" in raw:
        category = raw["provider_error_category"]
        need(category is None or (isinstance(category, str) and re.fullmatch(r"[A-Za-z0-9_.-]+", category)),
             f"Unsafe provider error category in {source.name}")
        safe["provider_error_category"] = category
    if requested_config is not None:
        need(raw.get("requested_config") == requested_config,
             f"Tail request configuration does not match the frozen amendment in {source.name}")
        safe["requested_config"] = requested_config
    else:
        need("requested_config" not in raw, f"Unexpected request configuration field in {source.name}")
    return safe


def _check_dispatches(run: Path, info: dict[str, Any], label: str) -> dict[str, set[str]]:
    manifest, rows = info["manifest"], info["rows"]
    sets = {folder: {path.stem for path in (run / folder).glob("*.json")}
            for folder in ("responses", "dispatches", "prompt_receipts")}
    need(sets["dispatches"] == sets["prompt_receipts"], f"{label} dispatch/prompt receipt sets differ")
    need(sets["responses"] <= sets["dispatches"], f"{label} response has no dispatch")
    expected_dispatch = set(info["schedule"][0]) | DISPATCH_EXTRA if info["schedule"] else DISPATCH_EXTRA
    for rid in sets["dispatches"]:
        need(rid in rows, f"{label} has an unscheduled receipt: {rid}")
        dispatch = exact_keys(read_json(run / "dispatches" / f"{rid}.json"), expected_dispatch,
                              f"{label} dispatch {rid}")
        prompt = exact_keys(read_json(run / "prompt_receipts" / f"{rid}.json"), PROMPT_RECEIPT_KEYS,
                            f"{label} prompt receipt {rid}")
        prompt_path = within(run, rows[rid]["prompt_path"])
        digest = sha_file(prompt_path)
        need(dispatch == rows[rid] | {"prompt_sha256": digest, "dispatched_utc": dispatch["dispatched_utc"]},
             f"{label} dispatch does not bind to its schedule: {rid}")
        need(prompt["request_id"] == rid and prompt["prompt_sha256"] == digest,
             f"{label} prompt receipt does not bind to its prompt: {rid}")
    return sets


def _copy_source_batch(run: Path, label: str, destination: Path, publisher: Any) -> dict[str, Any]:
    info = _source_metadata(run, label)
    manifest, freeze, status, rows = info["manifest"], info["freeze"], info["status"], info["rows"]
    destination.mkdir(parents=True)
    tail = label == "tail02"
    for relative, digest in freeze["hashes"].items():
        if tail and relative.startswith("inputs/retained/"):
            continue
        source = within(run, relative)
        target = within(destination, relative)
        write_bytes(target, source.read_bytes())
        need(sha_file(target) == digest, f"{label} copied freeze mismatch: {relative}")
    write_json(destination / ("source_freeze.json" if tail else "freeze.json"), freeze)
    for filename in ("manifest.json", "schedule.json", "status.json"):
        source_path, target_path = run / filename, destination / filename
        if target_path.exists():
            need(sha_file(target_path) == sha_file(source_path), f"{label} copied metadata changed: {filename}")
        else:
            write_bytes(target_path, source_path.read_bytes())
    summary_path = run / "analysis/completion_summary.json"
    need(summary_path.is_file(), f"{label} completion summary is missing")
    write_bytes(destination / "analysis/completion_summary.json", summary_path.read_bytes())
    stacks = _load_stack(publisher, run)
    prior, study, analyzer, _ = stacks
    sets = _check_dispatches(run, info, label)
    source_hashes = {folder: {} for folder in ("responses", "dispatches", "prompt_receipts")}
    published_hashes = {folder: {} for folder in source_hashes}
    projected_responses: dict[str, dict[str, Any]] = {}
    try:
        for folder, ids in sets.items():
            for rid in sorted(ids):
                source = run / folder / f"{rid}.json"
                target = destination / folder / source.name
                if folder == "responses":
                    row = rows[rid]
                    prompt = within(run, row["prompt_path"])
                    request_config = None
                    if label == "tail02":
                        request_config = manifest["configuration_by_model"][row["model"]]
                    projection = _project_response(source, row, study, prompt, request_config)
                    write_json(target, projection)
                    projected_responses[rid] = projection
                else:
                    write_bytes(target, source.read_bytes())
                source_hashes[folder][rid] = sha_file(source)
                published_hashes[folder][rid] = sha_file(target)
    finally:
        _release_stack(publisher, prior, run)
    return {**info, "sets": sets, "source_hashes": source_hashes,
            "published_hashes": published_hashes, "responses": projected_responses}


def _cutoff_info(package: Path) -> dict[str, Any]:
    result = {"manifest": {}, "schedule": {}, "status": {}, "summary": {}, "rows": {}, "receipt_hashes": {}}
    publication = read_json(package / "publication.json")
    ledger = read_json(package / "attempt_ledger.json")
    for batch, label in (("original", "original01"), ("recovery", "recovery02")):
        folder = package / batch
        manifest = read_json(folder / "manifest.json")
        schedule = read_json(folder / "schedule.json")
        summary = read_json(folder / "analysis/summary.json")
        result["manifest"][label] = manifest
        result["schedule"][label] = schedule
        result["status"][label] = read_json(folder / "status.json")
        result["summary"][label] = summary
        result["rows"][label] = {row["request_id"]: row for row in schedule}
        result["receipt_hashes"][label] = {
            attempt["request_id"]: {
                "response": attempt["source_receipt_sha256_lf"],
                "dispatch": publication["receipt_sha256_lf"][batch]["dispatches"]["source"][attempt["request_id"]],
                "prompt_receipt": publication["receipt_sha256_lf"][batch]["prompt_receipts"]["source"][attempt["request_id"]],
            }
            for attempt in ledger["attempts"] if attempt["batch"] == batch
        }
    result["publication"] = publication
    result["ledger"] = ledger
    return result


def _actual_config(response: dict[str, Any], label: str, row: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    if label == "tail02":
        return response.get("requested_config", manifest["configuration_by_model"][row["model"]])
    return manifest["configuration_by_model"][row["model"]]


def _attempt_rows(package: Path, source: dict[str, Any], batches: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cutoff_ledger = source["ledger"]["attempts"]
    for attempt in cutoff_ledger:
        old_label = attempt["batch"]
        label = "original01" if old_label == "original" else "recovery02"
        path_prefix = f"cutoff/{old_label}"
        response_path = package / path_prefix / "responses" / f"{attempt['request_id']}.json"
        rec = read_json(response_path)
        rows.append({
            "batch": label, "request_id": attempt["request_id"], "schedule_index": attempt["schedule_index"],
            "status": rec["status"], "strict_parse_status": rec["parse_status"],
            "completion_parse_status": rec["completion_parse_status"], "http_status": rec.get("http_status"),
            "error_type": rec.get("error_type"), "provider_error_category": rec.get("provider_error_category"),
            "prompt_sha256": rec["prompt_sha256"], "requested_config": None,
            "response_path": f"{path_prefix}/responses/{attempt['request_id']}.json",
            "dispatch_path": f"{path_prefix}/dispatches/{attempt['request_id']}.json",
            "prompt_receipt_path": f"{path_prefix}/prompt_receipts/{attempt['request_id']}.json",
            "source_sha256_lf": {"response": attempt["source_receipt_sha256_lf"],
                                  "dispatch": source["publication"]["receipt_sha256_lf"][old_label]["dispatches"]["source"][attempt["request_id"]],
                                  "prompt_receipt": source["publication"]["receipt_sha256_lf"][old_label]["prompt_receipts"]["source"][attempt["request_id"]]},
            "published_sha256_lf": {"response": sha_file(response_path),
                                     "dispatch": sha_file(package / path_prefix / "dispatches" / f"{attempt['request_id']}.json"),
                                     "prompt_receipt": sha_file(package / path_prefix / "prompt_receipts" / f"{attempt['request_id']}.json")},
        })
    for label in ("supplement01", "tail02"):
        info = batches[label]
        for rid in sorted(info["sets"]["dispatches"], key=lambda name: info["rows"][name]["schedule_index"]):
            row = info["rows"][rid]
            response_path = package / label / "responses" / f"{rid}.json"
            rec = read_json(response_path) if response_path.exists() else {}
            rows.append({
                "batch": label, "request_id": rid, "schedule_index": row["schedule_index"],
                "status": rec.get("status", "no_response"), "strict_parse_status": rec.get("parse_status", "not_received"),
                "completion_parse_status": rec.get("completion_parse_status", "not_received"),
                "http_status": rec.get("http_status"), "error_type": rec.get("error_type"),
                "provider_error_category": rec.get("provider_error_category"), "prompt_sha256": read_json(
                    package / label / "prompt_receipts" / f"{rid}.json")["prompt_sha256"],
                "requested_config": rec.get("requested_config"),
                "response_path": f"{label}/responses/{rid}.json" if rec else None,
                "dispatch_path": f"{label}/dispatches/{rid}.json",
                "prompt_receipt_path": f"{label}/prompt_receipts/{rid}.json",
                "source_sha256_lf": {
                    "response": info["source_hashes"]["responses"].get(rid),
                    "dispatch": info["source_hashes"]["dispatches"].get(rid),
                    "prompt_receipt": info["source_hashes"]["prompt_receipts"].get(rid),
                },
                "published_sha256_lf": {
                    "response": info["published_hashes"]["responses"].get(rid),
                    "dispatch": info["published_hashes"]["dispatches"].get(rid),
                    "prompt_receipt": info["published_hashes"]["prompt_receipts"].get(rid),
                },
            })
    rows.sort(key=lambda item: (BATCH_ORDER.index(item["batch"]), item["schedule_index"], item["request_id"]))
    counts: dict[str, int] = {}
    for row in rows:
        rid = row["request_id"]
        counts[rid] = counts.get(rid, 0) + 1
        row["attempt_number_for_slot"] = counts[rid]
        row["is_repeated_slot"] = counts[rid] > 1
    need(len(rows) == 51, f"Expected 51 physical attempts, found {len(rows)}")
    return rows


def _source_map_for_selection(package: Path, source: dict[str, Any], batches: dict[str, dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for label, old_label in (("original01", "original"), ("recovery02", "recovery")):
        root = package / "cutoff" / old_label
        result[label] = {"root": root, "rows": source["rows"][label],
                         "response_ids": {p.stem for p in (root / "responses").glob("*.json")},
                         "manifest": source["manifest"][label]}
    for label in ("supplement01", "tail02"):
        result[label] = {"root": package / label, "rows": batches[label]["rows"],
                         "response_ids": batches[label]["sets"]["responses"],
                         "manifest": batches[label]["manifest"]}
    return result


def _selection(package: Path, source: dict[str, Any], batches: dict[str, dict[str, Any]],
               attempt_ledger: list[dict[str, Any]], full_schedule: list[dict[str, Any]]) -> dict[str, Any]:
    all_sources = _source_map_for_selection(package, source, batches)
    order = {label: index for index, label in enumerate(BATCH_ORDER)}
    selected: dict[str, dict[str, Any]] = {}
    records_by_id: dict[str, list[dict[str, Any]]] = {}
    for attempt in attempt_ledger:
        records_by_id.setdefault(attempt["request_id"], []).append(attempt)
        label = attempt["batch"]
        if attempt["status"] != "response_received" or attempt["strict_parse_status"] != "valid" or attempt["completion_parse_status"] != "valid":
            continue
        root = all_sources[label]["root"]
        response = read_json(root / "responses" / f"{attempt['request_id']}.json")
        row = all_sources[label]["rows"][attempt["request_id"]]
        need(response.get("returned_model") == row["model"], f"Selected model mismatch for {attempt['request_id']}")
        prior = selected.get(attempt["request_id"])
        if prior is None or order[label] > order[prior["batch"]]:
            selected[attempt["request_id"]] = {"batch": label, "attempt": attempt, "row": row, "response": response}
    entries = []
    for row in full_schedule:
        rid = row["request_id"]
        chosen = selected.get(rid)
        prompt = package / "cutoff/original" / row["prompt_path"]
        digest = sha_file(prompt)
        if chosen is not None:
            response = chosen["response"]
            need(response["prompt_sha256"] == digest, f"Selected response changed prompt for {rid}")
            target_prompt = package / "selected/prompts" / f"{rid}.txt"
            target_response = package / "selected/responses" / f"{rid}.json"
            if not target_prompt.exists():
                write_bytes(target_prompt, prompt.read_bytes())
            if not target_response.exists():
                write_json(target_response, response)
            selected_attempt = chosen["attempt"]
            chosen_batch = chosen["batch"]
        else:
            selected_attempt, chosen_batch = None, None
        entries.append({
            "request_id": rid, "model": row["model"], "simulation_condition": row["simulation_condition"],
            "history_ones": row["history_ones"], "ones_seat": row["ones_seat"], "repeat": row["repeat"],
            "posterior_A": row["posterior_A"], "plugin_posterior_A": row["plugin_posterior_A"],
            "prompt_sha256": digest, "selected_batch": chosen_batch,
            "selected_response_path": f"selected/responses/{rid}.json" if chosen is not None else None,
            "selected_response_source_sha256_lf": selected_attempt["source_sha256_lf"]["response"] if selected_attempt else None,
            "attempts": [{"batch": a["batch"], "status": a["status"],
                          "strict_parse_status": a["strict_parse_status"],
                          "completion_parse_status": a["completion_parse_status"]}
                         for a in records_by_id.get(rid, [])],
        })
    need(len(entries) == 48, "Selected schedule does not contain all 48 frozen slots")
    return {"schema_version": 1, "selection_rule": "Last strict-valid response by the fixed batch order; no score-based selection.",
            "planned_slots": 48, "selected_strict_valid": sum(e["selected_batch"] is not None for e in entries),
            "slots": entries}


def _analysis(package: Path, source: dict[str, Any], batches: dict[str, dict[str, Any]],
              selection: dict[str, Any], full_schedule: list[dict[str, Any]], publisher: Any) -> dict[str, Any]:
    prior, study, analyzer, _ = _load_stack(publisher, package / "cutoff/original")
    try:
        items = [analyzer._item(package / "selected", row) for row in full_schedule]
        valid = [item for item in items if item["status"] == "valid"]
        strict_valid = [item for item in valid if item["strict_valid"]]
        cells = [analyzer._cell(items, model, condition) for model in study.MODELS for condition in study.CONDITIONS]
        strict_cells = [analyzer._cell(items, model, condition, strict=True)
                        for model in study.MODELS for condition in study.CONDITIONS]
        contrasts = []
        for model in study.MODELS:
            persistent = next(cell for cell in cells if cell["model"] == model and cell["simulation_condition"] == "PERSISTENT")
            refreshed = next(cell for cell in cells if cell["model"] == model and cell["simulation_condition"] == "REFRESHED")
            complete = persistent["complete"] and refreshed["complete"]
            delta = persistent["history_delta"] - refreshed["history_delta"] if complete else None
            contrasts.append({"model": model, "complete": complete,
                              "persistent_delta": persistent["history_delta"], "persistent_delta_target": 65 / 67,
                              "refreshed_delta": refreshed["history_delta"], "refreshed_delta_target": 0,
                              "interaction": delta, "interaction_target": 65 / 67,
                              "interaction_absolute_error": abs(delta - 65 / 67) if complete else None})
        usage: dict[str, float] = {}
        for item in valid:
            response = read_json(package / "selected/responses" / f"{item['request_id']}.json")
            for key, value in response.get("usage", {}).items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    usage[key] = usage.get(key, 0.0) + value
        selected_by_id = {slot["request_id"]: slot for slot in selection["slots"]}
        historical_items = [dict(item) for item in items]
        for item in historical_items:
            if selected_by_id[item["request_id"]]["selected_batch"] == "tail02":
                item["status"] = "missing"
                item["strict_valid"] = False
        historical_cells = [analyzer._cell(historical_items, model, condition)
                            for model in study.MODELS for condition in study.CONDITIONS]
        historical_valid = sum(item["status"] == "valid" and item["strict_valid"]
                               for item in historical_items)
        historical_glm_persistent = next(
            cell["valid"] for cell in historical_cells
            if cell["model"] == "glm-5.3" and cell["simulation_condition"] == "PERSISTENT")
        return {
            "schema_version": 1, "study_id": "opponent_strategy_inference48_20261009",
            "completion": "COMPLETE_VALID" if len(valid) == 48 else "INCOMPLETE",
            "planned": 48, "selected_responses": len(valid), "strict_valid": len(strict_valid),
            "invalid_or_missing": 48 - len(valid), "cells": cells, "strict_only_cells": strict_cells,
            "contrasts": contrasts, "usage_scalar_fields_summed": usage, "items": items,
            "physical_attempts": 51, "batch_attempts": {"original01": 1, "recovery02": 3,
                                                              "supplement01": 45, "tail02": 2},
            "mixed_output_budget": True,
            "original_budget_valid_slots": historical_valid,
            "original_budget_glm_persistent_valid": historical_glm_persistent,
            "original_budget_cells": [{key: cell[key] for key in ("model", "simulation_condition", "planned", "valid", "complete")}
                                       for cell in historical_cells],
            "budget_amended_request_ids": list(TAIL_IDS),
            "original_configuration_by_model": read_json(package / "tail02/manifest.json")["original_configuration_by_model"],
            "tail_configuration_by_model": read_json(package / "tail02/manifest.json")["configuration_by_model"],
            "claim_boundary": "Complete 48-slot strict-valid overlay under a mixed GLM output cap; the original 4096-token endpoint remains 46/48.",
        }
    finally:
        _release_stack(publisher, prior, package / "cutoff/original")


def _amended_slot_rows(package: Path, summary: dict[str, Any]) -> list[dict[str, Any]]:
    items = {item["request_id"]: item for item in summary["items"]}
    rows = []
    for rid in TAIL_IDS:
        item = items[rid]
        rec = read_json(package / "tail02/responses" / f"{rid}.json")
        rows.append({"request_id": rid, "p_A": item["p_A"], "posterior_A": item["posterior_A"],
                     "absolute_error": item["absolute_error"], "decision": item["decision"],
                     "action_matches_oracle": item["action_matches_oracle"],
                     "within_1e4": item["within_1e4"],
                     "completion_tokens": rec.get("usage", {}).get("completion_tokens"),
                     "max_tokens": rec["requested_config"]["max_tokens"]})
    return rows


def _report(summary: dict[str, Any], attempts: list[dict[str, Any]], amended: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "verification": "PASS", "study_id": summary["study_id"], "completion": summary["completion"],
        "planned_slots": 48, "selected_responses": summary["selected_responses"],
        "selected_strict_valid": summary["strict_valid"], "invalid_or_missing": summary["invalid_or_missing"],
        "physical_attempts": len(attempts), "batch_attempts": summary["batch_attempts"],
        "unique_slots_attempted": len({item["request_id"] for item in attempts}),
        "mixed_output_budget": True, "original_budget_valid_slots": 46,
        "original_budget_glm_persistent_valid": 10, "budget_amended_request_ids": list(TAIL_IDS),
        "original_budget_glm_max_tokens": 4096, "tail_glm_max_tokens": 16384,
        "complete_cells": sum(cell["complete"] for cell in summary["cells"]),
        "cells": summary["cells"], "contrasts": summary["contrasts"], "amended_slots": amended,
    }


def _fmt(value: Any) -> str:
    return "—" if value is None else f"{value:.8f}"


def _results_text(report: dict[str, Any]) -> str:
    amended_by_id = {row["request_id"]: row for row in report["amended_slots"]}
    h4_tokens = amended_by_id[TAIL_IDS[0]]["completion_tokens"]
    h7_tokens = amended_by_id[TAIL_IDS[1]]["completion_tokens"]
    lines = [
        "# OSI48 completion overlay results", "",
        f"The selected-slot overlay is **{report['selected_strict_valid']}/48 strict-valid** across "
        f"{report['physical_attempts']} physical attempts. It contains 46 retained replies under the original "
        "per-model settings (22 GLM at a 4096-token ceiling and 24 Qwen at 8192), plus two fixed-slot GLM replies "
        "with a 16384-token output ceiling. The 48 prompts are unchanged. This is a "
        "complete mixed-budget overlay; the original-budget endpoint remains 46/48, with GLM Persistent at 10/12.", "",
        "| Model | Condition | Valid / planned | Posterior MSE ↓ | Posterior MAE ↓ | Expected decision loss ↓ | Excess decision loss ↓ |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for cell in report["cells"]:
        lines.append(f"| {cell['model']} | {cell['simulation_condition']} | {cell['valid']}/{cell['planned']} | "
                     f"{_fmt(cell['posterior_mse'])} | {_fmt(cell['posterior_mae'])} | "
                     f"{_fmt(cell['expected_decision_loss'])} | {_fmt(cell['excess_decision_loss'])} |")
    lines += ["", "## Two amended GLM slots", "",
              "| Request | p(A) | Oracle p(A) | Absolute error | Decision | Oracle action match | Within 1e-4 | Output tokens | Cap |",
              "|---|---:|---:|---:|---|---:|---:|---:|---:|"]
    for row in report["amended_slots"]:
        lines.append(f"| {row['request_id']} | {_fmt(row['p_A'])} | {_fmt(row['posterior_A'])} | "
                     f"{_fmt(row['absolute_error'])} | {row['decision']} | {row['action_matches_oracle']} | "
                     f"{row['within_1e4']} | {row['completion_tokens']} | {row['max_tokens']} |")
    lines += ["", "The H7 reply is strict-valid and its action matches the oracle action, while its probability estimate "
              f"does not fall within 1e-4 of the oracle probability. The H4 reply used {h4_tokens} output tokens; "
              f"the H7 reply used {h7_tokens}. Those two outcomes do not establish that the earlier 4096-token truncation was caused by "
              "the cap. The tail IDs were fixed by the prior invalid and unstarted slots; no answer was selected by score.", "",
              "The original-budget endpoint remains incomplete: 46/48 valid slots, including 10/12 GLM Persistent slots. "
              "The mixed-budget overlay completes slot coverage but does not replace that original-budget record. "
              "There are 12 selected stimuli per cell; these calls are not 48 independent task families. No claim is made "
              "about general model capability, internal reasoning, or a causal effect of the output cap.", "",
              "The [attempt ledger](../attempt_ledger.json), [selected-slot summary](summary.json), and "
              "[two amended replies](../tail02/responses/) preserve the audit trail. Run `python -X utf8 -B "
              "scripts/publish_opponent_strategy_completion.py --verify` from the project root.", ""]
    return "\n".join(lines)


def _readme_text(report: dict[str, Any]) -> str:
    return (
        "# Opponent Strategy Inference OSI48 completion overlay\n\n"
        "This package preserves the original cutoff, supplement and two-slot tail as distinct evidence batches. "
        "It includes all 48 exact prompts, selected final-visible replies, all 51 safe physical-attempt receipt sets, "
        "the frozen source code and protocols, parser-derived results, and source-to-public hash mappings. Provider "
        "raw envelopes, hidden reasoning, launch receipts, credentials and machine paths are excluded.\n\n"
        f"The completion status is **{report['completion']}**: {report['selected_strict_valid']}/48 selected strict-valid "
        "slots. The two named GLM tail requests used a 16384-token output ceiling; the other GLM requests used "
        "4096 and Qwen requests used 8192. Their actual completions used 358 and 575 output tokens. The original-budget endpoint remains "
        f"{report['original_budget_valid_slots']}/48. Treat this as a mixed-budget "
        "finite-stimulus result, not a same-budget completion or a general capability claim.\n\n"
        "Start with [results](analysis/RESULTS.md), then read [selected summary](analysis/summary.json), "
        "[slot selection](selection.json), and [physical attempt ledger](attempt_ledger.json). The previous "
        "[original cutoff package](cutoff/README.md) is retained. Source snapshots and the tail amendment are under "
        "`supplement01/inputs/` and `tail02/inputs/`.\n\n"
        "Verify in a clean checkout with `python -X utf8 -B scripts/publish_opponent_strategy_completion.py --verify`. "
        "Verification is offline and uses only this package.\n"
    )


def _publication(package: Path, source: dict[str, Any], batches: dict[str, dict[str, Any]], cutoff: Path,
                 attempt_ledger: list[dict[str, Any]], selection: dict[str, Any]) -> dict[str, Any]:
    entries: dict[str, Any] = {}
    for label in ("supplement01", "tail02"):
        info = batches[label]
        entries[label] = {
            "source_run_id": RUN_NAMES[label],
            "source_manifest_sha256_lf": sha_file(RUNS[label] / "manifest.json"),
            "published_manifest_sha256_lf": sha_file(package / label / "manifest.json"),
            "source_schedule_sha256_lf": sha_file(RUNS[label] / "schedule.json"),
            "published_schedule_sha256_lf": sha_file(package / label / "schedule.json"),
            "source_status_sha256_lf": sha_file(RUNS[label] / "status.json"),
            "published_status_sha256_lf": sha_file(package / label / "status.json"),
            "source_completion_summary_sha256_lf": sha_file(RUNS[label] / "analysis/completion_summary.json"),
            "published_completion_summary_sha256_lf": sha_file(package / label / "analysis/completion_summary.json"),
            "source_freeze_sha256_lf": sha_file(RUNS[label] / "freeze.json"),
            "source_artifacts": info["manifest"].get("source_artifacts", {}),
            "configuration_by_model": info["manifest"].get("configuration_by_model", {}),
            "source_receipt_sha256_lf": info["source_hashes"],
            "published_receipt_sha256_lf": info["published_hashes"],
            "prompt_sha256_lf": {rid: sha_file(within(RUNS[label], row["prompt_path"]))
                                  for rid, row in info["rows"].items()},
        }
    cutoff_publication = source["publication"]
    source_ids = {"original01": RUN_NAMES["original01"], "recovery02": RUN_NAMES["recovery02"],
                  "supplement01": RUN_NAMES["supplement01"], "tail02": RUN_NAMES["tail02"]}
    return {
        "schema_version": 1, "study_id": "opponent_strategy_inference48_20261009",
        "source_run_ids": source_ids, "cutoff_package_freeze_sha256_lf": sha_file(cutoff / "freeze.json"),
        "cutoff_source_run_ids": cutoff_publication["source_run_ids"],
        "batches": entries,
        "cutoff_source_receipt_sha256_lf": {
            label: {folder: cutoff_publication["receipt_sha256_lf"][old][folder]["source"]
                    for folder in ("responses", "dispatches", "prompt_receipts")}
            for old, label in (("original", "original01"), ("recovery", "recovery02"))
        },
        "tail_retained_source_by_id": batches["tail02"]["manifest"]["retained_source_by_id"],
        "tail_retained_artifact_hashes": batches["tail02"]["manifest"]["retained_artifact_hashes"],
        "tail_source_freeze_excluded_content": "inputs/retained/** copied as digest map only; source receipts are published through safe projections",
        "selected_prompt_sha256_lf": {entry["request_id"]: entry["prompt_sha256"] for entry in selection["slots"]},
        "selected_response_sha256_utf8": {
            entry["request_id"]: sha_text(read_json(package / entry["selected_response_path"])["visible_text"])
            for entry in selection["slots"] if entry["selected_response_path"]
        },
        "physical_attempt_total": len(attempt_ledger),
        "configuration_interpretation": {
            "original_glm_max_tokens": 4096, "tail_glm_max_tokens": 16384,
            "affected_request_ids": list(TAIL_IDS), "mixed_output_budget": True,
            "original_budget_endpoint_complete": False,
        },
    }


def _expected_files(package: Path) -> set[str]:
    expected = {"README.md", "publication.json", "attempt_ledger.json", "selection.json",
                "freeze.json", "analysis/RESULTS.md", "analysis/summary.json", "analysis/public_verification.json",
                "selected/schedule.json"}
    cutoff_freeze = read_json(package / "cutoff/freeze.json")
    expected |= {f"cutoff/{relative}" for relative in cutoff_freeze["hashes"]}
    expected.add("cutoff/freeze.json")
    for label in ("supplement01", "tail02"):
        root = package / label
        manifest = read_json(root / "manifest.json")
        freeze_name = "source_freeze.json" if label == "tail02" else "freeze.json"
        source_freeze = read_json(root / freeze_name)
        expected |= {f"{label}/{relative}" for relative in source_freeze["hashes"]
                     if not (label == "tail02" and relative.startswith("inputs/retained/"))}
        expected |= {f"{label}/{name}" for name in ("manifest.json", "schedule.json", "status.json", freeze_name,
                                                        "analysis/completion_summary.json")}
        for folder in ("responses", "dispatches", "prompt_receipts"):
            expected |= {f"{label}/{folder}/{path.stem}.json" for path in (root / folder).glob("*.json")}
    selection = read_json(package / "selection.json")
    for item in selection["slots"]:
        expected.add(f"selected/prompts/{item['request_id']}.txt")
        if item["selected_response_path"]:
            expected.add(item["selected_response_path"])
    return expected


def _verify_publication_mapping(package: Path, source: dict[str, Any],
                                batches: dict[str, dict[str, Any]]) -> dict[str, Any]:
    publication = read_json(package / "publication.json")
    need(publication["source_run_ids"] == RUN_NAMES, "Publication source run IDs differ")
    need(publication["cutoff_source_run_ids"] == source["publication"]["source_run_ids"],
         "Cutoff source run mapping differs")
    need(publication["cutoff_package_freeze_sha256_lf"] == sha_file(package / "cutoff/freeze.json"),
         "Nested cutoff package hash differs")
    expected_cutoff_hashes = {
        label: {folder: source["publication"]["receipt_sha256_lf"][old][folder]["source"]
                for folder in ("responses", "dispatches", "prompt_receipts")}
        for old, label in (("original", "original01"), ("recovery", "recovery02"))
    }
    need(publication["cutoff_source_receipt_sha256_lf"] == expected_cutoff_hashes,
         "Cutoff source receipt hash mapping differs")
    for label in ("supplement01", "tail02"):
        info = batches[label]
        meta = publication["batches"][label]
        root = package / label
        freeze_name = "source_freeze.json" if label == "tail02" else "freeze.json"
        need(meta["source_run_id"] == RUN_NAMES[label], f"{label} source identity differs")
        for source_key, published_key, filename in (
            ("source_manifest_sha256_lf", "published_manifest_sha256_lf", "manifest.json"),
            ("source_schedule_sha256_lf", "published_schedule_sha256_lf", "schedule.json"),
            ("source_status_sha256_lf", "published_status_sha256_lf", "status.json"),
            ("source_completion_summary_sha256_lf", "published_completion_summary_sha256_lf",
             "analysis/completion_summary.json"),
        ):
            digest = sha_file(root / filename)
            need(meta[source_key] == meta[published_key] == digest,
                 f"{label} source/public {filename} hash mapping differs")
        need(meta["source_freeze_sha256_lf"] == sha_file(root / freeze_name),
             f"{label} source freeze mapping differs")
        need(meta["source_artifacts"] == info["manifest"].get("source_artifacts", {})
             and meta["configuration_by_model"] == info["manifest"].get("configuration_by_model", {}),
             f"{label} source artifact/configuration mapping differs")
        need(meta["source_receipt_sha256_lf"] == info["source_hashes"]
             and meta["published_receipt_sha256_lf"] == info["published_hashes"],
             f"{label} source receipt hash mapping differs")
        for folder in ("responses", "dispatches", "prompt_receipts"):
            need(set(meta["published_receipt_sha256_lf"][folder]) == info["sets"][folder],
                 f"{label} published {folder} hash set differs")
            for rid, digest in meta["published_receipt_sha256_lf"][folder].items():
                need(digest == sha_file(root / folder / f"{rid}.json"),
                     f"{label} published {folder} hash mismatch for {rid}")
        for folder in ("dispatches", "prompt_receipts"):
            need(meta["source_receipt_sha256_lf"][folder] == meta["published_receipt_sha256_lf"][folder],
                 f"{label} public {folder} differs from the source receipt")
        expected_prompts = {rid: sha_file(within(root, row["prompt_path"])) for rid, row in info["rows"].items()}
        need(meta["prompt_sha256_lf"] == expected_prompts, f"{label} prompt hash map differs")
    need(publication["tail_retained_source_by_id"] == batches["tail02"]["manifest"]["retained_source_by_id"]
         and publication["tail_retained_artifact_hashes"] == batches["tail02"]["manifest"]["retained_artifact_hashes"],
         "Tail retained-artifact provenance differs")
    need(publication["physical_attempt_total"] == 51, "Publication physical-attempt count differs")
    return publication


def _verify_public(package: Path) -> dict[str, Any]:
    package = package.resolve()
    need(package.is_dir(), "Public OSI48 completion package is missing")
    freeze = read_json(package / "freeze.json")
    need(freeze.get("hash_convention") == "SHA256 with CRLF normalized to LF" and isinstance(freeze.get("hashes"), dict),
         "Unexpected completion package freeze")
    for relative, digest in freeze["hashes"].items():
        path = within(package, relative)
        need(path.is_file() and sha_file(path) == digest, f"Public file hash mismatch: {relative}")
        _scan(path)
    _scan(package / "freeze.json")
    actual = {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()}
    expected = _expected_files(package) | {"freeze.json"}
    need(actual == expected, f"Public file allowlist differs: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
    need(set(freeze["hashes"]) == expected - {"freeze.json"}, "Completion freeze does not cover the full allowlist")
    need(read_json(package / "publication.json")["study_id"] == "opponent_strategy_inference48_20261009",
         "Publication study identity differs")
    publisher = _load_publisher()
    cutoff_report = publisher._verify_public(package / "cutoff")
    need(cutoff_report["physical_attempts"] == 4, "Nested cutoff package did not verify")

    source = _cutoff_info(package / "cutoff")
    batches: dict[str, dict[str, Any]] = {}
    for label in ("supplement01", "tail02"):
        root = package / label
        manifest = read_json(root / "manifest.json")
        schedule = read_json(root / "schedule.json")
        freeze_name = "source_freeze.json" if label == "tail02" else "freeze.json"
        freeze_batch = read_json(root / freeze_name)
        status = read_json(root / "status.json")
        need(manifest["requests"] == schedule, f"{label} manifest and schedule differ")
        rows = {row["request_id"]: row for row in schedule}
        need(len(rows) == len(schedule), f"{label} schedule has duplicate IDs")
        for relative, digest in freeze_batch["hashes"].items():
            if label == "tail02" and relative.startswith("inputs/retained/"):
                suffix = relative[len("inputs/retained/"):]
                source_run, folder, filename = suffix.split("/", 2)
                source_label = next((key for key, name in RUN_NAMES.items() if name == source_run), None)
                need(source_label in {"recovery02", "supplement01"}, "Tail retained hash names an unexpected source")
                rid = Path(filename).stem
                if source_label in ("original01", "recovery02"):
                    old = "original" if source_label == "original01" else "recovery"
                    source_digest = source["publication"]["receipt_sha256_lf"][old][folder]["source"].get(rid)
                else:
                    source_digest = read_json(package / "publication.json")["batches"][source_label]["source_receipt_sha256_lf"][folder].get(rid)
                need(source_digest == digest, f"Tail retained input hash does not map to {source_label}/{folder}/{rid}")
            else:
                path = within(root, relative)
                need(path.is_file() and sha_file(path) == digest, f"{label} frozen file changed: {relative}")
        for relative, digest in manifest.get("source_artifacts", {}).items():
            path = within(root / "inputs", relative)
            need(path.is_file() and sha_file(path) == digest, f"{label} source snapshot changed: {relative}")
        sets = {folder: {p.stem for p in (root / folder).glob("*.json")}
                for folder in ("responses", "dispatches", "prompt_receipts")}
        need(sets["dispatches"] == sets["prompt_receipts"] and sets["responses"] <= sets["dispatches"],
             f"{label} receipt sets do not align")
        prior, study, analyzer, _ = _load_stack(publisher, root)
        source_hashes = read_json(package / "publication.json")["batches"][label]["source_receipt_sha256_lf"]
        published_hashes = read_json(package / "publication.json")["batches"][label]["published_receipt_sha256_lf"]
        try:
            for rid in sets["dispatches"]:
                row = rows[rid]
                prompt = within(root, row["prompt_path"])
                dispatch = read_json(root / "dispatches" / f"{rid}.json")
                prompt_rec = read_json(root / "prompt_receipts" / f"{rid}.json")
                digest = sha_file(prompt)
                need(prompt_rec == {"request_id": rid, "prompt_sha256": digest,
                                    "created_utc": prompt_rec["created_utc"]}, f"{label} prompt receipt mismatch")
                need(dispatch == row | {"prompt_sha256": digest, "dispatched_utc": dispatch["dispatched_utc"]},
                     f"{label} dispatch mismatch")
                for folder in ("dispatches", "prompt_receipts"):
                    need(published_hashes[folder].get(rid) == sha_file(root / folder / f"{rid}.json"),
                         f"{label} published {folder} hash mismatch")
                if rid in sets["responses"]:
                    path = root / "responses" / f"{rid}.json"
                    request_config = manifest["configuration_by_model"][row["model"]] if label == "tail02" else None
                    projection = _project_response(path, row, study, prompt, request_config)
                    need(projection == read_json(path), f"{label} safe response projection changed for {rid}")
                    need(source_hashes["responses"].get(rid) and
                         published_hashes["responses"].get(rid) == sha_file(path),
                         f"{label} response hash mapping is incomplete for {rid}")
        finally:
            _release_stack(publisher, prior, root)
        batches[label] = {"manifest": manifest, "schedule": schedule, "status": status, "rows": rows,
                          "sets": sets, "source_hashes": source_hashes, "published_hashes": published_hashes}

    full_schedule = source["schedule"]["original01"]
    need(len(full_schedule) == 48 and source["schedule"]["recovery02"] == full_schedule,
         "Cutoff schedules differ or do not contain 48 slots")
    need({row["request_id"] for row in batches["tail02"]["schedule"]} == set(TAIL_IDS),
         "Tail schedule does not contain the two amended slots")
    need(batches["supplement01"]["manifest"]["retained_valid_ids"] == [
        "OSI_QWEN_PERSISTENT_H7_ONESB_R2", "OSI_QWEN_REFRESHED_H4_ONESA_R2"],
        "Supplement retained-valid selection changed")
    supplement_valid_ids = {
        rid for rid in batches["supplement01"]["sets"]["responses"]
        if read_json(package / "supplement01/responses" / f"{rid}.json")["parse_status"] == "valid"
        and read_json(package / "supplement01/responses" / f"{rid}.json")["completion_parse_status"] == "valid"
    }
    need(batches["tail02"]["manifest"]["mixed_output_budget"] is True
         and set(batches["tail02"]["manifest"]["retained_source_by_id"]) ==
         set(batches["supplement01"]["manifest"]["retained_valid_ids"]) | supplement_valid_ids,
         "Tail retained-source mapping does not identify the 46 pre-tail strict-valid slots")
    tail = batches["tail02"]["manifest"]
    need(tail["study_id"] == TAIL_STUDY_ID and tail["configuration_by_model"]["glm-5.3"]["max_tokens"] == 16384
         and tail["original_configuration_by_model"]["glm-5.3"]["max_tokens"] == 4096,
         "Tail budget amendment does not match the explicit mixed-budget overlay")
    need(all(sha_file(package / "tail02" / row["prompt_path"]) ==
             sha_file(package / "cutoff/original" / row["prompt_path"])
             for row in batches["tail02"]["schedule"]), "Tail prompt bytes differ from the frozen prompt")
    for rel, digest in tail["retained_artifact_hashes"].items():
        normalized = "inputs/retained/" + rel.replace("\\", "/")
        need(freeze_batch["hashes"].get(normalized) == digest, f"Tail retained hash is not frozen: {rel}")

    publication = _verify_publication_mapping(package, source, batches)
    need(read_json(package / "selected/schedule.json") == full_schedule,
         "Selected schedule differs from the frozen 48-slot schedule")
    attempt_ledger = read_json(package / "attempt_ledger.json")["attempts"]
    need(len(attempt_ledger) == 51, "Physical attempt ledger does not contain 51 attempts")
    need(attempt_ledger == _attempt_rows(package, source, batches),
         "Physical attempt ledger does not reproduce from the safe receipt files")
    need(read_json(package / "selection.json")["planned_slots"] == 48, "Selection does not retain the 48-slot schedule")
    selection = read_json(package / "selection.json")
    need(len(selection["slots"]) == 48 and selection["selected_strict_valid"] == 48,
         "Published selection is not 48/48 strict-valid")
    selection_calc = _selection(package, source, batches, attempt_ledger, full_schedule)
    need(selection_calc == selection, "Selected response map does not reproduce from physical receipts")
    summary = _analysis(package, source, batches, selection, full_schedule, publisher)
    saved_summary = read_json(package / "analysis/summary.json")
    need(summary == saved_summary, "Selected summary does not reproduce from the bundled analyzer")
    need(summary["selected_responses"] == 48 and summary["strict_valid"] == 48,
         "Selected summary is not a 48/48 strict-valid overlay")
    need(summary["original_budget_valid_slots"] == 46 and summary["original_budget_glm_persistent_valid"] == 10,
         "Original-budget completeness boundary changed")
    tail_summary = read_json(package / "tail02/analysis/completion_summary.json")
    inner = tail_summary["analysis_summary"]
    need(inner["completion"] == "COMPLETE_VALID" and inner["valid"] == inner["strict_valid"] == 48
         and inner["format_exception_count"] == 0, "Tail source analysis does not confirm 48 strict-valid slots")
    for key in ("items", "cells", "strict_only_cells", "contrasts", "usage_scalar_fields_summed"):
        need(summary[key] == inner[key], f"Selected {key} differ from the tail completion analysis")
    need(tail_summary["physical_attempts"] == {"original01": 1, "recovery02": 3, "supplement01": 45, "tail02": 2}
         and tail_summary["physical_attempt_total"] == 51 and tail_summary["mixed_output_budget"] is True
         and tail_summary["budget_amended_request_ids"] == list(TAIL_IDS),
         "Tail completion provenance does not match the 51-attempt amended overlay")
    need(publication["selected_prompt_sha256_lf"] == {
        slot["request_id"]: sha_file(package / "selected/prompts" / f"{slot['request_id']}.txt")
        for slot in selection["slots"]}, "Selected prompt hash mapping differs")
    need(publication["selected_response_sha256_utf8"] == {
        slot["request_id"]: sha_text(read_json(package / slot["selected_response_path"])["visible_text"])
        for slot in selection["slots"] if slot["selected_response_path"]},
        "Selected visible-text hash mapping differs")
    amended = _amended_slot_rows(package, summary)
    report = _report(summary, attempt_ledger, amended)
    need(read_json(package / "analysis/public_verification.json") == report,
         "Public verification report does not reproduce")
    need((package / "analysis/RESULTS.md").read_text(encoding="utf-8") == _results_text(report),
         "Public results text does not reproduce")
    need((package / "README.md").read_text(encoding="utf-8") == _readme_text(report),
         "Public README does not reproduce")
    return report


def export() -> dict[str, Any]:
    need(not PUBLIC.exists(), "Public OSI48 completion package already exists; export is write-once")
    need(CUTOFF_SOURCE.is_dir() and all(path.is_dir() for path in RUNS.values()),
         "Required cutoff, supplement, or tail source package is unavailable")
    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    publisher = _load_publisher()
    with tempfile.TemporaryDirectory(prefix="osi48_completion_export_", dir=PUBLIC.parent) as temp:
        stage = Path(temp) / PUBLIC.name
        stage.mkdir()
        shutil.copytree(CUTOFF_SOURCE, stage / "cutoff")
        publisher._verify_public(stage / "cutoff")
        cutoff = _cutoff_info(stage / "cutoff")
        batches = {label: _copy_source_batch(RUNS[label], label, stage / label, publisher)
                   for label in ("supplement01", "tail02")}
        need(batches["supplement01"]["status"]["provider_requests"] == 45
             and batches["tail02"]["status"]["provider_requests"] == 2,
             "Physical attempt counts do not match the 45-call supplement and two-call tail")
        need(len(cutoff["ledger"]["attempts"]) == 4, "Cutoff attempt ledger changed")
        tail_summary = read_json(stage / "tail02/analysis/completion_summary.json")
        need(tail_summary["mixed_output_budget"] is True and tail_summary["physical_attempt_total"] == 51
             and tail_summary["analysis_summary"]["strict_valid"] == 48,
             "Tail does not record the completed mixed-budget overlay")
        full_schedule = cutoff["schedule"]["original01"]
        attempt_ledger = _attempt_rows(stage, cutoff, batches)
        write_json(stage / "attempt_ledger.json", {"schema_version": 1,
            "study_id": "opponent_strategy_inference48_20261009", "attempts": attempt_ledger})
        write_json(stage / "selected/schedule.json", full_schedule)
        selection = _selection(stage, cutoff, batches, attempt_ledger, full_schedule)
        write_json(stage / "selection.json", selection)
        summary = _analysis(stage, cutoff, batches, selection, full_schedule, publisher)
        need(summary["selected_responses"] == summary["strict_valid"] == 48,
             "Recomputed selection is not 48/48 strict-valid")
        write_json(stage / "analysis/summary.json", summary)
        amended = _amended_slot_rows(stage, summary)
        report = _report(summary, attempt_ledger, amended)
        write_json(stage / "analysis/public_verification.json", report)
        write_text(stage / "analysis/RESULTS.md", _results_text(report))
        write_text(stage / "README.md", _readme_text(report))
        publication = _publication(stage, cutoff, batches, stage / "cutoff", attempt_ledger, selection)
        write_json(stage / "publication.json", publication)
        expected = _expected_files(stage) - {"freeze.json"}
        actual = {path.relative_to(stage).as_posix() for path in stage.rglob("*") if path.is_file()}
        need(actual == expected, f"Export staging files differ: extra={sorted(actual-expected)} missing={sorted(expected-actual)}")
        for path in stage.rglob("*"):
            if path.is_file():
                _scan(path)
        hashes = {path.relative_to(stage).as_posix(): sha_file(path)
                  for path in sorted(stage.rglob("*")) if path.is_file()}
        write_json(stage / "freeze.json", {"hash_convention": "SHA256 with CRLF normalized to LF", "hashes": hashes})
        need(not PUBLIC.exists(), "Public package appeared during export; refusing replacement")
        stage.rename(PUBLIC)
    return _verify_public(PUBLIC)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--export", action="store_true", help="Create the public safe projection once from frozen runs")
    modes.add_argument("--verify", action="store_true", help="Verify the published package offline (default)")
    args = parser.parse_args()
    try:
        report = export() if args.export else _verify_public(PUBLIC)
    except (AssertionError, OSError, ValueError, KeyError, TypeError, PublicationError) as exc:
        parser.exit(1, f"publication error: {exc}\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
