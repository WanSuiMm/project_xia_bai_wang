"""Offline allowlisted export and audit for the completed CSB30 run."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "epistemic_boundary_mimicry"
RUN = BASE / "runs/opencode_go_20261008_counterfactual_source_boundary30_01"
PUBLIC = BASE / "published_runs/go_counterfactual_source_boundary30_20261008"
RUN_ID = RUN.name
CASES = tuple(f"CS{i:02d}" for i in range(1, 7))
VERSIONS = ("V0", "V1")

COMMON_RESPONSE_KEYS = {
    "request_id", "model", "kind", "case_id", "prompt_sha256", "status", "sent_utc",
    "visible_text", "parsed", "parse_status", "returned_model", "usage", "finish_reason",
    "http_status", "elapsed_seconds", "captured_utc", "reader_seat",
}
SPEAKER_RESPONSE_KEYS = COMMON_RESPONSE_KEYS | {"condition", "speaker_condition"}
JUDGE_RESPONSE_KEYS = COMMON_RESPONSE_KEYS | {"reader_version", "bluffer_condition", "judge_condition"}
SPEAKER_DISPATCH_KEYS = {
    "request_id", "kind", "model", "case_id", "condition", "reader_seat", "depends_on",
    "prompt_path", "schedule_index", "prompt_sha256", "dependency_response_sha256", "dispatched_utc",
}
JUDGE_DISPATCH_KEYS = {
    "request_id", "kind", "model", "case_id", "reader_version", "reader_seat", "bluffer_condition",
    "judge_condition", "depends_on", "prompt_path", "schedule_index", "prompt_sha256",
    "dependency_response_sha256", "dispatched_utc",
}
PROMPT_RECEIPT_KEYS = {"request_id", "prompt_sha256", "dependency_response_sha256", "created_utc"}
PUBLIC_DEPENDENCY_KEYS = {
    "source_dependency_response_receipt_sha256_lf",
    "published_dependency_response_receipt_sha256_lf",
}
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
SOURCE_SNAPSHOT_MAP = {
    "epistemic_boundary_mimicry/counterfactual_source_boundary/materials_20261008.json": "inputs/materials_20261008.json",
    "epistemic_boundary_mimicry/counterfactual_source_boundary/PROMPT_MODULES_20261008.json": "inputs/PROMPT_MODULES_20261008.json",
    "epistemic_boundary_mimicry/counterfactual_source_boundary/PROTOCOL_20261008.md": "inputs/PROTOCOL_20261008.md",
    "scripts/run_counterfactual_source_boundary.py": "inputs/run_counterfactual_source_boundary.py",
    "scripts/run_strategic_qualification.py": "inputs/run_strategic_qualification.py",
    "scripts/analyze_counterfactual_source_boundary.py": "inputs/analyze_counterfactual_source_boundary.py",
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value.replace(b"\r\n", b"\n")).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    path.write_text(payload, encoding="utf-8", newline="\n")


def within(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    need(path != root.resolve(), "Expected a file path, not a root directory")
    return path


def module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec is not None and spec.loader is not None, f"Cannot load {path.name}")
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def scan(path: Path):
    raw = path.read_bytes()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Non-UTF8 public file: {path.name}") from exc
    for label, pattern in SCAN_PATTERNS.items():
        need(not re.search(pattern, content), f"Unsafe {label} in {path.name}")
    if path.suffix == ".json":
        def visit(value):
            if isinstance(value, dict):
                keys = {str(key).casefold() for key in value}
                need(not (keys & FORBIDDEN_KEYS), f"Unsafe metadata field in {path.name}")
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(read(path))


def expected_package_files(schedule: list[dict], source_freeze: dict) -> set[str]:
    expected = {
        "README.md", "manifest.json", "schedule.json", "source_freeze.json", "status.json",
        "publication.json", "analysis/summary.json", "analysis/public_verification.json",
        "analysis/RESULTS.md",
    }
    expected.update(source_freeze["hashes"])
    for row in schedule:
        rid = row["request_id"]
        for folder, suffix in (("prompts", ".txt"), ("prompt_receipts", ".json"),
                               ("dispatches", ".json"), ("responses", ".json")):
            expected.add(f"{folder}/{rid}{suffix}")
    return expected


def public_receipt_projection(source: dict, folder: str, schedule_row: dict,
                               public_response_hashes: dict[str, str]) -> dict:
    if folder == "responses":
        allowed = SPEAKER_RESPONSE_KEYS if schedule_row["kind"] == "speaker" else JUDGE_RESPONSE_KEYS
        need(set(source) == allowed, f"Unexpected response receipt fields: {schedule_row['request_id']}")
        return {key: source[key] for key in source if key in allowed}

    if folder == "dispatches":
        allowed = SPEAKER_DISPATCH_KEYS if schedule_row["kind"] == "speaker" else JUDGE_DISPATCH_KEYS
        need(set(source) == allowed, f"Unexpected dispatch receipt fields: {schedule_row['request_id']}")
        projection = {key: source[key] for key in source if key in allowed and key != "dependency_response_sha256"}
    elif folder == "prompt_receipts":
        need(set(source) == PROMPT_RECEIPT_KEYS, f"Unexpected prompt receipt fields: {schedule_row['request_id']}")
        projection = {key: source[key] for key in source if key != "dependency_response_sha256"}
    else:
        raise ValueError(f"Unexpected receipt folder: {folder}")

    source_deps = source["dependency_response_sha256"]
    need(set(source_deps) == set(schedule_row["depends_on"]),
         f"Dependency set mismatch: {schedule_row['request_id']}")
    projection["source_dependency_response_receipt_sha256_lf"] = source_deps
    projection["published_dependency_response_receipt_sha256_lf"] = {
        dep: public_response_hashes[dep] for dep in schedule_row["depends_on"]
    }
    # Keep the public projection readable in the same order as the source receipt,
    # with its two explicitly named dependency hash views at the end.
    return projection


def temp_receipt_for_frozen_runner(public_receipt: dict) -> dict:
    """Adapt explicit public dependency fields to the frozen runner's local schema."""
    result = {key: value for key, value in public_receipt.items()
              if key not in PUBLIC_DEPENDENCY_KEYS}
    if "published_dependency_response_receipt_sha256_lf" in public_receipt:
        result["dependency_response_sha256"] = public_receipt["published_dependency_response_receipt_sha256_lf"]
    return result


def rebuild_summary_from_public(package: Path) -> dict:
    """Run the frozen analyzer over a temporary root reconstructed from public files only."""
    manifest = read(package / "manifest.json")
    source_freeze = read(package / "source_freeze.json")
    schedule = read(package / "schedule.json")
    publication = read(package / "publication.json")
    with tempfile.TemporaryDirectory(prefix=".csb30-public-rebuild-", dir=package.parent) as temp_name:
        temp_root = Path(temp_name) / "repo"
        temp_root.mkdir()
        for source_rel, package_rel in publication["source_artifact_snapshots"].items():
            src = within(package, package_rel)
            dest = within(temp_root, source_rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)

        run = temp_root / "epistemic_boundary_mimicry" / "runs" / RUN_ID
        run.mkdir(parents=True)
        shutil.copyfile(package / "source_freeze.json", run / "freeze.json")
        shutil.copyfile(package / "status.json", run / "status.json")
        for rel in source_freeze["hashes"]:
            src, dest = within(package, rel), within(run, rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)

        public_response_hashes = {
            row["request_id"]: sha(package / f"responses/{row['request_id']}.json") for row in schedule
        }
        for row in schedule:
            rid = row["request_id"]
            for folder in ("responses", "dispatches", "prompt_receipts"):
                source_path = package / f"{folder}/{rid}.json"
                public_value = read(source_path)
                if folder == "responses":
                    local_value = public_value
                else:
                    local_value = temp_receipt_for_frozen_runner(public_value)
                write(run / f"{folder}/{rid}.json", local_value)
            prompt_source = package / f"prompts/{rid}.txt"
            shutil.copyfile(prompt_source, run / f"prompts/{rid}.txt")

        # Module names used inside the frozen analyzer are fixed. Remove any prior
        # import from the surrounding local audit before loading the reconstructed copy.
        for name in ("run_strategic_qualification", "csb30_runner_for_analysis"):
            sys.modules.pop(name, None)
        scripts_dir = temp_root / "scripts"
        sys.path.insert(0, str(scripts_dir))
        try:
            analyzer = module(
                f"csb30_public_analyzer_{id(package)}",
                scripts_dir / "analyze_counterfactual_source_boundary.py",
            )
            return analyzer.build_summary(run)
        finally:
            try:
                sys.path.remove(str(scripts_dir))
            except ValueError:
                pass
            for name in ("run_strategic_qualification", "csb30_runner_for_analysis"):
                sys.modules.pop(name, None)


def visible_hashes(package: Path, schedule: list[dict]) -> dict[str, str]:
    return {row["request_id"]: sha_text(read(package / f"responses/{row['request_id']}.json")["visible_text"])
            for row in schedule}


def check_bluffer_and_seats(package: Path, summary: dict):
    seats = {family["case_id"]: family["reader_seat"] for family in summary["family_evidence"]}
    counts = {seat: sum(value == seat for value in seats.values()) for seat in ("A", "B")}
    need(set(seats) == set(CASES) and counts == {"A": 3, "B": 3}, "Reader seats are not fixed and balanced 3/3")
    schedule = {row["request_id"]: row for row in read(package / "schedule.json")}
    outputs = {}
    for case in CASES:
        record = read(package / f"responses/SP_{case}_BLUFFER.json")
        outputs[case] = record["visible_text"]
        need(record["parsed"]["answer"], f"Empty frozen Bluffer output: {case}")
        shared_id = f"SP_{case}_BLUFFER"
        for version in VERSIONS:
            judge = schedule[f"JG_{case}_{version}"]
            need(shared_id in judge["depends_on"], f"Judge dependency does not reuse the frozen Bluffer: {case}/{version}")
            receipt = read(package / f"prompt_receipts/JG_{case}_{version}.json")
            need(receipt["published_dependency_response_receipt_sha256_lf"].get(shared_id) ==
                 sha(package / f"responses/{shared_id}.json"),
                 f"Judge prompt receipt does not bind the same frozen Bluffer: {case}/{version}")
    return seats, counts, outputs


def make_public_verification(package: Path, canonical: dict, summary_hash: str) -> dict:
    schedule = read(package / "schedule.json")
    seats, seat_counts, bluffer_outputs = check_bluffer_and_seats(package, canonical)
    need(canonical["run_state"] == "COMPLETE_30_ATTEMPTED" and
         canonical["dispatched_calls"] == 30 and canonical["response_receipt_count"] == 30 and
         canonical["valid"] == {"calls": 30, "speakers": 18, "judges": 12},
         "Publicly reconstructed run is not 30/30 complete")
    need(canonical["paired_primary_contrast"]["n_complete_families"] == 6,
         "Expected exactly six complete Reader-version pairs")
    need(canonical["status_counts_consistent"] and not canonical["invalid_receipts"] and
         not canonical["missing_request_ids"] and not canonical["not_dispatched_request_ids"] and
         not canonical["dispatched_without_receipt_ids"], "Canonical summary reports an incomplete ledger")
    return {
        "schema_version": 1,
        "study_id": canonical["study_id"],
        "offline_reconstruction": "PASS",
        "method": "The included frozen runner and analyzer were executed from a temporary repository layout reconstructed only from this public package. The runner audited every exact prompt and dependency; the analyzer rebuilt the canonical summary.",
        "canonical_summary_sha256_lf": summary_hash,
        "scheduled_calls": len(schedule),
        "dispatched_calls": canonical["dispatched_calls"],
        "response_receipts": canonical["response_receipt_count"],
        "strict_valid": canonical["valid"],
        "fixed_reader_seats": seats,
        "reader_seat_counts": seat_counts,
        "same_frozen_bluffer_visible_text_per_family": {case: True for case in CASES},
        "bluffer_visible_text_sha256_utf8": {case: sha_text(bluffer_outputs[case]) for case in CASES},
        "judge_metrics_by_reader_version": canonical["judge_metrics_by_reader_version"],
        "paired_primary_contrast": canonical["paired_primary_contrast"],
        "manual_coding_status": canonical["manual_coding_status"],
        "interpretation_limits": canonical["interpretation_limits"],
    }


def audit(package: Path = PUBLIC) -> dict:
    package = package.resolve()
    manifest = read(package / "manifest.json")
    schedule = read(package / "schedule.json")
    source_freeze = read(package / "source_freeze.json")
    public_freeze = read(package / "freeze.json")
    publication = read(package / "publication.json")
    status = read(package / "status.json")

    need(manifest["study_id"] == "counterfactual_source_boundary30_20261008" and
         manifest["planned_provider_requests"] == 30, "Unexpected study or planned sample size")
    need(len(schedule) == 30 and manifest["requests"] == schedule, "Manifest/schedule mismatch")
    ids = [row["request_id"] for row in schedule]
    need(len(set(ids)) == 30 and len(set(row["schedule_index"] for row in schedule)) == 30,
         "Duplicate request IDs or schedule positions")
    need(source_freeze["experimental_requests_at_freeze"] == 0, "Missing pre-request freeze witness")
    need(set(publication["source_artifact_snapshots"]) == set(manifest["source_artifacts"]) == set(SOURCE_SNAPSHOT_MAP),
         "Source artifact snapshot map is incomplete")
    need(publication["source_artifact_snapshots"] == SOURCE_SNAPSHOT_MAP,
         "Source artifact snapshot destinations changed")

    source_expected = set(source_freeze["hashes"])
    need(source_expected == {
        "manifest.json", "schedule.json", "inputs/analyze_counterfactual_source_boundary.py",
        "inputs/materials_20261008.json", "inputs/PROMPT_MODULES_20261008.json",
        "inputs/PROTOCOL_20261008.md", "inputs/run_counterfactual_source_boundary.py",
        "inputs/run_strategic_qualification.py",
        *(f"prompts/SP_{case}_{condition}.txt" for case in CASES
          for condition in ("BLUFFER", "READER_V0", "READER_V1")),
    }, "Original frozen input allowlist changed")
    for rel, digest in source_freeze["hashes"].items():
        path = within(package, rel)
        need(sha(path) == digest, f"Frozen scientific input changed: {rel}")
    for source_rel, package_rel in SOURCE_SNAPSHOT_MAP.items():
        need(manifest["source_artifacts"][source_rel] == sha(within(package, package_rel)),
             f"Frozen source snapshot mismatch: {source_rel}")

    expected = expected_package_files(schedule, source_freeze)
    actual = {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()}
    need(actual == expected | {"freeze.json"}, "Unexpected or missing public package files")
    need(set(public_freeze["hashes"]) == expected, "Public package hash allowlist is incomplete")
    need(public_freeze["hash_convention"] == "SHA256 with CRLF normalized to LF",
         "Unexpected public hash convention")
    for rel, digest in public_freeze["hashes"].items():
        path = within(package, rel)
        need(sha(path) == digest, f"Published file hash mismatch: {rel}")
        scan(path)
    scan(package / "freeze.json")
    need(publication["source_freeze_sha256_lf"] == sha(package / "source_freeze.json"),
         "Source freeze witness hash mismatch")
    need(publication["source_manifest_sha256_lf"] == source_freeze["hashes"]["manifest.json"],
         "Source manifest reference hash mismatch")

    by_id = {row["request_id"]: row for row in schedule}
    receipt_sections = ("prompt_receipts", "dispatches", "responses")
    source_hashes = publication["source_receipt_sha256_lf"]
    public_hashes = publication["published_projection_sha256_lf"]
    need(set(source_hashes) == set(receipt_sections) == set(public_hashes),
         "Receipt hash provenance sections are incomplete")
    source_prompts, public_prompts = publication["prompt_sha256_lf"]["source"], publication["prompt_sha256_lf"]["published"]
    need(set(source_prompts) == set(ids) and set(public_prompts) == set(ids), "Prompt hashes are incomplete")
    source_text_hashes = publication["visible_text_sha256_utf8"]["source"]
    public_text_hashes = publication["visible_text_sha256_utf8"]["published"]
    need(set(source_text_hashes) == set(ids) and set(public_text_hashes) == set(ids),
         "Visible output hashes are incomplete")

    public_response_hashes = {}
    for row in schedule:
        rid = row["request_id"]
        prompt = within(package, row["prompt_path"])
        prompt_digest = sha(prompt)
        need(source_prompts[rid] == public_prompts[rid] == prompt_digest,
             f"Exact prompt hash mismatch: {rid}")
        response = read(package / f"responses/{rid}.json")
        allowed_response = SPEAKER_RESPONSE_KEYS if row["kind"] == "speaker" else JUDGE_RESPONSE_KEYS
        need(set(response) == allowed_response, f"Unsafe or incomplete response receipt: {rid}")
        need(response["request_id"] == rid and response["kind"] == row["kind"] and
             response["model"] == row["model"] and response["case_id"] == row["case_id"] and
             response["prompt_sha256"] == prompt_digest and response["status"] == "response_received" and
             response["returned_model"] == row["model"] and response["http_status"] == 200 and
             response["parse_status"] == "valid", f"Response receipt binding failed: {rid}")
        need(public_text_hashes[rid] == sha_text(response["visible_text"]),
             f"Visible output hash mismatch: {rid}")
        need(source_text_hashes[rid] == public_text_hashes[rid],
             f"Visible output changed during export: {rid}")
        public_response_hashes[rid] = sha(package / f"responses/{rid}.json")

        for folder in receipt_sections:
            receipt_path = package / f"{folder}/{rid}.json"
            receipt = read(receipt_path)
            expected_keys = (
                (PROMPT_RECEIPT_KEYS - {"dependency_response_sha256"}) | PUBLIC_DEPENDENCY_KEYS
                if folder == "prompt_receipts" else
                ((SPEAKER_DISPATCH_KEYS if row["kind"] == "speaker" else JUDGE_DISPATCH_KEYS)
                 - {"dependency_response_sha256"}) | PUBLIC_DEPENDENCY_KEYS
                if folder == "dispatches" else allowed_response
            )
            need(set(receipt) == expected_keys, f"Unexpected public {folder} fields: {rid}")
            need(source_hashes[folder].get(rid) and public_hashes[folder].get(rid) == sha(receipt_path),
                 f"Receipt source/public projection provenance mismatch: {folder}/{rid}")
            if folder != "responses":
                need(receipt["request_id"] == rid and receipt["prompt_sha256"] == prompt_digest,
                     f"Prompt/dispatch binding failed: {folder}/{rid}")
                source_deps = receipt["source_dependency_response_receipt_sha256_lf"]
                published_deps = receipt["published_dependency_response_receipt_sha256_lf"]
                need(set(source_deps) == set(row["depends_on"]) == set(published_deps),
                     f"Dependency receipt set changed: {folder}/{rid}")
                need(source_deps == {dep: source_hashes["responses"][dep] for dep in row["depends_on"]},
                     f"Source dependency hash does not bind to its original response receipt: {folder}/{rid}")
                need(published_deps == {dep: public_response_hashes[dep] for dep in row["depends_on"]},
                     f"Published dependency hash does not bind: {folder}/{rid}")
                if folder == "dispatches":
                    need(receipt["schedule_index"] == row["schedule_index"] and
                         receipt["depends_on"] == row["depends_on"] and
                         receipt["prompt_path"] == row["prompt_path"] and
                         receipt["kind"] == row["kind"] and receipt["model"] == row["model"] and
                         receipt["case_id"] == row["case_id"] and
                         all(receipt.get(key) == row.get(key) for key in
                             ("condition", "reader_version", "reader_seat", "bluffer_condition", "judge_condition")
                             if key in row), f"Dispatch schedule changed: {rid}")

    for folder in receipt_sections:
        need(set(source_hashes[folder]) == set(ids) and set(public_hashes[folder]) == set(ids),
             f"Receipt provenance does not cover all calls: {folder}")
    need(status == {"state": "COMPLETE_30_ATTEMPTED", "halt_reason": None, "planned": 30,
                    "provider_requests": 30, "response_count": 30, "valid": 30,
                    "updated_utc": status.get("updated_utc")}, "Public status is not complete 30/30")
    need(publication["source_receipt_hash_note"] ==
         "source_receipt_sha256_lf identifies the original local receipt bytes; published_projection_sha256_lf hashes each allowlisted public JSON projection. They are recorded separately and are not asserted to be equal.",
         "Receipt hash semantics are missing or ambiguous")

    rebuilt = rebuild_summary_from_public(package)
    saved = read(package / "analysis/summary.json")
    need(rebuilt == saved, "Frozen analyzer did not reproduce the published canonical summary")
    need(publication["source_analysis_summary_sha256_lf"] == sha(package / "analysis/summary.json"),
         "Canonical summary source hash mismatch")
    verification = make_public_verification(package, rebuilt, sha(package / "analysis/summary.json"))
    need(read(package / "analysis/public_verification.json") == verification,
         "Public verification report does not reproduce")
    need((package / "analysis/RESULTS.md").read_text(encoding="utf-8") == results_markdown(rebuilt),
         "Generated public results report does not reproduce")
    return {"study_id": saved["study_id"], "planned": 30, "dispatched": 30,
            "strict_valid": saved["valid"], "family_material_units": 6,
            "public_file_count": len(actual), "reconstruction": "PASS"}


def results_markdown(summary: dict) -> str:
    metrics = summary["judge_metrics_by_reader_version"]
    contrast = summary["paired_primary_contrast"]
    v0, v1 = metrics["V0"], metrics["V1"]
    return (
        "# CSB30 public results\n\n"
        "The completed six-family qualification produced 30 strict-valid outputs: 18 Speaker calls and 12 Judge calls. "
        "The six authored fictional source pairs are the material units. Reader seats were fixed within each pair and balanced three per seat.\n\n"
        "| Reader source | Mean probability of true Reader | Mean realized-label Brier | Correct decisions / 6 | Coverage |\n"
        "| --- | ---: | ---: | ---: | ---: |\n"
        f"| V0 | {v0['mean_p_reader']:.6f} | {v0['mean_realized_label_brier']:.6f} | "
        f"{int(round(v0['decision_accuracy_all_valid'] * 6))}/6 | {v0['coverage']:.3f} |\n"
        f"| V1 | {v1['mean_p_reader']:.6f} | {v1['mean_realized_label_brier']:.6f} | "
        f"{int(round(v1['decision_accuracy_all_valid'] * 6))}/6 | {v1['coverage']:.3f} |\n\n"
        f"The paired primary contrast, equal-family mean pReader(V1) minus pReader(V0), was "
        f"{contrast['mean_p_reader_v1_minus_v0']:.6f} across {contrast['n_complete_families']} complete families.\n\n"
        f"Manual Reader-fidelity coding remains `{summary['manual_coding_status']}` in the frozen analysis. "
        "This is a descriptive qualification over six authored materials with one draw per condition. It does not establish a population effect, calibration, a general source-boundary result, or that a Judge directly detected source use. The two Judge packets share the same frozen Bluffer reply and Reader seat; each Judge saw only one packet.\n\n"
        "See [canonical summary](summary.json) for per-family evidence and [public verification](public_verification.json) for the standalone reconstruction record.\n"
    )


def export():
    need(not PUBLIC.exists(), "Public package already exists; default to offline audit")
    need(RUN.is_dir(), "Completed source run is unavailable")
    source_analyzer = module("csb30_source_analyzer_for_export", ROOT / "scripts/analyze_counterfactual_source_boundary.py")
    source_summary = source_analyzer.build_summary(RUN)
    source_summary_path = RUN / "analysis/summary.json"
    need(source_summary_path.is_file() and source_summary == read(source_summary_path),
         "Source summary does not reproduce from the frozen analyzer")
    need(source_summary["run_state"] == "COMPLETE_30_ATTEMPTED" and
         source_summary["valid"] == {"calls": 30, "speakers": 18, "judges": 12} and
         source_summary["status_counts_consistent"] and not source_summary["invalid_receipts"],
         "Source run is not complete and strict-valid")

    source_manifest = read(RUN / "manifest.json")
    source_schedule = read(RUN / "schedule.json")
    source_freeze = read(RUN / "freeze.json")
    source_status = read(RUN / "status.json")
    need(set(source_manifest["source_artifacts"]) == set(SOURCE_SNAPSHOT_MAP),
         "Unexpected source artifact set")
    need(source_status["state"] == "COMPLETE_30_ATTEMPTED" and
         (source_status["provider_requests"], source_status["response_count"], source_status["valid"]) == (30, 30, 30),
         "Source status does not report 30/30 complete")
    source_receipt_hashes = {folder: {} for folder in ("prompt_receipts", "dispatches", "responses")}
    for row in source_schedule:
        rid = row["request_id"]
        need((RUN / f"prompts/{rid}.txt").is_file(), f"Missing exact prompt: {rid}")
        for folder in source_receipt_hashes:
            path = RUN / f"{folder}/{rid}.json"
            need(path.is_file(), f"Missing source receipt: {folder}/{rid}")
            source_receipt_hashes[folder][rid] = sha(path)

    # Confirm one and only one frozen Bluffer response feeds both Judge prompts per family.
    seats = source_manifest["reader_seat_by_case"]
    need(seats == {"CS01": "A", "CS02": "A", "CS03": "B", "CS04": "A", "CS05": "B", "CS06": "B"} and
         sum(value == "A" for value in seats.values()) == 3 and sum(value == "B" for value in seats.values()) == 3,
         "Frozen Reader seats changed or are not balanced")
    for case in CASES:
        bluffer = read(RUN / f"responses/SP_{case}_BLUFFER.json")
        # The frozen runner audit reconstructs both prompts from this same response;
        # the explicit prompt receipts must bind that dependency in each case.
        for version in VERSIONS:
            prompt_receipt = read(RUN / f"prompt_receipts/JG_{case}_{version}.json")
            need(prompt_receipt["dependency_response_sha256"][f"SP_{case}_BLUFFER"] ==
                 sha(RUN / f"responses/SP_{case}_BLUFFER.json"), f"Bluffer dependency changed: {case}/{version}")
        need(isinstance(bluffer["visible_text"], str) and bluffer["visible_text"],
             f"Missing frozen Bluffer visible output: {case}")

    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".csb30-stage-", dir=PUBLIC.parent) as stage_name:
        stage = Path(stage_name)
        for rel in source_freeze["hashes"]:
            src, dest = within(RUN, rel), within(stage, rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
        shutil.copyfile(RUN / "freeze.json", stage / "source_freeze.json")
        shutil.copyfile(RUN / "status.json", stage / "status.json")
        (stage / "analysis").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_summary_path, stage / "analysis/summary.json")
        for row in source_schedule:
            src, dest = RUN / row["prompt_path"], stage / row["prompt_path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copyfile(src, dest)
            need(sha(dest) == sha(src), f"Prompt changed during copy: {row['request_id']}")

        response_projection_hashes = {}
        for row in source_schedule:
            rid = row["request_id"]
            raw = read(RUN / f"responses/{rid}.json")
            allowed = SPEAKER_RESPONSE_KEYS if row["kind"] == "speaker" else JUDGE_RESPONSE_KEYS
            need(set(raw) == allowed, f"Source response has unreviewed transport fields: {rid}")
            response_path = stage / f"responses/{rid}.json"
            write(response_path, {key: raw[key] for key in raw if key in allowed})
            response_projection_hashes[rid] = sha(response_path)
            prompt_path = stage / f"prompts/{rid}.txt"
            need(sha(prompt_path) == sha(RUN / row["prompt_path"]), f"Prompt changed during copy: {rid}")

        public_projection_hashes = {folder: {} for folder in source_receipt_hashes}
        for row in source_schedule:
            rid = row["request_id"]
            for folder in ("prompt_receipts", "dispatches"):
                raw = read(RUN / f"{folder}/{rid}.json")
                projection = public_receipt_projection(raw, folder, row, response_projection_hashes)
                dest = stage / f"{folder}/{rid}.json"
                write(dest, projection)
                public_projection_hashes[folder][rid] = sha(dest)
            public_projection_hashes["responses"][rid] = response_projection_hashes[rid]

        source_prompt_hashes = {row["request_id"]: sha(RUN / row["prompt_path"]) for row in source_schedule}
        published_prompt_hashes = {row["request_id"]: sha(stage / row["prompt_path"]) for row in source_schedule}
        source_text_hashes, published_text_hashes = {}, {}
        for row in source_schedule:
            rid = row["request_id"]
            source_text_hashes[rid] = sha_text(read(RUN / f"responses/{rid}.json")["visible_text"])
            published_text_hashes[rid] = sha_text(read(stage / f"responses/{rid}.json")["visible_text"])
            need(source_text_hashes[rid] == published_text_hashes[rid], f"Visible output changed: {rid}")

        write(stage / "publication.json", {
            "schema_version": 1,
            "study_id": source_manifest["study_id"],
            "source_run_id": RUN_ID,
            "scope": "Offline export of exact frozen scientific inputs, all 30 exact prompts, all final visible replies, and explicit safe receipt projections. No provider request or network operation is made.",
            "source_freeze_sha256_lf": sha(RUN / "freeze.json"),
            "source_manifest_sha256_lf": sha(RUN / "manifest.json"),
            "source_analysis_summary_sha256_lf": sha(source_summary_path),
            "source_artifact_snapshots": SOURCE_SNAPSHOT_MAP,
            "source_receipt_sha256_lf": source_receipt_hashes,
            "published_projection_sha256_lf": public_projection_hashes,
            "source_receipt_hash_note": "source_receipt_sha256_lf identifies the original local receipt bytes; published_projection_sha256_lf hashes each allowlisted public JSON projection. They are recorded separately and are not asserted to be equal.",
            "prompt_sha256_lf": {"source": source_prompt_hashes, "published": published_prompt_hashes},
            "visible_text_sha256_utf8": {"source": source_text_hashes, "published": published_text_hashes},
            "source_receipt_projection_policy": "Responses preserve exact visible_text and parsed values plus allowlisted model, timing, HTTP, usage, and parse metadata. Prompt/dispatch dependency fields name original-source and published-projection response hashes separately. Private launch/session records and hidden reasoning are excluded.",
        })

        (stage / "README.md").write_text(
            "# CSB30 public evidence\n\n"
            "This package contains the completed 30-call Counterfactual Source Boundary qualification: six fictional source families, 18 Qwen Speaker outputs, and 12 GLM Judge outputs. It preserves every exact prompt and final visible reply.\n\n"
            "Start with [results](analysis/RESULTS.md), then [canonical analysis](analysis/summary.json) and [public reconstruction record](analysis/public_verification.json). The exact per-call prompts, replies, and safe receipt projections are secondary evidence.\n\n"
            "Reader seats were fixed within each family and balanced three per seat. The same saved Bluffer reply appears in both Judge prompts for a family. Results remain descriptive over six authored materials; the frozen analyzer marks manual Reader-fidelity coding as pending.\n\n"
            "`source_freeze.json` preserves the pre-request hashes for the scientific inputs and 18 Speaker prompts. `publication.json` separately records original source receipt hashes, public projection hashes, exact prompt hashes, and visible-text hashes. A source receipt hash refers to the original local receipt bytes; it is not presented as the hash of a sanitized public projection.\n\n"
            "The source launch directory, credentials, machine paths, host/PID/session values, raw provider bodies, and hidden reasoning are excluded. The public package includes frozen source snapshots for offline reproduction. From the project root, run `python -X utf8 -B scripts/publish_counterfactual_source_boundary.py` to audit the package without network access. `--export` is only for the original local source checkout and refuses to overwrite an existing package.\n",
            encoding="utf-8", newline="\n")

        # The stage contains a canonical analysis copy and enough frozen code/data to
        # reproduce it without relying on ignored local run artifacts.
        rebuilt = rebuild_summary_from_public(stage)
        need(rebuilt == source_summary, "Public-only frozen reconstruction differs from source analysis")
        verification = make_public_verification(stage, rebuilt, sha(stage / "analysis/summary.json"))
        write(stage / "analysis/public_verification.json", verification)
        (stage / "analysis/RESULTS.md").write_text(results_markdown(rebuilt), encoding="utf-8", newline="\n")

        stage_files = {path.relative_to(stage).as_posix(): sha(path)
                       for path in stage.rglob("*") if path.is_file()}
        write(stage / "freeze.json", {
            "schema_version": 1,
            "hash_convention": "SHA256 with CRLF normalized to LF",
            "hashes": stage_files,
        })
        audit(stage)
        need(not PUBLIC.exists(), "Destination appeared during export; refuse overwrite")
        stage.rename(PUBLIC)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", action="store_true", help="create the allowlisted public package once")
    args = parser.parse_args()
    try:
        if args.export:
            export()
        result = audit()
        print(json.dumps({"offline_audit": "PASS", **result}, ensure_ascii=False, allow_nan=False))
    except (ValueError, KeyError, OSError, TypeError, UnicodeError, json.JSONDecodeError,
            AssertionError, AttributeError, ImportError) as exc:
        print(f"CSB30 publication audit failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
