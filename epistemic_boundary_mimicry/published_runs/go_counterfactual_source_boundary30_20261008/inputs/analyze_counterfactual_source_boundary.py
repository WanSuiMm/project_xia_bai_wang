#!/usr/bin/env python3
"""Offline descriptive analysis for the frozen CSB30 run."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "epistemic_boundary_mimicry"
DEFAULT_RUN = BASE / "runs/opencode_go_20261008_counterfactual_source_boundary30_01"
MATERIALS = BASE / "counterfactual_source_boundary/materials_20261008.json"
CASES = tuple(f"CS{i:02d}" for i in range(1, 7))
VERSIONS = ("V0", "V1")


class AnalysisError(RuntimeError):
    pass


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AnalysisError(f"cannot read {path.name}: {type(exc).__name__}") from None


def lf_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_runner():
    path = ROOT / "scripts/run_counterfactual_source_boundary.py"
    if not path.is_file():
        raise AnalysisError("the frozen CSB30 runner module is missing")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("csb30_runner_for_analysis", path)
    if spec is None or spec.loader is None:
        raise AnalysisError("cannot load the CSB30 runner module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def valid_receipts(run: Path, schedule: list[dict], parser):
    accepted, missing, invalid = {}, [], []
    for row in schedule:
        request_id = row["request_id"]
        path = run / "responses" / f"{request_id}.json"
        if not path.is_file():
            missing.append(request_id)
            continue
        try:
            receipt = read_json(path)
        except AnalysisError:
            invalid.append({"request_id": request_id, "reasons": ["receipt_json_invalid"]})
            continue
        reasons = []
        if not isinstance(receipt, dict):
            invalid.append({"request_id": request_id, "reasons": ["receipt_not_object"]})
            continue
        for key, wanted in (("request_id", request_id), ("model", row.get("model")), ("kind", row.get("kind")), ("case_id", row.get("case_id"))):
            if receipt.get(key) != wanted:
                reasons.append(key + "_mismatch")
        if receipt.get("returned_model") != row.get("model"):
            reasons.append("returned_model_mismatch")
        if receipt.get("status") != "response_received":
            reasons.append("response_not_received")
        if receipt.get("http_status") != 200:
            reasons.append("http_status_not_200")
        if receipt.get("reader_seat") != row.get("reader_seat"):
            reasons.append("reader_seat_mismatch")
        if row.get("kind") == "speaker" and receipt.get("condition") != row.get("condition"):
            reasons.append("condition_mismatch")
        if row.get("kind") == "judge" and receipt.get("reader_version") != row.get("reader_version"):
            reasons.append("reader_version_mismatch")
        parsed, parse_status = parser(receipt.get("visible_text"), receipt.get("finish_reason"), row["kind"])
        if parse_status != "valid" or receipt.get("parse_status") != parse_status:
            reasons.append("strict_parse_invalid")
        elif parsed != receipt.get("parsed"):
            reasons.append("receipt_parse_disagrees")
        if reasons:
            invalid.append({"request_id": request_id, "reasons": sorted(set(reasons))})
        else:
            accepted[request_id] = parsed
    return accepted, missing, invalid


def mean(values):
    return sum(values) / len(values) if values else None


def score_judge(row: dict, seat: str, value: dict) -> dict:
    p_a = float(value["p_A"])
    p_reader = p_a if seat == "A" else 1.0 - p_a
    side = "A" if p_a > 0.5 else "B" if p_a < 0.5 else None
    decision = value["decision"]
    return {"request_id": row["request_id"], "case_id": row["case_id"], "reader_version": row["reader_version"],
            "reader_seat": seat, "p_A": p_a, "p_reader": p_reader,
            "realized_label_brier": (1.0 - p_reader) ** 2, "decision": decision,
            "decision_correct_including_abstain_as_wrong": decision == seat, "p_A_side": side,
            "decision_probability_side_disagreement": (decision != side) if decision in {"A", "B"} and side else None,
            "reason_exact": value["reason"]}


def build_summary(run: Path) -> dict:
    run = run.resolve()
    try:
        relative_run = run.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        raise AnalysisError("run path must be inside the project root") from None
    runner, runner_path = load_runner()
    runner.audit(run)  # Frozen inputs, schedule, prompts, dependencies and no-API audit.
    manifest = read_json(run / "manifest.json")
    schedule = read_json(run / "schedule.json")
    status = read_json(run / "status.json")
    planned = manifest.get("planned_provider_requests", manifest.get("planned", 30))
    if planned != 30 or not isinstance(schedule, list) or len(schedule) != 30: raise AnalysisError("manifest and schedule must preserve the planned 30-call design")
    if sum(row.get("kind") == "speaker" for row in schedule) != 18 or sum(row.get("kind") == "judge" for row in schedule) != 12: raise AnalysisError("schedule must contain 18 Speakers and 12 Judges")
    ids = [row.get("request_id") for row in schedule]
    if len(set(ids)) != 30 or any(not isinstance(value, str) for value in ids): raise AnalysisError("schedule request IDs must be unique strings")
    if manifest.get("requests") != schedule:
        raise AnalysisError("manifest request schedule differs from schedule.json")

    materials_doc = read_json(run / "inputs" / MATERIALS.name)
    materials_rows = materials_doc if isinstance(materials_doc, list) else materials_doc.get("cases", [])
    materials = {row["case_id"]: row for row in materials_rows}
    if set(materials) != set(CASES): raise AnalysisError("frozen materials must contain CS01 through CS06")
    reader_seats = manifest.get("reader_seat_by_case", {})
    if set(reader_seats) != set(CASES) or any(reader_seats[c] not in {"A", "B"} for c in CASES): raise AnalysisError("manifest reader seats must assign A or B to all six cases")

    parsed, missing, invalid = valid_receipts(run, schedule, runner.parse_response)
    row_by_id = {row["request_id"]: row for row in schedule}
    dispatch_ids = {p.stem for p in (run / "dispatches").glob("*.json")}
    receipt_ids = {p.stem for p in (run / "responses").glob("*.json")}
    family_evidence, judge_rows = [], []
    for case_id in CASES:
        material = materials[case_id]
        seat = reader_seats[case_id]
        speakers, family_judges = [], {}
        for row in schedule:
            if row.get("case_id") == case_id and row.get("kind") == "speaker":
                value = parsed.get(row["request_id"])
                answer, gold = (value.get("answer") if value else None), material["gold_answer"]
                speakers.append({"request_id": row["request_id"], "condition": row.get("condition"),
                                 "valid": value is not None, "answer_exact": answer,
                                 "gold_answer_substring_present_descriptive_only": gold.casefold() in answer.casefold() if answer is not None else None})
        for version in VERSIONS:
            row = next((r for r in schedule if r.get("case_id") == case_id and r.get("kind") == "judge" and r.get("reader_version") == version), None)
            if row is None:
                raise AnalysisError(f"schedule lacks {case_id} Judge {version}")
            value = parsed.get(row["request_id"])
            if value is None:
                family_judges[version] = None
                continue
            detail = score_judge(row, seat, value)
            family_judges[version] = detail
            judge_rows.append(detail)
        family_evidence.append({"case_id": case_id, "reader_seat": seat,
            "question_id": material.get("question_id"), "question": material.get("question"),
            "public_context_exact": material.get("public_context"), "gold_answer_exact_from_frozen_materials": material["gold_answer"],
            "omission_check_exact": material.get("omission_check"),
            "insertion_sentence_exact": material.get("insertion_sentence", material.get("addition_sentence")),
            "source_v0_exact": material.get("source_v0"), "source_v1_exact": material.get("source_v1"),
            "speaker_answers": speakers, "judges_by_reader_version": family_judges})

    by_version = {}
    for version in VERSIONS:
        values = [r for r in judge_rows if r["reader_version"] == version]
        covered = [r for r in values if r["decision"] != "ABSTAIN"]
        side_eligible = [r for r in values if r["decision_probability_side_disagreement"] is not None]
        by_version[version] = {
            "n_valid_judges": len(values), "mean_p_reader": mean([r["p_reader"] for r in values]),
            "mean_realized_label_brier": mean([r["realized_label_brier"] for r in values]),
            "decision_accuracy_all_valid": mean([float(r["decision_correct_including_abstain_as_wrong"]) for r in values]),
            "coverage": len(covered) / len(values) if values else None,
            "conditional_accuracy": mean([float(r["decision_correct_including_abstain_as_wrong"]) for r in covered]),
            "covered_n": len(covered), "probability_side_disagreement_n": sum(r["decision_probability_side_disagreement"] for r in side_eligible),
            "probability_side_disagreement_eligible_n": len(side_eligible),
        }
    pairs = []
    for family in family_evidence:
        v0, v1 = (family["judges_by_reader_version"][v] for v in VERSIONS)
        if v0 is not None and v1 is not None:
            pairs.append({"case_id": family["case_id"],
                          "p_reader_v1_minus_v0": v1["p_reader"] - v0["p_reader"],
                          "brier_v1_minus_v0": v1["realized_label_brier"] - v0["realized_label_brier"]})
    script_hashes = {"analyzer_lf_sha256": lf_sha(Path(__file__).resolve()),
                     "runner_lf_sha256": lf_sha(runner_path)}
    return {
        "study_id": manifest.get("study_id"), "run_relative_path": relative_run,
        "script_lf_sha256": script_hashes, "configuration_by_model": manifest.get("configuration_by_model"),
        "run_state": status.get("state"), "halt_reason": status.get("halt_reason"),
        "planned": {"calls": 30, "speakers": 18, "judges": 12},
        "dispatched_calls": len(dispatch_ids), "response_receipt_count": len(receipt_ids),
        "valid": {"calls": len(parsed), "speakers": sum(row_by_id[r]["kind"] == "speaker" for r in parsed),
                  "judges": sum(row_by_id[r]["kind"] == "judge" for r in parsed)},
        "status_counts": {k: status.get(k) for k in ("provider_requests", "response_count", "valid")},
        "missing_request_ids": missing, "invalid_receipts": invalid,
        "not_dispatched_request_ids": sorted(set(ids) - dispatch_ids),
        "dispatched_without_receipt_ids": sorted(dispatch_ids - receipt_ids),
        "status_counts_consistent": status.get("provider_requests") == len(dispatch_ids)
            and status.get("response_count") == len(receipt_ids) and status.get("valid") == len(parsed),
        "family_material_unit_n": 6,
        "manual_coding_status": "pending_manual_review; no automatic manipulation pass computed",
        "judge_metrics_by_reader_version": by_version,
        "paired_primary_contrast": {
            "estimand": "equal-family mean p_reader(V1) minus p_reader(V0)",
            "n_complete_families": len(pairs),
            "mean_p_reader_v1_minus_v0": mean([p["p_reader_v1_minus_v0"] for p in pairs]),
            "mean_brier_v1_minus_v0": mean([p["brier_v1_minus_v0"] for p in pairs]),
            "complete_family_deltas": pairs,
        },
        "family_evidence": family_evidence,
        "interpretation_limits": [
            "One draw per condition cannot estimate within-family sampling distributions.",
            "The six authored families are the material units; this is descriptive, not a population estimate.",
            "A Judge sees one hidden-version packet and cannot observe the source-to-answer dependence directly.",
            "Reader/Bluffer policy differences and the one-sentence length change limit causal interpretation.",
            "Marginal-rate versus joint-process mimicry remains untested.",
        ],
    }
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--write", action="store_true", help="write summary.json once under this run's analysis/")
    args = parser.parse_args()
    try:
        summary = build_summary(args.run)
        payload = json.dumps(summary, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
        if args.write:
            out = args.run.resolve() / "analysis"
            if out.exists(): raise AnalysisError("analysis directory already exists; write-once output refused")
            out.mkdir()
            path = out / "summary.json"
            with path.open("x", encoding="utf-8", newline="\n") as handle: handle.write(payload)
            print("Wrote analysis/summary.json")
        else:
            sys.stdout.write(payload)
    except (AnalysisError, OSError, KeyError, TypeError, ValueError, AttributeError) as exc:
        print(f"analysis failed: {exc}", file=sys.stderr)


        raise SystemExit(2)


if __name__ == "__main__":
    main()
