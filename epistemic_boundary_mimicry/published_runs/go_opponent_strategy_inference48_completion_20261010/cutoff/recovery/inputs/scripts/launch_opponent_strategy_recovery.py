"""Newly authorized credential-only recovery; never mutate the original OSI48 run."""
from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path

import run_opponent_strategy_inference as study

PARENT = study.DEFAULT_RUN
RUN = study.BASE / "runs/opencode_go_20261009_opponent_strategy_inference48_02"
AMENDMENT = study.DESIGN / "CREDENTIAL_RECOVERY_20261009.md"


def validate_parent():
    study.audit(PARENT)
    parent_status = study.read(PARENT / "status.json")
    assert parent_status["state"] == "HALTED"
    assert parent_status["provider_requests"] == parent_status["response_count"] == 1
    assert parent_status["valid"] == parent_status["strict_valid"] == 0
    rows = study.read(PARENT / "schedule.json")
    response = study.read(PARENT / f"responses/{rows[0]['request_id']}.json")
    assert response["status"] == "http_error" and response["http_status"] == 403
    assert response["provider_error_category"] == "payment"
    assert not response["visible_text"] and response["parsed"] is None
    return rows


def audit_recovery():
    rows = validate_parent()
    study.audit(RUN)
    assert study.read(RUN / "schedule.json") == rows
    for row in rows:
        assert (RUN / row["prompt_path"]).read_bytes() == (PARENT / row["prompt_path"]).read_bytes()
    manifest = study.read(RUN / "manifest.json")
    for path in (AMENDMENT, Path(__file__).resolve()):
        assert manifest["source_artifacts"][path.relative_to(study.ROOT).as_posix()] == study.sha(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--launch-hidden", action="store_true")
    args = parser.parse_args()
    validate_parent()
    if args.prepare:
        original_sources = study.source_paths
        study.source_paths = lambda: original_sources() + [AMENDMENT, Path(__file__).resolve()]
        study.prepare(RUN)
        audit_recovery()
        return
    audit_recovery()
    assert study.read(RUN / "status.json")["state"] == "PREPARED"
    key = getpass.getpass("Replacement OpenCode Go key (hidden input): ").strip()
    assert key, "Empty credential; no request sent"
    os.environ["OPENCODE_GO_API_KEY"] = key
    try:
        study.launch(RUN)
    finally:
        os.environ.pop("OPENCODE_GO_API_KEY", None)


if __name__ == "__main__":
    main()
