"""Offline, provenance-preserving OSI48 completion overlay."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import tempfile

import analyze_opponent_strategy_inference as frozen


study = frozen.study
BASE = study.BASE
ORIGINAL = BASE / "runs/opencode_go_20261009_opponent_strategy_inference48_01"
RECOVERY = BASE / "runs/opencode_go_20261009_opponent_strategy_inference48_02"
DEFAULT_RUN = BASE / "runs/opencode_go_20261009_opponent_strategy_inference48_supplement01"
TOTAL, RETAINED, SUPPLEMENT = 48, 2, 46


def _need(condition, message):
    if not condition:
        raise AssertionError(message)


def _read(path):
    return study.read(path)


def _json_files(folder):
    return list(folder.glob("*.json")) if folder.is_dir() else []


def _copy_parent_freeze(parent, view):
    freeze_path = parent / "freeze.json"
    freeze = _read(freeze_path)
    hashes = freeze.get("hashes", {})
    _need({"manifest.json", "schedule.json"} <= set(hashes),
          "parent freeze must bind manifest.json and schedule.json")
    _need(any(path.startswith("inputs/") for path in hashes), "parent freeze has no frozen inputs")
    _need(any(path.startswith("prompts/") for path in hashes), "parent freeze has no frozen prompts")
    for rel, digest in hashes.items():
        source = study.api.within(parent, rel)
        target = study.api.within(view, rel)
        _need(source.is_file() and study.sha(source) == digest, f"parent frozen hash mismatch: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        _need(study.sha(target) == digest, f"copied parent frozen hash mismatch: {rel}")
    (view / "freeze.json").write_bytes(freeze_path.read_bytes())
    return freeze


def _check_parent_artifacts(run, parent, manifest):
    hashes = manifest.get("parent_artifact_hashes")
    _need(isinstance(hashes, dict) and hashes, "manifest must bind parent_artifact_hashes")
    copied_root = run / "inputs/parent"
    for rel, digest in hashes.items():
        source = study.api.within(parent, rel)
        copied = study.api.within(copied_root, rel)
        _need(source.is_file() and copied.is_file(), f"missing parent artifact: {rel}")
        _need(study.sha(source) == digest == study.sha(copied), f"parent artifact hash mismatch: {rel}")
    _need(isinstance(manifest.get("source_artifacts"), dict), "manifest must include source_artifacts")
    return len(hashes)


def _dispatch_for_view(source, row, prompt_sha):
    item = _read(source)
    _need(all(item.get(key) == value for key, value in row.items()),
          f"dispatch does not match frozen request: {source.name}")
    _need(item.get("prompt_sha256") == prompt_sha, f"dispatch prompt hash mismatch: {source.name}")
    timestamp = item.get("dispatched_utc")
    _need(isinstance(timestamp, str) and timestamp, f"dispatch timestamp missing: {source.name}")
    # The frozen analyzer requires its original dispatch schema. Safe diagnostics
    # stay in the source run; only this derived view is normalized.
    return row | {"prompt_sha256": prompt_sha, "dispatched_utc": timestamp}


def _assemble_view(run, parent, rows, retained_ids, view):
    freeze = _copy_parent_freeze(parent, view)
    schedule = _read(view / "schedule.json")
    ids = {row["request_id"] for row in schedule}
    retained = set(retained_ids)
    pending = ids - retained
    _need(len(ids) == TOTAL and len(retained) == RETAINED and len(pending) == SUPPLEMENT,
          "retained and supplement allocations must partition the 48 frozen slots")

    recovery_dirs = {folder: RECOVERY / folder for folder in ("dispatches", "prompt_receipts", "responses")}
    supplement_dirs = {folder: run / folder for folder in ("dispatches", "prompt_receipts", "responses")}
    for folder, source_dir in recovery_dirs.items():
        _need({p.stem for p in _json_files(source_dir)} <= ids,
              f"recovery {folder} include a non-parent request")
    for folder, source_dir in supplement_dirs.items():
        _need({p.stem for p in _json_files(source_dir)} <= pending,
              f"supplement {folder} include a retained or non-parent request")

    slots = []
    for row in schedule:
        rid = row["request_id"]
        source_run = RECOVERY if rid in retained else run
        source_name = "recovery_02_retained" if rid in retained else "supplement_01"
        prompt = study.api.within(view, row["prompt_path"])
        _need(prompt.is_file(), f"frozen prompt missing: {rid}")
        prompt_sha = study.sha(prompt)
        present = {}
        for folder in ("dispatches", "prompt_receipts", "responses"):
            src = source_run / folder / f"{rid}.json"
            dst = view / folder / f"{rid}.json"
            present[folder] = src.is_file()
            if not present[folder]:
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            if folder == "dispatches":
                study.dump(dst, _dispatch_for_view(src, row, prompt_sha))
            else:
                dst.write_bytes(src.read_bytes())
        slots.append({"request_id": rid, "source": source_name,
                      "dispatch_present": present["dispatches"],
                      "prompt_receipt_present": present["prompt_receipts"],
                      "response_present": present["responses"]})
    frozen.study.audit(view, live_sources=False)
    return freeze, slots


def _build_view(run, parent, rows, retained_ids, write):
    if write:
        analysis_dir = run / "analysis"
        if analysis_dir.is_symlink():
            raise AssertionError("refuse using a symlinked analysis directory")
        analysis_dir.mkdir(parents=True, exist_ok=True)
        analysis_root = analysis_dir.resolve()
        analysis_root.relative_to(run.resolve())
        view = analysis_root / "completion_view"
        if view.is_symlink():
            raise AssertionError("refuse replacing a symlinked completion_view")
        view.resolve().relative_to(analysis_root)
        if view.exists():
            _need(view.is_dir(), "completion_view is not a directory")
            shutil.rmtree(view)
        view.mkdir(parents=True)
        _, slots = _assemble_view(run, parent, rows, retained_ids, view)
        return view, slots
    temporary = tempfile.TemporaryDirectory(prefix="osi48-completion-view-")
    view = Path(temporary.name) / "completion_view"
    view.mkdir()
    _, slots = _assemble_view(run, parent, rows, retained_ids, view)
    return temporary, view, slots


def analyze(run, write=True):
    run = Path(run).resolve()
    run.relative_to((BASE / "runs").resolve())
    manifest = _read(run / "manifest.json")
    _need(manifest.get("study_id") == "opponent_strategy_inference48_completion_20261009",
          "unexpected supplement study_id")
    _need(manifest.get("parent_run_name") == RECOVERY.name,
          f"parent_run_name must identify {RECOVERY.name}")
    _need(RECOVERY.is_dir() and ORIGINAL.is_dir(), "original and recovery runs must exist")

    parent_manifest = frozen.study.audit(RECOVERY, live_sources=False)
    rows = _read(RECOVERY / "schedule.json")
    _need(parent_manifest["requests"] == rows and len(rows) == TOTAL,
          "recovery frozen manifest must contain the 48-slot parent schedule")
    retained_ids = manifest.get("retained_valid_ids")
    _need(isinstance(retained_ids, list) and len(retained_ids) == RETAINED
          and len(set(retained_ids)) == RETAINED, "manifest must retain exactly two unique IDs")
    recovery_result = frozen.analyze(RECOVERY, write=False)
    recovery_valid = {r["request_id"] for r in recovery_result["items"]
                      if r["status"] == "valid" and r["strict_valid"]}
    _need(recovery_valid == set(retained_ids) and recovery_result["strict_valid"] == RETAINED,
          "retained_valid_ids must equal the recovery run's two strict-valid receipts")

    expected = [row for row in rows if row["request_id"] not in set(retained_ids)]
    _need(manifest.get("planned_provider_requests") == SUPPLEMENT
          and manifest.get("requests") == expected
          and _read(run / "schedule.json") == expected,
          "supplement must contain the 46 non-retained frozen rows in original order")
    parent_hash_count = _check_parent_artifacts(run, RECOVERY, manifest)
    for row in rows:
        parent_prompt = RECOVERY / row["prompt_path"]
        supplement_prompt = run / row["prompt_path"]
        _need(parent_prompt.is_file() and supplement_prompt.is_file()
              and parent_prompt.read_bytes() == supplement_prompt.read_bytes(),
              f"supplement prompt differs from frozen parent: {row['request_id']}")

    if write:
        view, slot_sources = _build_view(run, RECOVERY, rows, retained_ids, write=True)
        result = frozen.analyze(view, write=True)
    else:
        temporary, view, slot_sources = _build_view(run, RECOVERY, rows, retained_ids, write=False)
        try:
            result = frozen.analyze(view, write=False)
        finally:
            temporary.cleanup()

    physical = {
        "original_01_dispatches": len(_json_files(ORIGINAL / "dispatches")),
        "recovery_02_dispatches": len(_json_files(RECOVERY / "dispatches")),
        "supplement01_dispatches": len(_json_files(run / "dispatches")),
    }
    _need(physical["original_01_dispatches"] == 1 and physical["recovery_02_dispatches"] == 3,
          "preserved physical dispatch counts must remain original 1 plus recovery 3")
    _need(physical["supplement01_dispatches"] <= SUPPLEMENT,
          "supplement dispatch count exceeds the 46-slot plan")
    physical["total_physical_dispatches"] = sum(physical.values())
    physical["valid_retained_ids"] = RETAINED
    physical["new_api_calls_from_analysis"] = 0

    completion = {
        "schema_version": 1, "supplement_run_name": run.name,
        "parent_run_name": RECOVERY.name, "original_run_name": ORIGINAL.name,
        "completion_view": "analysis/completion_view" if write else None,
        "parent_manifest_sha256": study.sha(RECOVERY / "manifest.json"),
        "parent_freeze_sha256": study.sha(RECOVERY / "freeze.json"),
        "parent_schedule_sha256": study.sha(RECOVERY / "schedule.json"),
        "parent_artifact_hashes_verified": parent_hash_count,
        "retained_valid_ids": retained_ids,
        "selection_rule": "Use the two manifest-retained strict-valid recovery IDs; use the supplement record for every other slot; no correctness- or score-based selection.",
        "slot_allocation": {"recovery_retained": RETAINED, "supplement": SUPPLEMENT},
        "physical_attempts": physical,
        "completion_view_dispatch_records": result["provider_requests"],
        "analysis_summary": result, "slot_sources": slot_sources,
    }
    if write:
        out = run / "analysis"
        study.dump(out / "completion_summary.json", completion)
        study.write_bytes(out / "RESULTS.md", render(completion).encode("utf8"))
    return completion


def render(completion):
    result, attempts = completion["analysis_summary"], completion["physical_attempts"]
    lines = [frozen.render(result).rstrip(), "", "## Completion overlay provenance", "",
        "The 48 frozen slots use the two IDs named in `manifest.json.retained_valid_ids` and the matching supplement artifact for every other ID. Source selection does not use correctness, scores, or cell metrics.", "",
        f"Physical dispatches across runs: original `_01` {attempts['original_01_dispatches']} + recovery `_02` {attempts['recovery_02_dispatches']} + supplement {attempts['supplement01_dispatches']} = {attempts['total_physical_dispatches']}. The analyzer's dispatch count above covers records selected into the completion view, not all physical attempts.", "",
        f"All 48 prompts and the parent frozen manifest, freeze, inputs, and schedule were copied byte-for-byte. Analysis made {attempts['new_api_calls_from_analysis']} provider calls.", "",
        f"Retained recovery slots: {RETAINED}; supplement slots: {SUPPLEMENT}; supplement dispatches: {attempts['supplement01_dispatches']}.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    args = parser.parse_args()
    completion = analyze(args.run)
    result = completion["analysis_summary"]
    print(json.dumps({"completion": result["completion"], "planned": result["planned"],
                      "selected_dispatch_records": result["provider_requests"],
                      "responses_received": result["responses_received"],
                      "valid": result["valid"], "strict_valid": result["strict_valid"],
                      "physical_attempts": completion["physical_attempts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
