"""Freeze and dispatch the bounded 48-call opponent-history inference study."""
from __future__ import annotations

import argparse
from fractions import Fraction
from itertools import product
import json
from math import prod
import os
from pathlib import Path
import random
import subprocess
import sys
from uuid import uuid4

import run_joint_epistemic_simulation as api
import run_joint_epistemic_supplement as formatting
import run_strategic_qualification as transport

ROOT, BASE = api.ROOT, api.BASE
DESIGN = BASE / "opponent_strategy_inference"
DEFAULT_RUN = BASE / "runs/opencode_go_20261009_opponent_strategy_inference48_01"
TOTAL, SEED = 48, 2026100902
MODELS = ("glm-5.3", "qwen3.8-max")
CONDITIONS = ("PERSISTENT", "REFRESHED")
HISTORIES = {1: "00100000", 4: "01101001", 7: "11011111"}
read, sha, now = api.read, api.sha, api.now
dump, write_bytes = api.dump, api.write_bytes


def oracle(s, condition, ones_seat):
    """Exact sequence predictive integration, not plug-in mean likelihoods."""
    assert s in HISTORIES and condition in CONDITIONS and ones_seat in ("A", "B")
    alpha, beta = 1+s, 9-s
    if condition == "PERSISTENT":
        lo, hi = prod(alpha+i for i in range(4)), prod(beta+i for i in range(4))
        p_ones = Fraction(hi, lo+hi)
        mean = Fraction(alpha, alpha+beta)
        plug_ones = (1-mean)**4 / ((1-mean)**4 + mean**4)
    else:
        p_ones = plug_ones = Fraction(1, 2)
    p_a = p_ones if ones_seat == "A" else 1-p_ones
    plug_a = plug_ones if ones_seat == "A" else 1-plug_ones
    return {"posterior_A": float(p_a), "posterior_A_exact": str(p_a),
            "posterior_1111": float(p_ones), "plugin_posterior_A": float(plug_a)}


def schedule():
    rows = []
    for model, condition, s, seat, repeat in product(MODELS, CONDITIONS, HISTORIES, ("A", "B"), (1, 2)):
        alias = "GLM" if model == MODELS[0] else "QWEN"
        packet = f"{condition}_H{s}_ONES{seat}"
        rid = f"OSI_{alias}_{packet}_R{repeat}"
        rows.append({"request_id": rid, "kind": "judge", "model": model, "case_id": packet,
                     "simulation_condition": condition, "bluffer_condition": condition,
                     "judge_condition": "UNKNOWN_PARAMETER_KNOWN_FAMILY",
                     "history_ones": s, "history": [int(x) for x in HISTORIES[s]],
                     "ones_seat": seat, "repeat": repeat,
                     "vector_A": [1 if seat == "A" else 0]*4,
                     "vector_B": [1 if seat == "B" else 0]*4,
                     "prompt_path": f"prompts/{rid}.txt", **oracle(s, condition, seat)})
    random.Random(SEED).shuffle(rows)
    for i, row in enumerate(rows, 1):
        row["schedule_index"] = i
    assert len(rows) == TOTAL
    return rows


def make_prompt(row, modules):
    archive = {"answers_in_chronological_order": row["history"]}
    packet = {"record_ids": ["Q1", "Q2", "Q3", "Q4"],
              "A_answers": row["vector_A"], "B_answers": row["vector_B"]}
    return transport.join_prompt(
        modules["common"], modules["archive"], modules[row["simulation_condition"].lower()],
        transport.tagged_json("archived_non_reader_answers", archive),
        transport.tagged_json("current_answers", packet), modules["decision"], modules["output"])


def status(run, state, reason=None):
    receipts = [read(p) for p in (run / "responses").glob("*.json")]
    out = {"state": state, "halt_reason": reason, "planned": TOTAL,
           "provider_requests": len(list((run / "dispatches").glob("*.json"))),
           "response_count": len(receipts),
           "valid": sum(r.get("completion_parse_status") == "valid" for r in receipts),
           "strict_valid": sum(r.get("parse_status") == "valid" for r in receipts),
           "format_exception_count": sum(r.get("format_acceptance") == "identical_duplicate_trailer" for r in receipts),
           "updated_utc": now()}
    dump(run / "status.json", out)
    return out


def source_paths():
    paths = [DESIGN / name for name in ("PROTOCOL_20261009.md", "PROMPT_MODULES_20261009.json", "THEORY_V2_20261009.md")]
    paths += [ROOT / "scripts" / name for name in (
        "run_opponent_strategy_inference.py", "analyze_opponent_strategy_inference.py",
        "test_opponent_strategy_inference.py", "check_opponent_strategy_theory.py",
        "run_joint_epistemic_simulation.py", "run_joint_epistemic_supplement.py",
        "run_counterfactual_source_boundary.py", "run_strategic_qualification.py")]
    return paths


def prepare(run):
    assert not run.exists(), "Refuse overwriting a run"
    paths = source_paths()
    assert all(p.is_file() for p in paths), "All sources and offline checks must exist before freeze"
    modules = read(DESIGN / "PROMPT_MODULES_20261009.json")
    assert set(modules) == {"common", "archive", "persistent", "refreshed", "decision", "output"}
    for folder in ("inputs", "prompts", "prompt_receipts", "dispatches", "responses", "launch"):
        (run / folder).mkdir(parents=True, exist_ok=True)
    for path in paths:
        write_bytes(run / "inputs" / path.relative_to(ROOT), path.read_bytes())
    rows = schedule()
    for row in rows:
        write_bytes(run / row["prompt_path"], make_prompt(row, modules).encode("utf8"))
    dump(run / "schedule.json", rows)
    dump(run / "manifest.json", {
        "schema_version": 1, "study_id": "opponent_strategy_inference48_20261009",
        "created_utc": now(), "planned_provider_requests": TOTAL, "randomization_seed": SEED,
        "configuration_by_model": api.configurations(), "timeout_seconds": 300, "max_concurrency": 1,
        "requests": rows, "source_artifacts": {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
        "format_exception": "identical_duplicate_trailer_only_v1",
        "retry_policy": "No retry or fallback; continue isolated format failures only",
        "weighting": "equal selected stimulus, separately by model/coupling; not population weighting"})
    dump(run / "freeze.json", {"created_utc": now(), "experimental_requests_at_freeze": 0,
         "hashes": {p.relative_to(run).as_posix(): sha(p) for p in run.rglob("*") if p.is_file()}})
    status(run, "PREPARED")
    audit(run)
    print(json.dumps({"prepared": True, "planned_provider_requests": TOTAL, "new_provider_requests": 0}))


def audit(run, live_sources=True):
    frozen, manifest = read(run / "freeze.json"), read(run / "manifest.json")
    assert frozen["experimental_requests_at_freeze"] == 0
    assert manifest["study_id"] == "opponent_strategy_inference48_20261009"
    assert manifest["planned_provider_requests"] == TOTAL
    assert manifest["configuration_by_model"] == api.configurations()
    for rel, digest in frozen["hashes"].items():
        assert sha(api.within(run, rel)) == digest, rel
    for rel, digest in manifest["source_artifacts"].items():
        assert sha(api.within(run / "inputs", rel)) == digest, rel
        if live_sources:
            assert sha(api.within(ROOT, rel)) == digest, rel
    rows = read(run / "schedule.json")
    assert rows == manifest["requests"] == schedule()
    modules = read(run / "inputs/epistemic_boundary_mimicry/opponent_strategy_inference/PROMPT_MODULES_20261009.json")
    ids = {r["request_id"] for r in rows}
    for folder in ("responses", "dispatches", "prompt_receipts"):
        assert {p.stem for p in (run / folder).glob("*.json")} <= ids
    for row in rows:
        rid = row["request_id"]
        assert (run / row["prompt_path"]).read_text(encoding="utf8") == make_prompt(row, modules)
        digest = sha(run / row["prompt_path"])
        dispatch = run / f"dispatches/{rid}.json"
        response = run / f"responses/{rid}.json"
        if dispatch.exists():
            item = read(dispatch)
            assert item == row | {"prompt_sha256": digest, "dispatched_utc": item["dispatched_utc"]}
            receipt = read(run / f"prompt_receipts/{rid}.json")
            assert receipt["request_id"] == rid and receipt["prompt_sha256"] == digest
        if response.exists():
            rec = read(response)
            assert dispatch.exists() and rec["prompt_sha256"] == digest
            for field in ("request_id", "model", "kind", "case_id", "simulation_condition", "bluffer_condition", "judge_condition"):
                assert rec[field] == row[field], (rid, field)
            if rec["status"] == "response_received" and rec.get("returned_model") == row["model"]:
                assert (rec["parsed"], rec["parse_status"]) == api.parse_response(rec["visible_text"], rec["finish_reason"])
                assert (rec["completion_parsed"], rec["completion_parse_status"], rec["format_acceptance"]) == formatting.parse_completion(rec["visible_text"], rec["finish_reason"])
    return manifest


def execute(run):
    audit(run)
    launch_receipt = transport.wait_for_launch_receipt(run)
    assert launch_receipt["manifest_sha256"] == sha(run / "manifest.json")
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
            rid, path = row["request_id"], run / row["prompt_path"]
            digest = sha(path)
            assert not (run / f"dispatches/{rid}.json").exists()
            session = "xia-osi-" + str(uuid4())
            sessions.append({"request_id": rid, "session_id": session})
            dump(run / "launch/session_mappings.private.json", sessions)
            dump(run / f"prompt_receipts/{rid}.json", {"request_id": rid, "prompt_sha256": digest, "created_utc": now()})
            dump(run / f"dispatches/{rid}.json", row | {"prompt_sha256": digest, "dispatched_utc": now()})
            status(run, "RUNNING")
            rec = api.provider_call(row, path.read_text(encoding="utf8"), digest, key, session)
            if rec["status"] == "response_received" and rec.get("returned_model") == row["model"]:
                value, parse, acceptance = formatting.parse_completion(rec["visible_text"], rec["finish_reason"])
                rec.update(completion_parsed=value, completion_parse_status=parse, format_acceptance=acceptance)
            else:
                rec.update(completion_parsed=None, completion_parse_status=rec["parse_status"], format_acceptance=None)
            dump(run / f"responses/{rid}.json", rec)
            halt = None
            if rec["status"] != "response_received" or rec.get("returned_model") != row["model"]:
                halt = transport.halt_reason(rec) or "delivery_or_model_failure"
            current = status(run, "HALTED" if halt else "RUNNING", halt)
            print(json.dumps({"request_id": rid, "state": current["state"],
                              "received": current["response_count"], "valid": current["valid"], "planned": TOTAL}), flush=True)
            if halt:
                break
        else:
            status(run, "COMPLETE_48_ATTEMPTED")
        subprocess.run([sys.executable, "-X", "utf8", "-B", str(ROOT / "scripts/analyze_opponent_strategy_inference.py"),
                        "--run", str(run)], check=True)
    except BaseException as exc:
        status(run, "HALTED", "local_fatal/" + type(exc).__name__)
        raise
    finally:
        lock.unlink(missing_ok=True)


def launch(run):
    audit(run)
    assert os.name == "nt" and read(run / "status.json")["state"] == "PREPARED"
    assert os.environ.get("OPENCODE_GO_API_KEY", "").strip(), "Credential unavailable; no worker launched"
    folder = run / "launch"
    assert not (folder / "launch_receipt.private.json").exists()
    assert not list((run / "dispatches").glob("*.json"))
    os.close(os.open(folder / "launcher_reservation.private", os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    out, err = folder / "worker.stdout.private.log", folder / "worker.stderr.private.log"
    with out.open("xb") as stdout, err.open("xb") as stderr:
        child = subprocess.Popen([sys.executable, "-X", "utf8", "-B", str(Path(__file__).resolve()), "--run", str(run), "--execute"],
            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, env=os.environ.copy(), close_fds=True,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)
    dump(folder / "launch_receipt.private.json", {
        "state": "LAUNCHED", "pid": child.pid, "host": os.environ.get("COMPUTERNAME"), "launch_utc": now(),
        "run_path": str(run), "manifest_sha256": sha(run / "manifest.json"), "planned_provider_requests": TOTAL,
        "command": "python -X utf8 -B scripts/run_opponent_strategy_inference.py --execute",
        "stdout_path": str(out), "stderr_path": str(err)})
    print(json.dumps({"launch": "accepted", "planned_provider_requests": TOTAL, "private_receipt_saved": True}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    modes = parser.add_mutually_exclusive_group(required=True)
    for name in ("prepare", "audit", "launch", "execute"):
        modes.add_argument("--"+name, action="store_true")
    args = parser.parse_args()
    run = args.run.resolve()
    run.relative_to((BASE / "runs").resolve())
    assert run != (BASE / "runs").resolve()
    if args.prepare:
        prepare(run)
    elif args.audit:
        audit(run)
        print(json.dumps({"offline_audit": "PASS", "planned": TOTAL, "new_provider_requests": 0}))
    elif args.launch:
        launch(run)
    else:
        execute(run)


if __name__ == "__main__":
    main()
