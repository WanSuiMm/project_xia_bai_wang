"""Offline allowlisted export and public-only verification for the JES32 completion."""
from __future__ import annotations

import argparse
import hashlib
import importlib
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
ORIGINAL_RUN = BASE / "runs/opencode_go_20261008_joint_epistemic_simulation32_01"
SUPPLEMENT_RUN = BASE / "runs/opencode_go_20261009_joint_epistemic_simulation32_supplement01"
PUBLIC = BASE / "published_runs/go_joint_epistemic_simulation32_completion_20261009"
ORIGINAL_ID = ORIGINAL_RUN.name
SUPPLEMENT_ID = SUPPLEMENT_RUN.name
STUDY_ID = "joint_epistemic_simulation32_20261008"
TOTAL = 32
MODELS = ("glm-5.3", "qwen3.8-max")
CONDITIONS = ("MARGINAL", "JOINT")
EXCESS_BRIER_LIMIT = 0.01

RESPONSE_KEYS = {
    "request_id", "model", "kind", "case_id", "prompt_sha256", "status", "sent_utc",
    "visible_text", "parsed", "parse_status", "returned_model", "usage", "finish_reason",
    "http_status", "elapsed_seconds", "captured_utc", "simulation_condition",
    "bluffer_condition", "judge_condition",
}
SUPPLEMENT_RESPONSE_KEYS = RESPONSE_KEYS | {
    "completion_parsed", "completion_parse_status", "format_acceptance",
}
PROMPT_RECEIPT_KEYS = {"request_id", "prompt_sha256", "created_utc"}
DISPATCH_EXTRA_KEYS = {"prompt_sha256", "dispatched_utc"}
ORIGINAL_MANIFEST_KEYS = {
    "schema_version", "study_id", "created_utc", "planned_provider_requests",
    "configuration_by_model", "randomization_seed", "timeout_seconds", "max_concurrency",
    "requests", "source_artifacts",
}
SUPPLEMENT_MANIFEST_KEYS = {
    "schema_version", "study_id", "created_utc", "parent_run_name", "parent_artifact_hashes",
    "retained_valid_ids", "planned_provider_requests", "requests", "configuration_by_model",
    "timeout_seconds", "max_concurrency", "source_artifacts", "format_amendment",
    "selection_rule", "retry_policy",
}
ORIGINAL_STATUS_KEYS = {
    "state", "halt_reason", "planned", "provider_requests", "response_count", "valid", "updated_utc",
}
SUPPLEMENT_STATUS_KEYS = ORIGINAL_STATUS_KEYS | {
    "strict_valid", "identical_duplicate_trailer_count", "retained_original_valid", "completion_valid_slots",
}
FREEZE_KEYS = {"schema_version", "created_utc", "experimental_requests_at_freeze", "hashes"}
SUPPLEMENT_FREEZE_KEYS = {"created_utc", "experimental_requests_at_freeze", "hashes"}

FORBIDDEN_KEYS = {
    "authorization", "api_key", "x-api-key", "headers", "session_id", "session_ids",
    "account_id", "pid", "host", "absolute_path", "provenance_private", "reasoning_content",
    "hidden_reasoning", "raw_provider_body", "x-opencode-session", "launch_receipt",
    "stdout_path", "stderr_path", "run_path",
}
SCAN_PATTERNS = {
    "credential": r"oc_sk_[A-Za-z0-9_-]+|\bsk-[A-Za-z0-9_-]{20,}|\bgh[pousr]_[A-Za-z0-9_]{20,}|\bxox[baprs]-[A-Za-z0-9-]{20,}|(?i:Bearer\s+)[A-Za-z0-9._-]{16,}",
    "machine_path": r"(?i)\b[A-Z]:[\\/]|/(?:Users|home|mnt/[a-z])/",
    "private_session_url": r"https?://(?:arena\.ai/c/|chatgpt\.com/c/)",
    "ip_address": r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])",
}


class PublicationError(RuntimeError):
    """Raised when the frozen source evidence or public projection is inconsistent."""


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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(json_bytes(value))


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(value.encode("utf-8"))


def copy_new(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    need(not destination.exists(), f"Refusing to replace staged file: {destination.name}")
    shutil.copyfile(source, destination)


def within(root: Path, relative: str) -> Path:
    result = (root / relative).resolve()
    result.relative_to(root.resolve())
    need(result != root.resolve(), "Expected a file path, not a directory root")
    return result


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec is not None and spec.loader is not None, f"Cannot load frozen analyzer: {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _fresh_source_analyses() -> tuple[dict[str, Any], dict[str, Any]]:
    """Recompute both frozen analyses from the local source runs, without writing."""
    scripts = ROOT / "scripts"
    names = (
        "run_strategic_qualification", "run_counterfactual_source_boundary",
        "run_joint_epistemic_simulation", "run_joint_epistemic_supplement",
        "analyze_joint_epistemic_simulation", "analyze_joint_epistemic_supplement",
    )
    prior = {name: sys.modules.pop(name, None) for name in names}
    sys.path.insert(0, str(scripts))
    try:
        original_analyzer = _load_module(
            "analyze_joint_epistemic_simulation", scripts / "analyze_joint_epistemic_simulation.py"
        )
        supplement_analyzer = _load_module(
            "analyze_joint_epistemic_supplement", scripts / "analyze_joint_epistemic_supplement.py"
        )
        original = original_analyzer.build_summary(ORIGINAL_RUN)
        supplement = supplement_analyzer.build_summary(SUPPLEMENT_RUN)
        return original, supplement
    finally:
        try:
            sys.path.remove(str(scripts))
        except ValueError:
            pass
        for name in names:
            sys.modules.pop(name, None)
        for name, module in prior.items():
            if module is not None:
                sys.modules[name] = module


def _assert_exact_keys(value: Any, expected: set[str], where: str) -> dict[str, Any]:
    need(isinstance(value, dict), f"{where} must be an object")
    need(set(value) == expected, f"{where} has an unreviewed or missing field")
    return value


def _check_source_inputs(run: Path, freeze: dict[str, Any], where: str) -> None:
    need(isinstance(freeze.get("hashes"), dict), f"{where} freeze hashes must be an object")
    need(freeze.get("experimental_requests_at_freeze") == 0,
         f"{where} freeze does not record zero requests at freeze")
    for relative, digest in freeze["hashes"].items():
        need(isinstance(relative, str) and not Path(relative).is_absolute(),
             f"{where} freeze contains a non-relative file path")
        need(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
             f"{where} freeze contains an invalid SHA256")
        path = within(run, relative)
        need(path.is_file() and sha_file(path) == digest,
             f"{where} frozen input changed: {relative}")


def _assert_manifest_schedule(manifest: dict[str, Any], schedule: Any, where: str) -> list[dict[str, Any]]:
    need(isinstance(schedule, list), f"{where} schedule must be a list")
    need(manifest.get("requests") == schedule, f"{where} schedule differs from manifest.requests")
    need(all(isinstance(row, dict) for row in schedule), f"{where} schedule rows must be objects")
    return schedule


def _safe_source_metadata(original: dict[str, Any], supplement: dict[str, Any]) -> None:
    _assert_exact_keys(original, ORIGINAL_MANIFEST_KEYS, "original manifest")
    _assert_exact_keys(supplement, SUPPLEMENT_MANIFEST_KEYS, "supplement manifest")
    need(original["study_id"] == STUDY_ID and original["planned_provider_requests"] == TOTAL,
         "Original manifest does not identify the frozen 32-slot study")
    need(supplement["study_id"] == "joint_epistemic_simulation32_supplement_20261009",
         "Supplement manifest does not identify the frozen completion overlay")
    need(supplement["parent_run_name"] == ORIGINAL_ID, "Supplement parent run does not match the original")
    need(supplement["planned_provider_requests"] == 30, "Supplement must retain its 30-slot schedule")
    need(original["configuration_by_model"] == supplement["configuration_by_model"],
         "Original and supplement model configurations differ")
    need(set(original["configuration_by_model"]) == set(MODELS), "Unexpected model configuration")
    for source_map in (original["source_artifacts"], supplement["source_artifacts"]):
        need(isinstance(source_map, dict), "source_artifacts must be an object")
        for path, digest in source_map.items():
            need(isinstance(path, str) and not Path(path).is_absolute(),
                 "source_artifacts contains a non-relative path")
            need(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
                 "source_artifacts contains an invalid SHA256")


def _copy_pre_request_freeze(run: Path, label: str, freeze: dict[str, Any], stage: Path) -> None:
    """Copy only frozen inputs named by the source freeze, sharing exact prompts."""
    for relative in freeze["hashes"]:
        source = within(run, relative)
        if relative.startswith("prompts/"):
            destination = within(stage, relative)
        else:
            destination = within(stage, f"{label}/{relative}")
        if destination.exists():
            need(sha_file(destination) == sha_file(source),
                 f"Original and supplement frozen inputs differ: {relative}")
        else:
            copy_new(source, destination)


def _copy_attempt_receipts(run: Path, label: str, schedule: list[dict[str, Any]],
                           supplement: bool, stage: Path) -> dict[str, dict[str, dict[str, str]]]:
    rows = {row["request_id"]: row for row in schedule}
    expected_dispatch_keys = set(schedule[0]) | DISPATCH_EXTRA_KEYS
    hashes: dict[str, dict[str, dict[str, str]]] = {
        "responses": {}, "dispatches": {}, "prompt_receipts": {},
    }
    file_ids: dict[str, set[str]] = {}
    for folder in hashes:
        paths = sorted((run / folder).glob("*.json"))
        file_ids[folder] = {path.stem for path in paths}
        for path in paths:
            rid = path.stem
            need(rid in rows, f"{label}/{folder} contains an unscheduled request")
            receipt = read_json(path)
            if folder == "responses":
                _assert_exact_keys(receipt, SUPPLEMENT_RESPONSE_KEYS if supplement else RESPONSE_KEYS,
                                   f"{label}/{folder}/{rid}")
            elif folder == "dispatches":
                _assert_exact_keys(receipt, expected_dispatch_keys, f"{label}/{folder}/{rid}")
            else:
                _assert_exact_keys(receipt, PROMPT_RECEIPT_KEYS, f"{label}/{folder}/{rid}")
            destination = stage / label / folder / path.name
            copy_new(path, destination)
            hashes[folder][rid] = {
                "source_sha256_lf": sha_file(path),
                "published_sha256_lf": sha_file(destination),
            }
    need(file_ids["responses"] == file_ids["dispatches"] == file_ids["prompt_receipts"],
         f"{label} receipt/dispatch/prompt-receipt sets differ")
    return hashes


def _summaries_and_source_paths() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    original_manifest = read_json(ORIGINAL_RUN / "manifest.json")
    supplement_manifest = read_json(SUPPLEMENT_RUN / "manifest.json")
    original_freeze = read_json(ORIGINAL_RUN / "freeze.json")
    supplement_freeze = read_json(SUPPLEMENT_RUN / "freeze.json")
    need(_fresh_source_analyses() == (
        read_json(ORIGINAL_RUN / "analysis/summary.json"),
        read_json(SUPPLEMENT_RUN / "analysis/completion_summary.json"),
    ), "Frozen analyzer output differs from the registered source summaries")
    _safe_source_metadata(original_manifest, supplement_manifest)
    _assert_exact_keys(original_freeze, FREEZE_KEYS, "original freeze")
    _assert_exact_keys(supplement_freeze, SUPPLEMENT_FREEZE_KEYS, "supplement freeze")
    _check_source_inputs(ORIGINAL_RUN, original_freeze, "original")
    _check_source_inputs(SUPPLEMENT_RUN, supplement_freeze, "supplement")
    return original_manifest, supplement_manifest, original_freeze, supplement_freeze


def _validate_source_completion(original_manifest: dict[str, Any], supplement_manifest: dict[str, Any],
                                original_summary: dict[str, Any], completion_summary: dict[str, Any],
                                original_status: dict[str, Any], supplement_status: dict[str, Any]) -> None:
    need(original_summary.get("analysis_status") == "incomplete"
         and original_summary.get("overall_gate") == "INCOMPLETE"
         and original_summary.get("valid_response_count") == 2
         and original_summary.get("dispatched_calls") == 3
         and original_summary.get("response_receipt_count") == 3,
         "Registered original analysis must remain incomplete at 2/3 attempted")
    need(original_status.get("state") == "HALTED"
         and original_status.get("provider_requests") == 3
         and original_status.get("response_count") == 3
         and original_status.get("valid") == 2,
         "Original status does not preserve its 3-attempt halt")
    need(completion_summary.get("analysis_status") == "complete"
         and completion_summary.get("completion_complete_32_valid") is True
         and completion_summary.get("completion_valid_response_count") == 32,
         "Completion overlay does not contain all 32 fixed slots")
    need(completion_summary.get("physical_attempts") == {
        "parent_attempt_count": 3,
        "parent_response_receipt_count": 3,
        "parent_valid_count": 2,
        "parent_invalid_count": 1,
        "parent_missing_slot_count": 29,
        "supplement_attempt_count": 30,
        "supplement_response_receipt_count": 30,
        "combined_physical_attempt_count": 33,
        "supplement_unattempted_request_ids": [],
        "original_invalid_request_ids_excluded": ["JG_GLM_JJ_11_00"],
        "retained_original_valid_request_ids": ["JG_GLM_JM_10_11", "JG_QWEN_JM_01_00"],
    }, "Completion overlay attempt ledger differs from the frozen 3+30 selection")
    need(completion_summary.get("narrow_normalization_counts", {}).get("valid_normalized_response_count") == 0
         and completion_summary.get("narrow_normalization_counts", {}).get("request_ids") == [],
         "The completion overlay must preserve zero normalized supplement responses")
    need(completion_summary.get("strict_only_sensitivity", {}).get("valid_response_count") == 32,
         "Strict-only sensitivity does not retain all 32 selected responses")
    need(supplement_status.get("state") == "COMPLETE_30_ATTEMPTED"
         and supplement_status.get("provider_requests") == 30
         and supplement_status.get("response_count") == 30
         and supplement_status.get("valid") == 30
         and supplement_status.get("strict_valid") == 30,
         "Supplement status does not report 30 strict-valid attempts")
    need(completion_summary.get("overall_gate") == "FAIL",
         "The completed finite-cell gate must preserve its FAIL verdict")
    need(original_manifest.get("configuration_by_model") == completion_summary.get("configuration_by_model"),
         "Original configuration differs from the completion analysis")


def _attempt_ledger(original_schedule: list[dict[str, Any]], supplement_schedule: list[dict[str, Any]],
                    original_summary: dict[str, Any], completion_summary: dict[str, Any],
                    source_receipt_hashes: dict[str, dict[str, dict[str, dict[str, str]]]]) -> dict[str, Any]:
    original_rows = {row["request_id"]: row for row in original_schedule}
    original_analysis_rows = {row["request_id"]: row for row in original_summary["response_rows"]}
    completion_rows = {row["request_id"]: row for row in completion_summary["response_rows"]}
    original_ids = set(source_receipt_hashes["original"]["responses"])
    supplement_ids = set(source_receipt_hashes["supplement"]["responses"])
    retained = set(completion_summary["physical_attempts"]["retained_original_valid_request_ids"])
    attempts: list[dict[str, Any]] = []
    for label, ids in (("original", original_ids), ("supplement", supplement_ids)):
        for rid in sorted(ids, key=lambda value: original_rows[value]["schedule_index"]):
            row = original_rows[rid]
            selected = rid in retained if label == "original" else True
            if label == "original":
                classification = original_analysis_rows[rid]
                strict_state = classification["status"]
                invalid_reason = classification.get("invalid_reason")
                strict_parse_status = classification.get("raw_parse_status")
                completion_parse_status = None
                format_acceptance = "strict" if selected else None
                selection_role = "retained_original_strict_valid" if selected else "original_strict_invalid_excluded"
            else:
                classification = completion_rows[rid]
                strict_state = "valid"
                invalid_reason = classification.get("parent_invalid_reason")
                strict_parse_status = classification.get("raw_parse_status")
                completion_parse_status = classification.get("completion_parse_status")
                format_acceptance = classification.get("format_acceptance")
                selection_role = "supplement_first_attempt_selected"
            public_path = f"{label}/responses/{rid}.json"
            attempts.append({
                "run_role": label,
                "request_id": rid,
                "schedule_index": row["schedule_index"],
                "attempt_number_for_slot": (2 if label == "supplement" and rid in original_ids else 1),
                "strict_state": strict_state,
                "original_invalid_reason": invalid_reason,
                "raw_parse_status": strict_parse_status,
                "completion_parse_status": completion_parse_status,
                "format_acceptance": format_acceptance,
                "selection_role": selection_role,
                "selected_for_completion": selected,
                "receipt_path": public_path,
                "source_receipt_sha256_lf": source_receipt_hashes[label]["responses"][rid]["source_sha256_lf"],
                "published_receipt_sha256_lf": source_receipt_hashes[label]["responses"][rid]["published_sha256_lf"],
            })
    slots = []
    for row in sorted(original_schedule, key=lambda value: value["schedule_index"]):
        rid = row["request_id"]
        selected_row = completion_rows[rid]
        source = selected_row["selection_source"]
        selected_run = "original" if source == "original_strict_valid" else "supplement"
        selected_path = f"{selected_run}/responses/{rid}.json"
        original_item = original_analysis_rows[rid]
        count = int(rid in original_ids) + int(rid in supplement_ids)
        slots.append({
            "request_id": rid,
            "schedule_index": row["schedule_index"],
            "model": row["model"],
            "simulation_condition": row["simulation_condition"],
            "prior_predictive_weight": row["prior_predictive_weight"],
            "posterior_A": row["posterior_A"],
            "original_strict_status": original_item["status"],
            "original_invalid_reason": original_item.get("invalid_reason"),
            "original_attempted": rid in original_ids,
            "supplement_attempted": rid in supplement_ids,
            "physical_attempt_count_for_slot": count,
            "selection_source": source,
            "selected_attempt_path": selected_path,
            "format_acceptance": selected_row.get("format_acceptance"),
        })
    need(len(attempts) == 33 and len(slots) == TOTAL, "Attempt ledger must contain 33 attempts and 32 slots")
    return {
        "schema_version": 1,
        "original_run_id": ORIGINAL_ID,
        "supplement_run_id": SUPPLEMENT_ID,
        "physical_attempt_count": len(attempts),
        "fixed_slot_count": len(slots),
        "attempts": attempts,
        "completion_slots": slots,
        "selection_rule": "Retain the two original strict-valid first slots; exclude the original strict-invalid third receipt; use the first supplement attempt for each of the other 30 fixed slots.",
    }


def _results_markdown(original: dict[str, Any], completion: dict[str, Any]) -> str:
    cells = {
        (cell["model"], cell["simulation_condition"]): cell
        for cell in completion["cells"]
    }
    lines = [
        "# JES32 completion results",
        "",
        "The original frozen run remains `INCOMPLETE`: it scheduled 32 requests, attempted the first three, and produced two strict-valid receipts plus one strict-invalid receipt. The other 29 slots were not dispatched in that run.",
        "",
        "The separately frozen supplement attempted the 30 slots not retained from the original. The completion overlay therefore has 32 selected strict-valid slots from 33 physical attempts. It retains the first two original receipts, excludes the original third invalid receipt, and selects one supplement attempt for each remaining slot. No supplement response used the narrow duplicate-trailer normalization.",
        "",
        "| Model | Condition | Positive-support packets | Selected valid | Primary excess Brier | Gate |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for model in MODELS:
        for condition in CONDITIONS:
            cell = cells[(model, condition)]
            lines.append(
                f"| {model} | {condition} | {cell['expected_packets']} | {cell['valid_packets']} | "
                f"{cell['primary_excess_brier']:.12f} | {'PASS' if cell['gate_pass'] else 'FAIL'} |"
            )
    lines.extend([
        "",
        f"The finite-cell gate is **{completion['overall_gate']}**. GLM-5.3/MARGINAL excess Brier is "
        f"{cells[('glm-5.3', 'MARGINAL')]['primary_excess_brier']:.12f}, above the frozen 0.01 limit. "
        "This is a finite known-mechanism Judge qualification over the enumerated packets; it does not establish population calibration, population Theory of Mind, Actor strategy, or general model performance.",
        "",
        "The original canonical analysis is preserved separately in [original summary](original_summary.json). The completion overlay and strict-only sensitivity are in [completion summary](completion_summary.json). The exact prompts, all 33 safe final-visible response receipts, and their dispatch ledgers are secondary evidence.",
        "",
        "The public-only check verifies frozen hashes, source and supplement schedules, receipt bindings, raw strict parsing, the zero-normalization fields, all 32 weights, and each published primary aggregate. Run `python -X utf8 -B scripts/publish_joint_epistemic_simulation.py --verify` from the project root.",
        "",
    ])
    need(original.get("analysis_status") == "incomplete", "Original summary unexpectedly changed")
    return "\n".join(lines)


def _read_public_parsers(package: Path):
    """Load only the bundled frozen parser sources; this path performs no I/O outside package."""
    inputs = package / "supplement/inputs"
    names = (
        "run_strategic_qualification", "run_counterfactual_source_boundary",
        "run_joint_epistemic_simulation", "run_joint_epistemic_supplement",
        "analyze_joint_epistemic_simulation", "analyze_joint_epistemic_supplement",
    )
    prior = {name: sys.modules.pop(name, None) for name in names}
    sys.path.insert(0, str(inputs))
    try:
        study = importlib.import_module("run_joint_epistemic_simulation")
        supplement = importlib.import_module("run_joint_epistemic_supplement")
        original_analysis = importlib.import_module("analyze_joint_epistemic_simulation")
        return study, supplement, original_analysis
    except Exception:
        try:
            sys.path.remove(str(inputs))
        except ValueError:
            pass
        for name in names:
            sys.modules.pop(name, None)
        for name, module in prior.items():
            if module is not None:
                sys.modules[name] = module
        raise


def _release_public_parsers(package: Path, prior: dict[str, Any]) -> None:
    inputs = str(package / "supplement/inputs")
    try:
        sys.path.remove(inputs)
    except ValueError:
        pass
    for name in prior:
        sys.modules.pop(name, None)
        if prior[name] is not None:
            sys.modules[name] = prior[name]


def _source_artifact_path(package: Path, label: str, relative: str) -> Path:
    if relative.startswith("prompts/"):
        return within(package, relative)
    return within(package, f"{label}/{relative}")


def _expected_package_files(package: Path, ledger: dict[str, Any]) -> set[str]:
    expected = {
        "README.md", "publication.json", "attempt_ledger.json",
        "original/manifest.json", "original/schedule.json", "original/freeze.json",
        "original/status.json", "original/oracle_packets.json",
        "supplement/manifest.json", "supplement/schedule.json", "supplement/parent_schedule.json",
        "supplement/freeze.json", "supplement/status.json",
        "analysis/original_summary.json", "analysis/completion_summary.json",
        "analysis/RESULTS.md", "analysis/public_verification.json",
    }
    for label in ("original", "supplement"):
        freeze = read_json(package / f"{label}/freeze.json")
        for relative in freeze["hashes"]:
            expected.add(relative if relative.startswith("prompts/") else f"{label}/{relative}")
    for attempt in ledger["attempts"]:
        label, rid = attempt["run_role"], attempt["request_id"]
        for folder in ("responses", "dispatches", "prompt_receipts"):
            expected.add(f"{label}/{folder}/{rid}.json")
    expected.add("prompts/JG_GLM_JJ_00_00.txt")  # Guard that the shared prompt tree exists.
    return expected


def _walk_safety(path: Path) -> None:
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


def _verify_public(package: Path) -> dict[str, Any]:
    """Verify the frozen public package without consulting its local source runs."""
    package = package.resolve()
    need(package.is_dir(), "Published completion package is missing")
    public_freeze = read_json(package / "freeze.json")
    need(public_freeze.get("hash_convention") == "SHA256 with CRLF normalized to LF",
         "Unexpected public file hash convention")
    need(isinstance(public_freeze.get("hashes"), dict), "Public freeze hashes must be an object")
    for relative, digest in public_freeze["hashes"].items():
        path = within(package, relative)
        need(path.is_file() and sha_file(path) == digest, f"Published file hash mismatch: {relative}")
        _walk_safety(path)
    _walk_safety(package / "freeze.json")

    ledger = read_json(package / "attempt_ledger.json")
    expected = _expected_package_files(package, ledger)
    actual = {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()}
    need(actual == expected | {"freeze.json"},
         f"Public package contains unexpected or missing files: missing={sorted((expected | {'freeze.json'}) - actual)} extra={sorted(actual - (expected | {'freeze.json'}))}")
    need(set(public_freeze["hashes"]) == expected,
         f"Public freeze file allowlist is incomplete: missing={sorted(expected - set(public_freeze['hashes']))} extra={sorted(set(public_freeze['hashes']) - expected)}")

    original_manifest = _assert_exact_keys(read_json(package / "original/manifest.json"),
                                           ORIGINAL_MANIFEST_KEYS, "published original manifest")
    supplement_manifest = _assert_exact_keys(read_json(package / "supplement/manifest.json"),
                                             SUPPLEMENT_MANIFEST_KEYS, "published supplement manifest")
    original_schedule = _assert_manifest_schedule(original_manifest,
                                                  read_json(package / "original/schedule.json"), "published original")
    supplement_schedule = _assert_manifest_schedule(supplement_manifest,
                                                    read_json(package / "supplement/schedule.json"), "published supplement")
    need(read_json(package / "supplement/parent_schedule.json") == original_schedule,
         "Published supplement parent schedule differs from the original")
    need(len(original_schedule) == TOTAL and len(supplement_schedule) == 30,
         "Published schedules do not contain 32 and 30 rows")
    retained = set(supplement_manifest["retained_valid_ids"])
    original_by_id = {row["request_id"]: row for row in original_schedule}
    supplement_by_id = {row["request_id"]: row for row in supplement_schedule}
    need(set(supplement_by_id) == set(original_by_id) - retained
         and all(supplement_by_id[rid] == original_by_id[rid] for rid in supplement_by_id),
         "Supplement schedule is not the frozen 30-slot overlay")
    need(original_manifest["configuration_by_model"] == supplement_manifest["configuration_by_model"],
         "Published model configurations differ")

    source_freezes = {
        "original": _assert_exact_keys(read_json(package / "original/freeze.json"), FREEZE_KEYS,
                                       "published original freeze"),
        "supplement": _assert_exact_keys(read_json(package / "supplement/freeze.json"), SUPPLEMENT_FREEZE_KEYS,
                                          "published supplement freeze"),
    }
    for label, freeze in source_freezes.items():
        need(freeze.get("experimental_requests_at_freeze") == 0,
             f"{label} source freeze does not precede requests")
        for relative, digest in freeze["hashes"].items():
            path = _source_artifact_path(package, label, relative)
            need(path.is_file() and sha_file(path) == digest,
                 f"Published {label} frozen input hash mismatch: {relative}")

    for label, manifest in (("original", original_manifest), ("supplement", supplement_manifest)):
        for source_relative, digest in manifest["source_artifacts"].items():
            snapshot = within(package, f"{label}/inputs/{Path(source_relative).name}")
            need(snapshot.is_file() and sha_file(snapshot) == digest,
                 f"Published {label} source snapshot hash mismatch: {source_relative}")

    publication = read_json(package / "publication.json")
    need(publication.get("original_run_id") == ORIGINAL_ID
         and publication.get("supplement_run_id") == SUPPLEMENT_ID,
         "Publication source run identities differ")
    need(publication.get("source_freeze_sha256_lf") == {
        "original": sha_file(package / "original/freeze.json"),
        "supplement": sha_file(package / "supplement/freeze.json"),
    }, "Source freeze provenance differs from the preserved freeze files")
    need(publication.get("source_manifest_sha256_lf") == {
        "original": sha_file(package / "original/manifest.json"),
        "supplement": sha_file(package / "supplement/manifest.json"),
    }, "Source manifest provenance differs from the preserved manifests")
    need(publication.get("source_schedule_sha256_lf") == {
        "original": sha_file(package / "original/schedule.json"),
        "supplement": sha_file(package / "supplement/schedule.json"),
        "supplement_parent": sha_file(package / "supplement/parent_schedule.json"),
    }, "Source schedule provenance differs from preserved schedules")
    need(publication.get("source_summary_sha256_lf") == {
        "original_registered": sha_file(package / "analysis/original_summary.json"),
        "completion_overlay": sha_file(package / "analysis/completion_summary.json"),
    }, "Summary provenance differs from the preserved canonical summaries")
    source_prompts = publication.get("prompt_sha256_lf", {}).get("source")
    published_prompts = publication.get("prompt_sha256_lf", {}).get("published")
    prompt_hashes = {row["request_id"]: sha_file(within(package, row["prompt_path"])) for row in original_schedule}
    need(source_prompts == published_prompts == prompt_hashes,
         "Exact prompt provenance does not match the published prompts")
    need(publication.get("source_artifact_snapshots") == {
        label: {source_path: f"{label}/inputs/{Path(source_path).name}"
                for source_path in manifest["source_artifacts"]}
        for label, manifest in (("original", original_manifest), ("supplement", supplement_manifest))
    }, "Source artifact snapshot map differs from the published bundle")

    receipt_hashes = {"original": {}, "supplement": {}}
    visible_hashes = {"original": {}, "supplement": {}}
    for label in ("original", "supplement"):
        for folder in ("responses", "dispatches", "prompt_receipts"):
            receipt_hashes[label][folder] = {
                path.stem: sha_file(path) for path in sorted((package / label / folder).glob("*.json"))
            }
        visible_hashes[label] = {
            path.stem: sha_text(read_json(path)["visible_text"])
            for path in sorted((package / label / "responses").glob("*.json"))
        }
    need(publication.get("published_receipt_sha256_lf") == receipt_hashes,
         "Published receipt hashes do not match the attempt files")
    need(publication.get("source_receipt_sha256_lf") == receipt_hashes,
         "Source receipt hashes do not bind to the preserved safe receipt bytes")
    need(publication.get("visible_text_sha256_utf8") == visible_hashes,
         "Visible-text hashes do not match the final-visible receipts")

    original_summary = read_json(package / "analysis/original_summary.json")
    completion_summary = read_json(package / "analysis/completion_summary.json")
    original_status = _assert_exact_keys(read_json(package / "original/status.json"), ORIGINAL_STATUS_KEYS,
                                         "published original status")
    supplement_status = _assert_exact_keys(read_json(package / "supplement/status.json"), SUPPLEMENT_STATUS_KEYS,
                                            "published supplement status")
    _validate_source_completion(original_manifest, supplement_manifest, original_summary,
                                completion_summary, original_status, supplement_status)

    report = _audit_public_calculate(package)
    need(read_json(package / "analysis/public_verification.json") == report,
         "Public verification report does not reproduce")
    need((package / "analysis/RESULTS.md").read_text(encoding="utf-8") ==
         _results_markdown(original_summary, completion_summary), "Public results report does not reproduce")
    need((package / "README.md").read_text(encoding="utf-8") == _readme_text(),
         "Public README does not reproduce")
    return {
        "verification": "PASS",
        "study_id": STUDY_ID,
        "fixed_slots": TOTAL,
        "physical_attempts": 33,
        "selected_strict_valid": 32,
        "normalized_responses": 0,
        "overall_gate": completion_summary["overall_gate"],
        "public_file_count": len(actual),
    }


def _readme_text() -> str:
    return (
        "# Joint Epistemic Simulation32 completion evidence\n\n"
        "This package contains the finite known-mechanism Judge qualification and its separately frozen completion overlay. "
        "It preserves all 32 exact prompts, all 33 final-visible response receipts, both schedules and configurations, "
        "the original incomplete summary, and the completion summary.\n\n"
        "Start with [results](analysis/RESULTS.md), then read the [completion summary](analysis/completion_summary.json) "
        "and [original registered summary](analysis/original_summary.json). The [attempt ledger](attempt_ledger.json) "
        "shows which physical receipt was selected for each fixed slot. Exact prompts and receipts are supporting evidence.\n\n"
        "The original run attempted three of 32 requests and remains `INCOMPLETE` with two strict-valid responses and one "
        "strict-invalid third response. The supplement made one attempt for each of the other 30 slots. The completion "
        "overlay contains 32 strict-valid selected slots from 33 physical attempts; the invalid original third response "
        "remains excluded. All 30 supplement responses passed the original strict parser, so the narrow normalization "
        "count is zero.\n\n"
        "The completed finite-cell gate is `FAIL`: GLM-5.3/MARGINAL primary excess Brier is 0.018896604938, above "
        "the frozen 0.01 limit. This qualification covers only the enumerated positive-support packets under the stated "
        "known mechanism. It does not establish population calibration, population Theory of Mind, Actor strategy, or "
        "general model performance.\n\n"
        "The package includes frozen analyzer, runner, parser, prompt-module, and protocol snapshots. Run `python -X utf8 -B "
        "scripts/publish_joint_epistemic_simulation.py --verify` from the project root for a public-package-only check. "
        "Verification reads this package only and makes no provider request.\n"
    )


def export() -> dict[str, Any]:
    need(not PUBLIC.exists(), "Public completion package already exists; export is write-once")
    need(ORIGINAL_RUN.is_dir() and SUPPLEMENT_RUN.is_dir(), "Frozen source runs are unavailable")
    original_manifest, supplement_manifest, original_freeze, supplement_freeze = _summaries_and_source_paths()
    original_schedule = _assert_manifest_schedule(original_manifest, read_json(ORIGINAL_RUN / "schedule.json"),
                                                  "original source")
    supplement_schedule = _assert_manifest_schedule(supplement_manifest, read_json(SUPPLEMENT_RUN / "schedule.json"),
                                                    "supplement source")
    need(read_json(SUPPLEMENT_RUN / "parent_schedule.json") == original_schedule,
         "Supplement parent schedule differs from the frozen original")
    original_status = read_json(ORIGINAL_RUN / "status.json")
    supplement_status = read_json(SUPPLEMENT_RUN / "status.json")
    original_summary = read_json(ORIGINAL_RUN / "analysis/summary.json")
    completion_summary = read_json(SUPPLEMENT_RUN / "analysis/completion_summary.json")
    _validate_source_completion(original_manifest, supplement_manifest, original_summary, completion_summary,
                                original_status, supplement_status)

    retained = set(supplement_manifest["retained_valid_ids"])
    original_ids = {row["request_id"] for row in original_schedule}
    supplement_ids = {row["request_id"] for row in supplement_schedule}
    need(len(original_schedule) == TOTAL and len(supplement_schedule) == 30
         and supplement_ids == original_ids - retained,
         "Source schedules do not preserve the fixed 32-slot plus 30-slot overlay")
    for row in original_schedule:
        rid = row["request_id"]
        original_prompt = ORIGINAL_RUN / row["prompt_path"]
        supplement_prompt = SUPPLEMENT_RUN / row["prompt_path"]
        need(original_prompt.is_file() and supplement_prompt.is_file()
             and original_prompt.read_bytes() == supplement_prompt.read_bytes(),
             f"Original and supplement exact prompts differ: {rid}")

    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".jes32-public-stage-", dir=PUBLIC.parent) as stage_name:
        stage = Path(stage_name)
        _copy_pre_request_freeze(ORIGINAL_RUN, "original", original_freeze, stage)
        _copy_pre_request_freeze(SUPPLEMENT_RUN, "supplement", supplement_freeze, stage)
        # The source freezes contain every exact prompt; both source copies must match.
        need(len(list((stage / "prompts").glob("*.txt"))) == TOTAL,
             "Public package must contain all 32 exact prompts")
        for label, run, freeze, allowed_freeze, status_keys in (
            ("original", ORIGINAL_RUN, original_freeze, FREEZE_KEYS, ORIGINAL_STATUS_KEYS),
            ("supplement", SUPPLEMENT_RUN, supplement_freeze, SUPPLEMENT_FREEZE_KEYS, SUPPLEMENT_STATUS_KEYS),
        ):
            _assert_exact_keys(freeze, allowed_freeze, f"{label} freeze")
            _assert_exact_keys(read_json(run / "status.json"), status_keys, f"{label} status")
            copy_new(run / "freeze.json", stage / f"{label}/freeze.json")
            copy_new(run / "status.json", stage / f"{label}/status.json")
        original_hashes = _copy_attempt_receipts(ORIGINAL_RUN, "original", original_schedule, False, stage)
        supplement_hashes = _copy_attempt_receipts(SUPPLEMENT_RUN, "supplement", supplement_schedule, True, stage)
        source_receipt_hashes = {"original": original_hashes, "supplement": supplement_hashes}

        # These source files are canonical, separate records. Copy exact bytes and leave the source runs untouched.
        copy_new(ORIGINAL_RUN / "analysis/summary.json", stage / "analysis/original_summary.json")
        copy_new(SUPPLEMENT_RUN / "analysis/completion_summary.json", stage / "analysis/completion_summary.json")

        # Manifest, schedule, and oracle bytes are already copied by their pre-request freeze maps.
        for relative in ("manifest.json", "schedule.json", "oracle_packets.json"):
            need((stage / f"original/{relative}").is_file(), f"Original public snapshot missing: {relative}")
        for relative in ("manifest.json", "schedule.json", "parent_schedule.json"):
            need((stage / f"supplement/{relative}").is_file(), f"Supplement public snapshot missing: {relative}")

        attempt_ledger = _attempt_ledger(original_schedule, supplement_schedule, original_summary,
                                         completion_summary, source_receipt_hashes)
        write_json(stage / "attempt_ledger.json", attempt_ledger)
        write_text(stage / "README.md", _readme_text())
        write_text(stage / "analysis/RESULTS.md", _results_markdown(original_summary, completion_summary))

        prompt_source_hashes = {
            row["request_id"]: sha_file(ORIGINAL_RUN / row["prompt_path"]) for row in original_schedule
        }
        prompt_published_hashes = {
            row["request_id"]: sha_file(within(stage, row["prompt_path"])) for row in original_schedule
        }
        source_artifact_snapshots: dict[str, dict[str, str]] = {}
        for label, manifest in (("original", original_manifest), ("supplement", supplement_manifest)):
            source_artifact_snapshots[label] = {
                source_path: f"{label}/inputs/{Path(source_path).name}"
                for source_path in manifest["source_artifacts"]
            }
        write_json(stage / "publication.json", {
            "schema_version": 1,
            "study_id": STUDY_ID,
            "original_run_id": ORIGINAL_ID,
            "supplement_run_id": SUPPLEMENT_ID,
            "scope": "Offline allowlisted export of the fixed 32-slot design, exact prompts, 33 final-visible attempt receipts, and canonical separate analyses. No provider request, network operation, or credential access is performed.",
            "source_freeze_sha256_lf": {
                "original": sha_file(ORIGINAL_RUN / "freeze.json"),
                "supplement": sha_file(SUPPLEMENT_RUN / "freeze.json"),
            },
            "source_manifest_sha256_lf": {
                "original": sha_file(ORIGINAL_RUN / "manifest.json"),
                "supplement": sha_file(SUPPLEMENT_RUN / "manifest.json"),
            },
            "source_schedule_sha256_lf": {
                "original": sha_file(ORIGINAL_RUN / "schedule.json"),
                "supplement": sha_file(SUPPLEMENT_RUN / "schedule.json"),
                "supplement_parent": sha_file(SUPPLEMENT_RUN / "parent_schedule.json"),
            },
            "source_summary_sha256_lf": {
                "original_registered": sha_file(ORIGINAL_RUN / "analysis/summary.json"),
                "completion_overlay": sha_file(SUPPLEMENT_RUN / "analysis/completion_summary.json"),
            },
            "source_artifact_snapshots": source_artifact_snapshots,
            "source_receipt_sha256_lf": {
                label: {
                    folder: {rid: values["source_sha256_lf"] for rid, values in receipts.items()}
                    for folder, receipts in folders.items()
                }
                for label, folders in source_receipt_hashes.items()
            },
            "published_receipt_sha256_lf": {
                label: {
                    folder: {rid: values["published_sha256_lf"] for rid, values in receipts.items()}
                    for folder, receipts in folders.items()
                }
                for label, folders in source_receipt_hashes.items()
            },
            "receipt_hash_note": "Receipt files preserve only the reviewed final-visible schema and safe bindings. Source and published hashes are recorded separately; no launch records, private raw provider bodies, or hidden reasoning are included.",
            "prompt_sha256_lf": {"source": prompt_source_hashes, "published": prompt_published_hashes},
            "visible_text_sha256_utf8": {
                label: {
                    rid: sha_text(read_json(run / "responses" / f"{rid}.json")["visible_text"])
                    for rid in hashes["responses"]
                }
                for label, run, hashes in (
                    ("original", ORIGINAL_RUN, original_hashes),
                    ("supplement", SUPPLEMENT_RUN, supplement_hashes),
                )
            },
            "selection": {
                "original_strict_valid_retained": sorted(retained),
                "original_strict_invalid_excluded": ["JG_GLM_JJ_11_00"],
                "supplement_first_attempts_selected": 30,
                "selected_completion_slots": 32,
                "total_physical_attempts": 33,
                "normalized_supplement_responses": 0,
            },
        })
        verification = _build_public_verification(stage)
        write_json(stage / "analysis/public_verification.json", verification)
        file_hashes = {
            path.relative_to(stage).as_posix(): sha_file(path)
            for path in stage.rglob("*") if path.is_file()
        }
        write_json(stage / "freeze.json", {
            "schema_version": 1,
            "hash_convention": "SHA256 with CRLF normalized to LF",
            "hashes": file_hashes,
        })
        _verify_public(stage)
        need(not PUBLIC.exists(), "Public package appeared during export; refuse overwrite")
        stage.rename(PUBLIC)
    return _verify_public(PUBLIC)


def _build_public_verification(package: Path) -> dict[str, Any]:
    """Compute the public verification record without requiring it to exist yet."""
    return _audit_public_calculate(package)


def _audit_public_calculate(package: Path) -> dict[str, Any]:
    """Public-only scientific checks and deterministic verification record."""
    package = package.resolve()
    original_manifest = read_json(package / "original/manifest.json")
    supplement_manifest = read_json(package / "supplement/manifest.json")
    original_schedule = read_json(package / "original/schedule.json")
    supplement_schedule = read_json(package / "supplement/schedule.json")
    original_summary = read_json(package / "analysis/original_summary.json")
    completion_summary = read_json(package / "analysis/completion_summary.json")
    original_status = read_json(package / "original/status.json")
    supplement_status = read_json(package / "supplement/status.json")
    ledger = read_json(package / "attempt_ledger.json")
    _validate_source_completion(original_manifest, supplement_manifest, original_summary,
                                completion_summary, original_status, supplement_status)
    original_by_id = {row["request_id"]: row for row in original_schedule}
    retained = set(supplement_manifest["retained_valid_ids"])
    original_attempt_ids = {path.stem for path in (package / "original/responses").glob("*.json")}
    supplement_attempt_ids = {path.stem for path in (package / "supplement/responses").glob("*.json")}
    need(original_attempt_ids == {row["request_id"] for row in original_schedule[:3]},
         "Original attempts are not the first three fixed slots")
    need(supplement_attempt_ids == set(original_by_id) - retained,
         "Supplement attempts do not cover all remaining slots")
    prior_modules = {name: sys.modules.pop(name, None) for name in (
        "run_strategic_qualification", "run_counterfactual_source_boundary",
        "run_joint_epistemic_simulation", "run_joint_epistemic_supplement",
        "analyze_joint_epistemic_simulation", "analyze_joint_epistemic_supplement",
    )}
    study, supplement_runner, original_analyzer = _read_public_parsers(package)
    try:
        original_analyzer._validate_manifest(original_manifest)
        strict_statuses = {}
        for label, ids in (("original", original_attempt_ids), ("supplement", supplement_attempt_ids)):
            rows = original_by_id if label == "original" else {
                row["request_id"]: row for row in supplement_schedule
            }
            expected_response_keys = RESPONSE_KEYS if label == "original" else SUPPLEMENT_RESPONSE_KEYS
            for folder in ("responses", "dispatches", "prompt_receipts"):
                observed = {path.stem for path in (package / label / folder).glob("*.json")}
                need(observed == ids, f"{label}/{folder} does not match its physical attempts")
            for rid in ids:
                row = rows[rid]
                receipt = read_json(package / f"{label}/responses/{rid}.json")
                _assert_exact_keys(receipt, expected_response_keys, f"{label} response {rid}")
                need(receipt.get("status") == "response_received"
                     and receipt.get("http_status") == 200
                     and receipt.get("returned_model") == row["model"],
                     f"Transport binding mismatch: {label}/{rid}")
                need(sha_file(within(package, row["prompt_path"])) == receipt.get("prompt_sha256"),
                     f"Prompt hash binding mismatch: {label}/{rid}")
                dispatch = read_json(package / f"{label}/dispatches/{rid}.json")
                _assert_exact_keys(dispatch, set(row) | DISPATCH_EXTRA_KEYS,
                                   f"{label} dispatch {rid}")
                need(all(dispatch.get(key) == value for key, value in row.items()),
                     f"Dispatch schedule binding mismatch: {label}/{rid}")
                need(dispatch.get("prompt_sha256") == receipt.get("prompt_sha256"),
                     f"Dispatch prompt binding mismatch: {label}/{rid}")
                prompt_receipt = read_json(package / f"{label}/prompt_receipts/{rid}.json")
                _assert_exact_keys(prompt_receipt, PROMPT_RECEIPT_KEYS,
                                   f"{label} prompt receipt {rid}")
                need(prompt_receipt.get("request_id") == rid
                     and prompt_receipt.get("prompt_sha256") == receipt.get("prompt_sha256"),
                     f"Prompt receipt binding mismatch: {label}/{rid}")
                for field in ("request_id", "model", "kind", "case_id", "simulation_condition",
                              "bluffer_condition", "judge_condition"):
                    need(receipt.get(field) == row.get(field), f"Response binding mismatch: {label}/{rid}/{field}")
                parsed, status = study.parse_response(receipt.get("visible_text"), receipt.get("finish_reason"))
                need(receipt.get("parsed") == parsed and receipt.get("parse_status") == status,
                     f"Raw strict parser fields differ: {label}/{rid}")
                strict_statuses[(label, rid)] = status
                if label == "supplement":
                    parsed_completion, completion_status, acceptance = supplement_runner.parse_completion(
                        receipt.get("visible_text"), receipt.get("finish_reason")
                    )
                    need(receipt.get("completion_parsed") == parsed_completion
                         and receipt.get("completion_parse_status") == completion_status
                         and receipt.get("format_acceptance") == acceptance,
                         f"Supplement normalization/parser fields differ: {rid}")
        original_summary_rows = {row["request_id"]: row for row in original_summary["response_rows"]}
        invalid_ids = original_attempt_ids - retained
        need(len(retained) == 2 and len(invalid_ids) == 1
             and all(strict_statuses[("original", rid)] == "valid" for rid in retained)
             and all(strict_statuses[("original", rid)] != "valid" for rid in invalid_ids),
             "Original strict-valid and strict-invalid outcomes changed")
        need(all(strict_statuses[("supplement", rid)] == "valid" for rid in supplement_attempt_ids),
             "A supplement raw response is not strict-valid")
        need(all(read_json(package / f"supplement/responses/{rid}.json").get("format_acceptance") == "strict"
                 for rid in supplement_attempt_ids),
             "A supplement response used normalization")
        need(sum(item.get("status") == "valid" for item in original_summary_rows.values()) == 2,
             "Original registered summary no longer records two strict-valid responses")
        ledger_attempts = {
            (item.get("run_role"), item.get("request_id")): item for item in ledger["attempts"]
        }
        expected_attempt_keys = ({("original", rid) for rid in original_attempt_ids}
                                 | {("supplement", rid) for rid in supplement_attempt_ids})
        need(len(ledger_attempts) == 33 and set(ledger_attempts) == expected_attempt_keys,
             "Attempt ledger does not map each physical receipt exactly once")
        need(sum(bool(item.get("selected_for_completion")) for item in ledger["attempts"]) == 32,
             "Attempt ledger must select exactly 32 physical receipts")
        for label, ids in (("original", original_attempt_ids), ("supplement", supplement_attempt_ids)):
            for rid in ids:
                entry = ledger_attempts[(label, rid)]
                response_path = package / f"{label}/responses/{rid}.json"
                need(entry.get("receipt_path") == f"{label}/responses/{rid}.json"
                     and entry.get("published_receipt_sha256_lf") == sha_file(response_path)
                     and entry.get("source_receipt_sha256_lf") == sha_file(response_path),
                     f"Attempt ledger receipt hash mismatch: {label}/{rid}")
                should_select = (rid in retained) if label == "original" else True
                need(entry.get("selected_for_completion") is should_select,
                     f"Attempt ledger selection flag mismatch: {label}/{rid}")

        selected_summary_rows = {row["request_id"]: row for row in completion_summary["response_rows"]}
        slot_ledger = {row["request_id"]: row for row in ledger["completion_slots"]}
        need(set(selected_summary_rows) == set(original_by_id) == set(slot_ledger),
             "Completion summary and ledger must cover exactly 32 slots")
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {
            (model, condition): [] for model in MODELS for condition in CONDITIONS
        }
        for row in original_schedule:
            rid = row["request_id"]
            label = "original" if rid in retained else "supplement"
            receipt = read_json(package / f"{label}/responses/{rid}.json")
            parsed = receipt["parsed"] if label == "original" else receipt["completion_parsed"]
            summary_row = selected_summary_rows[rid]
            source = "original_strict_valid" if label == "original" else "supplement_first_attempt"
            need(summary_row.get("selection_source") == source
                 and summary_row.get("status") == "valid"
                 and summary_row.get("p_A") == parsed["p_A"]
                 and summary_row.get("decision") == parsed["decision"]
                 and summary_row.get("reason") == parsed["reason"],
                 f"Selected completion receipt differs from aggregate row: {rid}")
            need(summary_row.get("prior_predictive_weight") == row["prior_predictive_weight"]
                 and summary_row.get("posterior_A") == row["posterior_A"],
                 f"Selected weight/posterior differs from schedule: {rid}")
            need(slot_ledger[rid].get("selected_attempt_path") == f"{label}/responses/{rid}.json",
                 f"Attempt ledger selected the wrong receipt: {rid}")
            grouped[(row["model"], row["simulation_condition"])].append(row | {"p_A": parsed["p_A"]})
        summaries = {(cell["model"], cell["simulation_condition"]): cell for cell in completion_summary["cells"]}
        strict_summaries = {
            (cell["model"], cell["simulation_condition"]): cell
            for cell in completion_summary["strict_only_sensitivity"]["cells"]
        }
        per_cell = []
        for model in MODELS:
            for condition in CONDITIONS:
                rows = grouped[(model, condition)]
                count = 12 if condition == "MARGINAL" else 4
                weight_mass = sum(float(row["prior_predictive_weight"]) for row in rows)
                need(len(rows) == count and math.isclose(weight_mass, 1.0, rel_tol=0.0, abs_tol=1e-12),
                     f"{model}/{condition} support or weight mass is invalid")
                primary = sum(float(row["prior_predictive_weight"]) *
                              (float(row["p_A"]) - float(row["posterior_A"])) ** 2 for row in rows)
                cell, strict_cell = summaries[(model, condition)], strict_summaries[(model, condition)]
                need(cell.get("expected_packets") == count and cell.get("valid_packets") == count
                     and cell.get("complete_positive_support") is True,
                     f"{model}/{condition} is not complete positive support")
                need(math.isclose(primary, float(cell["primary_excess_brier"]), rel_tol=0.0, abs_tol=1e-12)
                     and math.isclose(primary, float(cell["observed_excess_brier_contribution"]),
                                      rel_tol=0.0, abs_tol=1e-12)
                     and math.isclose(primary, float(strict_cell["primary_excess_brier"]),
                                      rel_tol=0.0, abs_tol=1e-12),
                     f"{model}/{condition} primary aggregate does not reproduce")
                gate_pass = primary <= EXCESS_BRIER_LIMIT
                need(cell.get("gate_pass") is gate_pass,
                     f"{model}/{condition} gate does not match its primary")
                per_cell.append({
                    "model": model,
                    "simulation_condition": condition,
                    "positive_support_packets": count,
                    "selected_valid_packets": len(rows),
                    "prior_predictive_weight_sum": weight_mass,
                    "recomputed_primary_excess_brier": primary,
                    "published_primary_excess_brier": cell["primary_excess_brier"],
                    "gate_pass": gate_pass,
                })
        need(completion_summary["narrow_normalization_counts"]["valid_normalized_response_count"] == 0
             and completion_summary["narrow_normalization_counts"]["request_ids"] == [],
             "Published narrow normalization count is not zero")
        need(completion_summary["overall_gate"] == "FAIL", "Published completion gate must remain FAIL")
        need(original_summary["analysis_status"] == "incomplete"
             and original_summary["overall_gate"] == "INCOMPLETE"
             and original_summary["valid_response_count"] == 2,
             "Original registered incomplete summary was altered")
        return {
            "schema_version": 1,
            "verification": "PASS",
            "verification_scope": "Public package only; no local source run, network request, or credential access.",
            "original": {
                "planned_slots": TOTAL,
                "physical_attempts": original_summary["dispatched_calls"],
                "strict_valid": original_summary["valid_response_count"],
                "strict_invalid_attempts": len(invalid_ids),
                "unattempted_slots": TOTAL - original_summary["dispatched_calls"],
                "registered_status": original_summary["analysis_status"],
                "registered_gate": original_summary["overall_gate"],
            },
            "completion_overlay": {
                "fixed_slots": TOTAL,
                "physical_attempts": 33,
                "strict_valid_selected_slots": completion_summary["completion_valid_response_count"],
                "retained_original_valid": len(retained),
                "original_invalid_excluded": len(invalid_ids),
                "supplement_first_attempts": len(supplement_attempt_ids),
                "normalized_supplement_responses": completion_summary["narrow_normalization_counts"]["valid_normalized_response_count"],
                "overall_gate": completion_summary["overall_gate"],
                "per_cell_primary": per_cell,
            },
            "checks": {
                "source_freeze_hashes": "PASS",
                "exact_prompt_hashes": "PASS",
                "strict_raw_parse_fields": "PASS",
                "supplement_completion_parse_fields": "PASS",
                "attempt_selection_and_bindings": "PASS",
                "all_32_weights_and_primary_aggregates": "PASS",
                "zero_normalization_fields": "PASS",
                "public_file_safety_and_allowlist": "PASS",
            },
        }
    finally:
        _release_public_parsers(package, prior_modules)


def verify() -> dict[str, Any]:
    return _verify_public(PUBLIC)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--export", action="store_true", help="create the public package once from local frozen runs")
    group.add_argument("--verify", action="store_true", help="verify only the public package and bundled sources")
    args = parser.parse_args(argv)
    try:
        result = export() if args.export else verify()
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (PublicationError, AssertionError, OSError, UnicodeError, json.JSONDecodeError,
            ValueError, KeyError, TypeError, ImportError, AttributeError) as exc:
        print(f"JES32 publication verification failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
