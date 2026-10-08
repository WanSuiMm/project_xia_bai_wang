"""Offline analysis for the failure-selected JES32 amended-parser supplement."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import analyze_joint_epistemic_simulation as original_analysis
import run_joint_epistemic_simulation as study
import run_joint_epistemic_supplement as recovery


ROOT = recovery.ROOT
DEFAULT_RUN = recovery.DEFAULT_RUN
TOTAL = original_analysis.TOTAL
MODELS = original_analysis.MODELS
CONDITIONS = original_analysis.CONDITIONS
EXCESS_BRIER_LIMIT = original_analysis.EXCESS_BRIER_LIMIT
MASS_TOLERANCE = original_analysis.MASS_TOLERANCE
SUPPLEMENT_STUDY_ID = "joint_epistemic_simulation32_supplement_20261009"


class AnalysisError(RuntimeError):
    """Raised when a parent, supplement, or receipt binding is inconsistent."""


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise AnalysisError(message)


def _within(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    _need(path != root.resolve(), f"path must identify a file below its root: {relative}")
    return path


def _object(path: Path, where: str) -> dict[str, Any]:
    value = study.read(path)
    _need(isinstance(value, dict), f"{where} must contain an object")
    return value


def _file_ids(folder: Path) -> set[str]:
    return {path.stem for path in folder.glob("*.json")}


def _receipt_binding(run: Path, row: dict[str, Any], receipt: dict[str, Any]) -> str | None:
    request_id = row["request_id"]
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
            return f"receipt_binding_mismatch:{field}"

    prompt = _within(run, row["prompt_path"])
    if not prompt.is_file():
        return "missing_frozen_prompt"
    prompt_digest = study.sha(prompt)
    if receipt.get("prompt_sha256") != prompt_digest:
        return "prompt_sha256_mismatch"

    dispatch_path = run / "dispatches" / f"{request_id}.json"
    prompt_receipt_path = run / "prompt_receipts" / f"{request_id}.json"
    if not dispatch_path.is_file():
        return "missing_dispatch_receipt"
    if not prompt_receipt_path.is_file():
        return "missing_prompt_receipt"
    dispatch = _object(dispatch_path, f"dispatches/{request_id}.json")
    expected_dispatch = row | {
        "prompt_sha256": prompt_digest,
        "dispatched_utc": dispatch.get("dispatched_utc"),
    }
    if dispatch != expected_dispatch or not isinstance(dispatch.get("dispatched_utc"), str):
        return "dispatch_binding_mismatch"
    prompt_receipt = _object(prompt_receipt_path, f"prompt_receipts/{request_id}.json")
    if prompt_receipt.get("request_id") != request_id or prompt_receipt.get("prompt_sha256") != prompt_digest:
        return "prompt_receipt_binding_mismatch"
    return None


def _verify_parser_fields(receipt: dict[str, Any], row: dict[str, Any]) -> tuple[Any, str, Any, str, Any]:
    """Recompute raw and completion parses; return strict and completion results."""
    visible_text = receipt.get("visible_text")
    finish_reason = receipt.get("finish_reason")
    _need(isinstance(visible_text, str), f"{row['request_id']} visible_text must be a string")
    state = receipt.get("status")
    returned_model = receipt.get("returned_model")

    if state == "response_received" and returned_model == row["model"]:
        strict_parsed, strict_status = study.parse_response(visible_text, finish_reason)
        completion_parsed, completion_status, acceptance = recovery.parse_completion(visible_text, finish_reason)
    else:
        strict_parsed = None
        strict_status = "unexpected_model" if state == "response_received" else "not_received"
        completion_parsed, completion_status, acceptance = None, "not_received", None

    _need(receipt.get("parsed") == strict_parsed and receipt.get("parse_status") == strict_status,
          f"{row['request_id']} strict parser fields disagree with the original parser")
    _need(
        receipt.get("completion_parsed") == completion_parsed
        and receipt.get("completion_parse_status") == completion_status
        and receipt.get("format_acceptance") == acceptance,
        f"{row['request_id']} stored completion parser fields disagree with recomputation",
    )

    if completion_status == "valid":
        _need(isinstance(completion_parsed, dict), f"{row['request_id']} valid completion parse must be an object")
        _need(acceptance in {"strict", "identical_duplicate_trailer"},
              f"{row['request_id']} has an unrecognized format acceptance")
        if acceptance == "strict":
            _need(strict_status == "valid" and completion_parsed == strict_parsed,
                  f"{row['request_id']} strict acceptance differs from the original parse")
        else:
            _need(strict_status != "valid", f"{row['request_id']} duplicate-trailer acceptance was already strict-valid")
    else:
        _need(completion_parsed is None and acceptance is None,
              f"{row['request_id']} invalid completion parse must not contain a parsed value")
    return strict_parsed, strict_status, completion_parsed, completion_status, acceptance


def _score(row: dict[str, Any], parsed: dict[str, Any]) -> dict[str, Any]:
    predicted_p = float(parsed["p_A"])
    posterior = float(row["posterior_A"])
    decision = parsed["decision"]
    actual_loss = original_analysis._decision_loss(decision, posterior)
    optimal_decision = original_analysis._optimal_decision(posterior)
    optimal_loss = min(posterior, 1.0 - posterior, 0.25)
    return {
        "request_id": row["request_id"],
        "model": row["model"],
        "packet_id": row.get("packet_id", row["case_id"]),
        "simulation_condition": row["simulation_condition"],
        "bluffer_condition": row["bluffer_condition"],
        "judge_condition": row["judge_condition"],
        "vector_A": row["vector_A"],
        "vector_B": row["vector_B"],
        "prior_predictive_weight": float(row["prior_predictive_weight"]),
        "posterior_A": posterior,
        "status": "valid",
        "invalid_reason": None,
        "p_A": predicted_p,
        "decision": decision,
        "reason": parsed["reason"],
        "excess_brier": (predicted_p - posterior) ** 2,
        "expected_brier": (predicted_p - posterior) ** 2 + posterior * (1.0 - posterior),
        "forced_accuracy": original_analysis._forced_accuracy(predicted_p, posterior),
        "decision_loss": actual_loss,
        "optimal_posterior_decision": optimal_decision,
        "optimal_posterior_loss": optimal_loss,
        "decision_matches_reported_probability_policy": decision == original_analysis._optimal_decision(predicted_p),
        "excess_decision_loss": max(0.0, actual_loss - optimal_loss),
        "covered": decision != "ABSTAIN",
        "sign_accuracy": original_analysis._sign_accuracy(predicted_p, posterior),
        "ambiguous_p_half_absolute_error": abs(predicted_p - 0.5) if posterior == 0.5 else None,
    }


def _classify_supplement(run: Path, row: dict[str, Any]) -> dict[str, Any]:
    request_id = row["request_id"]
    path = run / "responses" / f"{request_id}.json"
    if not path.is_file():
        return {
            "state": "missing",
            "strict_state": "missing",
            "record": {
                "request_id": request_id,
                "model": row["model"],
                "packet_id": row.get("packet_id", row["case_id"]),
                "simulation_condition": row["simulation_condition"],
                "prior_predictive_weight": float(row["prior_predictive_weight"]),
                "posterior_A": float(row["posterior_A"]),
                "status": "missing",
                "invalid_reason": None,
            },
            "strict_record": None,
            "format_acceptance": None,
            "receipt_sha256": None,
        }

    try:
        receipt = study.read(path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return {
            "state": "invalid",
            "strict_state": "invalid",
            "record": {
                "request_id": request_id,
                "model": row["model"],
                "packet_id": row.get("packet_id", row["case_id"]),
                "simulation_condition": row["simulation_condition"],
                "prior_predictive_weight": float(row["prior_predictive_weight"]),
                "posterior_A": float(row["posterior_A"]),
                "status": "invalid",
                "invalid_reason": f"unreadable_receipt:{type(exc).__name__}",
            },
            "strict_record": None,
            "format_acceptance": None,
            "receipt_sha256": study.sha(path),
        }
    if not isinstance(receipt, dict):
        reason = "receipt_not_object"
        binding_reason = reason
        strict_parsed = strict_status = completion_parsed = completion_status = acceptance = None
    else:
        binding_reason = _receipt_binding(run, row, receipt)
        reason = binding_reason
        strict_parsed, strict_status, completion_parsed, completion_status, acceptance = _verify_parser_fields(receipt, row)
        if reason is None:
            state = receipt.get("status")
            if state != "response_received":
                reason = f"transport_status:{state}"
            elif receipt.get("http_status") != 200:
                reason = f"http_status:{receipt.get('http_status')}"
            elif receipt.get("returned_model") != row["model"]:
                reason = "returned_model_mismatch"
            elif completion_status != "valid":
                reason = f"completion_parse:{completion_status}"
            elif set(completion_parsed) != {"p_A", "decision", "reason"}:
                reason = "completion_schema_mismatch"
            elif not original_analysis._number(completion_parsed.get("p_A")) or not 0.0 <= float(completion_parsed["p_A"]) <= 1.0:
                reason = "invalid_p_A"
            elif completion_parsed.get("decision") not in {"A", "B", "ABSTAIN"}:
                reason = "invalid_decision"
            elif not isinstance(completion_parsed.get("reason"), str) or not completion_parsed["reason"].strip():
                reason = "missing_reason"

    if not isinstance(receipt, dict):
        state, strict_status, completion_status = "invalid", None, None
    else:
        state = receipt.get("status")
    if reason is not None:
        strict_valid = (
            isinstance(receipt, dict)
            and binding_reason is None
            and receipt.get("status") == "response_received"
            and receipt.get("http_status") == 200
            and receipt.get("returned_model") == row["model"]
            and strict_status == "valid"
            and isinstance(strict_parsed, dict)
        )
        return {
            "state": "invalid",
            "strict_state": "valid" if strict_valid else "invalid",
            "record": {
                "request_id": request_id,
                "model": row["model"],
                "packet_id": row.get("packet_id", row["case_id"]),
                "simulation_condition": row["simulation_condition"],
                "prior_predictive_weight": float(row["prior_predictive_weight"]),
                "posterior_A": float(row["posterior_A"]),
                "status": "invalid",
                "invalid_reason": reason,
                "raw_parse_status": strict_status,
                "completion_parse_status": completion_status,
                "format_acceptance": acceptance,
                "receipt_status": receipt.get("status") if isinstance(receipt, dict) else None,
                "http_status": receipt.get("http_status") if isinstance(receipt, dict) else None,
            },
            "strict_record": _score(row, strict_parsed) if strict_valid else None,
            "format_acceptance": acceptance,
            "receipt_sha256": study.sha(path),
        }

    record = _score(row, completion_parsed)
    record.update({
        "raw_parse_status": strict_status,
        "completion_parse_status": completion_status,
        "format_acceptance": acceptance,
        "receipt_status": receipt.get("status"),
        "http_status": receipt.get("http_status"),
    })
    strict_record = _score(row, strict_parsed) if strict_status == "valid" and isinstance(strict_parsed, dict) else None
    return {
        "state": "valid",
        "strict_state": "valid" if strict_record is not None else "invalid",
        "record": record,
        "strict_record": strict_record,
        "format_acceptance": acceptance,
        "receipt_sha256": study.sha(path),
    }


def _weighted_sum(records: list[dict[str, Any]], key: str) -> float:
    return sum(float(row["prior_predictive_weight"]) * float(row[key]) for row in records)


def _summarize_cell(
    model: str,
    condition: str,
    rows: list[dict[str, Any]],
    classified: dict[str, dict[str, Any]],
    variant: str,
) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda value: value["schedule_index"])
    records: list[dict[str, Any]] = []
    missing_ids: list[str] = []
    invalid_ids: list[str] = []
    for row in ordered:
        item = classified[row["request_id"]]
        state = item["state"] if variant == "completion" else item["strict_state"]
        record = item["record"] if variant == "completion" else item["strict_record"]
        if state == "missing":
            missing_ids.append(row["request_id"])
        elif state != "valid" or record is None:
            invalid_ids.append(row["request_id"])
        else:
            records.append(record)

    expected_mass = sum(float(row["prior_predictive_weight"]) for row in ordered)
    observed_mass = sum(float(row["prior_predictive_weight"]) for row in records)
    by_id = {row["request_id"]: row for row in ordered}
    missing_mass = sum(float(by_id[rid]["prior_predictive_weight"]) for rid in missing_ids)
    invalid_mass = sum(float(by_id[rid]["prior_predictive_weight"]) for rid in invalid_ids)
    complete = (
        not missing_ids and not invalid_ids and len(records) == len(ordered)
        and math.isclose(observed_mass, 1.0, rel_tol=0.0, abs_tol=MASS_TOLERANCE)
        and math.isclose(expected_mass, 1.0, rel_tol=0.0, abs_tol=MASS_TOLERANCE)
    )

    observed_primary = _weighted_sum(records, "excess_brier")
    observed_brier = _weighted_sum(records, "expected_brier")
    observed_accuracy = _weighted_sum(records, "forced_accuracy")
    observed_decision_loss = _weighted_sum(records, "decision_loss")
    observed_excess_loss = _weighted_sum(records, "excess_decision_loss")
    observed_coverage = sum(float(row["prior_predictive_weight"]) for row in records if row["covered"])
    ambiguous = [row for row in records if row["ambiguous_p_half_absolute_error"] is not None]
    all_ambiguous = [row for row in ordered if float(row["posterior_A"]) == 0.5]
    ambiguous_mass = sum(float(row["prior_predictive_weight"]) for row in all_ambiguous)
    observed_ambiguous_mass = sum(float(row["prior_predictive_weight"]) for row in ambiguous)
    observed_ambiguous_error_mass = sum(
        float(row["prior_predictive_weight"]) * float(row["ambiguous_p_half_absolute_error"])
        for row in ambiguous
    )
    sign_records = [row for row in records if row["sign_accuracy"] is not None]
    informative_mass = sum(
        float(row["prior_predictive_weight"])
        for row in ordered if float(row["posterior_A"]) != 0.5
    )
    observed_informative_mass = sum(float(row["prior_predictive_weight"]) for row in sign_records)
    observed_sign_correct_mass = _weighted_sum(sign_records, "sign_accuracy") if sign_records else 0.0
    observed_max_error = max((abs(float(row["p_A"]) - float(row["posterior_A"])) for row in records), default=None)
    observed_sign_accuracy = (
        observed_sign_correct_mass / observed_informative_mass if observed_informative_mass > 0 else None
    )
    observed_ambiguous_error = (
        observed_ambiguous_error_mass / observed_ambiguous_mass if observed_ambiguous_mass > 0 else None
    )

    summary = {
        "analysis_variant": variant,
        "model": model,
        "simulation_condition": condition,
        "expected_packets": len(ordered),
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
        "theoretical_bayes_risk": 0.125 if condition == "MARGINAL" else 0.25,
        "theoretical_forced_bayes_accuracy": 0.75 if condition == "MARGINAL" else 0.5,
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
    return summary


def _source_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def build_summary(run: Path) -> dict[str, Any]:
    """Audit both runs and score the fixed 32 slots with the supplement overlay."""
    run = run.resolve()
    run.relative_to(ROOT.resolve())
    _need(run != ROOT.resolve(), "run must be below the project root")

    recovery.audit(run)
    parent = recovery.parent(run).resolve()
    parent.relative_to(ROOT.resolve())
    study.audit(parent)

    parent_manifest = _object(parent / "manifest.json", "parent manifest.json")
    parent_grouped = original_analysis._validate_manifest(parent_manifest)
    parent_rows = parent_manifest["requests"]
    parent_rows_by_id = {row["request_id"]: row for row in parent_rows}
    parent_schedule = study.read(parent / "schedule.json")
    _need(parent_schedule == parent_rows, "parent schedule.json differs from its manifest")

    manifest = _object(run / "manifest.json", "supplement manifest.json")
    _need(manifest.get("study_id") == SUPPLEMENT_STUDY_ID, "supplement study_id differs from the authorized supplement")
    _need(manifest.get("parent_run_name") == parent.name, "supplement parent_run_name does not identify its audited parent")
    _need(manifest.get("planned_provider_requests") == 30, "supplement must schedule the remaining 30 rows")
    _need(manifest.get("configuration_by_model") == parent_manifest.get("configuration_by_model"),
          "supplement provider configuration differs from the parent")
    retained = manifest.get("retained_valid_ids")
    _need(isinstance(retained, list) and len(retained) == 2 and len(set(retained)) == 2,
          "retained_valid_ids must identify exactly two original strict-valid responses")
    _need(set(retained) <= set(parent_rows_by_id), "retained_valid_ids contains a non-parent request")

    parent_schedule_copy_path = run / "parent_schedule.json"
    copied_parent_rows = study.read(parent_schedule_copy_path)
    _need(copied_parent_rows == parent_rows, "parent_schedule.json differs from the original 32-row schedule")
    _need(len(copied_parent_rows) == TOTAL, "parent_schedule.json must contain all 32 original rows")

    supplement_rows = manifest.get("requests")
    _need(isinstance(supplement_rows, list) and len(supplement_rows) == 30,
          "supplement manifest.requests must contain exactly 30 rows")
    supplement_ids = [row.get("request_id") if isinstance(row, dict) else None for row in supplement_rows]
    _need(all(isinstance(rid, str) for rid in supplement_ids) and len(set(supplement_ids)) == 30,
          "supplement request IDs must be unique strings")
    expected_supplement_ids = set(parent_rows_by_id) - set(retained)
    _need(set(supplement_ids) == expected_supplement_ids, "supplement requests must be exactly the 30 non-retained parent IDs")
    for row in supplement_rows:
        _need(row == parent_rows_by_id[row["request_id"]],
              f"{row['request_id']} differs from its frozen original schedule row")
    own_schedule_path = run / "schedule.json"
    if own_schedule_path.is_file():
        _need(study.read(own_schedule_path) == supplement_rows, "supplement schedule.json differs from manifest.requests")

    original_summary = original_analysis.build_summary(parent)
    registered_path = parent / "analysis" / "summary.json"
    _need(registered_path.is_file(), "registered original analysis/summary.json is missing")
    registered_summary = _object(registered_path, "registered original analysis/summary.json")
    _need(registered_summary == original_summary, "registered original summary differs from a fresh strict-only receipt analysis")
    _need(registered_summary.get("analysis_status") == "incomplete"
          and registered_summary.get("overall_gate") == "INCOMPLETE",
          "registered original summary must remain INCOMPLETE")
    _need(registered_summary.get("valid_response_count") == 2,
          "registered original summary must preserve the two strict-valid responses")

    original_classified: dict[str, dict[str, Any]] = {}
    parent_states: dict[str, str] = {}
    for row in parent_rows:
        state, record = original_analysis._classify_receipt(parent, row)
        original_classified[row["request_id"]] = {"state": state, "record": record, "strict_state": state,
                                                   "strict_record": record if state == "valid" else None,
                                                   "format_acceptance": "strict" if state == "valid" else None,
                                                   "receipt_sha256": record.get("receipt_sha256")}
        parent_states[row["request_id"]] = state
    parent_valid_ids = {rid for rid, state in parent_states.items() if state == "valid"}
    parent_invalid_ids = {rid for rid, state in parent_states.items() if state == "invalid"}
    parent_missing_ids = {rid for rid, state in parent_states.items() if state == "missing"}
    _need(parent_valid_ids == set(retained), "retained_valid_ids must equal the original analyzer's strict-valid IDs")
    _need(len(parent_valid_ids) == 2 and len(parent_invalid_ids) == 1 and len(parent_missing_ids) == 29,
          "original strict classifications must remain 2 valid, 1 invalid, and 29 missing")

    parent_dispatch_ids = _file_ids(parent / "dispatches")
    parent_response_ids = _file_ids(parent / "responses")
    _need(len(parent_dispatch_ids) == 3 and parent_dispatch_ids == parent_response_ids,
          "original parent must retain exactly three physical attempts with receipts")
    _need(_file_ids(parent / "prompt_receipts") == parent_dispatch_ids,
          "original parent prompt receipts must match its three physical attempts")
    _need(parent_dispatch_ids <= set(parent_rows_by_id), "parent dispatch contains an unscheduled request")
    by_schedule_index = sorted(parent_rows, key=lambda row: row["schedule_index"])
    _need(parent_dispatch_ids == {row["request_id"] for row in by_schedule_index[:3]},
          "parent attempts must remain the original first three scheduled slots")
    _need(parent_states[by_schedule_index[0]["request_id"]] == "valid"
          and parent_states[by_schedule_index[1]["request_id"]] == "valid"
          and parent_states[by_schedule_index[2]["request_id"]] == "invalid",
          "the original third physical attempt must remain strict-invalid and excluded")

    new_dispatch_ids = _file_ids(run / "dispatches")
    new_response_ids = _file_ids(run / "responses")
    _need(new_dispatch_ids <= expected_supplement_ids, "supplement dispatched an unplanned request")
    _need(new_response_ids <= new_dispatch_ids, "supplement has a response without a dispatch")
    _need(len(new_dispatch_ids) <= 30, "supplement contains more than one attempt per fixed slot")
    _need(_file_ids(run / "prompt_receipts") <= expected_supplement_ids,
          "supplement prompt receipt contains an unplanned request")
    supplement_status = _object(run / "status.json", "supplement status.json")
    status_counts_consistent = (
        supplement_status.get("provider_requests") == len(new_dispatch_ids)
        and supplement_status.get("response_count") == len(new_response_ids)
    )

    supplement_classified: dict[str, dict[str, Any]] = {}
    receipt_hashes: list[str] = []
    for row in supplement_rows:
        item = _classify_supplement(run, row)
        supplement_classified[row["request_id"]] = item
        if item.get("receipt_sha256"):
            receipt_hashes.append(f"{row['request_id']}:{item['receipt_sha256']}")

    combined: dict[str, dict[str, Any]] = {}
    response_rows: list[dict[str, Any]] = []
    row_attempt_counts: dict[str, int] = {}
    for row in by_schedule_index:
        request_id = row["request_id"]
        original_item = original_classified[request_id]
        parent_attempt = request_id in parent_dispatch_ids
        if request_id in retained:
            selected = original_item
            source = "original_strict_valid"
        else:
            selected = supplement_classified[request_id]
            source = "supplement_first_attempt"
        combined[request_id] = selected
        row_attempt_counts[request_id] = int(parent_attempt) + int(request_id in new_dispatch_ids)
        response_row = dict(selected["record"])
        response_row.update({
            "schedule_index": row["schedule_index"],
            "selection_source": source,
            "parent_strict_status": original_item["state"],
            "parent_invalid_reason": original_item["record"].get("invalid_reason"),
            "parent_attempted": parent_attempt,
            "supplement_attempted": request_id in new_dispatch_ids,
            "physical_attempt_count_for_slot": row_attempt_counts[request_id],
            "format_acceptance": selected.get("format_acceptance"),
            "receipt_sha256": selected.get("receipt_sha256"),
        })
        response_rows.append(response_row)

    cells: list[dict[str, Any]] = []
    strict_cells: list[dict[str, Any]] = []
    normalization_by_cell: list[dict[str, Any]] = []
    for model in MODELS:
        for condition in CONDITIONS:
            rows = [row for row in parent_rows if row["model"] == model and row["simulation_condition"] == condition]
            completion_cell = _summarize_cell(model, condition, rows, combined, "completion")
            strict_cell = _summarize_cell(model, condition, rows, combined, "strict")
            completions = [
                rid for rid in (row["request_id"] for row in rows)
                if combined[rid]["state"] == "valid" and combined[rid].get("format_acceptance") == "identical_duplicate_trailer"
            ]
            completion_cell["narrow_normalization_count"] = len(completions)
            completion_cell["narrow_normalization_request_ids"] = completions
            strict_cell["narrow_normalization_excluded_count"] = len(completions)
            normalization_by_cell.append({
                "model": model,
                "simulation_condition": condition,
                "accepted_identical_duplicate_trailer_count": len(completions),
                "request_ids": completions,
            })
            cells.append(completion_cell)
            strict_cells.append(strict_cell)

    all_valid = sum(cell["valid_packets"] for cell in cells)
    all_strict_valid = sum(cell["valid_packets"] for cell in strict_cells)
    completion_complete = all(cell["complete_positive_support"] for cell in cells)
    strict_complete = all(cell["complete_positive_support"] for cell in strict_cells)
    completion_gate = (
        "INCOMPLETE" if not completion_complete else "PASS" if all(cell["gate_pass"] for cell in cells) else "FAIL"
    )
    strict_gate = (
        "INCOMPLETE" if not strict_complete else "PASS" if all(cell["gate_pass"] for cell in strict_cells) else "FAIL"
    )
    normalized_ids = [
        row["request_id"] for row in response_rows
        if row.get("status") == "valid" and row.get("format_acceptance") == "identical_duplicate_trailer"
    ]
    receipt_bundle = hashlib.sha256(("\n".join(sorted(receipt_hashes)) + "\n").encode("utf-8")).hexdigest()
    new_attempt_count = len(new_dispatch_ids)
    return {
        "schema_version": 1,
        "study_id": original_analysis.STUDY_ID,
        "supplement_study_id": SUPPLEMENT_STUDY_ID,
        "analysis_kind": "failure_selected_amended_parser_overlay",
        "analysis_status": "complete" if completion_complete else "incomplete",
        "audit": "passed",
        "planned_provider_requests": TOTAL,
        "completion_valid_response_count": all_valid,
        "run_state": supplement_status.get("state"),
        "halt_reason": supplement_status.get("halt_reason"),
        "supplement_status_counts_consistent": status_counts_consistent,
        "completion_complete_32_valid": completion_complete,
        "completion_overall_gate": completion_gate,
        "completion_gate_interpretation": "A pass qualifies only these exhaustive finite cells under the stated known mechanism; it is not a statistical or population claim.",
        "selection_boundary": [
            "This is a failure-selected overlay created after the original strict-parser run halted at its third attempt.",
            "The two original strict-valid receipts are retained; the original strict-invalid third receipt remains excluded.",
            "Only the first supplement attempt is available for each remaining fixed slot; no best-of selection or repeated-call averaging is used.",
            "The overlay does not replace the registered original incomplete summary and is not a clean original 32-call run.",
        ],
        "original_registered_analysis": {
            "path": "analysis/summary.json",
            "sha256": study.sha(registered_path),
            "analysis_status": registered_summary["analysis_status"],
            "overall_gate": registered_summary["overall_gate"],
            "planned_provider_requests": registered_summary["planned_provider_requests"],
            "valid_response_count": registered_summary["valid_response_count"],
            "dispatched_calls": registered_summary["dispatched_calls"],
            "response_receipt_count": registered_summary["response_receipt_count"],
            "preserved_unchanged": True,
        },
        "physical_attempts": {
            "parent_attempt_count": len(parent_dispatch_ids),
            "parent_response_receipt_count": len(parent_response_ids),
            "parent_valid_count": len(parent_valid_ids),
            "parent_invalid_count": len(parent_invalid_ids),
            "parent_missing_slot_count": len(parent_missing_ids),
            "supplement_attempt_count": new_attempt_count,
            "supplement_response_receipt_count": len(new_response_ids),
            "combined_physical_attempt_count": len(parent_dispatch_ids) + new_attempt_count,
            "supplement_unattempted_request_ids": sorted(expected_supplement_ids - new_dispatch_ids),
            "original_invalid_request_ids_excluded": sorted(parent_invalid_ids),
            "retained_original_valid_request_ids": sorted(parent_valid_ids),
        },
        "configuration_by_model": manifest["configuration_by_model"],
        "cells": cells,
        "overall_gate": completion_gate,
        "strict_only_sensitivity": {
            "analysis_status": "complete" if strict_complete else "incomplete",
            "valid_response_count": all_strict_valid,
            "complete_32_valid": strict_complete,
            "overall_gate": strict_gate,
            "gate_interpretation": "Strict-format sensitivity includes only the two retained original strict-valid receipts and supplement responses accepted by the original parser.",
            "cells": strict_cells,
        },
        "narrow_normalization_counts": {
            "acceptance_label": "identical_duplicate_trailer",
            "valid_normalized_response_count": len(normalized_ids),
            "request_ids": normalized_ids,
            "by_model_condition": normalization_by_cell,
            "original_invalid_third_included": False,
        },
        "response_rows": response_rows,
        "provenance": {
            "run_name": run.name,
            "parent_run_name": parent.name,
            "analyzer_sha256_lf_utf8": _source_sha(Path(__file__).resolve()),
            "recovery_runner_sha256_lf_utf8": _source_sha(Path(recovery.__file__).resolve()),
            "original_runner_sha256_lf_utf8": _source_sha(Path(study.__file__).resolve()),
            "original_analyzer_sha256_lf_utf8": _source_sha(Path(original_analysis.__file__).resolve()),
            "parent_manifest_sha256": study.sha(parent / "manifest.json"),
            "parent_schedule_sha256": study.sha(parent / "schedule.json"),
            "parent_registered_summary_sha256": study.sha(registered_path),
            "supplement_manifest_sha256": study.sha(run / "manifest.json"),
            "supplement_parent_schedule_sha256": study.sha(parent_schedule_copy_path),
            "supplement_schedule_sha256": study.sha(own_schedule_path) if own_schedule_path.is_file() else None,
            "receipt_bundle_sha256_sorted_request_id_and_receipt_sha256": receipt_bundle,
            "parent_analyzer_validated_32_row_oracle": True,
            "original_registered_summary_recomputed_equal": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN, help="supplement run directory")
    parser.add_argument("--write", action="store_true", help="write analysis/completion_summary.json once")
    args = parser.parse_args(argv)
    try:
        summary = build_summary(args.run)
        payload = (json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
        if args.write:
            output = args.run.resolve() / "analysis" / "completion_summary.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            try:
                with output.open("xb") as stream:
                    stream.write(payload)
                    stream.flush()
            except FileExistsError:
                raise AnalysisError("analysis/completion_summary.json is write-once and already exists") from None
            print(output.relative_to(ROOT.resolve()).as_posix())
        else:
            sys.stdout.buffer.write(payload)
        return 0
    except (AnalysisError, AssertionError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"analysis error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
