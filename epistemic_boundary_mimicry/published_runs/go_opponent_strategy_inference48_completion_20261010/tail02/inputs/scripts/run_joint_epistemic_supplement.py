"""One bounded, failure-selected JES32 completion batch; preserve original evidence."""
from __future__ import annotations

import argparse
import getpass
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4

import run_joint_epistemic_simulation as study

ROOT, BASE = study.ROOT, study.BASE
DEFAULT_PARENT = study.DEFAULT_RUN
DEFAULT_RUN = BASE / "runs/opencode_go_20261009_joint_epistemic_simulation32_supplement01"
AMENDMENT = study.DESIGN / "SUPPLEMENT_PROTOCOL_20261009.md"
TOTAL = 30
read, sha, now, dump, write_bytes = study.read, study.sha, study.now, study.dump, study.write_bytes


def parse_completion(text, finish):
    """Accept strict JSON or one exactly redundant, fully consumed trailer only."""
    parsed, strict_status = study.parse_response(text, finish)
    if strict_status == "valid":
        return parsed, "valid", "strict"
    if strict_status != "invalid_response" or not isinstance(text, str):
        return None, strict_status, None
    try:
        raw = text.lstrip()
        _, end = json.JSONDecoder().raw_decode(raw)
        value, status = study.parse_response(raw[:end], finish)
        if status != "valid":
            return None, strict_status, None
        match = re.fullmatch(
            r"<\|assistant\|>_p_A:(?P<p>[^\r\n]+)\n"
            r"decision:(?P<decision>A|B|ABSTAIN)\nreason:(?P<reason>[\s\S]+)_",
            raw[end:].strip(),
        )
        if match is None:
            return None, strict_status, None
        probability = json.loads(match["p"])
        if (not isinstance(probability, (int, float)) or isinstance(probability, bool)
                or not math.isfinite(probability) or not 0 <= probability <= 1
                or probability != value["p_A"] or match["decision"] != value["decision"]
                or match["reason"] != value["reason"]):
            return None, strict_status, None
        return value, "valid", "identical_duplicate_trailer"
    except (ValueError, TypeError, KeyError, OverflowError):
        return None, strict_status, None


def parent(run):
    name = read(run / "manifest.json")["parent_run_name"]
    assert Path(name).name == name
    result = study.within(BASE / "runs", name)
    assert result == DEFAULT_PARENT.resolve(), "This supplement targets only the authorized parent"
    return result


def selection(original):
    study.audit(original)
    rows = read(original / "schedule.json")
    retained, pending = [], []
    for row in rows:
        path = original / f"responses/{row['request_id']}.json"
        if path.exists():
            receipt = read(path)
            good = (receipt["status"] == "response_received" and receipt.get("http_status") == 200
                    and receipt.get("returned_model") == row["model"]
                    and receipt.get("parse_status") == "valid")
        else:
            good = False
        (retained if good else pending).append(row)
    assert len(retained) == 2 and len(pending) == TOTAL
    assert [r["schedule_index"] for r in retained] == [1, 2]
    assert [r["schedule_index"] for r in pending] == list(range(3, 33))
    assert read(original / "status.json")["state"] == "HALTED"
    assert len(list((original / "dispatches").glob("*.json"))) == 3
    assert len(list((original / "responses").glob("*.json"))) == 3
    return retained, pending


def prepare(run):
    assert run.resolve() == DEFAULT_RUN.resolve(), "Only the one authorized supplement directory is allowed"
    assert not run.exists(), "Refuse overwriting a run"
    retained, pending = selection(DEFAULT_PARENT)
    sources = {p: ROOT / p for p in read(DEFAULT_PARENT / "manifest.json")["source_artifacts"]}
    for path in (AMENDMENT, Path(__file__).resolve(), ROOT / "scripts/analyze_joint_epistemic_supplement.py"):
        sources[path.relative_to(ROOT).as_posix()] = path
    assert all(path.is_file() for path in sources.values())
    run.mkdir(exist_ok=False)
    for folder in ("inputs", "prompts", "prompt_receipts", "dispatches", "responses", "launch"):
        (run / folder).mkdir(parents=True, exist_ok=True)
    for rel, path in sources.items():
        write_bytes(run / "inputs" / path.name, path.read_bytes())
    for row in read(DEFAULT_PARENT / "schedule.json"):
        write_bytes(run / row["prompt_path"], (DEFAULT_PARENT / row["prompt_path"]).read_bytes())
    parent_paths = [DEFAULT_PARENT / name for name in ("manifest.json", "freeze.json", "schedule.json", "status.json")]
    parent_paths += list((DEFAULT_PARENT / "responses").glob("*.json"))
    parent_paths += list((DEFAULT_PARENT / "dispatches").glob("*.json"))
    for path in parent_paths:
        write_bytes(run / "inputs/parent" / path.relative_to(DEFAULT_PARENT), path.read_bytes())
    dump(run / "parent_schedule.json", read(DEFAULT_PARENT / "schedule.json"))
    dump(run / "schedule.json", pending)
    dump(run / "manifest.json", {
        "schema_version": 1, "study_id": "joint_epistemic_simulation32_supplement_20261009",
        "created_utc": now(), "parent_run_name": DEFAULT_PARENT.name,
        "parent_artifact_hashes": {p.relative_to(DEFAULT_PARENT).as_posix(): sha(p) for p in parent_paths},
        "retained_valid_ids": [r["request_id"] for r in retained],
        "planned_provider_requests": TOTAL, "requests": pending,
        "configuration_by_model": study.configurations(), "timeout_seconds": 300, "max_concurrency": 1,
        "source_artifacts": {rel: sha(path) for rel, path in sources.items()},
        "format_amendment": "identical_duplicate_trailer_only_v1",
        "selection_rule": "All 30 non-strict-valid original slots, frozen before supplementation",
        "retry_policy": "One new attempt per selected slot; no automatic retry or fallback",
    })
    dump(run / "freeze.json", {"created_utc": now(), "experimental_requests_at_freeze": 0,
        "hashes": {p.relative_to(run).as_posix(): sha(p) for p in run.rglob("*") if p.is_file()}})
    status(run, "PREPARED")
    audit(run)


def audit(run):
    assert run.resolve() == DEFAULT_RUN.resolve(), "Only the one authorized supplement directory is allowed"
    manifest, freeze = read(run / "manifest.json"), read(run / "freeze.json")
    assert freeze["experimental_requests_at_freeze"] == 0
    for rel, digest in freeze["hashes"].items():
        assert sha(study.within(run, rel)) == digest, rel
    for rel, digest in manifest["source_artifacts"].items():
        assert sha(study.within(ROOT, rel)) == digest, rel
    original = parent(run)
    retained, pending = selection(original)
    assert manifest["requests"] == read(run / "schedule.json") == pending
    assert manifest["retained_valid_ids"] == [r["request_id"] for r in retained]
    assert manifest["planned_provider_requests"] == TOTAL
    assert manifest["configuration_by_model"] == study.configurations()
    assert manifest["format_amendment"] == "identical_duplicate_trailer_only_v1"
    assert read(run / "parent_schedule.json") == read(original / "schedule.json")
    for rel, digest in manifest["parent_artifact_hashes"].items():
        assert sha(study.within(original, rel)) == digest, rel
        assert sha(study.within(run / "inputs/parent", rel)) == digest, rel
    for row in read(run / "parent_schedule.json"):
        assert (run / row["prompt_path"]).read_bytes() == (original / row["prompt_path"]).read_bytes()
    ids = {r["request_id"] for r in pending}
    for folder in ("responses", "dispatches", "prompt_receipts"):
        assert {p.stem for p in (run / folder).glob("*.json")} <= ids
    for row in pending:
        rid, digest = row["request_id"], sha(run / row["prompt_path"])
        dispatch_path = run / f"dispatches/{rid}.json"
        response_path = run / f"responses/{rid}.json"
        if dispatch_path.exists():
            dispatch = read(dispatch_path)
            assert dispatch == row | {"prompt_sha256": digest, "dispatched_utc": dispatch["dispatched_utc"]}
            prompt_receipt = read(run / f"prompt_receipts/{rid}.json")
            assert prompt_receipt["request_id"] == rid and prompt_receipt["prompt_sha256"] == digest
        if response_path.exists():
            receipt = read(response_path)
            assert dispatch_path.exists() and receipt["prompt_sha256"] == digest
            for field in ("request_id", "model", "kind", "case_id", "simulation_condition", "bluffer_condition", "judge_condition"):
                assert receipt[field] == row[field], field
            if receipt["status"] == "response_received" and receipt.get("returned_model") == row["model"]:
                strict_value, strict_status = study.parse_response(receipt["visible_text"], receipt["finish_reason"])
                assert (receipt["parsed"], receipt["parse_status"]) == (strict_value, strict_status)
                value, parse, acceptance = parse_completion(receipt["visible_text"], receipt["finish_reason"])
                assert (receipt["completion_parsed"], receipt["completion_parse_status"], receipt["format_acceptance"]) == (value, parse, acceptance)


def status(run, state, reason=None):
    receipts = [read(p) for p in (run / "responses").glob("*.json")]
    valid = sum(r.get("completion_parse_status") == "valid" for r in receipts)
    result = {"state": state, "halt_reason": reason, "planned": TOTAL,
        "provider_requests": len(list((run / "dispatches").glob("*.json"))), "response_count": len(receipts),
        "valid": valid, "strict_valid": sum(r.get("parse_status") == "valid" for r in receipts),
        "identical_duplicate_trailer_count": sum(r.get("format_acceptance") == "identical_duplicate_trailer" for r in receipts),
        "retained_original_valid": 2, "completion_valid_slots": 2 + valid, "updated_utc": now()}
    dump(run / "status.json", result)
    return result


def execute(run):
    audit(run)
    receipt = study.transport.wait_for_launch_receipt(run)
    assert receipt["manifest_sha256"] == sha(run / "manifest.json")
    assert read(run / "status.json")["state"] == "PREPARED"
    assert not list((run / "dispatches").glob("*.json"))
    key = os.environ.get("OPENCODE_GO_API_KEY", "").strip()
    assert key, "Credential unavailable; no request sent"
    lock = run / "execution.lock"
    os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    sessions = []
    try:
        status(run, "RUNNING")
        for row in read(run / "schedule.json"):
            rid = row["request_id"]
            prompt_path = run / row["prompt_path"]
            digest = sha(prompt_path)
            assert not (run / f"dispatches/{rid}.json").exists()
            session = "xia-jes-supplement-" + str(uuid4())
            sessions.append({"request_id": rid, "session_id": session})
            dump(run / "launch/session_mappings.private.json", sessions)
            dump(run / f"prompt_receipts/{rid}.json", {"request_id": rid, "prompt_sha256": digest, "created_utc": now()})
            dump(run / f"dispatches/{rid}.json", row | {"prompt_sha256": digest, "dispatched_utc": now()})
            status(run, "RUNNING")
            rec = study.provider_call(row, prompt_path.read_text(encoding="utf8"), digest, key, session)
            value, parse, acceptance = None, "not_received", None
            if rec["status"] == "response_received" and rec.get("returned_model") == row["model"]:
                value, parse, acceptance = parse_completion(rec["visible_text"], rec["finish_reason"])
            rec.update(completion_parsed=value, completion_parse_status=parse, format_acceptance=acceptance)
            dump(run / f"responses/{rid}.json", rec)
            # Isolated content/schema failures are recorded and do not block the other fixed slots.
            halt = None
            if rec["status"] != "response_received":
                halt = rec.get("provider_error_category") or rec["status"]
            elif rec.get("returned_model") != row["model"]:
                halt = "unexpected_model"
            current = status(run, "HALTED" if halt else "RUNNING", halt)
            print(json.dumps({"request_id": rid, "state": current["state"], "valid": current["valid"], "planned": TOTAL}), flush=True)
            if halt:
                return
        status(run, "COMPLETE_30_ATTEMPTED")
        audit(run)
        import analyze_joint_epistemic_supplement as analysis
        result = analysis.build_summary(run)
        dump(run / "analysis/completion_summary.json", result)
        print(json.dumps({"state": "COMPLETE_30_ATTEMPTED", "analysis_saved": True}), flush=True)
    except BaseException as exc:
        status(run, "HALTED", "local_fatal/" + type(exc).__name__)
        raise
    finally:
        lock.unlink(missing_ok=True)


def launch(run):
    audit(run)
    assert os.name == "nt" and read(run / "status.json")["state"] == "PREPARED"
    folder = run / "launch"
    assert not (folder / "launch_receipt.private.json").exists()
    key = getpass.getpass("OpenCode Go key (hidden): ").strip()
    assert key, "Credential unavailable; no worker launched"
    env = os.environ.copy()
    env["OPENCODE_GO_API_KEY"] = key
    os.close(os.open(folder / "launcher_reservation.private", os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    out, err = folder / "worker.stdout.private.log", folder / "worker.stderr.private.log"
    with out.open("xb") as stdout, err.open("xb") as stderr:
        child = subprocess.Popen([sys.executable, "-X", "utf8", "-B", str(Path(__file__).resolve()), "--run", str(run.resolve()), "--execute"],
            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, env=env, close_fds=True,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)
    dump(folder / "launch_receipt.private.json", {"state": "LAUNCHED", "pid": child.pid,
        "host": os.environ.get("COMPUTERNAME"), "launch_utc": now(), "run_path": str(run.resolve()),
        "manifest_sha256": sha(run / "manifest.json"), "planned_provider_requests": TOTAL,
        "command": "python -X utf8 -B scripts/run_joint_epistemic_supplement.py --execute",
        "stdout_path": str(out.resolve()), "stderr_path": str(err.resolve())})
    print(json.dumps({"launch": "accepted", "planned_provider_requests": TOTAL, "private_receipt_saved": True}), flush=True)


def self_test():
    original = read(DEFAULT_PARENT / "responses/JG_GLM_JJ_11_00.json")
    raw = original["visible_text"]
    assert study.parse_response(raw, "stop") == (None, "invalid_response")
    parsed, status_value, accepted = parse_completion(raw, "stop")
    assert status_value == "valid" and accepted == "identical_duplicate_trailer" and parsed["p_A"] == .5
    good = json.dumps(parsed)
    assert parse_completion(good, "stop") == (parsed, "valid", "strict")
    for invalid in (raw.replace("_p_A:0.5", "_p_A:0.6"), raw.replace("decision:ABSTAIN", "decision:A"),
                    raw + "extra", good + " explanation", raw.replace("_p_A:0.5", "_p_A:NaN"),
                    raw.replace("_p_A:0.5", "_p_A:true"), raw.replace("reason:The observed", "reason:Changed observed"),
                    raw.replace('{"p_A":0.5,', '{"p_A":0.5,"p_A":0.5,')):
        assert parse_completion(invalid, "stop")[1] != "valid"
    assert parse_completion(raw, "length")[1] != "valid"
    retained, pending = selection(DEFAULT_PARENT)
    assert len(retained) == 2 and len(pending) == 30
    print(json.dumps({"offline_smoke": "PASS", "planned_new_calls": TOTAL, "new_provider_requests": 0}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    modes = parser.add_mutually_exclusive_group(required=True)
    for name in ("prepare", "audit", "launch-hidden", "execute", "self-test"):
        modes.add_argument("--" + name, action="store_true")
    args = parser.parse_args()
    run = args.run.resolve()
    run.relative_to((BASE / "runs").resolve())
    assert run == DEFAULT_RUN.resolve(), "Only the one authorized supplement directory is allowed"
    if args.self_test:
        self_test()
    elif args.prepare:
        prepare(run)
        print(json.dumps({"prepared": True, "planned_new_calls": TOTAL, "new_provider_requests": 0}))
    elif args.audit:
        audit(run)
        print(json.dumps({"offline_audit": "PASS", "planned_new_calls": TOTAL}))
    elif args.launch_hidden:
        launch(run)
    else:
        execute(run)


if __name__ == "__main__":
    main()
