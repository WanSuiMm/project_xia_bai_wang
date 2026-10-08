"""Offline scoring for the finite Joint Epistemic Simulation qualification."""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import run_joint_epistemic_simulation as study


ROOT = study.ROOT
DEFAULT_RUN = study.DEFAULT_RUN
TOTAL = study.TOTAL
STUDY_ID = "joint_epistemic_simulation32_20261008"
MODELS = ("glm-5.3", "qwen3.8-max")
CONDITIONS = ("MARGINAL", "JOINT")
EXCESS_BRIER_LIMIT = 0.01
MASS_TOLERANCE = 1e-12


class AnalysisError(RuntimeError):
    """Raised when the frozen design or raw receipt bindings are inconsistent."""


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise AnalysisError(message)


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _vector(value: Any, where: str) -> tuple[int, int]:
    _need(isinstance(value, list) and len(value) == 2, f"{where} must be a length-two list")
    _need(all(isinstance(bit, int) and not isinstance(bit, bool) and bit in (0, 1) for bit in value),
          f"{where} must contain only integer bits 0 or 1")
    return int(value[0]), int(value[1])


def _reader_probability(vector: tuple[int, int]) -> float:
    return 0.5 if vector in ((0, 0), (1, 1)) else 0.0


def _bluffer_probability(vector: tuple[int, int], condition: str) -> float:
    if condition == "MARGINAL":
        return 0.25
    return _reader_probability(vector)


def _expected_packet_rows(condition: str) -> dict[tuple[tuple[int, int], tuple[int, int]], tuple[float, float]]:
    """Return (a,b) -> (prior predictive weight, posterior P(A is Reader))."""
    vectors = ((0, 0), (0, 1), (1, 0), (1, 1))
    expected: dict[tuple[tuple[int, int], tuple[int, int]], tuple[float, float]] = {}
    for a in vectors:
        for b in vectors:
            likelihood_a_reader = _reader_probability(a) * _bluffer_probability(b, condition)
            likelihood_b_reader = _bluffer_probability(a, condition) * _reader_probability(b)
            denominator = likelihood_a_reader + likelihood_b_reader
            if denominator <= 0:
                continue
            expected[(a, b)] = (denominator / 2.0, likelihood_a_reader / denominator)
    return expected


def _validate_manifest(manifest: Any) -> dict[str, dict[str, dict[str, dict[str, Any]]]]:
    _need(isinstance(manifest, dict), "manifest.json must contain an object")
    _need(manifest.get("study_id") == STUDY_ID, "manifest study_id does not match the frozen study")
    _need(manifest.get("planned_provider_requests") == TOTAL, "planned_provider_requests must equal 32")
    configuration = manifest.get("configuration_by_model")
    _need(isinstance(configuration, dict) and set(configuration) == set(MODELS),
          "configuration_by_model must contain exactly glm-5.3 and qwen3.8-max")
    requests = manifest.get("requests")
    _need(isinstance(requests, list) and len(requests) == TOTAL,
          "manifest.requests must contain exactly 32 fixed request rows")
    request_ids: set[str] = set()
    indices: set[int] = set()
    grouped: dict[str, dict[str, dict[str, Any]]] = {
        model: {condition: {} for condition in CONDITIONS} for model in MODELS
    }
    schedule_packets: dict[tuple[str, str], dict[tuple[tuple[int, int], tuple[int, int]], dict[str, Any]]] = defaultdict(dict)

    for index, row in enumerate(requests):
        _need(isinstance(row, dict), f"manifest.requests[{index}] must be an object")
        request_id = row.get("request_id")
        _need(isinstance(request_id, str) and request_id.strip() and request_id not in request_ids,
              f"manifest.requests[{index}] has a missing or duplicate request_id")
        request_ids.add(request_id)
        _need(row.get("kind") == "judge", f"{request_id} must be a Judge request")
        model, condition = row.get("model"), row.get("simulation_condition")
        _need(model in MODELS, f"{request_id} has an unknown model")
        _need(condition in CONDITIONS, f"{request_id} has an unknown simulation_condition")
        _need(row.get("bluffer_condition") == condition,
              f"{request_id} bluffer_condition must equal simulation_condition")
        _need(row.get("judge_condition") == "KNOWN_MECHANISM",
              f"{request_id} must use judge_condition=KNOWN_MECHANISM")
        _need(isinstance(row.get("case_id"), str) and row["case_id"].strip(),
              f"{request_id} must identify its packet in case_id")
        if row.get("packet_id") is not None:
            _need(row["case_id"] == row["packet_id"],
                  f"{request_id} case_id must bind the packet_id")
        schedule_index = row.get("schedule_index")
        _need(isinstance(schedule_index, int) and not isinstance(schedule_index, bool)
              and 1 <= schedule_index <= TOTAL and schedule_index not in indices,
              f"{request_id} has an invalid or duplicate schedule_index")
        indices.add(schedule_index)

        vector_a = _vector(row.get("vector_A"), f"{request_id}.vector_A")
        vector_b = _vector(row.get("vector_B"), f"{request_id}.vector_B")
        weight, posterior = row.get("prior_predictive_weight"), row.get("posterior_A")
        _need(_number(weight) and 0.0 < float(weight) <= 1.0,
              f"{request_id} prior_predictive_weight must be finite and positive")
        _need(_number(posterior) and 0.0 <= float(posterior) <= 1.0,
              f"{request_id} posterior_A must be in [0,1]")

        expected_packets = _expected_packet_rows(condition)
        key = (vector_a, vector_b)
        _need(key in expected_packets, f"{request_id} is outside the positive-support {condition} packet set")
        expected_weight, expected_posterior = expected_packets[key]
        _need(math.isclose(float(weight), expected_weight, rel_tol=0.0, abs_tol=MASS_TOLERANCE),
              f"{request_id} prior predictive weight does not match the frozen mechanism")
        _need(math.isclose(float(posterior), expected_posterior, rel_tol=0.0, abs_tol=MASS_TOLERANCE),
              f"{request_id} posterior_A does not match the frozen mechanism")

        slot = (model, condition)
        _need(key not in schedule_packets[slot], f"duplicate packet support row for {model}/{condition}: {key}")
        schedule_packets[slot][key] = row
        grouped[model][condition][request_id] = row

    _need(indices == set(range(1, TOTAL + 1)), "schedule_index must cover 1 through 32")
    expected_sizes = {"MARGINAL": 12, "JOINT": 4}
    for model in MODELS:
        for condition in CONDITIONS:
            expected_packets = _expected_packet_rows(condition)
            observed_packets = schedule_packets[(model, condition)]
            _need(len(observed_packets) == expected_sizes[condition],
                  f"{model}/{condition} must contain {expected_sizes[condition]} positive-support packets")
            _need(set(observed_packets) == set(expected_packets),
                  f"{model}/{condition} does not enumerate the complete positive-support packet set")
            total_weight = sum(float(row["prior_predictive_weight"]) for row in observed_packets.values())
            _need(math.isclose(total_weight, 1.0, rel_tol=0.0, abs_tol=MASS_TOLERANCE),
                  f"{model}/{condition} prior predictive weights must sum to one")
    return grouped


def _decision_loss(decision: str, posterior: float) -> float:
    if decision == "A":
        return 1.0 - posterior
    if decision == "B":
        return posterior
    return 0.25


def _optimal_decision(posterior: float) -> str:
    if posterior > 0.75:
        return "A"
    if posterior < 0.25:
        return "B"
    return "ABSTAIN"


def _forced_accuracy(predicted_p: float, posterior: float) -> float:
    if predicted_p > 0.5:
        return posterior
    if predicted_p < 0.5:
        return 1.0 - posterior
    return 0.5


def _sign_accuracy(predicted_p: float, posterior: float) -> float | None:
    if posterior == 0.5:
        return None
    if predicted_p == 0.5:
        return 0.5
    return float((predicted_p > 0.5) == (posterior > 0.5))


def _classify_receipt(run: Path, row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    request_id = row["request_id"]
    result: dict[str, Any] = {
        "request_id": request_id,
        "model": row["model"],
        "packet_id": row.get("packet_id", row["case_id"]),
        "simulation_condition": row["simulation_condition"],
        "bluffer_condition": row["bluffer_condition"],
        "judge_condition": row["judge_condition"],
        "vector_A": row["vector_A"],
        "vector_B": row["vector_B"],
        "prior_predictive_weight": float(row["prior_predictive_weight"]),
        "posterior_A": float(row["posterior_A"]),
    }
    path = run / "responses" / f"{request_id}.json"
    if not path.is_file():
        result.update({"status": "missing", "invalid_reason": None})
        return "missing", result

    try:
        receipt = study.read(path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        result.update({"status": "invalid", "invalid_reason": f"unreadable_receipt:{type(exc).__name__}"})
        return "invalid", result
    if not isinstance(receipt, dict):
        result.update({"status": "invalid", "invalid_reason": "receipt_not_object"})
        return "invalid", result
    result.update({"status": "invalid", "invalid_reason": None, "receipt_sha256": study.sha(path)})
    parsed, parse_status = study.parse_response(receipt.get("visible_text"), receipt.get("finish_reason"))
    result["raw_parse_status"] = parse_status
    result["receipt_parse_status"] = receipt.get("parse_status")
    result["raw_parse_matches_receipt"] = (
        receipt.get("parse_status") == parse_status and receipt.get("parsed") == parsed
    )
    if parsed is not None and isinstance(parsed, dict):
        if isinstance(parsed.get("reason"), str):
            result["reason"] = parsed["reason"]
        if _number(parsed.get("p_A")):
            result["p_A"] = float(parsed["p_A"])
        if isinstance(parsed.get("decision"), str) and parsed["decision"] in {"A", "B", "ABSTAIN"}:
            result["decision"] = parsed["decision"]
    for field, expected in (
        ("request_id", request_id),
        ("kind", "judge"),
        ("model", row["model"]),
        ("case_id", row["case_id"]),
        ("simulation_condition", row["simulation_condition"]),
        ("bluffer_condition", row["bluffer_condition"]),
        ("judge_condition", row["judge_condition"]),
    ):
        if receipt.get(field) != expected:
            result["invalid_reason"] = f"receipt_binding_mismatch:{field}"
            return "invalid", result

    if receipt.get("status") != "response_received":
        result["invalid_reason"] = f"transport_status:{receipt.get('status')}"
    elif receipt.get("http_status") != 200:
        result["invalid_reason"] = f"http_status:{receipt.get('http_status')}"
    elif receipt.get("returned_model") != row["model"]:
        result["invalid_reason"] = "returned_model_mismatch"
    elif parse_status != "valid":
        result["invalid_reason"] = f"raw_parse:{parse_status}"
    elif receipt.get("parse_status") != parse_status or receipt.get("parsed") != parsed:
        result["invalid_reason"] = "stored_parse_disagrees_with_raw_response"
    elif not isinstance(parsed, dict) or set(parsed) != {"p_A", "decision", "reason"}:
        result["invalid_reason"] = "strict_schema_mismatch"
    elif not _number(parsed.get("p_A")) or not 0.0 <= float(parsed["p_A"]) <= 1.0:
        result["invalid_reason"] = "invalid_p_A"
    elif not isinstance(parsed.get("decision"), str) or parsed["decision"] not in {"A", "B", "ABSTAIN"}:
        result["invalid_reason"] = "invalid_decision"
    elif not isinstance(parsed.get("reason"), str) or not parsed["reason"].strip():
        result["invalid_reason"] = "missing_reason"

    if result["invalid_reason"] is not None:
        return "invalid", result

    predicted_p = float(parsed["p_A"])
    posterior = float(row["posterior_A"])
    decision = parsed["decision"]
    actual_loss = _decision_loss(decision, posterior)
    optimal_decision = _optimal_decision(posterior)
    optimal_loss = min(posterior, 1.0 - posterior, 0.25)
    result.update({
        "status": "valid",
        "invalid_reason": None,
        "p_A": predicted_p,
        "decision": decision,
        "reason": parsed["reason"],
        "excess_brier": (predicted_p - posterior) ** 2,
        "expected_brier": (predicted_p - posterior) ** 2 + posterior * (1.0 - posterior),
        "forced_accuracy": _forced_accuracy(predicted_p, posterior),
        "decision_loss": actual_loss,
        "optimal_posterior_decision": optimal_decision,
        "optimal_posterior_loss": optimal_loss,
        "decision_matches_reported_probability_policy": decision == _optimal_decision(predicted_p),
        "excess_decision_loss": max(0.0, actual_loss - optimal_loss),
        "covered": decision != "ABSTAIN",
        "sign_accuracy": _sign_accuracy(predicted_p, posterior),
        "ambiguous_p_half_absolute_error": abs(predicted_p - 0.5) if posterior == 0.5 else None,
    })
    return "valid", result


def _weighted_sum(records: list[dict[str, Any]], key: str) -> float:
    return sum(row["prior_predictive_weight"] * float(row[key]) for row in records)


def _summarize_cell(model: str, condition: str, schedule_rows: dict[str, dict[str, Any]], run: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    expected_rows = list(schedule_rows.values())
    records: list[dict[str, Any]] = []
    response_rows: list[dict[str, Any]] = []
    missing_ids, invalid_ids = [], []
    for row in sorted(expected_rows, key=lambda value: value["schedule_index"]):
        state, record = _classify_receipt(run, row)
        response_rows.append(record)
        if state == "missing":
            missing_ids.append(row["request_id"])
        elif state == "invalid":
            invalid_ids.append(row["request_id"])
        else:
            records.append(record)

    expected_mass = sum(float(row["prior_predictive_weight"]) for row in expected_rows)
    observed_mass = sum(row["prior_predictive_weight"] for row in records)
    missing_mass = sum(float(schedule_rows[request_id]["prior_predictive_weight"]) for request_id in missing_ids)
    invalid_mass = sum(float(schedule_rows[request_id]["prior_predictive_weight"]) for request_id in invalid_ids)
    complete = (
        not missing_ids and not invalid_ids and len(records) == len(expected_rows)
        and math.isclose(observed_mass, 1.0, rel_tol=0.0, abs_tol=MASS_TOLERANCE)
        and math.isclose(expected_mass, 1.0, rel_tol=0.0, abs_tol=MASS_TOLERANCE)
    )

    observed_primary = _weighted_sum(records, "excess_brier")
    observed_brier = _weighted_sum(records, "expected_brier")
    observed_accuracy = _weighted_sum(records, "forced_accuracy")
    observed_decision_loss = _weighted_sum(records, "decision_loss")
    observed_excess_loss = _weighted_sum(records, "excess_decision_loss")
    observed_coverage = sum(row["prior_predictive_weight"] for row in records if row["covered"])
    ambiguous = [row for row in records if row["ambiguous_p_half_absolute_error"] is not None]
    all_ambiguous = [row for row in expected_rows if float(row["posterior_A"]) == 0.5]
    ambiguous_mass = sum(float(row["prior_predictive_weight"]) for row in all_ambiguous)
    observed_ambiguous_mass = sum(row["prior_predictive_weight"] for row in ambiguous)
    observed_ambiguous_error_mass = sum(
        row["prior_predictive_weight"] * float(row["ambiguous_p_half_absolute_error"])
        for row in ambiguous
    )
    sign_records = [row for row in records if row["sign_accuracy"] is not None]
    informative_mass = sum(
        float(row["prior_predictive_weight"])
        for row in expected_rows if float(row["posterior_A"]) != 0.5
    )
    observed_informative_mass = sum(row["prior_predictive_weight"] for row in sign_records)
    observed_sign_correct_mass = _weighted_sum(sign_records, "sign_accuracy") if sign_records else 0.0

    theoretical_bayes_risk = 0.125 if condition == "MARGINAL" else 0.25
    theoretical_forced_bayes_accuracy = 0.75 if condition == "MARGINAL" else 0.5
    observed_max_error = max((abs(row["p_A"] - row["posterior_A"]) for row in records), default=None)
    observed_sign_accuracy = (
        observed_sign_correct_mass / observed_informative_mass if observed_informative_mass > 0 else None
    )
    observed_ambiguous_error = (
        observed_ambiguous_error_mass / observed_ambiguous_mass if observed_ambiguous_mass > 0 else None
    )

    summary = {
        "model": model,
        "simulation_condition": condition,
        "expected_packets": len(expected_rows),
        "valid_packets": len(records),
        "missing_count": len(missing_ids),
        "missing_request_ids": missing_ids,
        "invalid_count": len(invalid_ids),
        "invalid_request_ids": invalid_ids,
        "observed_probability_mass": observed_mass,
        "missing_probability_mass": missing_mass,
        "invalid_probability_mass": invalid_mass,
        "expected_probability_mass": expected_mass,
        "complete_positive_support": complete,
        "theoretical_bayes_risk": theoretical_bayes_risk,
        "theoretical_forced_bayes_accuracy": theoretical_forced_bayes_accuracy,
        "primary_excess_brier": observed_primary if complete else None,
        "observed_excess_brier_contribution": observed_primary,
        "normalized_expected_brier": observed_brier if complete else None,
        "observed_normalized_expected_brier_contribution": observed_brier,
        "expected_forced_accuracy_argmax_p_A": observed_accuracy if complete else None,
        "observed_forced_accuracy_contribution": observed_accuracy,
        "expected_actual_decision_loss": observed_decision_loss if complete else None,
        "observed_actual_decision_loss_contribution": observed_decision_loss,
        "excess_decision_loss_vs_posterior_optimum": observed_excess_loss if complete else None,
        "observed_excess_decision_loss_contribution": observed_excess_loss,
        "weighted_coverage": observed_coverage if complete else None,
        "observed_coverage_mass": observed_coverage,
        "diagnostic_sign_accuracy_nonambiguous": (
            observed_sign_accuracy if complete and informative_mass > 0 else None
        ),
        "observed_sign_correct_mass": observed_sign_correct_mass,
        "observed_nonambiguous_probability_mass": observed_informative_mass,
        "nonambiguous_probability_mass": informative_mass,
        "ambiguous_p_half_error": observed_ambiguous_error if complete and ambiguous_mass > 0 else None,
        "observed_ambiguous_p_half_error_mass": observed_ambiguous_error_mass,
        "observed_ambiguous_probability_mass": observed_ambiguous_mass,
        "ambiguous_probability_mass": ambiguous_mass,
        "max_absolute_probability_error": observed_max_error if complete else None,
        "observed_max_absolute_probability_error": observed_max_error,
        "gate_pass": bool(complete and observed_primary <= EXCESS_BRIER_LIMIT),
        "gate_limit_excess_brier": EXCESS_BRIER_LIMIT,
        "gate_basis": "complete finite support and weighted excess Brier <= 0.01; practical finite-cell qualification only",
    }
    return summary, response_rows


def build_summary(run: Path) -> dict[str, Any]:
    run = run.resolve()
    run.relative_to(ROOT.resolve())
    # The runner audit checks frozen inputs, exact schedules, prompts and receipts.
    # Re-reading and parsing each response below binds every scored value to raw text.
    study.audit(run)
    manifest = study.read(run / "manifest.json")
    status = study.read(run / "status.json")
    grouped = _validate_manifest(manifest)

    # If the run stores a separate schedule, require byte-decoded JSON equality to the manifest copy.
    schedule_path = run / "schedule.json"
    if schedule_path.is_file():
        _need(study.read(schedule_path) == manifest["requests"], "schedule.json differs from manifest.requests")

    cells, response_rows = [], []
    for model in MODELS:
        for condition in CONDITIONS:
            cell, rows = _summarize_cell(model, condition, grouped[model][condition], run)
            cells.append(cell)
            response_rows.extend(rows)

    valid_count = sum(cell["valid_packets"] for cell in cells)
    dispatched = {p.stem for p in (run / "dispatches").glob("*.json")}
    received = {p.stem for p in (run / "responses").glob("*.json")}
    scheduled = {r["request_id"] for r in manifest["requests"]}
    complete_32_valid = valid_count == TOTAL and all(cell["complete_positive_support"] for cell in cells)
    if not complete_32_valid:
        overall_gate = "INCOMPLETE"
    elif all(cell["gate_pass"] for cell in cells):
        overall_gate = "PASS"
    else:
        overall_gate = "FAIL"

    analyzer_hash = hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    return {
        "schema_version": 1,
        "study_id": STUDY_ID,
        "analysis_status": "complete" if complete_32_valid else "incomplete",
        "audit": "passed",
        "planned_provider_requests": TOTAL,
        "valid_response_count": valid_count,
        "run_state": status.get("state"),
        "halt_reason": status.get("halt_reason"),
        "configuration_by_model": manifest["configuration_by_model"],
        "dispatched_calls": len(dispatched),
        "response_receipt_count": len(received),
        "not_dispatched_request_ids": sorted(scheduled - dispatched),
        "dispatched_without_receipt_ids": sorted(dispatched - received),
        "status_counts_consistent": status.get("provider_requests") == len(dispatched)
            and status.get("response_count") == len(received) and status.get("valid") == valid_count,
        "complete_32_valid": complete_32_valid,
        "overall_gate": overall_gate,
        "gate_interpretation": "A pass qualifies only these exhaustive finite cells under the stated known mechanism; it is not a statistical or population claim.",
        "claim_boundary": [
            "This is a finite known-mechanism Judge qualification over the enumerated positive-support packets.",
            "It does not establish population calibration, population Theory of Mind, Actor strategy, or general model performance.",
            "Each model-condition packet is a single call; the finite rows are not treated as independent population samples.",
        ],
        "cells": cells,
        "response_rows": response_rows,
        "provenance": {
            "run_name": run.name,
            "analyzer_sha256_lf_utf8": analyzer_hash,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN, help="frozen simulation run directory")
    parser.add_argument("--write", action="store_true", help="write analysis/summary.json once inside the run")
    args = parser.parse_args(argv)
    try:
        summary = build_summary(args.run)
        payload = (json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
        if args.write:
            output = args.run.resolve() / "analysis" / "summary.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            try:
                with output.open("xb") as stream:
                    stream.write(payload)
                    stream.flush()
            except FileExistsError:
                raise AnalysisError("analysis/summary.json is write-once and already exists") from None
            print(output.relative_to(ROOT.resolve()).as_posix())
        else:
            sys.stdout.buffer.write(payload)
        return 0
    except (AnalysisError, AssertionError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"analysis error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
