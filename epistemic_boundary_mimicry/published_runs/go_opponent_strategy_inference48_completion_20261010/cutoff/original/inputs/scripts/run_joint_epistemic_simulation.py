"""Freeze and launch 32 known-mechanism joint-response Judge calls."""
from __future__ import annotations

import argparse
import getpass
from itertools import product
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time
import urllib.error
import urllib.request
from uuid import uuid4

import run_strategic_qualification as transport
from run_counterfactual_source_boundary import parse_response as strict_parser

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "epistemic_boundary_mimicry"
DESIGN = BASE / "joint_epistemic_simulation"
DEFAULT_RUN = BASE / "runs/opencode_go_20261008_joint_epistemic_simulation32_01"
SEED, TOTAL = 2026100807, 32
MODELS = ("glm-5.3", "qwen3.8-max")
CONDITIONS = ("MARGINAL", "JOINT")
read, sha, now = transport.read_json, transport.sha_file, transport.now
dump, write_bytes = transport.durable_dump, transport.durable_bytes


def configurations():
    return {
        "glm-5.3": {"endpoint": "chat/completions", "temperature": .5, "max_tokens": 4096,
                    "thinking": {"type": "enabled"}, "reasoning_effort": "low", "stream": False},
        "qwen3.8-max": {"endpoint": "messages", "temperature": .5, "max_tokens": 8192,
                        "reasoning_controls": "omitted; deployment default", "stream": False},
    }


def parse_response(text, finish):
    return strict_parser(text, finish, "judge")


def packets():
    values = list(product((0, 1), repeat=2))
    rows = []
    for condition in CONDITIONS:
        def reader(y):
            return .5 if y[0] == y[1] else 0.0
        def bluffer(y):
            return .25 if condition == "MARGINAL" else reader(y)
        for a, b in product(values, repeat=2):
            la, lb = reader(a) * bluffer(b), bluffer(a) * reader(b)
            if not la + lb:
                continue
            label = "JM" if condition == "MARGINAL" else "JJ"
            rid = f"{label}_{a[0]}{a[1]}_{b[0]}{b[1]}"
            rows.append({"packet_id": rid, "simulation_condition": condition,
                         "vector_A": list(a), "vector_B": list(b),
                         "likelihood_reader_A": la, "likelihood_reader_B": lb,
                         "prior_predictive_weight": (la + lb) / 2,
                         "posterior_A": la / (la + lb)})
    assert len(rows) == 16
    for condition, count in (("MARGINAL", 12), ("JOINT", 4)):
        group = [r for r in rows if r["simulation_condition"] == condition]
        assert len(group) == count and sum(r["prior_predictive_weight"] for r in group) == 1
        accuracy = sum(r["prior_predictive_weight"] * max(r["posterior_A"], 1-r["posterior_A"]) for r in group)
        brier = sum(r["prior_predictive_weight"] * r["posterior_A"] * (1-r["posterior_A"]) for r in group)
        assert accuracy == (.75 if condition == "MARGINAL" else .5)
        assert brier == (.125 if condition == "MARGINAL" else .25)
    return rows


def schedule():
    rows = []
    for model in MODELS:
        alias = "GLM" if model == "glm-5.3" else "QWEN"
        for packet in packets():
            row = packet | {"request_id": f"JG_{alias}_{packet['packet_id']}", "kind": "judge",
                            "model": model, "case_id": packet["packet_id"],
                            "bluffer_condition": packet["simulation_condition"],
                            "judge_condition": "KNOWN_MECHANISM"}
            row["prompt_path"] = f"prompts/{row['request_id']}.txt"
            rows.append(row)
    random.Random(SEED).shuffle(rows)
    for i, row in enumerate(rows, 1):
        row["schedule_index"] = i
    assert len(rows) == TOTAL
    return rows


def make_prompt(row, modules):
    names = ("copper", "slate")
    def replies(vector):
        return [{"question_id": "Q1", "answer": names[vector[0]]},
                {"question_id": "Q2", "answer": names[vector[1]]}]
    visible = {"context": "A fictional harbor's morning and evening audit stamp entries.",
               "questions": [{"question_id": "Q1", "question": "Which stamp is listed for the morning audit?"},
                             {"question_id": "Q2", "question": "Which stamp is listed for the evening audit?"}],
               "A_replies": replies(row["vector_A"]), "B_replies": replies(row["vector_B"])}
    return transport.join_prompt(modules["common"], modules[row["simulation_condition"].lower()],
                                 transport.tagged_json("observed_packet", visible), modules["decision"], modules["output"])


def within(root, relative):
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    assert path != root.resolve()
    return path


def prepare(run):
    assert not run.exists(), "Refuse overwriting a run"
    modules = read(DESIGN / "PROMPT_MODULES_20261008.json")
    assert set(modules) == {"common", "marginal", "joint", "decision", "output"}
    sources = {
        "inputs/PROTOCOL_20261008.md": DESIGN / "PROTOCOL_20261008.md",
        "inputs/PROMPT_MODULES_20261008.json": DESIGN / "PROMPT_MODULES_20261008.json",
        "inputs/run_joint_epistemic_simulation.py": Path(__file__).resolve(),
        "inputs/analyze_joint_epistemic_simulation.py": ROOT / "scripts/analyze_joint_epistemic_simulation.py",
        "inputs/run_strategic_qualification.py": Path(transport.__file__).resolve(),
        "inputs/run_counterfactual_source_boundary.py": ROOT / "scripts/run_counterfactual_source_boundary.py",
    }
    assert all(p.is_file() for p in sources.values())
    for folder in ("inputs", "prompts", "prompt_receipts", "dispatches", "responses", "launch"):
        (run / folder).mkdir(parents=True, exist_ok=True)
    for rel, path in sources.items():
        write_bytes(run / rel, path.read_bytes())
    rows = schedule()
    for row in rows:
        write_bytes(run / row["prompt_path"], make_prompt(row, modules).encode("utf8"))
    dump(run / "oracle_packets.json", packets())
    dump(run / "schedule.json", rows)
    dump(run / "manifest.json", {"schema_version": 1, "study_id": "joint_epistemic_simulation32_20261008",
         "created_utc": now(), "planned_provider_requests": TOTAL, "configuration_by_model": configurations(),
         "randomization_seed": SEED, "timeout_seconds": 300, "max_concurrency": 1,
         "requests": rows, "source_artifacts": {p.relative_to(ROOT).as_posix(): sha(p) for p in sources.values()}})
    dump(run / "freeze.json", {"schema_version": 1, "created_utc": now(), "experimental_requests_at_freeze": 0,
         "hashes": {p.relative_to(run).as_posix(): sha(p) for p in run.rglob("*") if p.is_file()}})
    status(run, "PREPARED")
    audit(run)


def audit(run):
    frozen, manifest = read(run / "freeze.json"), read(run / "manifest.json")
    assert frozen["experimental_requests_at_freeze"] == 0
    for rel, digest in frozen["hashes"].items():
        assert sha(within(run, rel)) == digest, rel
    for rel, digest in manifest["source_artifacts"].items():
        assert sha(within(ROOT, rel)) == digest, rel
    rows = read(run / "schedule.json")
    assert rows == manifest["requests"] == schedule()
    assert manifest["configuration_by_model"] == configurations() and manifest["planned_provider_requests"] == TOTAL
    assert read(run / "oracle_packets.json") == packets()
    modules = read(run / "inputs/PROMPT_MODULES_20261008.json")
    ids = {r["request_id"] for r in rows}
    for folder in ("responses", "dispatches", "prompt_receipts"):
        assert {p.stem for p in (run / folder).glob("*.json")} <= ids
    for row in rows:
        rid = row["request_id"]
        assert (run / row["prompt_path"]).read_text(encoding="utf8") == make_prompt(row, modules)
        digest = sha(run / row["prompt_path"])
        dispatch, prompt_receipt, response = (run / f"{folder}/{rid}.json" for folder in ("dispatches", "prompt_receipts", "responses"))
        if dispatch.exists():
            assert read(dispatch) == row | {"prompt_sha256": digest, "dispatched_utc": read(dispatch)["dispatched_utc"]}
            assert prompt_receipt.exists() and read(prompt_receipt)["prompt_sha256"] == digest
            assert read(prompt_receipt)["request_id"] == rid
        if response.exists():
            rec = read(response)
            assert dispatch.exists() and rec["request_id"] == rid and rec["model"] == row["model"]
            assert rec["prompt_sha256"] == digest and rec["simulation_condition"] == row["simulation_condition"]
            assert rec["kind"] == "judge" and rec["case_id"] == row["case_id"]
            assert rec["bluffer_condition"] == row["bluffer_condition"] and rec["judge_condition"] == row["judge_condition"]
            if rec["status"] == "response_received" and rec["returned_model"] == row["model"]:
                value, parse = parse_response(rec["visible_text"], rec["finish_reason"])
                assert rec["parsed"] == value and rec["parse_status"] == parse


def status(run, state, reason=None):
    receipts = [read(p) for p in (run / "responses").glob("*.json")]
    value = {"state": state, "halt_reason": reason, "planned": TOTAL,
             "provider_requests": len(list((run / "dispatches").glob("*.json"))),
             "response_count": len(receipts), "valid": sum(r.get("parse_status") == "valid" for r in receipts),
             "updated_utc": now()}
    dump(run / "status.json", value)
    return value


def provider_call(row, prompt, digest, key, session):
    config = configurations()[row["model"]]
    endpoint = config["endpoint"]
    headers = {"Content-Type": "application/json", "User-Agent": "XiaBaiWangResearch/1.0", "x-opencode-session": session}
    if endpoint == "messages":
        headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
    else:
        headers["Authorization"] = "Bearer " + key
    body = {"model": row["model"], "messages": [{"role": "user", "content": prompt}],
            **{k: config[k] for k in ("max_tokens", "temperature", "stream")}}
    for k in ("thinking", "reasoning_effort"):
        if k in config:
            body[k] = config[k]
    rec = {"request_id": row["request_id"], "model": row["model"], "kind": "judge", "case_id": row["case_id"],
           "simulation_condition": row["simulation_condition"], "bluffer_condition": row["bluffer_condition"],
           "judge_condition": row["judge_condition"], "prompt_sha256": digest, "sent_utc": now(),
           "status": "inflight", "visible_text": "", "parsed": None, "parse_status": "not_received",
           "returned_model": None, "usage": {}, "finish_reason": None}
    started = time.monotonic()
    request = urllib.request.Request("https://opencode.ai/zen/go/v1/" + endpoint,
                                   data=json.dumps(body, ensure_ascii=False).encode("utf8"), headers=headers)
    try:
        with urllib.request.build_opener(transport.NoRedirect()).open(request, timeout=300) as reply:
            rec["http_status"] = reply.status
            if reply.status != 200:
                raise ValueError("Unexpected successful HTTP status")
            data = json.loads(reply.read().decode("utf8"))
        if not isinstance(data, dict):
            raise ValueError("Invalid provider envelope")
        visible, finish = transport.extract_visible(data, endpoint)
        rec.update(status="response_received", returned_model=data.get("model"), usage=data.get("usage", {}),
                   finish_reason=finish, visible_text=visible.replace(key, "[REDACTED]"))
        if rec["returned_model"] != row["model"]:
            rec["parse_status"] = "unexpected_model"
        else:
            rec["parsed"], rec["parse_status"] = parse_response(rec["visible_text"], finish)
    except urllib.error.HTTPError as exc:
        rec.update(status="http_error", http_status=exc.code, error_type=type(exc).__name__,
                   provider_error_category=transport.classify_http_error(exc))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        rec.update(status="transport_unknown", error_type=type(exc).__name__)
    except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        rec.update(status="invalid_provider_response", error_type=type(exc).__name__)
    rec.update(elapsed_seconds=round(time.monotonic()-started, 3), captured_utc=now())
    return rec


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
    sessions = []
    try:
        status(run, "RUNNING")
        for row in read(run / "schedule.json"):
            rid = row["request_id"]
            prompt_path = run / row["prompt_path"]
            digest = sha(prompt_path)
            assert not (run / f"dispatches/{rid}.json").exists()
            session = "xia-jes-" + str(uuid4())
            sessions.append({"request_id": rid, "session_id": session})
            dump(run / "launch/session_mappings.private.json", sessions)
            dump(run / f"prompt_receipts/{rid}.json", {"request_id": rid, "prompt_sha256": digest, "created_utc": now()})
            dump(run / f"dispatches/{rid}.json", row | {"prompt_sha256": digest, "dispatched_utc": now()})
            status(run, "RUNNING")
            rec = provider_call(row, prompt_path.read_text(encoding="utf8"), digest, key, session)
            dump(run / f"responses/{rid}.json", rec)
            halt = transport.halt_reason(rec)
            current = status(run, "HALTED" if halt else "RUNNING", halt)
            print(json.dumps({"request_id": rid, "state": current["state"], "valid": current["valid"], "planned": TOTAL}), flush=True)
            if halt:
                return
        print(json.dumps(status(run, "COMPLETE_32_ATTEMPTED")), flush=True)
    except BaseException as exc:
        status(run, "HALTED", "local_fatal/" + type(exc).__name__)
        raise
    finally:
        lock.unlink(missing_ok=True)


def launch(run, hidden):
    audit(run)
    assert os.name == "nt" and read(run / "status.json")["state"] == "PREPARED"
    folder = run / "launch"
    assert not (folder / "launch_receipt.private.json").exists() and not list((run / "dispatches").glob("*.json"))
    key = getpass.getpass("OpenCode Go key (hidden): ").strip() if hidden else os.environ.get("OPENCODE_GO_API_KEY", "").strip()
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
         "command": "python -X utf8 -B scripts/run_joint_epistemic_simulation.py --execute",
         "stdout_path": str(out.resolve()), "stderr_path": str(err.resolve())})
    print(json.dumps({"launch": "accepted", "planned_provider_requests": TOTAL, "private_receipt_saved": True}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    modes = parser.add_mutually_exclusive_group(required=True)
    for name in ("prepare", "audit", "launch", "launch-hidden", "execute"):
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
    elif args.launch or args.launch_hidden:
        launch(run, args.launch_hidden)
    else:
        execute(run)


if __name__ == "__main__":
    main()
