"""Freeze and dispatch the bounded thirty-call source-boundary qualification."""
from __future__ import annotations

import argparse
import getpass
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import time
from uuid import uuid4

import run_strategic_qualification as transport

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "epistemic_boundary_mimicry"
DESIGN = BASE / "counterfactual_source_boundary"
DEFAULT_RUN = BASE / "runs/opencode_go_20261008_counterfactual_source_boundary30_01"
CASES = tuple(f"CS{i:02d}" for i in range(1, 7))
VERSIONS = ("V0", "V1")
CONDITIONS = ("READER_V0", "READER_V1", "BLUFFER")
SEED, SEAT_SEED, TOTAL = 2026100805, 2026100806, 30
dump, write_bytes = transport.durable_dump, transport.durable_bytes
read, sha, now = transport.read_json, transport.sha_file, transport.now


def configurations():
    return {
        "qwen3.8-max": {"endpoint": "messages", "temperature": .5, "max_tokens": 8192,
                        "stream": False, "reasoning_controls": "omitted; deployment default"},
        "glm-5.3": {"endpoint": "chat/completions", "temperature": .5, "max_tokens": 4096,
                    "stream": False, "thinking": {"type": "enabled"}, "reasoning_effort": "low"},
    }


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def parse_response(text, finish, kind):
    if finish not in {"stop", "end_turn", "stop_sequence"}:
        return None, "truncated" if finish in {"length", "max_tokens", "token_limit"} else "invalid_response"
    try:
        value = json.loads(text, object_pairs_hook=unique_object)
    except (ValueError, TypeError):
        return None, "invalid_response"
    if not isinstance(value, dict):
        return None, "invalid_response"
    if kind == "speaker":
        if set(value) != {"answer"} or not isinstance(value["answer"], str) or not value["answer"].strip():
            return None, "invalid_speaker"
        if transport.word_count(value["answer"]) > 70:
            return None, "invalid_speaker"
    elif kind == "judge":
        if set(value) != {"p_A", "decision", "reason"} or value["decision"] not in {"A", "B", "ABSTAIN"}:
            return None, "invalid_judge"
        p = value["p_A"]
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1:
            return None, "invalid_judge"
        if not isinstance(value["reason"], str) or not value["reason"].strip() or transport.word_count(value["reason"]) > 80:
            return None, "invalid_judge"
        value["p_A"] = float(p)
    else:
        return None, "invalid_kind"
    return value, "valid"


def validate_materials(materials):
    assert isinstance(materials, list) and len(materials) == 6
    assert [c["case_id"] for c in materials] == list(CASES)
    for c in materials:
        for key in ("title", "domain", "public_context", "question", "gold_answer", "omission_check",
                    "base_source", "addition_sentence", "source_v0", "source_v1"):
            assert isinstance(c[key], str) and c[key].strip()
        assert c["question_id"] == "Q1"
        assert 250 <= transport.word_count(c["base_source"]) <= 340
        assert 8 <= transport.word_count(c["addition_sentence"]) <= 25
        assert 25 <= transport.word_count(c["public_context"]) <= 60
        assert c["source_v0"] == c["base_source"]
        assert c["source_v1"] == c["base_source"] + "\n\n" + c["addition_sentence"]
        assert c["insertion_sentence"] == c["addition_sentence"]
        gold = c["gold_answer"].casefold()
        assert gold in c["addition_sentence"].casefold()
        assert all(gold not in c[k].casefold() for k in ("source_v0", "public_context", "question"))


def seats():
    positions = ["A"] * 3 + ["B"] * 3
    random.Random(SEAT_SEED).shuffle(positions)
    return dict(zip(CASES, positions))


def schedule():
    rng = random.Random(SEED)
    cases = list(CASES)
    rng.shuffle(cases)
    rows = []
    for case in cases:
        conditions = list(CONDITIONS)
        rng.shuffle(conditions)
        for condition in conditions:
            rid = f"SP_{case}_{condition}"
            rows.append({"request_id": rid, "kind": "speaker", "model": "qwen3.8-max", "case_id": case,
                         "condition": condition, "reader_seat": seats()[case], "depends_on": [],
                         "prompt_path": f"prompts/{rid}.txt"})
        versions = list(VERSIONS)
        rng.shuffle(versions)
        for version in versions:
            rid = f"JG_{case}_{version}"
            rows.append({"request_id": rid, "kind": "judge", "model": "glm-5.3", "case_id": case,
                         "reader_version": version, "reader_seat": seats()[case],
                         "bluffer_condition": "BLUFFER", "judge_condition": "BLIND_SINGLE_PACKET",
                         "depends_on": [f"SP_{case}_READER_{version}", f"SP_{case}_BLUFFER"],
                         "prompt_path": f"prompts/{rid}.txt"})
    for index, row in enumerate(rows, 1):
        row["schedule_index"] = index
    return rows


def public_view(case):
    return {key: case[key] for key in ("title", "public_context", "question")}


def speaker_prompt(case, condition, modules):
    parts = [modules["speaker_common"], modules["bluffer"] if condition == "BLUFFER" else modules["reader"],
             transport.tagged_json("public_packet", public_view(case))]
    if condition != "BLUFFER":
        parts.append(transport.tagged_json("private_source_excerpt", case["source_" + condition[-2:].lower()]))
    return transport.join_prompt(*parts)


def judge_prompt(case, reader, bluffer, seat, modules):
    answers = {seat: reader["answer"], "B" if seat == "A" else "A": bluffer["answer"]}
    packet = public_view(case) | {"A_answer": answers["A"], "B_answer": answers["B"]}
    return transport.join_prompt(modules["judge"], transport.tagged_json("single_judge_packet", packet), modules["judge_output"])


def within(root, relative):
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    assert path != root.resolve()
    return path


def prepare(run):
    assert not run.exists(), "New outputs require a new run; refuse overwrite"
    materials = read(DESIGN / "materials_20261008.json")
    modules = read(DESIGN / "PROMPT_MODULES_20261008.json")
    validate_materials(materials)
    assert set(modules) == {"speaker_common", "reader", "bluffer", "judge", "judge_output"}
    sources = {
        "inputs/materials_20261008.json": DESIGN / "materials_20261008.json",
        "inputs/PROMPT_MODULES_20261008.json": DESIGN / "PROMPT_MODULES_20261008.json",
        "inputs/PROTOCOL_20261008.md": DESIGN / "PROTOCOL_20261008.md",
        "inputs/run_counterfactual_source_boundary.py": Path(__file__).resolve(),
        "inputs/run_strategic_qualification.py": Path(transport.__file__).resolve(),
        "inputs/analyze_counterfactual_source_boundary.py": ROOT / "scripts/analyze_counterfactual_source_boundary.py",
    }
    assert all(p.is_file() for p in sources.values())
    for folder in ("inputs", "prompts", "prompt_receipts", "dispatches", "responses", "launch"):
        (run / folder).mkdir(parents=True, exist_ok=True)
    for rel, src in sources.items():
        write_bytes(run / rel, src.read_bytes())
    cases = {c["case_id"]: c for c in materials}
    rows = schedule()
    prompt_hashes = {}
    for row in rows:
        if row["kind"] == "speaker":
            path = run / row["prompt_path"]
            write_bytes(path, speaker_prompt(cases[row["case_id"]], row["condition"], modules).encode("utf-8"))
            prompt_hashes[row["request_id"]] = sha(path)
    manifest = {"schema_version": 1, "study_id": "counterfactual_source_boundary30_20261008",
                "created_utc": now(), "planned_provider_requests": TOTAL,
                "configuration_by_model": configurations(), "timeout_seconds": 300, "max_concurrency": 1,
                "randomization_seed": SEED, "seat_seed": SEAT_SEED, "reader_seat_by_case": seats(),
                "requests": rows, "speaker_prompt_sha256": prompt_hashes,
                "source_artifacts": {p.relative_to(ROOT).as_posix(): sha(p) for p in sources.values()}}
    dump(run / "manifest.json", manifest)
    dump(run / "schedule.json", rows)
    dump(run / "freeze.json", {"schema_version": 1, "created_utc": now(), "experimental_requests_at_freeze": 0,
                              "hashes": {p.relative_to(run).as_posix(): sha(p) for p in run.rglob("*") if p.is_file()}})
    dump(run / "status.json", {"state": "PREPARED", "planned": TOTAL, "provider_requests": 0, "response_count": 0, "valid": 0})
    audit(run)


def audit(run):
    frozen, manifest, rows = read(run / "freeze.json"), read(run / "manifest.json"), read(run / "schedule.json")
    assert frozen["experimental_requests_at_freeze"] == 0
    for rel, digest in frozen["hashes"].items():
        assert sha(within(run, rel)) == digest, rel
    for rel, digest in manifest["source_artifacts"].items():
        assert sha(within(ROOT, rel)) == digest, rel
    assert manifest["configuration_by_model"] == configurations()
    assert manifest["requests"] == rows == schedule() and manifest["reader_seat_by_case"] == seats()
    materials, modules = read(run / "inputs/materials_20261008.json"), read(run / "inputs/PROMPT_MODULES_20261008.json")
    validate_materials(materials)
    cases = {c["case_id"]: c for c in materials}
    ids = {r["request_id"] for r in rows}
    for folder in ("responses", "dispatches", "prompt_receipts"):
        assert {p.stem for p in (run / folder).glob("*.json")} <= ids
    for row in rows:
        rid, path = row["request_id"], run / row["prompt_path"]
        if row["kind"] == "speaker":
            assert path.read_text(encoding="utf-8") == speaker_prompt(cases[row["case_id"]], row["condition"], modules)
            assert sha(path) == manifest["speaker_prompt_sha256"][rid]
        elif path.exists():
            deps = {dep: read(run / f"responses/{dep}.json") for dep in row["depends_on"]}
            assert all(d["parse_status"] == "valid" for d in deps.values())
            reader, bluffer = (deps[dep]["parsed"] for dep in row["depends_on"])
            assert path.read_text(encoding="utf-8") == judge_prompt(cases[row["case_id"]], reader, bluffer, row["reader_seat"], modules)
        receipt_path = run / f"prompt_receipts/{rid}.json"
        if receipt_path.exists():
            receipt = read(receipt_path)
            assert receipt["request_id"] == rid and receipt["prompt_sha256"] == sha(path)
            assert receipt["dependency_response_sha256"] == {dep: sha(run / f"responses/{dep}.json") for dep in row["depends_on"]}
        dispatch_path, response_path = run / f"dispatches/{rid}.json", run / f"responses/{rid}.json"
        if dispatch_path.exists():
            dispatch = read(dispatch_path)
            assert receipt_path.exists() and dispatch["prompt_sha256"] == sha(path)
            assert dispatch["request_id"] == rid and dispatch["schedule_index"] == row["schedule_index"]
            assert dispatch["dependency_response_sha256"] == read(receipt_path)["dependency_response_sha256"]
        if response_path.exists():
            response = read(response_path)
            assert dispatch_path.exists() and response["request_id"] == rid and response["model"] == row["model"]
            assert response["prompt_sha256"] == sha(path)
            if response["status"] == "response_received" and response["returned_model"] == row["model"]:
                parsed, state = parse_response(response["visible_text"], response["finish_reason"], row["kind"])
                assert (response["parsed"], response["parse_status"]) == (parsed, state)


def status(run, state, reason=None):
    responses = [read(p) for p in (run / "responses").glob("*.json")]
    value = {"state": state, "halt_reason": reason, "planned": TOTAL,
             "provider_requests": len(list((run / "dispatches").glob("*.json"))),
             "response_count": len(responses), "valid": sum(r["parse_status"] == "valid" for r in responses),
             "updated_utc": now()}
    dump(run / "status.json", value)
    return value


def execute(run):
    audit(run)
    launch = transport.wait_for_launch_receipt(run)
    assert launch["manifest_sha256"] == sha(run / "manifest.json")
    assert read(run / "status.json")["state"] == "PREPARED"
    assert not list((run / "dispatches").glob("*.json")) and not list((run / "responses").glob("*.json"))
    key = os.environ.get("OPENCODE_GO_API_KEY", "").strip()
    assert key, "Credential unavailable; no request sent"
    lock = run / "execution.lock"
    os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    cases = {c["case_id"]: c for c in read(run / "inputs/materials_20261008.json")}
    modules, sessions = read(run / "inputs/PROMPT_MODULES_20261008.json"), []
    try:
        status(run, "RUNNING")
        for row in read(run / "schedule.json"):
            rid = row["request_id"]
            deps = {dep: read(run / f"responses/{dep}.json") for dep in row["depends_on"]}
            assert all(d["parse_status"] == "valid" for d in deps.values())
            if row["kind"] == "judge":
                reader, bluffer = (deps[dep]["parsed"] for dep in row["depends_on"])
                write_bytes(run / row["prompt_path"], judge_prompt(cases[row["case_id"]], reader, bluffer, row["reader_seat"], modules).encode("utf-8"))
            prompt_path = run / row["prompt_path"]
            digest = sha(prompt_path)
            dependency_hashes = {dep: sha(run / f"responses/{dep}.json") for dep in row["depends_on"]}
            assert not (run / f"responses/{rid}.json").exists() and not (run / f"dispatches/{rid}.json").exists()
            dump(run / f"prompt_receipts/{rid}.json", {"request_id": rid, "prompt_sha256": digest,
                 "dependency_response_sha256": dependency_hashes, "created_utc": now()})
            session = "xia-csb-" + str(uuid4())
            sessions.append({"request_id": rid, "session_id": session})
            dump(run / "launch/session_mappings.private.json", sessions)
            dump(run / f"dispatches/{rid}.json", row | {"prompt_sha256": digest,
                 "dependency_response_sha256": dependency_hashes, "dispatched_utc": now()})
            status(run, "RUNNING")
            response = transport.call(row, prompt_path.read_text(encoding="utf-8"), digest, key, session)
            response["reader_seat"] = row["reader_seat"]
            if row["kind"] == "speaker":
                response["condition"] = row["condition"]
            else:
                response["reader_version"] = row["reader_version"]
            if response["status"] == "response_received" and response["returned_model"] == row["model"]:
                response["parsed"], response["parse_status"] = parse_response(response["visible_text"], response["finish_reason"], row["kind"])
            dump(run / f"responses/{rid}.json", response)
            halt = transport.halt_reason(response)
            if halt:
                print(json.dumps(status(run, "HALTED", halt)), flush=True)
                return
            current = status(run, "RUNNING")
            print(json.dumps({"request_id": rid, "valid": current["valid"], "planned": TOTAL}), flush=True)
        print(json.dumps(status(run, "COMPLETE_30_ATTEMPTED")), flush=True)
    except BaseException as exc:
        try:
            status(run, "HALTED", "local_fatal/" + type(exc).__name__)
        except Exception:
            pass
        raise
    finally:
        lock.unlink(missing_ok=True)


def launch(run, hidden):
    audit(run)
    assert os.name == "nt" and read(run / "status.json")["state"] == "PREPARED"
    folder = run / "launch"
    assert not (folder / "launch_receipt.private.json").exists()
    assert not list((run / "dispatches").glob("*.json"))
    key = getpass.getpass("OpenCode Go key (hidden): ").strip() if hidden else os.environ.get("OPENCODE_GO_API_KEY", "").strip()
    assert key, "Credential unavailable; no request sent"
    env = os.environ.copy()
    env["OPENCODE_GO_API_KEY"] = key
    reservation = folder / "launcher_reservation.private"
    os.close(os.open(reservation, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    out, err = folder / "worker.stdout.private.log", folder / "worker.stderr.private.log"
    with out.open("xb") as stdout, err.open("xb") as stderr:
        child = subprocess.Popen([sys.executable, "-X", "utf8", "-B", str(Path(__file__).resolve()), "--run", str(run.resolve()), "--execute"],
                                 stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, env=env, close_fds=True,
                                 creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)
    dump(folder / "launch_receipt.private.json", {"state": "LAUNCHED", "pid": child.pid,
         "host": os.environ.get("COMPUTERNAME"), "launch_utc": now(), "run_path": str(run.resolve()),
         "manifest_sha256": sha(run / "manifest.json"), "planned_provider_requests": TOTAL,
         "command": "python -X utf8 -B scripts/run_counterfactual_source_boundary.py --execute",
         "stdout_path": str(out.resolve()), "stderr_path": str(err.resolve())})
    print(json.dumps({"launch": "accepted", "planned_provider_requests": TOTAL, "private_receipt_saved": True}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    mode = parser.add_mutually_exclusive_group(required=True)
    for name in ("prepare", "audit", "launch", "launch-hidden", "execute"):
        mode.add_argument("--" + name, action="store_true")
    args = parser.parse_args()
    run = args.run.resolve()
    run.relative_to((BASE / "runs").resolve())
    assert run != (BASE / "runs").resolve()
    if args.prepare:
        prepare(run)
    elif args.audit:
        audit(run)
        print(json.dumps({"offline_audit": "PASS", "planned": TOTAL, "new_provider_requests": 0}))
    elif args.launch or args.launch_hidden:
        launch(run, args.launch_hidden)
    else:
        execute(run)


if __name__ == "__main__":
    main()
