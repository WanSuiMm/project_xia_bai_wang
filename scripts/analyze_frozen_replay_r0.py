#!/usr/bin/env python3
"""Offline, fixed-queue analysis for the R0 Frozen replay.

The script reads one run directory containing manifest.json and
responses/<request_id>.json. It makes no provider calls and never reads the
raw response targets referenced by receipts. Missing or invalid responses stay
missing in all fixed-weight summaries.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPECTED_MODELS = ("glm-5.3", "qwen3.8-max")
CONDITIONS = ("blind", "informed")
REPETITIONS = 3
PLANNED_REQUESTS = 84
ORACLE_P_A = 0.5
NULL_MAX_EXCESS_BRIER = 0.25
FAMILY_NAMES = tuple(f"EB{i:02d}" for i in range(1, 7))
EXPECTED_TRANSCRIPT_IDS = (
    "EB01_D1_symmetric_frozen",
    "EB02_D1_symmetric_frozen",
    "EB03_D1_symmetric_frozen",
    "EB04_D1_symmetric_frozen",
    "EB05_D1_symmetric_frozen",
    "EB05_D2_symmetric_frozen",
    "EB06_D1_symmetric_frozen",
)
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
SAFE_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class AnalysisError(Exception):
    """Raised when the frozen manifest is structurally inconsistent."""


def _read_json(path: Path, what: str) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise AnalysisError(f"missing {what}: {path.name}") from None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AnalysisError(f"cannot read {what} {path.name}: {exc}") from None


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise AnalysisError(message)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _family_for_transcript(transcript_id: str) -> str:
    family = transcript_id.split("_", 1)[0]
    _need(family in FAMILY_NAMES, f"transcript_id has unknown family prefix: {transcript_id}")
    return family


def _validate_manifest(manifest: Any) -> tuple[list[dict[str, Any]], dict[str, float], list[str]]:
    _need(isinstance(manifest, dict), "manifest.json must contain a JSON object")
    _need("schema_version" in manifest, "manifest.schema_version is required")
    planned = manifest.get("planned84", manifest.get("planned"))
    _need(planned == PLANNED_REQUESTS, "manifest planned request count must equal 84")
    if "planned84" in manifest and "planned" in manifest:
        _need(manifest["planned84"] == manifest["planned"], "manifest planned fields disagree")
    _need(manifest.get("repetitions") == REPETITIONS, "manifest.repetitions must equal 3")

    models = manifest.get("models")
    _need(
        isinstance(models, list)
        and len(models) == len(EXPECTED_MODELS)
        and all(isinstance(model, str) for model in models)
        and set(models) == set(EXPECTED_MODELS),
        "manifest.models must list exactly glm-5.3 and qwen3.8-max",
    )
    model_order = list(models)

    family_weights = manifest.get("family_weights")
    _need(isinstance(family_weights, dict), "manifest.family_weights must map transcript_id to weight")
    _need(len(family_weights) == 7, "manifest.family_weights must contain the seven frozen transcripts")
    _need(all(isinstance(key, str) for key in family_weights), "family_weights keys must be transcript IDs")
    _need(set(family_weights) == set(EXPECTED_TRANSCRIPT_IDS),
          "family_weights must name exactly the seven IDs in the frozen replay cohort")

    family_sizes: Counter[str] = Counter()
    weights: dict[str, float] = {}
    for transcript_id, value in family_weights.items():
        _need(_is_number(value) and math.isfinite(float(value)), f"invalid family weight for {transcript_id}")
        family = _family_for_transcript(transcript_id)
        family_sizes[family] += 1
        weights[transcript_id] = float(value)

    _need(set(family_sizes) == set(FAMILY_NAMES), "family_weights must cover EB01 through EB06")
    _need(family_sizes == Counter({**{f: 1 for f in FAMILY_NAMES}, "EB05": 2}),
          "family_weights must contain one transcript per family except two for EB05")
    for transcript_id, weight in weights.items():
        family = _family_for_transcript(transcript_id)
        expected_weight = 1.0 / (6 * family_sizes[family])
        _need(
            math.isclose(weight, expected_weight, rel_tol=0.0, abs_tol=1e-12),
            f"family weight for {transcript_id} must be {expected_weight:.12g}",
        )
    _need(math.isclose(sum(weights.values()), 1.0, rel_tol=0.0, abs_tol=1e-12),
          "family_weights must sum to 1")

    requests = manifest.get("requests")
    _need(isinstance(requests, list), "manifest.requests must be an array")
    _need(len(requests) == PLANNED_REQUESTS, "manifest.requests must contain exactly 84 request slots")

    request_ids: set[str] = set()
    cells: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    pair_ids: dict[str, tuple[str, str, int]] = {}
    seen_slots: set[tuple[str, str, str, int]] = set()
    normalized_requests: list[dict[str, Any]] = []

    for index, request in enumerate(requests):
        _need(isinstance(request, dict), f"manifest.requests[{index}] must be an object")
        request_id = request.get("request_id")
        _need(
            isinstance(request_id, str)
            and request_id not in (".", "..")
            and SAFE_REQUEST_ID_RE.fullmatch(request_id) is not None,
            f"manifest.requests[{index}].request_id must be a safe filename token",
        )
        _need(request_id not in request_ids, f"duplicate request_id: {request_id}")
        request_ids.add(request_id)

        transcript_id = request.get("transcript_id")
        _need(isinstance(transcript_id, str) and transcript_id in weights,
              f"request {request_id} has an unknown transcript_id")
        family = _family_for_transcript(transcript_id)

        model = request.get("model")
        _need(model in model_order, f"request {request_id} has an unknown model")
        condition = request.get("condition")
        _need(condition in CONDITIONS, f"request {request_id} has an unknown condition")
        replicate = request.get("replicate")
        _need(isinstance(replicate, int) and not isinstance(replicate, bool)
              and 1 <= replicate <= REPETITIONS, f"request {request_id} has invalid replicate")

        pair_id = request.get("pair_id")
        _need(isinstance(pair_id, str) and pair_id.strip(), f"request {request_id} has invalid pair_id")
        slot_order = request.get("slot_order")
        _need(isinstance(slot_order, int) and not isinstance(slot_order, bool) and slot_order in (1, 2),
              f"request {request_id} has invalid slot_order")
        prompt_hash = request.get("prompt_sha256")
        _need(isinstance(prompt_hash, str) and SHA256_RE.fullmatch(prompt_hash) is not None,
              f"request {request_id} has invalid prompt_sha256")
        max_tokens = request.get("max_tokens")
        _need(isinstance(max_tokens, int) and not isinstance(max_tokens, bool) and max_tokens > 0,
              f"request {request_id} has invalid max_tokens")

        slot_key = (transcript_id, model, condition, replicate)
        _need(slot_key not in seen_slots, f"duplicate transcript/model/condition/replicate slot: {slot_key}")
        seen_slots.add(slot_key)
        cell_key = (transcript_id, model, replicate)
        cells[cell_key].append(request)
        prior_pair = pair_ids.setdefault(pair_id, cell_key)
        _need(prior_pair == cell_key, f"pair_id reused across different cells: {pair_id}")
        normalized_requests.append({
            "request_id": request_id,
            "transcript_id": transcript_id,
            "family": family,
            "model": model,
            "condition": condition,
            "replicate": replicate,
            "pair_id": pair_id,
            "slot_order": slot_order,
            "family_weight": weights[transcript_id],
        })

    expected_slot_count = len(weights) * len(model_order) * len(CONDITIONS) * REPETITIONS
    _need(expected_slot_count == PLANNED_REQUESTS and len(seen_slots) == expected_slot_count,
          "manifest request slots do not cover the full fixed design")
    for transcript_id in weights:
        for model in model_order:
            for replicate in range(1, REPETITIONS + 1):
                pair = cells.get((transcript_id, model, replicate), [])
                _need(len(pair) == 2, f"incomplete Blind/Informed pair: {(transcript_id, model, replicate)}")
                _need({item["condition"] for item in pair} == set(CONDITIONS),
                      f"pair lacks one R0 condition: {(transcript_id, model, replicate)}")
                _need({item["slot_order"] for item in pair} == {1, 2},
                      f"pair slot_order must be 1 and 2: {(transcript_id, model, replicate)}")

    _need(len(pair_ids) == len(weights) * len(model_order) * REPETITIONS,
          "manifest must provide one unique pair_id per transcript/model/replicate")
    return normalized_requests, weights, model_order


def _slug(value: Any) -> str:
    text = str(value).strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return (slug or "unspecified")[:48]


def _has_tool_use(receipt: dict[str, Any]) -> bool:
    for key in ("tool_calls", "tool_call", "tools_used", "tool_used", "tool_use"):
        if key in receipt and receipt[key]:
            return True
    finish_reason = receipt.get("finish_reason")
    return isinstance(finish_reason, str) and "tool" in finish_reason.lower()


def _has_refusal(receipt: dict[str, Any]) -> bool:
    return bool(receipt.get("refusal") or receipt.get("refusal_reason"))


def _classify_receipt(
    path: Path, request: dict[str, Any], dispatch_dir: Path | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        if dispatch_dir is not None and (dispatch_dir / f"{request['request_id']}.json").is_file():
            return None, "dispatched_no_response"
        return None, "not_dispatched"
    try:
        with path.open("r", encoding="utf-8") as handle:
            receipt = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "invalid_receipt_file"
    if not isinstance(receipt, dict):
        return None, "invalid_receipt_schema"
    if receipt.get("request_id") != request["request_id"]:
        return None, "receipt_request_id_mismatch"

    status = receipt.get("status")
    if status != "response_received":
        return None, f"receipt_status_{_slug(status)}"
    if receipt.get("parse_status") != "valid":
        return None, f"parse_status_{_slug(receipt.get('parse_status'))}"

    parsed = receipt.get("parsed")
    if not isinstance(parsed, dict) or set(parsed) != {"p_A", "decision", "reason"}:
        return None, "parsed_schema_invalid"
    p_a = parsed.get("p_A")
    if not _is_number(p_a) or not math.isfinite(float(p_a)) or not 0.0 <= float(p_a) <= 1.0:
        return None, "probability_invalid"
    decision = parsed.get("decision")
    if decision not in ("A", "B", "ABSTAIN"):
        return None, "decision_invalid"
    reason = parsed.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        return None, "reason_empty"
    reason_words = len(reason.split())
    if reason_words > 120:
        return None, "reason_over_120_words"

    visible_text = receipt.get("visible_text")
    if not isinstance(visible_text, str) or not visible_text.strip():
        return None, "visible_text_empty"
    finish_reason = receipt.get("finish_reason")
    if not isinstance(finish_reason, str) or not finish_reason.strip():
        return None, "finish_reason_missing"
    finish_lower = finish_reason.strip().lower()
    if any(marker in finish_lower for marker in ("length", "max_token", "refus", "content_filter")):
        return None, "truncated_or_refusal"
    if _has_refusal(receipt):
        return None, "truncated_or_refusal"
    if _has_tool_use(receipt):
        return None, "tool_use"

    returned_model = receipt.get("returned_model")
    if not isinstance(returned_model, str) or not returned_model.strip():
        return None, "returned_model_missing"
    if returned_model.strip() != request["model"]:
        return None, "returned_model_mismatch"

    return {
        "p_A": float(p_a),
        "decision": decision,
        "reason_word_count": reason_words,
        "returned_model": returned_model.strip(),
        "elapsed_seconds": receipt.get("elapsed_seconds"),
        "finish_reason": finish_reason.strip(),
    }, None


def _minimizing_actions(p_a: float) -> tuple[str, ...]:
    losses = {"A": 1.0 - p_a, "B": p_a, "ABSTAIN": 0.25}
    minimum = min(losses.values())
    # Exact equality preserves both minimizers at p_A == .25 and .75.
    return tuple(action for action, loss in losses.items() if loss == minimum)


def _risk_summary(weighted_values: list[tuple[float, float | None]]) -> dict[str, Any]:
    observed = sum(weight * score for weight, score in weighted_values if score is not None)
    missing_weight = sum(weight for weight, score in weighted_values if score is None)
    missing_count = sum(1 for _, score in weighted_values if score is None)
    lower = observed
    upper = observed + NULL_MAX_EXCESS_BRIER * missing_weight
    complete = missing_count == 0
    return {
        "complete": complete,
        "complete_risk": observed if complete else None,
        "observed_contribution": observed,
        "missing_count": missing_count,
        "missing_totalweight": missing_weight,
        "completion_bounds": [lower, upper],
    }


def _difference_summary(blind: dict[str, Any], informed: dict[str, Any]) -> dict[str, Any]:
    b_lower, b_upper = blind["completion_bounds"]
    i_lower, i_upper = informed["completion_bounds"]
    complete = blind["complete"] and informed["complete"]
    point = blind["complete_risk"] - informed["complete_risk"] if complete else None
    return {
        "definition": "Blind minus Informed",
        "complete": complete,
        "complete_effect": point,
        "observed_contribution_difference": (
            blind["observed_contribution"] - informed["observed_contribution"]
        ),
        "completion_bounds": [b_lower - i_upper, b_upper - i_lower],
    }


def _null_action_metrics(decisions: list[str], incoherent_count: int) -> dict[str, Any]:
    valid_count = len(decisions)
    action_counts = dict(Counter(decisions))
    action_counts = {action: action_counts.get(action, 0) for action in ("A", "B", "ABSTAIN")}
    expected_null_losses = [0.25 if decision == "ABSTAIN" else 0.5 for decision in decisions]
    regrets = [loss - 0.25 for loss in expected_null_losses]
    return {
        "action_counts": action_counts,
        "report_action_incoherent_count": incoherent_count,
        "report_action_incoherent_rate": incoherent_count / valid_count if valid_count else None,
        "mean_expected_null_loss": sum(expected_null_losses) / valid_count if valid_count else None,
        "mean_null_regret": sum(regrets) / valid_count if valid_count else None,
        "null_regret_sum": sum(regrets),
        "null_regret_definition": "E[0/1 choice loss or 0.25 abstain loss | p*=0.5] minus the optimal null loss 0.25",
    }


def _cell_summary(
    transcript_id: str,
    family: str,
    model: str,
    condition: str,
    family_weight: float,
    observations: list[dict[str, Any] | None],
) -> dict[str, Any]:
    valid = [item for item in observations if item is not None]
    scores = [(item["p_A"] - ORACLE_P_A) ** 2 for item in valid]
    risk = _risk_summary([(1.0 / REPETITIONS, score) for score in [
        (item["p_A"] - ORACLE_P_A) ** 2 if item is not None else None for item in observations
    ]])

    unbiased_bias = None
    mean_p = None
    sample_variance = None
    if len(valid) == REPETITIONS:
        probabilities = [item["p_A"] for item in observations if item is not None]
        mean_p = sum(probabilities) / REPETITIONS
        sample_variance = sum((value - mean_p) ** 2 for value in probabilities) / (REPETITIONS - 1)
        unbiased_bias = (mean_p - ORACLE_P_A) ** 2 - sample_variance / REPETITIONS

    return {
        "transcript_id": transcript_id,
        "family": family,
        "model": model,
        "condition": condition,
        "family_weight": family_weight,
        "planned_replicates": REPETITIONS,
        "valid_replicates": len(valid),
        "missing_replicates": REPETITIONS - len(valid),
        "cell_risk": risk,
        "mean_p_A": mean_p,
        "sample_variance_p_A": sample_variance,
        "unbiased_bias_estimate_B": unbiased_bias,
        "B_replicate_count": REPETITIONS if unbiased_bias is not None else None,
    }


def _family_summary(
    family: str,
    family_weight: float,
    n_transcripts: int,
    slots: dict[tuple[str, str], list[float | None]],
) -> dict[str, Any]:
    condition_risks: dict[str, dict[str, Any]] = {}
    for condition in CONDITIONS:
        weighted_values: list[tuple[float, float | None]] = []
        for model_transcript in sorted(key for key in slots if key[0] == condition):
            for score in slots[model_transcript]:
                weighted_values.append((1.0 / (n_transcripts * REPETITIONS), score))
        condition_risks[condition] = _risk_summary(weighted_values)
    effect = _difference_summary(condition_risks["blind"], condition_risks["informed"])
    return {
        "family": family,
        "family_weight": family_weight,
        "transcript_count": n_transcripts,
        "conditions": condition_risks,
        "blind_minus_informed": effect,
    }


def analyze_run(run_dir: Path) -> dict[str, Any]:
    manifest = _read_json(run_dir / "manifest.json", "manifest.json")
    requests, family_weights, model_order = _validate_manifest(manifest)
    responses_dir = run_dir / "responses"

    response_by_id: dict[str, dict[str, Any] | None] = {}
    missing_by_id: dict[str, str] = {}
    for request in requests:
        receipt_path = responses_dir / f"{request['request_id']}.json"
        observation, missing_reason = _classify_receipt(receipt_path, request, run_dir / "dispatches")
        response_by_id[request["request_id"]] = observation
        if missing_reason is not None:
            missing_by_id[request["request_id"]] = missing_reason

    families = sorted({_family_for_transcript(transcript_id) for transcript_id in family_weights})
    family_transcripts = {
        family: sorted(tid for tid in family_weights if _family_for_transcript(tid) == family)
        for family in families
    }
    transcript_to_family = {
        transcript_id: _family_for_transcript(transcript_id) for transcript_id in family_weights
    }

    request_lookup = {
        (request["transcript_id"], request["model"], request["condition"], request["replicate"]): request
        for request in requests
    }
    cells: list[dict[str, Any]] = []
    model_results: dict[str, Any] = {}

    for model in model_order:
        condition_results: dict[str, Any] = {}
        per_condition_slots: dict[str, list[tuple[float, float | None]]] = {c: [] for c in CONDITIONS}
        family_cell_scores: dict[str, dict[tuple[str, str], list[float | None]]] = {
            family: {} for family in families
        }
        action_metrics: dict[str, dict[str, Any]] = {}

        for condition in CONDITIONS:
            decisions: list[str] = []
            incoherent_count = 0
            missing_reasons: Counter[str] = Counter()
            valid_count = 0
            for request in requests:
                if request["model"] != model or request["condition"] != condition:
                    continue
                observation = response_by_id[request["request_id"]]
                if observation is None:
                    missing_reasons[missing_by_id[request["request_id"]]] += 1
                    continue
                valid_count += 1
                decision = observation["decision"]
                decisions.append(decision)
                if decision not in _minimizing_actions(observation["p_A"]):
                    incoherent_count += 1

            risk = _risk_summary(per_condition_slots[condition])
            action = _null_action_metrics(decisions, incoherent_count)
            action_metrics[condition] = action
            condition_results[condition] = {
                "planned_requests": len(family_weights) * REPETITIONS,
                "valid_requests": valid_count,
                "missing_requests": len(family_weights) * REPETITIONS - valid_count,
                "missing_reasons": dict(sorted(missing_reasons.items())),
                "risk": risk,
                "actions": action,
            }

        # Cell- and family-specific scores use the same fixed request slots.
        for transcript_id in sorted(family_weights):
            family = transcript_to_family[transcript_id]
            for condition in CONDITIONS:
                replicate_observations: list[dict[str, Any] | None] = []
                for replicate in range(1, REPETITIONS + 1):
                    request = request_lookup[(transcript_id, model, condition, replicate)]
                    replicate_observations.append(response_by_id[request["request_id"]])
                cell = _cell_summary(
                    transcript_id, family, model, condition, family_weights[transcript_id],
                    replicate_observations,
                )
                cells.append(cell)
                scores_for_family = [
                    (item["p_A"] - ORACLE_P_A) ** 2 if item is not None else None
                    for item in replicate_observations
                ]
                family_cell_scores[family][(condition, transcript_id)] = scores_for_family
                for item, score in zip(replicate_observations, scores_for_family):
                    slot_weight = family_weights[transcript_id] / REPETITIONS
                    per_condition_slots[condition].append((slot_weight, score))

        # Rebuild condition risk now that all family-weighted slots are populated.
        for condition in CONDITIONS:
            risk = _risk_summary(per_condition_slots[condition])
            condition_results[condition]["risk"] = risk

        family_effects: list[dict[str, Any]] = []
        for family in families:
            family_slots = family_cell_scores[family]
            n_transcripts = len(family_transcripts[family])
            family_summary = _family_summary(family, 1.0 / len(families), n_transcripts, family_slots)
            family_effects.append(family_summary)

        delta = _difference_summary(
            condition_results["blind"]["risk"],
            condition_results["informed"]["risk"],
        )
        hoeffding = None
        if delta["complete"]:
            sum_weight_squares = sum(weight * weight for weight in family_weights.values()) / REPETITIONS
            half_width = math.sqrt(sum_weight_squares * math.log(2.0 / 0.05) / 8.0)
            estimate = delta["complete_effect"]
            hoeffding = {
                "level": 0.95,
                "estimate": estimate,
                "half_width": half_width,
                "interval": [estimate - half_width, estimate + half_width],
                "sum_squared_weights": sum_weight_squares,
                "assumptions": [
                    "independent new-session outputs for all Blind and Informed request slots",
                    "stable deployment over the fixed queue and three replicates",
                ],
                "scope": "this fixed transcript queue and deployment only; no population extrapolation or cross-model ranking",
            }

        model_results[model] = {
            "conditions": condition_results,
            "blind_minus_informed": delta,
            "hoeffding_95": hoeffding,
            "family_effects": family_effects,
            "action_summary_by_condition": action_metrics,
        }

    expected_files = {f"{request['request_id']}.json" for request in requests}
    if responses_dir.is_dir():
        actual_json_files = {path.name for path in responses_dir.glob("*.json") if path.is_file()}
        unexpected_receipt_files = sorted(actual_json_files - expected_files)
    else:
        unexpected_receipt_files = []

    return {
        "analysis_schema_version": 1,
        "manifest_schema_version": manifest.get("schema_version"),
        "design": {
            "planned_requests": PLANNED_REQUESTS,
            "repetitions": REPETITIONS,
            "models": model_order,
            "conditions": list(CONDITIONS),
            "transcript_count": len(family_weights),
            "family_weights": family_weights,
            "oracle_p_A": ORACLE_P_A,
            "primary_metric": "family-equal-weight fixed-null excess Brier: sum_j w_j/3 * (p_A - 0.5)^2",
            "effect_definition": "Blind minus Informed",
            "missing_score_range": [0.0, NULL_MAX_EXCESS_BRIER],
        },
        "validity": {
            "required_status": "response_received",
            "required_parse_status": "valid",
            "required_parsed_keys": ["p_A", "decision", "reason"],
            "required_reason_words_max": 120,
            "invalid_or_missing_requests": [
                {
                    "request_id": request["request_id"],
                    "transcript_id": request["transcript_id"],
                    "model": request["model"],
                    "condition": request["condition"],
                    "replicate": request["replicate"],
                    "reason": missing_by_id[request["request_id"]],
                }
                for request in requests
                if request["request_id"] in missing_by_id
            ],
            "unexpected_receipt_file_count": len(unexpected_receipt_files),
            "unexpected_receipt_files": unexpected_receipt_files,
        },
        "models": model_results,
        "transcript_cells": cells,
        "interpretation_limits": [
            "fixed-queue description only; no p-values or population-level inference",
            "models are reported separately; no cross-model ranking is computed",
            "R0 contains no noisy-cue observations",
            "B estimates are defined only for complete three-replicate transcript/model/condition cells and are not truncated at zero",
            "raw response files and visible text are not copied into this analysis output",
        ],
    }


def _fmt(value: Any, digits: int = 6) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}"


def _risk_display(risk: dict[str, Any]) -> str:
    lo, hi = risk["completion_bounds"]
    if risk["complete"]:
        return _fmt(risk["complete_risk"])
    return (
        f"部分贡献 {_fmt(risk['observed_contribution'])}; "
        f"缺失权重 {_fmt(risk['missing_totalweight'])}; "
        f"界 [{_fmt(lo)}, {_fmt(hi)}]"
    )


def _delta_display(delta: dict[str, Any]) -> str:
    lo, hi = delta["completion_bounds"]
    if delta["complete"]:
        return _fmt(delta["complete_effect"])
    return f"部分差 {_fmt(delta['observed_contribution_difference'])}; 界 [{_fmt(lo)}, {_fmt(hi)}]"


def render_results(analysis: dict[str, Any]) -> str:
    lines = [
        "# R0 Frozen replay analysis",
        "",
        "This report summarizes one fixed 7-transcript R0 queue. It is an offline analysis of the receipts present in this run directory; it does not make provider calls.",
        "",
        "## Coverage and primary risk",
        "",
        "The primary metric is family-equal-weight excess Brier risk against the known null $p_A^*=0.5$: $\\sum_j w_j/3\\sum_r(p_{A,jr}-0.5)^2$. Each EB05 transcript has weight 1/12; each other transcript has weight 1/6.",
        "",
        "Missing, invalid, truncated, refusal, tool-use, or undispatched responses remain missing. The report does not renormalize valid responses. For incomplete cells, it shows the observed weighted contribution and the completion range $[obs, obs+0.25\\times missing\\ weight]$.",
        "",
        "| Model | Condition | Planned | Valid | Missing | Fixed-null risk / partial contribution and completion range |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for model, result in analysis["models"].items():
        for condition in CONDITIONS:
            entry = result["conditions"][condition]
            lines.append(
                f"| `{model}` | {condition} | {entry['planned_requests']} | {entry['valid_requests']} | {entry['missing_requests']} | {_risk_display(entry['risk'])} |"
            )

    lines.extend(["", "## Blind minus Informed", "", "Effects are reported separately by model. Incomplete outcomes use the exact completion interval $[B_{lower}-I_{upper}, B_{upper}-I_{lower}]$.", "", "| Model | Complete effect | Observed contribution difference | Completion bounds | 95% fixed-queue Hoeffding interval |", "|---|---:|---:|---:|---|"])
    for model, result in analysis["models"].items():
        effect = result["blind_minus_informed"]
        lo, hi = effect["completion_bounds"]
        h = result["hoeffding_95"]
        h_display = "—"
        if h is not None:
            h_display = f"[{_fmt(h['interval'][0])}, {_fmt(h['interval'][1])}] (half-width {_fmt(h['half_width'], 12)})"
        lines.append(
            f"| `{model}` | {_fmt(effect['complete_effect'])} | {_fmt(effect['observed_contribution_difference'])} | [{_fmt(lo)}, {_fmt(hi)}] | {h_display} |"
        )

    lines.extend(["", "The Hoeffding interval is shown only when every planned Blind and Informed request for that model is valid. It assumes independent new-session outputs and a stable deployment; its scope is this fixed queue. With the registered weights and three repeats, the half-width is 0.153239845434. It does not support population generalization or comparisons between models.", "", "## Per-family effects", "", "Family risks use equal transcript weights within each family and equal replicate weights. Partial families retain their missing-slot weight and show completion ranges.", "", "| Model | Family | Blind risk | Informed risk | Blind − Informed |", "|---|---|---:|---:|---:|"])
    for model, result in analysis["models"].items():
        for family in result["family_effects"]:
            blind = family["conditions"]["blind"]
            informed = family["conditions"]["informed"]
            lines.append(
                f"| `{model}` | {family['family']} | {_risk_display(blind)} | {_risk_display(informed)} | {_delta_display(family['blind_minus_informed'])} |"
            )

    lines.extend(["", "## Transcript cells and repeat-bias estimate", "", "The reported $B=(\\bar p_A-0.5)^2-s^2/3$ uses the unbiased sample variance with denominator 2 and is defined only when all three repeats in that transcript × model × condition cell are valid. Negative values are retained. Partial-cell probability means and $B$ are left undefined.", "", "| Model | Transcript | Family | Condition | Valid / 3 | Cell excess Brier | Mean $p_A$ | Sample variance | $B$ |", "|---|---|---|---|---:|---:|---:|---:|---:|"])
    for cell in analysis["transcript_cells"]:
        risk = cell["cell_risk"]
        lines.append(
            f"| `{cell['model']}` | `{cell['transcript_id']}` | {cell['family']} | {cell['condition']} | {cell['valid_replicates']}/3 | {_risk_display(risk)} | {_fmt(cell['mean_p_A'])} | {_fmt(cell['sample_variance_p_A'])} | {_fmt(cell['unbiased_bias_estimate_B'])} |"
        )

    lines.extend(["", "## Action/report consistency and null regret", "", "Expected null loss uses the fair-target mechanism: choosing A or B has expected loss 0.5; ABSTAIN has loss 0.25. Null regret subtracts the optimal null loss 0.25. Report/action incoherence counts a decision outside the expected-loss minimizers under the reported $p_A$; at exactly 0.25 or 0.75 both boundary minimizers are accepted.", "", "| Model | Condition | A | B | ABSTAIN | Incoherent / valid | Mean expected null loss | Mean null regret |", "|---|---|---:|---:|---:|---:|---:|---:|"])
    for model, result in analysis["models"].items():
        for condition in CONDITIONS:
            actions = result["conditions"][condition]["actions"]
            counts = actions["action_counts"]
            incoherent_rate = actions["report_action_incoherent_rate"]
            incoherent = f"{actions['report_action_incoherent_count']}/{sum(counts.values())}"
            if incoherent_rate is not None:
                incoherent += f" ({_fmt(incoherent_rate)})"
            lines.append(
                f"| `{model}` | {condition} | {counts['A']} | {counts['B']} | {counts['ABSTAIN']} | {incoherent} | {_fmt(actions['mean_expected_null_loss'])} | {_fmt(actions['mean_null_regret'])} |"
            )

    invalid = analysis["validity"]["invalid_or_missing_requests"]
    lines.extend(["", "## Missing and invalid receipts", ""])
    if not invalid:
        lines.append("All 84 planned request slots have valid receipts.")
    else:
        counts = Counter(item["reason"] for item in invalid)
        lines.append("Missing slots by reason: " + ", ".join(f"`{reason}` {count}" for reason, count in sorted(counts.items())) + ".")
        lines.append("")
        lines.append("| Request | Transcript | Model | Condition | Replicate | Reason |")
        lines.append("|---|---|---|---|---:|---|")
        for item in invalid:
            lines.append(
                f"| `{item['request_id']}` | `{item['transcript_id']}` | `{item['model']}` | {item['condition']} | {item['replicate']} | `{item['reason']}` |"
            )

    lines.extend(["", "## Scope", "", "This report contains fixed-queue descriptions only. It reports no p-values or population-level inference, does not rank the two models, and contains no noisy-cue observations. Raw response paths, raw payloads, and visible response text are not copied into the analysis outputs.", ""])
    return "\n".join(lines)


def _write_outputs(run_dir: Path, analysis: dict[str, Any]) -> None:
    outputs = {
        run_dir / "analysis.json": json.dumps(analysis, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        run_dir / "RESULTS.md": render_results(analysis),
    }
    for path, content in outputs.items():
        temporary = path.with_name(path.name + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        temporary.replace(path)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        required=True,
        help="run directory; relative paths are resolved from the repository root",
    )
    args = parser.parse_args(argv)

    requested_path = Path(args.run)
    run_dir = requested_path if requested_path.is_absolute() else _repo_root() / requested_path
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        parser.error(f"run directory does not exist: {run_dir}")
    try:
        analysis = analyze_run(run_dir)
        _write_outputs(run_dir, analysis)
    except AnalysisError as exc:
        print(f"analysis error: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {run_dir / 'analysis.json'} and {run_dir / 'RESULTS.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
