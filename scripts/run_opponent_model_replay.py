"""Freeze and launch the bounded sixteen-call opponent behavior replay."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time
from uuid import uuid4

import run_strategic_qualification as transport


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "epistemic_boundary_mimicry"
DESIGN = BASE / "opponent_model_replay"
SOURCE = BASE / "published_runs/go_strategic_qualification28_20261008"
CODING = BASE / "strategic_qualification/analysis_20261008/answer_coding.json"
DEFAULT_RUN = BASE / "runs/opencode_go_20261008_opponent_model16_01"
CASES = ("SQ01", "SQ02", "SQ03", "SQ04")
ARMS = ("B0", "B1")
QIDS = tuple(f"Q{i}" for i in range(1, 7))
MODEL = "glm-5.3"
SEED = 2026100804
TOTAL = 16
read_json = transport.read_json
sha_file = transport.sha_file
dump = transport.durable_dump
write_bytes = transport.durable_bytes
now = transport.now


def configuration():
    return {"endpoint": "chat/completions", "model": MODEL, "temperature": .5,
            "max_tokens": 4096, "thinking": {"type": "enabled"},
            "reasoning_effort": "low", "stream": False, "tools": None,
            "timeout_seconds": 300, "max_concurrency": 1}


def parse_forecast(text: str, finish: str):
    if finish not in {"stop", "end_turn", "stop_sequence"}:
        return None, "truncated" if finish in {"length", "max_tokens", "token_limit"} else "invalid_forecast"
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None, "invalid_forecast"
    if not isinstance(value, dict) or set(value) != {"predictions", "reason"}:
        return None, "invalid_forecast"
    predictions = value["predictions"]
    if not isinstance(predictions, list) or len(predictions) != 6:
        return None, "invalid_forecast"
    for qid, item in zip(QIDS, predictions):
        if not isinstance(item, dict) or set(item) != {"question_id", "p_explicit_source_silence"} or item["question_id"] != qid:
            return None, "invalid_forecast"
        probability = item["p_explicit_source_silence"]
        if isinstance(probability, bool) or not isinstance(probability, (int, float)) or not math.isfinite(probability) or not 0 <= probability <= 1:
            return None, "invalid_forecast"
    if not isinstance(value["reason"], str) or not value["reason"].strip() or transport.word_count(value["reason"]) > 100:
        return None, "invalid_forecast"
    return value, "valid"


def make_prompt(target: str, modules: dict) -> str:
    settings = {"target_model": "qwen3.8-max", "temperature": .5,
                "max_tokens": 8192, "reasoning_controls": "omitted; deployment default",
                "six_answers_generated_together": True, "max_words_per_answer": 70}
    return transport.join_prompt(modules["forecaster"],
                                 transport.tagged_json("target_sampling", settings),
                                 transport.tagged_json("target_speaker_prompt", target),
                                 modules["event"], modules["output"])


def schedule():
    blocks = [(case, arm) for case in CASES for arm in ARMS]
    random.Random(SEED).shuffle(blocks)
    rows = []
    for repeat, sequence in ((1, blocks), (2, list(reversed(blocks)))):
        for case, arm in sequence:
            rid = f"OM_{case}_{arm}_R{repeat}"
            rows.append({"request_id": rid, "kind": "judge", "model": MODEL,
                         "case_id": case, "bluffer_condition": arm,
                         "judge_condition": "FORECAST", "repeat": repeat,
                         "schedule_index": len(rows) + 1,
                         "prompt_path": f"prompts/{rid}.txt"})
    return rows


def source_files():
    files = [Path(__file__).resolve(), Path(transport.__file__).resolve(),
             DESIGN / "PROTOCOL_20261008.md", DESIGN / "PROMPT_MODULES_20261008.json",
             CODING, SOURCE / "inputs/materials_20261008.json"]
    for case in CASES:
        for arm in ARMS:
            for folder, suffix in (("prompts", ".txt"), ("responses", ".json")):
                files.append(SOURCE / folder / f"SP_{case}_{arm}{suffix}")
    return files


def within(run: Path, relative: str):
    result = (run / relative).resolve()
    if not result.is_relative_to(run.resolve()):
        raise ValueError("Frozen artifact path escapes run")
    return result


def prepare(run: Path):
    if run.exists():
        raise SystemExit("Run already exists; refuse overwrite. Use --audit.")
    modules = read_json(DESIGN / "PROMPT_MODULES_20261008.json")
    assert set(modules) == {"forecaster", "event", "output"}
    sources = source_files()
    assert all(p.is_file() for p in sources)
    source_hashes = {p.relative_to(ROOT).as_posix(): sha_file(p) for p in sources}
    run.mkdir(parents=True)
    for folder in ("inputs/sq28/prompts", "inputs/sq28/responses", "prompts", "dispatches", "responses", "launch"):
        (run / folder).mkdir(parents=True)
    copies = [(DESIGN / "PROTOCOL_20261008.md", "inputs/PROTOCOL_20261008.md"),
              (DESIGN / "PROMPT_MODULES_20261008.json", "inputs/PROMPT_MODULES_20261008.json"),
              (SOURCE / "inputs/materials_20261008.json", "inputs/materials_20261008.json"),
              (CODING, "inputs/answer_coding.json"),
              (Path(__file__).resolve(), "inputs/run_opponent_model_replay.py"),
              (Path(transport.__file__).resolve(), "inputs/run_strategic_qualification.py")]
    for src, relative in copies:
        shutil.copyfile(src, run / relative)
    rows = schedule()
    for case in CASES:
        for arm in ARMS:
            name = f"SP_{case}_{arm}"
            for folder, suffix in (("prompts", ".txt"), ("responses", ".json")):
                shutil.copyfile(SOURCE / folder / (name + suffix), run / "inputs/sq28" / folder / (name + suffix))
    for row in rows:
        target_path = run / "inputs/sq28/prompts" / f"SP_{row['case_id']}_{row['bluffer_condition']}.txt"
        prompt = make_prompt(target_path.read_text(encoding="utf-8"), modules)
        write_bytes(run / row["prompt_path"], prompt.encode("utf-8"))
        row["prompt_sha256"] = sha_file(run / row["prompt_path"])
        row["source_target_prompt_sha256"] = sha_file(target_path)
    manifest = {"schema_version": 1, "study_id": "opponent_model16_20261008",
                "created_utc": now(), "planned_provider_requests": TOTAL,
                "model": MODEL, "configuration": configuration(), "randomization_seed": SEED,
                "source_run_id": SOURCE.name, "source_artifacts": source_hashes,
                "independent_material_families": 4, "requests": rows}
    dump(run / "manifest.json", manifest)
    dump(run / "schedule.json", rows)
    frozen_files = [p for p in run.rglob("*") if p.is_file()]
    freeze = {"schema_version": 1, "created_utc": now(), "experimental_requests_at_freeze": 0,
              "hashes": {p.relative_to(run).as_posix(): sha_file(p) for p in frozen_files},
              "source_hashes": {"runner": sha_file(Path(__file__).resolve()),
                                "transport_helper": sha_file(Path(transport.__file__).resolve())}}
    dump(run / "freeze.json", freeze)
    dump(run / "status.json", {"state": "PREPARED", "halt_reason": None,
                              "planned": TOTAL, "provider_requests": 0, "response_count": 0, "valid": 0})
    audit(run)


def audit(run: Path):
    freeze = read_json(run / "freeze.json")
    manifest = read_json(run / "manifest.json")
    rows = read_json(run / "schedule.json")
    assert freeze["experimental_requests_at_freeze"] == 0
    for rel, digest in freeze["hashes"].items():
        assert sha_file(within(run, rel)) == digest, f"Frozen hash mismatch: {rel}"
    assert sha_file(Path(__file__).resolve()) == freeze["source_hashes"]["runner"]
    assert sha_file(Path(transport.__file__).resolve()) == freeze["source_hashes"]["transport_helper"]
    for rel, digest in manifest["source_artifacts"].items():
        assert sha_file(within(ROOT, rel)) == digest, f"Source hash mismatch: {rel}"
    assert rows == manifest["requests"] and len(rows) == TOTAL
    assert manifest["configuration"] == configuration()
    expected = schedule()
    modules = read_json(run / "inputs/PROMPT_MODULES_20261008.json")
    for row, registered in zip(rows, expected):
        assert all(row[k] == v for k, v in registered.items())
        target_path = run / "inputs/sq28/prompts" / f"SP_{row['case_id']}_{row['bluffer_condition']}.txt"
        target = target_path.read_text(encoding="utf-8")
        assert "<source_text>" not in target and "<public_case>" in target and "<assigned_archive_packet>" in target
        assert sha_file(target_path) == row["source_target_prompt_sha256"]
        prompt_path = within(run, row["prompt_path"])
        assert prompt_path.read_text(encoding="utf-8") == make_prompt(target, modules)
        assert sha_file(prompt_path) == row["prompt_sha256"]
    for case in CASES:
        for arm in ARMS:
            pair = [r for r in rows if r["case_id"] == case and r["bluffer_condition"] == arm]
            assert len(pair) == 2 and pair[0]["prompt_sha256"] == pair[1]["prompt_sha256"]
    print(json.dumps({"offline_audit": "PASS", "planned": TOTAL, "new_provider_requests": 0}), flush=True)


def current_status(run: Path, state: str, reason=None):
    receipts = [read_json(p) for p in (run / "responses").glob("*.json")]
    value = {"state": state, "halt_reason": reason, "planned": TOTAL,
             "provider_requests": len(list((run / "dispatches").glob("*.json"))),
             "response_count": len(receipts), "valid": sum(r["parse_status"] == "valid" for r in receipts),
             "updated_utc": now()}
    if state == "COMPLETE_16_ATTEMPTED":
        value["completed_utc"] = now()
    dump(run / "status.json", value)
    return value


def execute(run: Path):
    audit(run)
    deadline = time.monotonic() + 30
    receipt_path = run / "launch/launch_receipt.private.json"
    while not receipt_path.exists() and time.monotonic() < deadline:
        time.sleep(.1)
    launch_receipt = read_json(receipt_path)
    assert launch_receipt["state"] == "LAUNCHED"
    assert launch_receipt["manifest_sha256"] == sha_file(run / "manifest.json")
    assert read_json(run / "status.json")["state"] == "PREPARED"
    assert not list((run / "dispatches").glob("*.json")) and not list((run / "responses").glob("*.json"))
    key = os.environ.get("OPENCODE_GO_API_KEY", "").strip()
    assert key, "Credential not configured; no request sent."
    lock = run / "execution.lock"
    os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    sessions = []
    try:
        current_status(run, "RUNNING")
        for row in read_json(run / "schedule.json"):
            rid = row["request_id"]
            target = run / "responses" / (rid + ".json")
            dispatch = run / "dispatches" / (rid + ".json")
            assert not target.exists() and not dispatch.exists(), "Refuse duplicate dispatch"
            prompt_path = within(run, row["prompt_path"])
            assert sha_file(prompt_path) == row["prompt_sha256"]
            session = "xia-omc-" + str(uuid4())
            sessions.append({"request_id": rid, "session_id": session})
            dump(run / "launch/session_mappings.private.json", sessions)
            dump(dispatch, {k: row[k] for k in ("request_id", "model", "kind", "case_id", "bluffer_condition", "repeat", "schedule_index", "prompt_sha256", "source_target_prompt_sha256")} | {"dispatched_utc": now()})
            current_status(run, "RUNNING")
            response = transport.call(row, prompt_path.read_text(encoding="utf-8"), row["prompt_sha256"], key, session)
            response["repeat"] = row["repeat"]
            if response["status"] == "response_received" and response["returned_model"] == MODEL:
                response["parsed"], response["parse_status"] = parse_forecast(response["visible_text"], response["finish_reason"])
            dump(target, response)
            halt = transport.halt_reason(response)
            if halt:
                value = current_status(run, "HALTED", halt)
                print(json.dumps(value), flush=True)
                return
            value = current_status(run, "RUNNING")
            print(json.dumps({"request_id": rid, "valid": value["valid"], "planned": TOTAL}), flush=True)
        print(json.dumps(current_status(run, "COMPLETE_16_ATTEMPTED")), flush=True)
    except BaseException as error:
        try:
            current_status(run, "HALTED", "local_fatal/" + type(error).__name__)
        except Exception:
            pass
        raise
    finally:
        lock.unlink(missing_ok=True)


def launch(run: Path):
    audit(run)
    assert os.name == "nt"
    assert read_json(run / "status.json")["state"] == "PREPARED"
    assert os.environ.get("OPENCODE_GO_API_KEY", "").strip(), "Existing environment credential unavailable"
    folder = run / "launch"
    receipt_path = folder / "launch_receipt.private.json"
    assert not receipt_path.exists() and not list((run / "dispatches").glob("*.json"))
    reservation = folder / "launcher_reservation.private"
    os.close(os.open(reservation, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    stdout_path, stderr_path = folder / "worker.stdout.private.log", folder / "worker.stderr.private.log"
    child = None
    published = False
    try:
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            child = subprocess.Popen([sys.executable, "-X", "utf8", "-B", str(Path(__file__).resolve()), "--run", str(run.resolve()), "--execute"],
                                     stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                     env=os.environ.copy(), close_fds=True,
                                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)
        dump(receipt_path, {"state": "LAUNCHED", "pid": child.pid, "host": os.environ.get("COMPUTERNAME"),
                           "launch_utc": now(), "manifest_sha256": sha_file(run / "manifest.json"),
                           "planned_provider_requests": TOTAL, "run_path": str(run.resolve()),
                           "command": "python -X utf8 -B scripts/run_opponent_model_replay.py --execute",
                           "stdout_path": str(stdout_path.resolve()), "stderr_path": str(stderr_path.resolve())})
        published = True
        print(json.dumps({"launch": "accepted", "pid": child.pid, "planned": TOTAL}), flush=True)
    except BaseException:
        if child is not None and not published:
            dump(receipt_path, {"state": "LAUNCH_FAILED", "pid": child.pid, "launch_utc": now()})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--audit", action="store_true")
    mode.add_argument("--launch", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    run = args.run.resolve()
    runs = (BASE / "runs").resolve()
    if not run.is_relative_to(runs) or run == runs:
        raise SystemExit("Run must be a specific directory beneath the owning project's runs directory")
    if args.prepare:
        prepare(run)
    elif args.audit:
        audit(run)
    elif args.launch:
        launch(run)
    else:
        execute(run)


if __name__ == "__main__":
    main()
