"""Complete only the two missing OSI48 slots, with an explicit budget amendment."""
from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

import analyze_opponent_strategy_inference as metrics
import run_opponent_strategy_completion as previous

study = previous.study
ROOT, BASE = study.ROOT, study.BASE
RUN = BASE / "runs/opencode_go_20261010_opponent_strategy_inference48_tail02"
AMENDMENT = study.DESIGN / "TAIL_COMPLETION_PROTOCOL_20261010.md"
IDS = ("OSI_GLM_PERSISTENT_H4_ONESA_R2", "OSI_GLM_PERSISTENT_H7_ONESA_R2")
read, dump, sha, now, write_bytes = study.read, study.dump, study.sha, study.now, study.write_bytes


def configs():
    values = study.api.configurations()
    values["glm-5.3"]["max_tokens"] = 16384
    return values


def allocation():
    previous.audit()
    assert read(previous.RUN / "status.json")["state"] == "HALTED"
    assert not (previous.RUN / "execution.lock").exists()
    rows = read(previous.PARENT / "schedule.json")
    original_retained = set(read(previous.RUN / "manifest.json")["retained_valid_ids"])
    retained, pending = {}, []
    for row in rows:
        source = previous.PARENT if row["request_id"] in original_retained else previous.RUN
        path = source / "responses" / (row["request_id"] + ".json")
        rec = read(path) if path.exists() else {}
        good = (rec.get("status") == "response_received" and rec.get("http_status") == 200
                and rec.get("returned_model") == row["model"]
                and rec.get("parse_status") == rec.get("completion_parse_status") == "valid")
        if good:
            retained[row["request_id"]] = source.name
        else:
            pending.append(row)
    assert len(retained) == 46 and tuple(r["request_id"] for r in pending) == IDS
    assert len(list((previous.RUN / "dispatches").glob("*.json"))) == 45
    return rows, retained, pending


def prepare():
    assert not RUN.exists(), "Refuse overwriting a run"
    rows, retained, pending = allocation()
    sources = study.source_paths() + [Path(previous.__file__).resolve(),
        ROOT / "scripts/analyze_opponent_strategy_completion.py", AMENDMENT, Path(__file__).resolve(),
        study.DESIGN / "SUPPLEMENT_PROTOCOL_20261009.md"]
    for folder in ("inputs", "prompts", "responses", "dispatches", "prompt_receipts", "launch"):
        (RUN / folder).mkdir(parents=True, exist_ok=True)
    for source in sources:
        write_bytes(RUN / "inputs" / source.relative_to(ROOT), source.read_bytes())
    retained_hashes = {}
    for row in rows:
        write_bytes(RUN / row["prompt_path"], (previous.PARENT / row["prompt_path"]).read_bytes())
        rid = row["request_id"]
        if rid in retained:
            for folder in ("responses", "dispatches", "prompt_receipts"):
                rel = f"{retained[rid]}/{folder}/{rid}.json"
                source = BASE / "runs" / rel
                write_bytes(RUN / "inputs/retained" / rel, source.read_bytes())
                retained_hashes[rel] = sha(source)
    dump(RUN / "schedule.json", pending)
    dump(RUN / "manifest.json", {"study_id": "opponent_strategy_inference48_tail_completion_20261010",
        "created_utc": now(), "planned_provider_requests": 2, "requests": pending,
        "retained_source_by_id": retained, "retained_artifact_hashes": retained_hashes,
        "configuration_by_model": configs(), "original_configuration_by_model": study.api.configurations(),
        "mixed_output_budget": True, "max_cumulative_physical_attempts": 51,
        "source_artifacts": {p.relative_to(ROOT).as_posix(): sha(p) for p in sources},
        "selection_rule": "Only the one truncated and one unstarted slot; retain all 46 valid observations",
        "retry_policy": "One new attempt per selected slot; no automatic retry or fallback"})
    dump(RUN / "freeze.json", {"created_utc": now(), "experimental_requests_at_freeze": 0,
        "hashes": {p.relative_to(RUN).as_posix(): sha(p) for p in RUN.rglob("*") if p.is_file()}})
    status("PREPARED")
    audit()
    print(json.dumps({"prepared": True, "retained_valid": 46, "new_calls_planned": 2,
                      "glm_tail_max_tokens": 16384, "new_requests": 0}))


def audit():
    rows, retained, pending = allocation()
    manifest, freeze = read(RUN / "manifest.json"), read(RUN / "freeze.json")
    assert manifest["requests"] == read(RUN / "schedule.json") == pending
    assert manifest["retained_source_by_id"] == retained
    assert manifest["configuration_by_model"] == configs()
    assert freeze["experimental_requests_at_freeze"] == 0
    for rel, digest in freeze["hashes"].items():
        assert sha(study.api.within(RUN, rel)) == digest, rel
    for rel, digest in manifest["source_artifacts"].items():
        assert sha(study.api.within(ROOT, rel)) == digest, rel
    for rel, digest in manifest["retained_artifact_hashes"].items():
        assert sha(study.api.within(BASE / "runs", rel)) == digest
        assert sha(study.api.within(RUN / "inputs/retained", rel)) == digest
    for row in rows:
        assert (RUN / row["prompt_path"]).read_bytes() == (previous.PARENT / row["prompt_path"]).read_bytes()


def status(state, reason=None):
    receipts = [read(p) for p in (RUN / "responses").glob("*.json")]
    value = {"state": state, "halt_reason": reason, "planned": 2,
        "provider_requests": len(list((RUN / "dispatches").glob("*.json"))), "response_count": len(receipts),
        "valid": sum(r.get("completion_parse_status") == "valid" for r in receipts),
        "retained_valid": 46, "completion_valid_slots": 46 + sum(r.get("completion_parse_status") == "valid" for r in receipts),
        "updated_utc": now()}
    dump(RUN / "status.json", value)
    return value


def analyze():
    audit()
    manifest = read(RUN / "manifest.json")
    view = RUN / "analysis/completion_view"
    view.mkdir(parents=True, exist_ok=True)
    import analyze_opponent_strategy_completion as parent_analysis
    parent_analysis._copy_parent_freeze(previous.PARENT, view)
    for row in read(previous.PARENT / "schedule.json"):
        rid = row["request_id"]
        source = (RUN / "inputs/retained" / manifest["retained_source_by_id"][rid]
                  if rid in manifest["retained_source_by_id"] else RUN)
        for folder in ("responses", "dispatches", "prompt_receipts"):
            path = source / folder / (rid + ".json")
            if path.exists():
                write_bytes(view / folder / path.name, path.read_bytes())
    result = metrics.analyze(view)
    physical = {"original01": 1, "recovery02": 3, "supplement01": 45,
                "tail02": len(list((RUN / "dispatches").glob("*.json")))}
    overlay = {"schema_version": 1, "analysis_summary": result, "physical_attempts": physical,
        "physical_attempt_total": sum(physical.values()), "mixed_output_budget": True,
        "budget_amended_request_ids": list(IDS), "tail_configuration_by_model": configs(),
        "original_configuration_by_model": study.api.configurations(),
        "unchanged_budget_valid_slots": 46, "unchanged_budget_glm_persistent_valid": 10,
        "limitation": "The complete selected-slot overlay mixes 4096- and 16384-token GLM ceilings; the original-budget endpoint remains incomplete."}
    dump(RUN / "analysis/completion_summary.json", overlay)
    text = metrics.render(result) + "\n\n## Amended completion provenance\n\n"
    text += (f"Selected-slot coverage uses 46 retained strict-valid observations and {result['valid']-46} final-slot replies. "
             f"Physical attempts: 1 original + 3 recovery + 45 supplement01 + {physical['tail02']} tail02 = {sum(physical.values())}. "
             "Two GLM slots use a 16384-token ceiling; the other 22 GLM slots use 4096, and all Qwen slots use 8192. "
             "This is an amended mixed-budget overlay, not a complete original-budget run. "
             "The original-budget cutoff remains 46/48 valid (GLM Persistent 10/12). No wrong valid answer was regenerated.\n")
    write_bytes(RUN / "analysis/RESULTS.md", text.encode("utf8"))
    return overlay


def execute(hidden):
    audit()
    assert read(RUN / "status.json")["state"] == "PREPARED"
    assert not list((RUN / "dispatches").glob("*.json"))
    key = getpass.getpass("OpenCode Go key (hidden input): ").strip() if hidden else os.environ.get("OPENCODE_GO_API_KEY", "").strip()
    assert key, "Credential unavailable; no request sent"
    lock = RUN / "execution.lock"
    os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    dump(RUN / "launch/launch_receipt.private.json", {"host": os.environ.get("COMPUTERNAME"),
        "pid": os.getpid(), "launch_utc": now(), "manifest_sha256": sha(RUN / "manifest.json"),
        "run_path": str(RUN), "planned_provider_requests": 2,
        "command": "python -X utf8 -B scripts/complete_opponent_strategy_tail.py --execute-hidden"})
    original_configs = study.api.configurations
    try:
        for row in read(RUN / "schedule.json"):
            rid, digest = row["request_id"], sha(RUN / row["prompt_path"])
            session = "xia-osi-tail-" + str(uuid4())
            dump(RUN / f"prompt_receipts/{rid}.json", {"request_id": rid, "prompt_sha256": digest, "created_utc": now()})
            dump(RUN / f"dispatches/{rid}.json", row | {"prompt_sha256": digest, "dispatched_utc": now()})
            status("RUNNING")
            requested = configs()
            study.api.configurations = lambda: requested
            try:
                rec = previous.provider_call(row, (RUN / row["prompt_path"]).read_text(encoding="utf8"), digest, key, session)
            finally:
                study.api.configurations = original_configs
            rec["requested_config"] = requested[row["model"]]
            dump(RUN / f"responses/{rid}.json", rec)
            good = (rec["status"] == "response_received" and rec.get("returned_model") == row["model"]
                    and rec["completion_parse_status"] == "valid")
            current = status("RUNNING" if good else "HALTED", None if good else rec["completion_parse_status"])
            print(json.dumps({"request_id": rid, "state": current["state"], "valid_slots": current["completion_valid_slots"],
                "parse_status": rec["completion_parse_status"], "finish_reason": rec.get("finish_reason")}), flush=True)
            if not good:
                break
        else:
            status("COMPLETE_2_VALID")
        result = analyze()
        print(json.dumps({"completion": result["analysis_summary"]["completion"],
                          "valid_slots": result["analysis_summary"]["valid"], "physical_attempts": result["physical_attempt_total"]}), flush=True)
    except BaseException as exc:
        status("HALTED", "local_fatal/" + type(exc).__name__)
        raise
    finally:
        study.api.configurations = original_configs
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for name in ("prepare", "audit", "execute", "execute-hidden", "analyze"):
        modes.add_argument("--" + name, action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.audit:
        audit()
        print(json.dumps({"audit": "PASS", "new_requests": 0}))
    elif args.analyze:
        result = analyze()
        print(json.dumps({"completion": result["analysis_summary"]["completion"], "valid_slots": result["analysis_summary"]["valid"]}))
    else:
        execute(args.execute_hidden)


if __name__ == "__main__":
    main()
