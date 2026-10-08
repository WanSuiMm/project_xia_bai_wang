#!/usr/bin/env python3
"""Export or audit the sanitized public 28-request strategic qualification.

The default command audits the existing public run using repository files
only. ``--export`` creates the public run once from the completed frozen run
and refuses to replace it. This script uses only the Python standard library
and makes no provider or network calls.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "epistemic_boundary_mimicry"
RUN = BASE / "runs/opencode_go_20261008_strategic_qualification28_01"
PUBLIC_PARENT = BASE / "published_runs"
PUBLIC = PUBLIC_PARENT / "go_strategic_qualification28_20261008"
RUNNER_PATH = ROOT / "scripts/run_strategic_qualification.py"
CASE_IDS = ("SQ01", "SQ02", "SQ03", "SQ04")
SEAT_BY_CASE = {"SQ01": "A", "SQ02": "B", "SQ03": "B", "SQ04": "A"}
SPEAKER_CONDITIONS = ("READER", "B0", "B1")
JUDGE_CONDITIONS = (("B0", "J0"), ("B0", "J1"), ("B1", "J0"), ("B1", "J1"))
SAFE_RESPONSE_KEYS = {
    "request_id", "model", "kind", "case_id", "prompt_sha256", "status", "sent_utc",
    "visible_text", "parsed", "parse_status", "returned_model", "usage", "finish_reason",
    "speaker_condition", "bluffer_condition", "judge_condition", "http_status", "elapsed_seconds", "captured_utc",
}
SAFE_DISPATCH_KEYS = {
    "request_id", "model", "kind", "case_id", "dispatched_utc", "prompt_sha256",
    "schedule_index", "dependencies", "dependency_response_sha256",
}
SAFE_PROMPT_RECEIPT_KEYS = {
    "request_id", "path", "prompt_sha256", "dependency_response_sha256", "created_utc",
    "shared_prefix_sha256",
}
FORBIDDEN_KEYS = {
    "authorization", "api_key", "x-api-key", "x-opencode-session", "headers", "session_id",
    "session_ids", "account_id", "pid", "host", "absolute_path", "provenance_private",
    "reasoning_content", "hidden_reasoning", "raw_provider_body",
}
STATIC_FILES = {
    "README.md", "manifest.json", "schedule.json", "freeze.json", "source_freeze.json",
    "publication.json", "status.json", "SHA256SUMS.txt",
    "inputs/materials_20261008.json", "inputs/PROMPT_MODULES_20261008.json",
    "inputs/judge_examples_20261008.json", "inputs/PROTOCOL_20261008.md",
    "inputs/run_strategic_qualification.py",
}


class PublicationError(Exception):
    """Raised when a source or public-package invariant fails."""


def need(ok: bool, message: str) -> None:
    if not ok:
        raise PublicationError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha_bytes_lf(payload: bytes) -> str:
    return hashlib.sha256(payload.replace(b"\r\n", b"\n")).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes_lf(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def _load_runner():
    need(RUNNER_PATH.is_file(), "the first-party qualification runner is missing")
    spec = importlib.util.spec_from_file_location("_strategic_qualification_runner", RUNNER_PATH)
    need(spec is not None and spec.loader is not None, "could not load the qualification parser")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _safe_relpath(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    need(not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts),
         f"unsafe repository-relative path: {value!r}")
    return path.as_posix()


def _historical_path(value: str) -> str:
    path = _safe_relpath(value)
    prefix = "project_xia_bai_wang/"
    if path.startswith(prefix):
        path = path[len(prefix):]
    need(path.startswith("epistemic_boundary_mimicry/"), "historical source is outside this project")
    return path


def _public_materials(source: dict[str, Any]) -> dict[str, Any]:
    case_fields = ("case_id", "title", "domain", "public_context", "source_text")
    question_fields = ("question_id", "question", "source_region", "gold_answer", "source_quotes", "absence_check")
    cases = []
    for case in source["cases"]:
        public_case = {key: case[key] for key in case_fields if key in case}
        public_case["questions"] = [
            {key: question[key] for key in question_fields if key in question}
            for question in case["questions"]
        ]
        cases.append(public_case)
    return {
        "schema_version": source["schema_version"],
        "material_set_id": source["material_set_id"],
        "scope": "Four hand-authored fictional dossiers; materials are not a random sample of source worlds.",
        "cases": cases,
    }


def _public_provenance(source: dict[str, Any]) -> dict[str, Any]:
    private = source["provenance_private"]
    selected = []
    for example in private["examples"]:
        run_file = _historical_path(example["published_run_file"])
        run_manifest = _historical_path(example["published_run_manifest"])
        audit_file = _historical_path(example["claim_audit_input_file"])
        run_path, manifest_path, audit_path = (ROOT / path for path in (run_file, run_manifest, audit_file))
        need(run_path.is_file() and manifest_path.is_file() and audit_path.is_file(),
             f"historical public provenance source is missing: {example['example_id']}")
        messages = []
        for message in example["message_provenance"]:
            messages.append({key: message[key] for key in (
                "role", "published_messages_index_zero_based", "question_index", "field",
                "returned_model", "verbatim_original_snippet") if key in message})
        models = example.get("model_ids", {})
        selected.append({
            "example_id": example["example_id"],
            "historical_case": example["historical_case"],
            "source_domain": example["source_domain"],
            "published_run_file": run_file,
            "published_run_file_sha256_lf_utf8": sha_file(run_path),
            "published_run_manifest": run_manifest,
            "published_run_manifest_sha256_lf_utf8": sha_file(manifest_path),
            "claim_audit_input_file": audit_file,
            "claim_audit_input_file_sha256_lf_utf8": sha_file(audit_path),
            "audit_evidence_sha256_lf_utf8": example["claim_audit_input_evidence_sha256_lf"],
            "selected_terminal_excerpt": example["terminal_units_exact_text"],
            "terminal_units_audit_note": example["terminal_units_audit_note"],
            "message_provenance": messages,
            "model_ids": {key: models[key] for key in (
                "trajectory_judge_model", "terminal_message_returned_model",
                "trajectory_speaker_model", "contextual_speaker_message_returned_model") if key in models},
        })
    return {
        "selection_scope": private["selection_scope"],
        "model_verification": private["model_verification"],
        "neutral_control_construction": private["neutral_control_construction"],
        "limitations": private["limitations"],
        "examples": selected,
    }


def _request_ids() -> set[str]:
    result = {f"SP_{case}_{condition}" for case in CASE_IDS for condition in SPEAKER_CONDITIONS}
    result.update(f"JG_{case}_{arm}_{notice}" for case in CASE_IDS for arm, notice in JUDGE_CONDITIONS)
    return result


def _safe_receipts(run: Path, schedule: list[dict[str, Any]]) -> None:
    need(len(schedule) == 28 and {r["request_id"] for r in schedule} == _request_ids(),
         "source schedule differs from the fixed 28-request design")
    for row in schedule:
        request_id = row["request_id"]
        response = read_json(run / "responses" / f"{request_id}.json")
        dispatch = read_json(run / "dispatches" / f"{request_id}.json")
        prompt_receipt = read_json(run / "prompt_receipts" / f"{request_id}.json")
        need(set(response) <= SAFE_RESPONSE_KEYS, f"unexpected response field for {request_id}")
        need(set(dispatch) <= SAFE_DISPATCH_KEYS, f"unexpected dispatch field for {request_id}")
        need(set(prompt_receipt) <= SAFE_PROMPT_RECEIPT_KEYS, f"unexpected prompt-receipt field for {request_id}")
        need(response.get("status") == "response_received" and response.get("parse_status") == "valid",
             f"response is not complete and valid: {request_id}")
        need(response.get("returned_model") == row["model"], f"unexpected returned model: {request_id}")
        need(dispatch.get("dependencies", []) == row.get("depends_on", []), f"dispatch dependency list mismatch: {request_id}")
        need(prompt_receipt.get("dependency_response_sha256", {}) == dispatch.get("dependency_response_sha256", {}),
             f"prompt/dispatch dependency witness mismatch: {request_id}")










def _audit_public_provenance(provenance: dict[str, Any]) -> None:
    _walk_json_keys(provenance, "public_provenance")
    need(len(provenance.get("examples", [])) == 2, "historical provenance must cover two selected examples")
    for example in provenance["examples"]:
        for key in ("published_run_file", "published_run_manifest", "claim_audit_input_file"):
            value = _safe_relpath(example[key])
            need(value.startswith("epistemic_boundary_mimicry/"), "historical provenance is not repository-relative")
        for key in ("published_run_file_sha256_lf_utf8", "published_run_manifest_sha256_lf_utf8",
                    "claim_audit_input_file_sha256_lf_utf8", "audit_evidence_sha256_lf_utf8"):
            need(re.fullmatch(r"[0-9a-f]{64}", example.get(key, "")) is not None,
                 f"historical provenance hash is malformed: {key}")
        need(bool(example.get("selected_terminal_excerpt")) and bool(example.get("message_provenance")),
             "historical public quote provenance is incomplete")








def _copy_private_run(stage: Path, runner) -> dict[str, Any]:
    """Build the run tree, returning hashes needed by the public metadata."""
    need(RUN.is_dir(), "completed private source run is missing")
    freeze = read_json(RUN / "freeze.json")
    manifest = read_json(RUN / "manifest.json")
    schedule = read_json(RUN / "schedule.json")
    source_materials = read_json(RUN / "inputs/materials_20261008.json")
    source_modules = read_json(RUN / "inputs/PROMPT_MODULES_20261008.json")
    source_examples = read_json(RUN / "inputs/judge_examples_20261008.json")
    need(freeze.get("schema_version") == 1 and freeze.get("experimental_requests_at_freeze") == 0,
         "unexpected or post-dispatch source freeze")
    for relative, expected in freeze.get("hashes", {}).items():
        rel = _safe_relpath(relative)
        source = RUN.joinpath(*PurePosixPath(rel).parts)
        need(source.is_file() and sha_file(source) == expected, f"source frozen hash mismatch: {rel}")
    runner_hash = sha_file(RUNNER_PATH)
    need(sha_file(RUN / "inputs/run_strategic_qualification.py") == runner_hash
         and freeze.get("source_hashes", {}).get("runner") == runner_hash,
         "current runner differs from frozen runner snapshot")
    need(manifest.get("planned_provider_requests") == 28
         and manifest.get("configuration_by_model") == runner.configuration()
         and manifest.get("endpoint_formats") == runner.ENDPOINTS,
         "source configuration differs from the frozen runner")
    need(schedule == manifest.get("requests"), "source manifest and schedule differ")
    runner.validate_inputs(source_materials, source_modules, source_examples)
    _safe_receipts(RUN, schedule)

    public_materials = _public_materials(source_materials)
    public_examples = {
        key: source_examples[key] for key in ("format_version", "aware_examples", "neutral_examples")
    }
    public_examples["provenance_public"] = _public_provenance(source_examples)
    write_json(stage / "inputs/materials_20261008.json", public_materials)
    write_json(stage / "inputs/PROMPT_MODULES_20261008.json", source_modules)
    write_json(stage / "inputs/judge_examples_20261008.json", public_examples)
    for name in ("PROTOCOL_20261008.md", "run_strategic_qualification.py"):
        shutil.copyfile(RUN / "inputs" / name, stage / "inputs" / name)

    for folder in ("prompts", "prompt_receipts", "responses", "dispatches"):
        destination = stage / folder
        destination.mkdir(parents=True, exist_ok=True)
        for source in (RUN / folder).glob("*"):
            if source.is_file():
                if folder == "responses":
                    receipt = read_json(source)
                    need(set(receipt) <= SAFE_RESPONSE_KEYS, f"unexpected response field in {source.name}")
                elif folder == "dispatches":
                    receipt = read_json(source)
                    need(set(receipt) <= SAFE_DISPATCH_KEYS, f"unexpected dispatch field in {source.name}")
                elif folder == "prompt_receipts":
                    receipt = read_json(source)
                    need(set(receipt) <= SAFE_PROMPT_RECEIPT_KEYS, f"unexpected prompt metadata in {source.name}")
                shutil.copyfile(source, destination / source.name)
    shutil.copyfile(RUN / "manifest.json", stage / "manifest.json")
    shutil.copyfile(RUN / "schedule.json", stage / "schedule.json")
    source_freeze_bytes = (RUN / "freeze.json").read_bytes()
    (stage / "source_freeze.json").write_bytes(source_freeze_bytes)
    source_freeze_hash = sha_bytes_lf(source_freeze_bytes)

    response_rows = [read_json(stage / "responses" / f"{row['request_id']}.json") for row in schedule]
    by_kind = {}
    for kind, planned in (("speaker", 12), ("judge", 16)):
        count = sum(response["kind"] == kind for response in response_rows)
        valid = sum(response["kind"] == kind and response["parse_status"] == "valid" for response in response_rows)
        by_kind[kind] = {"planned": planned, "dispatched": count, "responses": count, "valid": valid}
    source_status = read_json(RUN / "status.json")
    status = {"state": "COMPLETE_28_ATTEMPTED", "halt_reason": None, "planned": 28,
              "provider_requests": 28, "response_count": len(response_rows),
              "valid": sum(response["parse_status"] == "valid" for response in response_rows),
              "by_kind": by_kind,
              "completed_utc": source_status["completed_utc"],
              "updated_utc": source_status["updated_utc"]}
    write_json(stage / "status.json", status)

    hash_paths = sorted(path for path in stage.rglob("*") if path.is_file()
                        and path.name not in {"freeze.json", "source_freeze.json", "publication.json", "README.md", "SHA256SUMS.txt"})
    public_hashes = {path.relative_to(stage).as_posix(): sha_file(path) for path in hash_paths}
    published_freeze = {
        **freeze,
        "source_freeze_sha256_lf_utf8": source_freeze_hash,
        "source_frozen_hashes": freeze["hashes"],
        "hash_semantics": "hashes/public_copy_hashes cover on-disk published files; source_frozen_hashes retains original pre-dispatch values.",
        "hashes": public_hashes,
        "public_copy_hashes": public_hashes,
    }
    write_json(stage / "freeze.json", published_freeze)

    source_receipt_hashes = {
        folder: {request_id: sha_file(RUN / folder / f"{request_id}.json") for request_id in sorted(_request_ids())}
        for folder in ("prompt_receipts", "responses", "dispatches")
    }
    original_prompt_hashes = {
        request_id: sha_file(RUN / "prompts" / f"{request_id}.txt") for request_id in sorted(_request_ids())
    }
    # These are compact publication fields; the original manifest and schedule
    # remain byte-identical and retain their source hashes.
    publication = {
        "schema_version": 1,
        "study_id": "strategic_qualification28_20261008",
        "source_run_id": RUN.name,
        "provider": "OpenCode Go",
        "models": manifest["models"],
        "endpoint_formats": manifest["endpoint_formats"],
        "configuration_by_model": manifest["configuration_by_model"],
        "randomization_seed": manifest["randomization_seed"],
        "randomized_case_order": manifest["randomized_case_order"],
        "reader_seat_by_case": manifest["reader_seat_by_case"],
        "question_partition_by_case": {
            case["case_id"]: {
                region: [q["question_id"] for q in case["questions"] if q["source_region"] == region]
                for region in ("explicit", "unspecified")
            }
            for case in public_materials["cases"]
        },
        "schedule": schedule,
        "coverage": {
            "planned_provider_requests": 28,
            "dispatch_receipts": len(schedule),
            "saved_responses": len(response_rows),
            "valid_responses": sum(response["parse_status"] == "valid" for response in response_rows),
            "by_kind": by_kind,
            "interpretation": "Response coverage only; this export makes no scientific result claim.",
        },
        "original_source_freeze_sha256_lf_utf8": source_freeze_hash,
        "original_manifest_sha256_lf_utf8": sha_file(RUN / "manifest.json"),
        "original_schedule_sha256_lf_utf8": sha_file(RUN / "schedule.json"),
        "original_pre_dispatch_hashes": freeze["hashes"],
        "original_prompt_sha256_lf_utf8": original_prompt_hashes,
        "source_receipt_hashes_lf_utf8": source_receipt_hashes,
        "public_copy_hashes": public_hashes,
        "exclusions": [
            "launch, process, session, and host records",
            "credentials, provider headers, account metadata, and raw provider bodies",
            "hidden reasoning and researcher-only answer labels/notes",
            "scientific interpretation, which is reported separately",
        ],
    }
    write_json(stage / "publication.json", publication)
    (stage / "README.md").write_text(_readme(), encoding="utf-8", newline="\n")
    _write_hashes(stage)
    return {
        "source_freeze_sha256_lf_utf8": source_freeze_hash,
        "source_receipt_hashes_lf_utf8": source_receipt_hashes,
        "public_copy_hashes": public_hashes,
    }






def _walk_json_keys(value: Any, where: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            need(key.lower() not in FORBIDDEN_KEYS, f"private field exposed at {where}.{key}")
            _walk_json_keys(child, f"{where}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_json_keys(child, f"{where}[{index}]")


def _audit_provenance(value: dict[str, Any]) -> None:
    _walk_json_keys(value, "public_provenance")
    need(len(value.get("examples", [])) == 2, "historical provenance must cover two selected examples")
    for example in value["examples"]:
        for key in ("published_run_file", "published_run_manifest", "claim_audit_input_file"):
            path = _safe_relpath(example[key])
            need(path.startswith("epistemic_boundary_mimicry/"), "historical provenance is not repository-relative")
        for key in ("published_run_file_sha256_lf_utf8", "published_run_manifest_sha256_lf_utf8",
                    "claim_audit_input_file_sha256_lf_utf8", "audit_evidence_sha256_lf_utf8"):
            need(re.fullmatch(r"[0-9a-f]{64}", example.get(key, "")) is not None,
                 f"historical provenance hash is malformed: {key}")
        need(bool(example.get("selected_terminal_excerpt")) and bool(example.get("message_provenance")),
             "historical public quote provenance is incomplete")


def _extract_case_input(prompt: str) -> dict[str, Any]:
    match = re.search(r"<judge_case_input>\n(.*?)\n</judge_case_input>", prompt, flags=re.DOTALL)
    need(match is not None, "Judge prompt lacks its tagged case input")
    return json.loads(match.group(1))


def _audit_public(root: Path, runner=None) -> dict[str, Any]:
    runner = runner or _load_runner()
    need(root.is_dir(), "public evidence directory is missing")
    for path in root.rglob("*"):
        need(not path.is_symlink(), f"unexpected symlink in public package: {path.relative_to(root)}")
    freeze = read_json(root / "freeze.json")
    source_freeze = read_json(root / "source_freeze.json")
    publication = read_json(root / "publication.json")
    manifest = read_json(root / "manifest.json")
    schedule = read_json(root / "schedule.json")
    materials = read_json(root / "inputs/materials_20261008.json")
    modules = read_json(root / "inputs/PROMPT_MODULES_20261008.json")
    examples = read_json(root / "inputs/judge_examples_20261008.json")
    provenance = examples.get("provenance_public")

    need(sha_file(RUNNER_PATH) == freeze.get("source_hashes", {}).get("runner"),
         "current parser/runner differs from the frozen source hash")
    need(sha_file(root / "inputs/run_strategic_qualification.py") == freeze["source_hashes"]["runner"],
         "published runner snapshot differs from frozen code")
    need(freeze.get("source_freeze_sha256_lf_utf8") == sha_file(root / "source_freeze.json"),
         "source freeze digest mismatch")
    need(freeze.get("source_frozen_hashes") == source_freeze.get("hashes"),
         "original pre-dispatch hashes were not preserved")
    need(freeze.get("source_hashes") == source_freeze.get("source_hashes"),
         "original source code/input references were changed")
    need(freeze.get("hashes") == freeze.get("public_copy_hashes"),
         "published compatibility hashes differ from public-copy hashes")
    need(manifest.get("requests") == schedule and len(schedule) == 28,
         "public run manifest and schedule differ")
    need(manifest.get("configuration_by_model") == runner.configuration()
         and manifest.get("endpoint_formats") == runner.ENDPOINTS,
         "frozen configuration differs from first-party runner")
    runner.validate_inputs(materials, modules, examples)
    _audit_provenance(provenance)
    for value, label in ((freeze, "freeze"), (publication, "publication"), (materials, "materials"),
                         (modules, "prompt_modules"), (examples, "examples")):
        _walk_json_keys(value, label)

    need(publication.get("original_pre_dispatch_hashes") == source_freeze.get("hashes"),
         "publication metadata lost original frozen input hashes")
    need(publication.get("original_manifest_sha256_lf_utf8") == sha_file(root / "manifest.json")
         and publication.get("original_schedule_sha256_lf_utf8") == sha_file(root / "schedule.json"),
         "public manifest/schedule no longer matches original source artifacts")
    need(publication.get("public_copy_hashes") == freeze.get("public_copy_hashes"),
         "public-copy hash maps disagree")
    for relative, digest in freeze.get("public_copy_hashes", {}).items():
        path = root.joinpath(*PurePosixPath(_safe_relpath(relative)).parts)
        need(path.is_file() and sha_file(path) == digest, f"public-copy hash mismatch: {relative}")
    for relative, digest in freeze.get("hashes", {}).items():
        path = root.joinpath(*PurePosixPath(_safe_relpath(relative)).parts)
        need(path.is_file() and sha_file(path) == digest, f"published run hash mismatch: {relative}")

    need(publication.get("reader_seat_by_case") == SEAT_BY_CASE
         and Counter(publication["reader_seat_by_case"].values()) == Counter({"A": 2, "B": 2}),
         "Reader labels are not the frozen balanced seat map")
    case_map = {case["case_id"]: case for case in materials["cases"]}
    need(set(case_map) == set(CASE_IDS), "public materials do not contain the four frozen families")
    partitions = {
        case_id: {
            region: [q["question_id"] for q in case_map[case_id]["questions"] if q["source_region"] == region]
            for region in ("explicit", "unspecified")
        }
        for case_id in CASE_IDS
    }
    need(publication.get("question_partition_by_case") == partitions, "question partition differs from published materials")
    for case_id in CASE_IDS:
        need(len(case_map[case_id]["questions"]) == 6 and len(partitions[case_id]["explicit"]) == 3
             and len(partitions[case_id]["unspecified"]) == 3, f"question-region schema invalid for {case_id}")

    ids = _request_ids()
    need({row["request_id"] for row in schedule} == ids, "public schedule request IDs are incomplete")
    need([row["schedule_index"] for row in schedule] == list(range(1, 29)), "public schedule order is invalid")
    need(Counter(row["kind"] for row in schedule) == Counter({"speaker": 12, "judge": 16}),
         "public schedule role counts differ from design")
    need(schedule == runner.build_schedule(materials["cases"], manifest["randomization_seed"]),
         "public schedule cannot be regenerated from the frozen seed")

    response_map = {}
    for row in schedule:
        request_id = row["request_id"]
        paths = [root / folder / f"{request_id}.{suffix}" for folder, suffix in (
            ("responses", "json"), ("dispatches", "json"), ("prompt_receipts", "json"), ("prompts", "txt"))]
        need(all(path.is_file() for path in paths), f"missing public artifact for {request_id}")
        response_map[request_id] = read_json(root / "responses" / f"{request_id}.json")

    for row in schedule:
        request_id = row["request_id"]
        response = response_map[request_id]
        dispatch = read_json(root / "dispatches" / f"{request_id}.json")
        prompt_receipt = read_json(root / "prompt_receipts" / f"{request_id}.json")
        prompt_path = root / "prompts" / f"{request_id}.txt"
        prompt = prompt_path.read_text(encoding="utf-8")
        expected_model = manifest["models"]["speaker" if row["kind"] == "speaker" else "judge"]
        need(row["model"] == expected_model, f"schedule model mismatch: {request_id}")
        need(response["request_id"] == request_id and response["model"] == row["model"]
             and response["returned_model"] == row["model"] and response["kind"] == row["kind"]
             and response["case_id"] == row["case_id"], f"response provenance mismatch: {request_id}")
        need(response["status"] == "response_received" and response["parse_status"] == "valid",
             f"nonvalid public response: {request_id}")
        parser = runner.parse_speaker if row["kind"] == "speaker" else runner.parse_judge
        parsed, parse_status = parser(response["visible_text"], response["finish_reason"])
        need(parse_status == "valid" and parsed == response["parsed"], f"current parser disagrees: {request_id}")
        need(sha_file(prompt_path) == response["prompt_sha256"] == dispatch["prompt_sha256"] == prompt_receipt["prompt_sha256"],
             f"model-facing prompt hash mismatch: {request_id}")
        need(dispatch["request_id"] == request_id and dispatch["model"] == row["model"]
             and dispatch["schedule_index"] == row["schedule_index"] and dispatch["kind"] == row["kind"]
             and dispatch["case_id"] == row["case_id"], f"dispatch provenance mismatch: {request_id}")
        dependencies = row.get("depends_on", [])
        expected_dependencies = {dependency: sha_file(root / "responses" / f"{dependency}.json")
                                 for dependency in dependencies}
        need(dispatch.get("dependencies", []) == dependencies
             and prompt_receipt.get("dependency_response_sha256", {}) == expected_dependencies
             and dispatch.get("dependency_response_sha256", {}) == expected_dependencies,
             f"dependency-response witness mismatch: {request_id}")
        need(prompt_receipt.get("path") == f"prompts/{request_id}.txt", f"prompt path metadata mismatch: {request_id}")
        need(set(response) <= SAFE_RESPONSE_KEYS and set(dispatch) <= SAFE_DISPATCH_KEYS
             and set(prompt_receipt) <= SAFE_PROMPT_RECEIPT_KEYS, f"unsafe receipt field in {request_id}")
        need(isinstance(response.get("usage"), dict) and response["usage"], f"usage missing for {request_id}")
        for receipt, label in ((response, "response"), (dispatch, "dispatch"), (prompt_receipt, "prompt receipt")):
            _walk_json_keys(receipt, f"{label}.{request_id}")

        if row["kind"] == "speaker":
            expected_prompt = runner.speaker_prompt(case_map[row["case_id"]], row["condition"], modules, examples)
        else:
            arm = row["bluffer_condition"]
            reader_id, bluffer_id = f"SP_{row['case_id']}_READER", f"SP_{row['case_id']}_{arm}"
            prefix = runner.judge_prefix(row, case_map[row["case_id"]], response_map[reader_id]["parsed"],
                                         response_map[bluffer_id]["parsed"], examples, modules)
            need(prompt_receipt.get("shared_prefix_sha256") == runner.sha_bytes(prefix.encode("utf-8")),
                 f"dynamic Judge prefix hash mismatch: {request_id}")
            expected_prompt = runner.judge_prompt(row, prefix, modules)
            case_input = _extract_case_input(prompt)
            need(set(case_input) == {"case_id", "title", "public_context", "questions_with_replies", "Q6_prompt_only"},
                 f"Judge prompt contains unexpected case fields: {request_id}")
            need(len(case_input["questions_with_replies"]) == 5
                 and [q["question_id"] for q in case_input["questions_with_replies"]] == [f"Q{i}" for i in range(1, 6)],
                 f"Judge prompt does not contain exactly Q1-Q5 replies: {request_id}")
            need(all(set(q) == {"question_id", "question", "A_reply", "B_reply"}
                     for q in case_input["questions_with_replies"]), f"Judge reply schema mismatch: {request_id}")
            need(set(case_input["Q6_prompt_only"]) == {"question_id", "question"}
                 and case_input["Q6_prompt_only"]["question_id"] == "Q6",
                 f"Q6 answer leaked or prompt-only witness missing: {request_id}")
        need(prompt == expected_prompt, f"model-facing prompt differs from frozen inputs: {request_id}")

    for case_id in CASE_IDS:
        for arm in ("B0", "B1"):
            j0 = read_json(root / "prompt_receipts" / f"JG_{case_id}_{arm}_J0.json")
            j1 = read_json(root / "prompt_receipts" / f"JG_{case_id}_{arm}_J1.json")
            need(j0.get("shared_prefix_sha256") == j1.get("shared_prefix_sha256"),
                 f"J0/J1 prompts do not share an exact prefix: {case_id}/{arm}")

    coverage = publication.get("coverage", {})
    need(coverage.get("planned_provider_requests") == 28 and coverage.get("dispatch_receipts") == 28
         and coverage.get("saved_responses") == 28 and coverage.get("valid_responses") == 28,
         "coverage summary does not establish 28/28 valid responses")
    need(coverage.get("by_kind") == {
        "speaker": {"planned": 12, "dispatched": 12, "responses": 12, "valid": 12},
        "judge": {"planned": 16, "dispatched": 16, "responses": 16, "valid": 16},
    }, "role coverage summary is incomplete")

    expected_files = set(STATIC_FILES)
    for request_id in ids:
        expected_files.update({f"prompts/{request_id}.txt", f"prompt_receipts/{request_id}.json",
                               f"responses/{request_id}.json", f"dispatches/{request_id}.json"})
    actual_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    need(actual_files == expected_files,
         f"public file allowlist mismatch; extra={sorted(actual_files-expected_files)} missing={sorted(expected_files-actual_files)}")
    checksums = {}
    for line in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        need(match is not None, "malformed content-hash manifest")
        checksums[match.group(2)] = match.group(1)
    need(set(checksums) == actual_files - {"SHA256SUMS.txt"}, "content-hash inventory differs")
    for relative, digest in checksums.items():
        path = root.joinpath(*PurePosixPath(_safe_relpath(relative)).parts)
        need(sha_file(path) == digest, f"public content hash mismatch: {relative}")
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in {".json", ".txt", ".md"}:
            text = path.read_text(encoding="utf-8")
            for machine_path in ("D:\\Storage\\", "C:\\Users\\", "/mnt/", "\\\\?\\"):
                need(machine_path not in text, f"machine-specific path in {path.relative_to(root)}")

    runner.audit(root)
    return {"hashed_files": len(checksums), "provider_requests": 28, "valid_responses": 28,
            "speakers": 12, "judges": 16, "balanced_reader_seats": SEAT_BY_CASE}


def _write_hashes(root: Path) -> None:
    files = sorted(path for path in root.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt")
    entries = [f"{sha_file(path)}  {path.relative_to(root).as_posix()}" for path in files]
    (root / "SHA256SUMS.txt").write_text("\n".join(entries) + "\n", encoding="utf-8", newline="\n")


def _export_once(runner) -> dict[str, Any]:
    need(not PUBLIC.exists(), "public export already exists; --export never overwrites")
    need(PUBLIC_PARENT.is_dir(), "published_runs directory is missing")
    stage = Path(tempfile.mkdtemp(prefix=".go_strategic_qualification28_20261008-", dir=PUBLIC_PARENT))
    try:
        export_meta = _copy_private_run(stage, runner)
        (stage / "README.md").write_text(_readme(), encoding="utf-8", newline="\n")
        publication = read_json(stage / "publication.json")
        publication["public_copy_hashes"] = export_meta["public_copy_hashes"]
        write_json(stage / "publication.json", publication)
        _write_hashes(stage)
        result = _audit_public(stage, runner=runner)
        need(not PUBLIC.exists(), "public export appeared during creation; refusing to replace it")
        stage.rename(PUBLIC)
    except Exception:
        parent = PUBLIC_PARENT.resolve()
        resolved = stage.resolve()
        need(resolved.parent == parent and stage.name.startswith(".go_strategic_qualification28_20261008-"),
             "temporary export cleanup path failed its boundary check")
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return _audit_public(PUBLIC, runner=runner)


def _readme() -> str:
    return """# Strategic qualification: public evidence

This package preserves the completed 28-request OpenCode Go qualification: 12 Speaker and 16 Judge calls across four hand-authored fictional source families. It includes the exact model-facing prompts, visible completions, safe usage/parser receipts, dispatch records, frozen inputs, and original schedule. Hidden reasoning, credentials, provider headers, account/session/process data, and launch logs are excluded.

Start with the separate [delivery](../../strategic_qualification/DELIVERY_20261008.md) and [offline analysis](../../strategic_qualification/analysis_20261008/RESULTS.md). Then read [publication metadata](publication.json), the original [frozen manifest](manifest.json), [schedule](schedule.json), and [protocol](../../strategic_qualification/PROTOCOL_20261008.md). The sanitized [materials](inputs/materials_20261008.json) include the fictional sources, gold answers, and question regions. The [role modules](inputs/PROMPT_MODULES_20261008.json) and [historical example packets](inputs/judge_examples_20261008.json) preserve model-facing text; selected public source hashes, excerpts, and limitations are under `provenance_public` in that examples file. Exact prompts, prompt receipts, dispatch receipts, and visible response receipts are in their standard run directories. `source_freeze.json` retains the original pre-dispatch freeze; `freeze.json` distinguishes original hashes from hashes of published copies. `SHA256SUMS.txt` covers all package files except itself.

The package establishes response coverage and preserves primary artifacts; scientific conclusions are reported separately. From the project root, run `python -X utf8 -B scripts/publish_strategic_qualification.py` to audit this package. The standard-library audit makes no provider calls and does not require the private source run.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", action="store_true", help="create the public package once; refuse overwrite")
    parser.add_argument("--audit", action="store_true", help="audit the existing public package (default)")
    args = parser.parse_args(argv)
    if args.export and args.audit:
        parser.error("choose either --export or --audit")
    try:
        runner = _load_runner()
        result = _export_once(runner) if args.export else _audit_public(PUBLIC, runner=runner)
        label = "EXPORT_OK" if args.export else "AUDIT_OK"
        print(label + " " + json.dumps(result, sort_keys=True))
    except (PublicationError, OSError, ValueError, KeyError, TypeError, AssertionError) as exc:
        print(f"publication error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
