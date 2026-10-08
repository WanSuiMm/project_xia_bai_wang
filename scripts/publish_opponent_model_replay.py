"""Write-once OMC16 export; default is a credential-free public-only audit."""
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
RUN = BASE / "runs/opencode_go_20261008_opponent_model16_02"
FAILED = BASE / "runs/opencode_go_20261008_opponent_model16_01"
PUBLIC = BASE / "published_runs/go_opponent_model16_20261008"
RESPONSE_KEYS = {
    "request_id", "model", "kind", "case_id", "prompt_sha256", "status", "sent_utc",
    "visible_text", "parsed", "parse_status", "returned_model", "usage", "finish_reason",
    "bluffer_condition", "judge_condition", "http_status", "elapsed_seconds", "captured_utc", "repeat",
}
DISPATCH_KEYS = {
    "request_id", "model", "kind", "case_id", "bluffer_condition", "repeat",
    "schedule_index", "prompt_sha256", "source_target_prompt_sha256", "dispatched_utc",
}
FORBIDDEN_KEYS = {
    "authorization", "api_key", "x-api-key", "headers", "session_id", "session_ids",
    "account_id", "pid", "host", "absolute_path", "provenance_private", "reasoning_content",
    "hidden_reasoning", "raw_provider_body", "x-opencode-session",
}
PATTERNS = {
    "credential": r"oc_sk_[A-Za-z0-9_-]+|\bsk-[A-Za-z0-9_-]{20,}",
    "machine_path": r"(?i)\b[A-Z]:[\\/]|/(?:Users|home|mnt/[a-z])/",
    "private_session_url": r"https?://(?:arena\.ai/c/|chatgpt\.com/c/)",
    "ip_address": r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])",
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def within(root, relative):
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    need(path != root.resolve(), "Expected a file, not a root directory")
    return path


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def scan(path):
    text = path.read_text(encoding="utf-8")
    for label, pattern in PATTERNS.items():
        need(not re.search(pattern, text), f"Unsafe {label} in {path.name}")
    if path.suffix == ".json":
        def visit(value):
            if isinstance(value, dict):
                need(not (set(value) & FORBIDDEN_KEYS), f"Unsafe metadata field in {path.name}")
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(read(path))


def audit(package=PUBLIC):
    analyzer = module("omc16_public_analyzer", ROOT / "scripts/analyze_opponent_model_replay.py")
    runner = module("omc16_public_runner", ROOT / "scripts/run_opponent_model_replay.py")
    manifest, schedule = read(package / "manifest.json"), read(package / "schedule.json")
    original, frozen = read(package / "source_freeze.json"), read(package / "freeze.json")
    publication = read(package / "publication.json")
    need(manifest["study_id"] == "opponent_model16_20261008" and manifest["planned_provider_requests"] == 16,
         "Unexpected study or sample size")
    need(manifest["configuration"] == runner.configuration() and manifest["randomization_seed"] == runner.SEED,
         "Changed generation configuration")
    need(manifest["requests"] == schedule and len(schedule) == 16, "Changed schedule")
    need(original["experimental_requests_at_freeze"] == 0, "Missing pre-request freeze witness")
    need(original["source_hashes"] == {"runner": sha(ROOT / "scripts/run_opponent_model_replay.py"),
                                     "transport_helper": sha(ROOT / "scripts/run_strategic_qualification.py")},
         "Frozen collection code changed")
    for rel, digest in original["hashes"].items():
        need(sha(within(package, rel)) == digest, f"Original frozen-input hash changed: {rel}")
    for rel, digest in manifest["source_artifacts"].items():
        need(sha(within(ROOT, rel)) == digest, f"Repository dependency hash changed: {rel}")
    expected_files = set(original["hashes"]) | {
        "README.md", "source_freeze.json", "publication.json", "status.json", "failed_attempt.json",
        "analysis/summary.json", "analysis/RESULTS.md", "inputs/analyze_opponent_model_replay.py",
    }
    expected_files.update(f"{folder}/{row['request_id']}.json" for row in schedule
                          for folder in ("responses", "dispatches"))
    actual = {p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()}
    need(actual == expected_files | {"freeze.json"}, "Unexpected or missing public files")
    need(set(frozen["hashes"]) == expected_files, "Public hash allowlist is incomplete")
    for rel, digest in frozen["hashes"].items():
        path = within(package, rel)
        need(sha(path) == digest, f"Public-copy hash mismatch: {rel}")
        scan(path)
    scan(package / "freeze.json")
    need(sha(package / "source_freeze.json") == publication["original_recovery_freeze_sha256_lf"],
         "Original freeze witness changed")
    need(sha(package / "inputs/analyze_opponent_model_replay.py") == sha(ROOT / "scripts/analyze_opponent_model_replay.py"),
         "Analysis code does not match its published snapshot")

    rows, forecasts = {}, {}
    modules = read(package / "inputs/PROMPT_MODULES_20261008.json")
    for row, expected in zip(schedule, runner.schedule()):
        rid = row["request_id"]
        need(rid not in rows and all(row[k] == v for k, v in expected.items()), "Schedule ID/order mismatch")
        rows[rid] = row
        target = package / f"inputs/sq28/prompts/SP_{row['case_id']}_{row['bluffer_condition']}.txt"
        prompt = within(package, row["prompt_path"])
        need(sha(target) == row["source_target_prompt_sha256"] and sha(prompt) == row["prompt_sha256"],
             f"Prompt binding changed: {rid}")
        text = target.read_text(encoding="utf-8")
        need("<source_text>" not in text and "<public_case>" in text and "<assigned_archive_packet>" in text,
             "Target source-isolation markers changed")
        need(prompt.read_text(encoding="utf-8") == runner.make_prompt(text, modules), "Forecast prompt reconstruction failed")
        rec, dispatch = read(package / f"responses/{rid}.json"), read(package / f"dispatches/{rid}.json")
        need(set(rec) <= RESPONSE_KEYS and set(dispatch) <= DISPATCH_KEYS, "Unexpected receipt metadata")
        for key in ("request_id", "model", "kind", "case_id", "bluffer_condition", "repeat", "prompt_sha256"):
            need(rec[key] == row[key] == dispatch[key], f"Receipt mismatch: {rid}/{key}")
        need(dispatch["schedule_index"] == row["schedule_index"] and
             dispatch["source_target_prompt_sha256"] == row["source_target_prompt_sha256"], "Dispatch binding changed")
        need(rec["judge_condition"] == "FORECAST" and rec["status"] == "response_received" and
             rec["returned_model"] == "glm-5.3" and rec["http_status"] == 200, "Incomplete forecast")
        parsed, parse_status = analyzer.parse_forecast(rec["visible_text"], rec["finish_reason"])
        need(parse_status == "valid" and rec["parse_status"] == parse_status and rec["parsed"] == parsed,
             "Strict raw parsing failed")
        forecasts[rid] = {p["question_id"]: p["p_explicit_source_silence"] for p in parsed["predictions"]}
    need(len(rows) == 16, "Duplicate forecast IDs")
    for case in analyzer.CASES:
        for arm in analyzer.ARMS:
            need(rows[analyzer.request_id(case, arm, 1)]["prompt_sha256"] ==
                 rows[analyzer.request_id(case, arm, 2)]["prompt_sha256"], "Repeat inputs differ")

    answers, source_hashes = {}, {}
    source = ROOT / analyzer.SOURCE_REL
    for case in analyzer.CASES:
        for arm in analyzer.ARMS:
            name = f"SP_{case}_{arm}"
            for folder, suffix in (("prompts", ".txt"), ("responses", ".json")):
                copied, existing = package / f"inputs/sq28/{folder}/{name}{suffix}", source / folder / (name + suffix)
                rel = existing.relative_to(ROOT).as_posix()
                need(sha(copied) == sha(existing) == manifest["source_artifacts"][rel], "Original target copy changed")
            rec = read(package / f"inputs/sq28/responses/{name}.json")
            parsed = analyzer.parse_speaker(rec["visible_text"], rec["finish_reason"])
            need(rec["parse_status"] == "valid" and rec["parsed"] == parsed and
                 rec["returned_model"] == "qwen3.8-max", "Original Actor response changed")
            answers[case, arm] = parsed["answers"]
            source_hashes[f"{case}_{arm}"] = sha(source / f"responses/{name}.json")
    coding = package / "inputs/answer_coding.json"
    need(sha(coding) == analyzer.CODING_SHA == sha(analyzer.CODING), "Inherited coding changed")
    outcomes = {}
    for rec in read(coding)["records"]:
        if rec.get("role") not in analyzer.ARMS:
            continue
        key = rec["case_id"], rec["role"], rec["question_id"]
        need(key not in outcomes and rec["answer"] == answers[key[:2]][key[2]], "Coded answer mismatch")
        outcomes[key] = {"y": rec["source_silence_admission"], "region": rec["source_region"]}
    expected_outcomes = {(c, a, q) for c in analyzer.CASES for a in analyzer.ARMS for q in analyzer.QUESTIONS}
    need(set(outcomes) == expected_outcomes, "Expected exactly 48 target events")
    need([k for k, v in outcomes.items() if v["y"] is None] == [("SQ02", "B1", "Q6")], "Unresolved event changed")
    need(all(v["y"] in (0, None) for v in outcomes.values()), "Clear outcome labels changed")
    status = read(package / "status.json")
    need(status["state"] == "COMPLETE_16_ATTEMPTED" and
         (status["provider_requests"], status["response_count"], status["valid"]) == (16, 16, 16), "Incomplete recovery")
    execution = {"state": status["state"], "planned": 16, "dispatched": 16, "response_receipts": 16,
                 "runner_parse_valid": 16, "strict_valid": 16, "missing_dispatch_ids": [],
                 "dispatched_without_response_ids": [], "issues": []}
    rebuilt = analyzer.build_analysis((package, rows, forecasts, outcomes, source_hashes, sha(coding), execution))
    saved = read(package / "analysis/summary.json")
    need(saved["run_id"] == RUN.name, "Canonical analysis provenance changed")
    need(sha(package / "analysis/summary.json") == publication["canonical_analysis_sha256_lf"],
         "Canonical analysis source hash changed")
    rebuilt["run_id"] = saved["run_id"]  # Only the directory name differs in a public replay.
    need(rebuilt == saved, "Public analysis does not reproduce the canonical summary")
    need((package / "analysis/RESULTS.md").read_text(encoding="utf-8") == analyzer.markdown_report(saved),
         "Generated report does not reproduce")
    failure = read(package / "failed_attempt.json")
    need(failure["request_id"] == schedule[0]["request_id"] and failure["http_status"] == 403 and
         failure["provider_error_category"] == "payment" and failure["visible_model_reply_received"] is False and
         failure["dispatched"] == 1 and failure["unstarted"] == 15, "Original infrastructure failure changed")
    for folder in ("responses", "dispatches"):
        need(set(publication["source_receipt_hashes"][folder]) == set(rows), "Incomplete receipt provenance")
        need(set(publication["public_receipt_hashes"][folder]) == set(rows), "Incomplete public hash provenance")
        for rid in rows:
            need(sha(package / f"{folder}/{rid}.json") == publication["public_receipt_hashes"][folder][rid],
                 "Public receipt projection changed")
            need(publication["source_receipt_hashes"][folder][rid] ==
                 publication["public_receipt_hashes"][folder][rid],
                 "This fixed study's already-safe receipts must preserve their original bytes")
    return saved


def export():
    need(not PUBLIC.exists(), "Public package already exists; use the default audit")
    analyzer = module("omc16_export_analyzer", ROOT / "scripts/analyze_opponent_model_replay.py")
    rebuilt = analyzer.build_analysis(analyzer.audit_run(RUN))
    need(rebuilt == read(RUN / "analysis_complete/summary.json"), "Local canonical analysis differs")
    need(rebuilt["execution"]["strict_valid"] == 16 and not rebuilt["execution"]["issues"], "Incomplete source run")
    source_freeze, failed_freeze = read(RUN / "freeze.json"), read(FAILED / "freeze.json")
    for rel, digest in failed_freeze["hashes"].items():
        need(sha(within(FAILED, rel)) == digest, "Original failed freeze changed")
    old_manifest, manifest = read(FAILED / "manifest.json"), read(RUN / "manifest.json")
    need({k: v for k, v in old_manifest.items() if k != "created_utc"} ==
         {k: v for k, v in manifest.items() if k != "created_utc"}, "Recovery changed the design")
    schedule = read(RUN / "schedule.json")
    need(read(FAILED / "schedule.json") == schedule, "Recovery schedule changed")
    need(len(list((FAILED / "dispatches").glob("*.json"))) == 1 and
         len(list((FAILED / "responses").glob("*.json"))) == 1, "Original attempt ledger changed")
    rid = schedule[0]["request_id"]
    error = read(FAILED / f"responses/{rid}.json")
    failed_execution = analyzer.audit_run(FAILED)[-1]
    need(failed_execution["state"] == "HALTED" and failed_execution["dispatched"] == 1 and
         failed_execution["response_receipts"] == 1 and failed_execution["strict_valid"] == 0 and
         len(failed_execution["missing_dispatch_ids"]) == 15 and
         not failed_execution["dispatched_without_response_ids"], "Original failed status/counts changed")
    failed_dispatch = read(FAILED / f"dispatches/{rid}.json")
    for key in ("request_id", "model", "kind", "case_id", "bluffer_condition", "repeat", "prompt_sha256"):
        need(error[key] == failed_dispatch[key] == schedule[0][key], "Original failed receipt binding changed")
    need(failed_dispatch["schedule_index"] == 1 and failed_dispatch["source_target_prompt_sha256"] ==
         schedule[0]["source_target_prompt_sha256"], "Original failed dispatch position changed")
    need(error["status"] == "http_error" and error["http_status"] == 403 and
         error["provider_error_category"] == "payment" and not error["visible_text"], "Unexpected original failure")
    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".omc16-stage-", dir=PUBLIC.parent)).resolve()
    stage.relative_to(PUBLIC.parent.resolve())
    PUBLIC.resolve().relative_to(PUBLIC.parent.resolve())
    for rel in source_freeze["hashes"]:
        src, dest = within(RUN, rel), within(stage, rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    shutil.copyfile(RUN / "freeze.json", stage / "source_freeze.json")
    shutil.copyfile(RUN / "status.json", stage / "status.json")
    shutil.copyfile(ROOT / "scripts/analyze_opponent_model_replay.py", stage / "inputs/analyze_opponent_model_replay.py")
    (stage / "analysis").mkdir()
    for name in ("summary.json", "RESULTS.md"):
        shutil.copyfile(RUN / "analysis_complete" / name, stage / "analysis" / name)
    source_hashes, public_hashes = {}, {}
    for folder, allowed in (("responses", RESPONSE_KEYS), ("dispatches", DISPATCH_KEYS)):
        source_hashes[folder], public_hashes[folder] = {}, {}
        for row in schedule:
            rid = row["request_id"]
            source_path, dest = RUN / f"{folder}/{rid}.json", stage / f"{folder}/{rid}.json"
            rec = read(source_path)
            need(set(rec) <= allowed, f"Unexpected private receipt field: {rid}")
            write(dest, {k: v for k, v in rec.items() if k in allowed})
            source_hashes[folder][rid], public_hashes[folder][rid] = sha(source_path), sha(dest)
    write(stage / "failed_attempt.json", {
        "run_id": FAILED.name, "request_id": schedule[0]["request_id"],
        "state": "HALTED", "dispatched": 1, "unstarted": 15, "valid_forecasts": 0,
        "http_status": 403, "provider_error_category": "payment", "visible_model_reply_received": False,
        "charge_known": False, "original_response_sha256_lf": sha(FAILED / f"responses/{schedule[0]['request_id']}.json"),
        "original_freeze_sha256_lf": sha(FAILED / "freeze.json"),
        "note": "Infrastructure failure; raw account/error body is private. Separate identical recovery has 16 valid forecasts.",
    })
    write(stage / "publication.json", {
        "schema_version": 1, "study_id": "opponent_model16_20261008", "physical_requests_across_runs": 17,
        "original_recovery_freeze_sha256_lf": sha(RUN / "freeze.json"),
        "source_receipt_hashes": source_hashes, "public_receipt_hashes": public_hashes,
        "canonical_analysis_sha256_lf": sha(RUN / "analysis_complete/summary.json"),
        "scope": "Exact prompts/visible forecasts; safe receipt metadata. No new Actor samples or API calls during publication.",
    })
    (stage / "README.md").write_text(
        "# OMC16 public evidence\n\n"
        "Start with [results](../../opponent_model_replay/RESULTS_20261008.md) and "
        "[delivery](../../opponent_model_replay/DELIVERY_20261008.md), then "
        "[small summary](analysis/summary.json). Exact per-request files are secondary evidence.\n\n"
        "16 strict-valid GLM forecasts on eight old Qwen prompts; no new Speakers. Four authored families, "
        "two forecast repeats. B0 mean .0373, B1 .1292; every individual probability is below .5. "
        "Old coding: 47 clear non-admissions and one unresolved SQ02/B1/Q6. Three-family complete-case "
        "scores and four-family forecasts are distinct. No population calibration claim.\n\n"
        "The separate [initial failed attempt](failed_attempt.json) is HTTP 403/payment with no visible "
        "model reply, not a scientific outcome. Recovery preserves the design. Original hashes and "
        "public-copy hashes are separately recorded. Account/session/launch records, credentials, raw "
        "error bodies and hidden reasoning are excluded.\n\n"
        "From the repository root: `python -X utf8 -B scripts/publish_opponent_model_replay.py`. "
        "Default is public-only, offline and credential-free. `--export` requires original private "
        "sources and refuses overwrite.\n", encoding="utf-8", newline="\n")
    files = {p.relative_to(stage).as_posix(): sha(p) for p in stage.rglob("*") if p.is_file()}
    write(stage / "freeze.json", {"schema_version": 1, "hash_convention": "SHA256 with CRLF normalized to LF",
                                  "hashes": files})
    audit(stage)
    need(not PUBLIC.exists(), "Destination appeared during export; refuse overwrite")
    stage.rename(PUBLIC)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    try:
        if args.export:
            export()
        summary = audit()
        print(json.dumps({"offline_audit": "PASS", "valid_forecasts": summary["execution"]["strict_valid"],
                          "target_events": summary["coverage"]["historical_target_events"],
                          "clear_labels": summary["coverage"]["clear_labels"], "new_provider_requests": 0}))
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f"Publication audit failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
