"""Failure-selected OSI48 completion with safe provider-envelope diagnostics."""
from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request
from uuid import uuid4

import run_opponent_strategy_inference as study

ROOT, BASE = study.ROOT, study.BASE
PARENT = BASE / "runs/opencode_go_20261009_opponent_strategy_inference48_02"
RUN = BASE / "runs/opencode_go_20261009_opponent_strategy_inference48_supplement01"
AMENDMENT = study.DESIGN / "SUPPLEMENT_PROTOCOL_20261009.md"
TOTAL = 46
LIMIT_FINISHES = {"length", "max_tokens", "token_limit"}
read, dump, sha, now = study.read, study.dump, study.sha, study.now
write_bytes = study.write_bytes


def selection():
    study.audit(PARENT, live_sources=False)
    assert read(PARENT / "status.json")["state"] == "HALTED"
    assert not (PARENT / "execution.lock").exists()
    retained, pending = [], []
    for row in read(PARENT / "schedule.json"):
        path = PARENT / f"responses/{row['request_id']}.json"
        rec = read(path) if path.exists() else {}
        valid = (rec.get("status") == "response_received" and rec.get("http_status") == 200
                 and rec.get("returned_model") == row["model"]
                 and rec.get("parse_status") == rec.get("completion_parse_status") == "valid")
        (retained if valid else pending).append(row)
    assert [r["schedule_index"] for r in retained] == [1, 2]
    assert len(retained) == 2 and len(pending) == TOTAL
    assert [r["schedule_index"] for r in pending] == list(range(3, 49))
    return retained, pending


def safe_usage(data):
    if not isinstance(data, dict):
        return {}
    keys = ("input_tokens", "output_tokens", "prompt_tokens", "completion_tokens", "total_tokens",
            "cache_read_input_tokens", "cache_creation_input_tokens")
    result = {k: data[k] for k in keys if isinstance(data.get(k), (int, float))
              and not isinstance(data[k], bool)}
    for key in ("completion_tokens_details", "output_tokens_details"):
        detail = data.get(key)
        if isinstance(detail, dict) and isinstance(detail.get("reasoning_tokens"), int):
            result[key] = {"reasoning_tokens": detail["reasoning_tokens"]}
    return result


def decode_envelope(data, endpoint):
    """Retain safe envelope metadata even if final-content extraction fails."""
    if not isinstance(data, dict):
        return {}, {"failure_stage": "envelope_type"}
    meta = {"returned_model": data.get("model") if isinstance(data.get("model"), str) else None,
            "usage": safe_usage(data.get("usage"))}
    diag = {"provider_error_present": isinstance(data.get("error"), (dict, str))}
    if diag["provider_error_present"]:
        return meta, diag | {"failure_stage": "provider_error_envelope"}
    if endpoint == "messages":
        finish = data.get("stop_reason")
        meta["finish_reason"] = finish if isinstance(finish, str) else None
        try:
            visible, _ = study.transport.extract_visible(data, endpoint)
        except (ValueError, TypeError, AttributeError):
            return meta, diag | {"failure_stage": "messages_content"}
    else:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            return meta, diag | {"failure_stage": "choices"}
        choice = choices[0]
        finish = choice.get("finish_reason")
        meta["finish_reason"] = finish if isinstance(finish, str) else None
        message = choice.get("message")
        if not isinstance(message, dict):
            return meta, diag | {"failure_stage": "message"}
        content = message.get("content")
        diag.update(content_type=type(content).__name__,
                    reasoning_field_present=any(k in message for k in ("reasoning", "reasoning_content")))
        if isinstance(content, str):
            visible = content
        elif content is None and finish in LIMIT_FINISHES:
            visible = ""
            diag["null_content_at_token_limit"] = True
        elif isinstance(content, list) and content and all(
                isinstance(block, dict) and block.get("type") == "text"
                and isinstance(block.get("text"), str) for block in content):
            visible = "".join(block["text"] for block in content)
            diag["text_block_list"] = True
        else:
            return meta, diag | {"failure_stage": "message_content"}
    if not isinstance(meta.get("finish_reason"), str):
        return meta, diag | {"failure_stage": "finish_reason"}
    return meta | {"visible_text": visible}, diag | {"failure_stage": None}


def provider_call(row, prompt, digest, key, session):
    config = study.api.configurations()[row["model"]]
    endpoint = config["endpoint"]
    headers = {"Content-Type": "application/json", "User-Agent": "XiaBaiWangResearch/1.0",
               "x-opencode-session": session}
    if endpoint == "messages":
        headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
    else:
        headers["Authorization"] = "Bearer " + key
    body = {"model": row["model"], "messages": [{"role": "user", "content": prompt}],
            **{k: config[k] for k in ("max_tokens", "temperature", "stream")}}
    for k in ("thinking", "reasoning_effort"):
        if k in config:
            body[k] = config[k]
    rec = {k: row[k] for k in ("request_id", "model", "kind", "case_id", "simulation_condition",
                               "bluffer_condition", "judge_condition")}
    rec.update(prompt_sha256=digest, sent_utc=now(), status="inflight", visible_text="", parsed=None,
               parse_status="not_received", returned_model=None, usage={}, finish_reason=None,
               completion_parsed=None, completion_parse_status="not_received", format_acceptance=None)
    started = time.monotonic()
    request = urllib.request.Request("https://opencode.ai/zen/go/v1/" + endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf8"), headers=headers)
    stage = "request"
    try:
        with urllib.request.build_opener(study.transport.NoRedirect()).open(request, timeout=300) as reply:
            rec["http_status"] = reply.status
            assert reply.status == 200
            stage = "json_decode"
            data = json.loads(reply.read().decode("utf8"))
        stage = "envelope_extract"
        meta, diagnostic = decode_envelope(data, endpoint)
        rec.update(meta, provider_diagnostic=diagnostic)
        if diagnostic["failure_stage"] is not None:
            rec.update(status="invalid_provider_response", error_type="EnvelopeExtractionError")
        else:
            rec.update(status="response_received", visible_text=rec["visible_text"].replace(key, "[REDACTED]"))
            if rec["returned_model"] != row["model"]:
                rec.update(parse_status="unexpected_model", completion_parse_status="unexpected_model")
            else:
                rec["parsed"], rec["parse_status"] = study.api.parse_response(rec["visible_text"], rec["finish_reason"])
                value, parse, acceptance = study.formatting.parse_completion(rec["visible_text"], rec["finish_reason"])
                rec.update(completion_parsed=value, completion_parse_status=parse, format_acceptance=acceptance)
    except urllib.error.HTTPError as exc:
        rec.update(status="http_error", http_status=exc.code, error_type=type(exc).__name__,
                   provider_error_category=study.transport.classify_http_error(exc))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        rec.update(status="transport_unknown", error_type=type(exc).__name__)
    except (ValueError, KeyError, IndexError, TypeError, AttributeError, AssertionError) as exc:
        rec.update(status="invalid_provider_response", error_type=type(exc).__name__,
                   provider_diagnostic={"failure_stage": stage})
    rec.update(elapsed_seconds=round(time.monotonic()-started, 3), captured_utc=now())
    return rec


def prepare():
    assert not RUN.exists(), "Refuse overwriting a run"
    retained, pending = selection()
    sources = study.source_paths() + [AMENDMENT, Path(__file__).resolve(),
                ROOT / "scripts/analyze_opponent_strategy_completion.py",
                ROOT / "scripts/test_opponent_strategy_completion.py"]
    assert all(p.is_file() for p in sources)
    for folder in ("inputs", "prompts", "prompt_receipts", "dispatches", "responses", "launch"):
        (RUN / folder).mkdir(parents=True, exist_ok=True)
    for path in sources:
        write_bytes(RUN / "inputs" / path.relative_to(ROOT), path.read_bytes())
    for row in read(PARENT / "schedule.json"):
        write_bytes(RUN / row["prompt_path"], (PARENT / row["prompt_path"]).read_bytes())
    parent_paths = [PARENT / name for name in ("manifest.json", "freeze.json", "schedule.json", "status.json")]
    for folder in ("responses", "dispatches", "prompt_receipts"):
        parent_paths += list((PARENT / folder).glob("*.json"))
    for path in parent_paths:
        write_bytes(RUN / "inputs/parent" / path.relative_to(PARENT), path.read_bytes())
    dump(RUN / "schedule.json", pending)
    dump(RUN / "manifest.json", {"study_id": "opponent_strategy_inference48_completion_20261009",
        "created_utc": now(), "parent_run_name": PARENT.name,
        "parent_artifact_hashes": {p.relative_to(PARENT).as_posix(): sha(p) for p in parent_paths},
        "retained_valid_ids": [r["request_id"] for r in retained], "planned_provider_requests": TOTAL,
        "requests": pending, "configuration_by_model": study.api.configurations(),
        "source_artifacts": {p.relative_to(ROOT).as_posix(): sha(p) for p in sources},
        "selection_rule": "All 46 non-strict-valid recovery slots, original order; no correctness selection",
        "retry_policy": "One new attempt per selected slot; no automatic retry or fallback",
        "timeout_seconds": 300, "max_concurrency": 1})
    dump(RUN / "freeze.json", {"created_utc": now(), "experimental_requests_at_freeze": 0,
        "hashes": {p.relative_to(RUN).as_posix(): sha(p) for p in RUN.rglob("*") if p.is_file()}})
    status("PREPARED")
    audit()
    print(json.dumps({"prepared": True, "retained": 2, "planned_new_calls": TOTAL, "new_requests": 0}))


def audit():
    retained, pending = selection()
    manifest, freeze = read(RUN / "manifest.json"), read(RUN / "freeze.json")
    assert manifest["requests"] == read(RUN / "schedule.json") == pending
    assert manifest["retained_valid_ids"] == [r["request_id"] for r in retained]
    assert manifest["configuration_by_model"] == study.api.configurations()
    assert manifest["planned_provider_requests"] == TOTAL and freeze["experimental_requests_at_freeze"] == 0
    for rel, digest in freeze["hashes"].items():
        assert sha(study.api.within(RUN, rel)) == digest, rel
    for rel, digest in manifest["source_artifacts"].items():
        assert sha(study.api.within(ROOT, rel)) == digest, rel
    for rel, digest in manifest["parent_artifact_hashes"].items():
        assert sha(study.api.within(PARENT, rel)) == sha(study.api.within(RUN / "inputs/parent", rel)) == digest
    ids = {row["request_id"] for row in pending}
    for folder in ("responses", "dispatches", "prompt_receipts"):
        assert {p.stem for p in (RUN / folder).glob("*.json")} <= ids
    for row in read(PARENT / "schedule.json"):
        assert (RUN / row["prompt_path"]).read_bytes() == (PARENT / row["prompt_path"]).read_bytes()
    for row in pending:
        rid, digest = row["request_id"], sha(RUN / row["prompt_path"])
        path = RUN / f"dispatches/{rid}.json"
        if path.exists():
            item = read(path)
            assert item == row | {"prompt_sha256": digest, "dispatched_utc": item["dispatched_utc"]}
            assert read(RUN / f"prompt_receipts/{rid}.json")["prompt_sha256"] == digest
        response = RUN / f"responses/{rid}.json"
        if response.exists():
            rec = read(response)
            assert path.exists() and rec["prompt_sha256"] == digest
            for k in ("request_id", "model", "kind", "case_id", "simulation_condition", "bluffer_condition", "judge_condition"):
                assert rec[k] == row[k]
            if rec["status"] == "response_received" and rec.get("returned_model") == row["model"]:
                assert (rec["parsed"], rec["parse_status"]) == study.api.parse_response(rec["visible_text"], rec["finish_reason"])
                assert (rec["completion_parsed"], rec["completion_parse_status"], rec["format_acceptance"]) == study.formatting.parse_completion(rec["visible_text"], rec["finish_reason"])


def status(state, reason=None):
    receipts = [read(p) for p in (RUN / "responses").glob("*.json")]
    value = {"state": state, "halt_reason": reason, "planned": TOTAL,
        "provider_requests": len(list((RUN / "dispatches").glob("*.json"))), "response_count": len(receipts),
        "valid": sum(r.get("completion_parse_status") == "valid" for r in receipts),
        "strict_valid": sum(r.get("parse_status") == "valid" for r in receipts),
        "retained_valid": 2, "completion_valid_slots": 2 + sum(r.get("completion_parse_status") == "valid" for r in receipts),
        "updated_utc": now()}
    dump(RUN / "status.json", value)
    return value


def one(row):
    key = os.environ.get("OPENCODE_GO_API_KEY", "").strip()
    assert key, "Credential unavailable; no request sent"
    rid, digest = row["request_id"], sha(RUN / row["prompt_path"])
    assert not (RUN / f"dispatches/{rid}.json").exists(), "Never resend an existing dispatch"
    session = "xia-osi-completion-" + str(uuid4())
    sessions_path = RUN / "launch/session_mappings.private.json"
    sessions = read(sessions_path) if sessions_path.exists() else []
    dump(sessions_path, sessions + [{"request_id": rid, "session_id": session}])
    dump(RUN / f"prompt_receipts/{rid}.json", {"request_id": rid, "prompt_sha256": digest, "created_utc": now()})
    dump(RUN / f"dispatches/{rid}.json", row | {"prompt_sha256": digest, "dispatched_utc": now()})
    status("RUNNING")
    rec = provider_call(row, (RUN / row["prompt_path"]).read_text(encoding="utf8"), digest, key, session)
    dump(RUN / f"responses/{rid}.json", rec)
    halt = None
    if rec["status"] != "response_received" or rec.get("returned_model") != row["model"]:
        halt = study.transport.halt_reason(rec) or "delivery_or_model_failure"
    elif rec["completion_parse_status"] == "truncated":
        halt = "token_budget_truncation"
    current = status("HALTED" if halt else "RUNNING", halt)
    print(json.dumps({"request_id": rid, "state": current["state"], "valid_slots": current["completion_valid_slots"],
                      "parse_status": rec["completion_parse_status"], "provider_diagnostic": rec.get("provider_diagnostic")}), flush=True)
    return rec, halt


def execute(first=False):
    audit()
    current = read(RUN / "status.json")
    rows = read(RUN / "schedule.json")
    if first:
        assert current["state"] == "PREPARED" and current["provider_requests"] == 0
        todo = rows[:1]
    else:
        launch = study.transport.wait_for_launch_receipt(RUN)
        assert launch["manifest_sha256"] == sha(RUN / "manifest.json")
        assert current["state"] == "FIRST_REQUEST_VALIDATED" and current["provider_requests"] == 1
        todo = rows[1:]
    lock = RUN / "execution.lock"
    os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    try:
        if first:
            receipt_path = RUN / "launch/first_request.private.json"
            os.close(os.open(receipt_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            dump(receipt_path, {"host": os.environ.get("COMPUTERNAME"), "pid": os.getpid(),
                 "launch_utc": now(), "manifest_sha256": sha(RUN / "manifest.json")})
        for row in todo:
            rec, halt = one(row)
            if first:
                status("FIRST_REQUEST_VALIDATED" if rec["completion_parse_status"] == "valid" and not halt else "HALTED",
                       halt or (None if rec["completion_parse_status"] == "valid" else "first_request_invalid"))
            if halt or first:
                break
        else:
            status("COMPLETE_46_ATTEMPTED")
        import analyze_opponent_strategy_completion as analysis
        analysis.analyze(RUN)
    except BaseException as exc:
        status("HALTED", "local_fatal/" + type(exc).__name__)
        raise
    finally:
        lock.unlink(missing_ok=True)


def launch():
    audit()
    assert os.name == "nt" and os.environ.get("OPENCODE_GO_API_KEY", "").strip()
    assert read(RUN / "status.json")["state"] == "FIRST_REQUEST_VALIDATED"
    folder = RUN / "launch"
    assert not (folder / "launch_receipt.private.json").exists()
    os.close(os.open(folder / "launcher_reservation.private", os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    out, err = folder / "worker.stdout.private.log", folder / "worker.stderr.private.log"
    with out.open("xb") as stdout, err.open("xb") as stderr:
        child = subprocess.Popen([sys.executable, "-X", "utf8", "-B", str(Path(__file__).resolve()), "--execute"],
            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, env=os.environ.copy(), close_fds=True,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)
    dump(folder / "launch_receipt.private.json", {"state": "LAUNCHED", "pid": child.pid,
        "host": os.environ.get("COMPUTERNAME"), "launch_utc": now(), "run_path": str(RUN),
        "manifest_sha256": sha(RUN / "manifest.json"), "planned_provider_requests": TOTAL-1,
        "command": "python -X utf8 -B scripts/run_opponent_strategy_completion.py --execute",
        "stdout_path": str(out), "stderr_path": str(err)})
    print(json.dumps({"launch": "accepted", "retained_valid": 2, "new_valid": 1,
                      "remaining_calls": TOTAL-1, "private_receipt_saved": True}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    for name in ("prepare", "audit", "first", "launch", "execute", "start-hidden"):
        mode.add_argument("--" + name, action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.audit:
        audit()
        print(json.dumps({"audit": "PASS", "new_requests": 0}))
    elif args.launch:
        launch()
    elif args.start_hidden:
        original = os.environ.get("OPENCODE_GO_API_KEY")
        key = getpass.getpass("OpenCode Go key (hidden input): ").strip()
        assert key, "Credential unavailable; no request sent"
        os.environ["OPENCODE_GO_API_KEY"] = key
        try:
            execute(first=True)
            if read(RUN / "status.json")["state"] == "FIRST_REQUEST_VALIDATED":
                launch()
        finally:
            if original is None:
                os.environ.pop("OPENCODE_GO_API_KEY", None)
            else:
                os.environ["OPENCODE_GO_API_KEY"] = original
    else:
        execute(first=args.first)


if __name__ == "__main__":
    main()
