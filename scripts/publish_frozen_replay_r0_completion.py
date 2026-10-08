#!/usr/bin/env python3
"""Publish or audit the additive five-position R0 completion snapshot.

Default mode audits only the published add-on and the prior public cutoff
package.  ``--export`` creates the add-on once, after all five receipts are
present and valid.  No network, model, environment-variable, credential, log,
or process inspection is performed.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "epistemic_boundary_mimicry" / "published_runs" / "go_frozen_replay_r0_20261008"
SOURCE = ROOT / "epistemic_boundary_mimicry" / "runs" / "opencode_go_20261008_frozen_replay_r0_supplement05_low_01"
PARENT = ROOT / "epistemic_boundary_mimicry" / "published_runs"
PUBLIC = PARENT / "go_frozen_replay_r0_completion_20261008"
RUN_NAME = "supplement05_low"
SNAPSHOT_DATE = "2026-10-08"

EXTRA_RECEIPT_FIELDS = frozenset({"reasoning_effort_requested", "changed_configuration_supplement"})
COMPLETION_RECEIPT_FIELDS = frozenset(
    {
        "request_id", "source_request_id", "transcript_id", "model", "condition", "replicate",
        "pair_id", "slot_order", "prompt_sha256", "status", "parse_status", "http_status",
        "finish_reason", "returned_model", "usage", "elapsed_seconds", "visible_text", "parsed",
        "sent_utc", "captured_utc", "error_type", "reasoning_effort_requested",
        "changed_configuration_supplement", "failure_selected_supplement",
    }
)
REQUIRED_RECEIPT_FIELDS = frozenset(
    {
        "request_id", "source_request_id", "transcript_id", "model", "condition", "replicate",
        "pair_id", "slot_order", "prompt_sha256", "status", "parse_status", "finish_reason",
        "returned_model", "usage", "elapsed_seconds", "visible_text", "parsed",
    }
)
FORBIDDEN_KEYS = frozenset(
    {
        "raw_response_path", "session_id_private", "host", "hostname", "pid", "process_id",
        "headers", "request_headers", "response_headers", "account_url", "private_account_url",
        "api_key", "api_token", "authorization", "credential", "credentials", "private_key",
    }
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class PublishError(Exception):
    """A source snapshot or published add-on failed its bounded audit."""


def need(ok: bool, message: str) -> None:
    if not ok:
        raise PublishError(message)


def helpers() -> tuple[Any, Any]:
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        import publish_frozen_replay_r0 as base_tools  # type: ignore[import-not-found]
        analyzer = base_tools._load_analyzer()
    except Exception as exc:
        raise PublishError(f"cannot load local offline tools: {type(exc).__name__}") from None
    return base_tools, analyzer


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PublishError(f"cannot read {label}: {type(exc).__name__}") from None


def forbidden_keys(value: Any, label: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str):
                need(key.lower() not in FORBIDDEN_KEYS, f"private field found in {label}")
            forbidden_keys(child, label)
    elif isinstance(value, list):
        for child in value:
            forbidden_keys(child, label)


def safe_receipt(receipt: Any, label: str) -> dict[str, Any]:
    need(isinstance(receipt, dict), f"{label} must be a JSON object")
    excluded = set(getattr(sys.modules.get("publish_frozen_replay_r0"), "EXCLUDED_RECEIPT_FIELDS", ()))
    unknown = set(receipt) - COMPLETION_RECEIPT_FIELDS - excluded
    need(not unknown, f"{label} has a field outside the publication whitelist")
    need(REQUIRED_RECEIPT_FIELDS.issubset(receipt), f"{label} is missing a required public receipt field")
    result = {key: value for key, value in receipt.items() if key in COMPLETION_RECEIPT_FIELDS}
    forbidden_keys(result, label)
    return result


def public_json(path: Path, payload: Any, base_tools: Any) -> None:
    base_tools._write_json_lf(path, payload)


def public_lf(path: Path, text: str, base_tools: Any) -> None:
    base_tools._write_lf(path, text)


def _read_base(base_tools: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], Any]:
    need(BASE.is_dir(), "the prior 79/84 public cutoff package is missing")
    base_tools._audit_public(BASE)
    manifest = read_json(BASE / "manifest.json", "prior public manifest")
    analysis = read_json(BASE / "analysis.json", "prior public analysis")
    summary = read_json(BASE / "summary.json", "prior public summary")
    supplements = read_json(BASE / "supplemental_status.json", "prior public supplemental ledger")
    need(summary.get("registered_primary_analysis", {}).get("valid_responses") == 77,
         "the registered primary baseline changed from 77 valid responses")
    need(summary.get("supplemental_cutoff", {}).get("distinct_valid_primary_positions_after_first_valid_selection") == 79,
         "the prior public cutoff no longer has 79 distinct valid positions")
    return manifest, analysis, summary, supplements, base_tools._load_analyzer()


def _request_maps(manifest: dict[str, Any], label: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    rows = manifest.get("requests")
    need(isinstance(rows, list), f"{label} has no request list")
    mapped: dict[str, dict[str, Any]] = {}
    for row in rows:
        need(isinstance(row, dict), f"{label} contains a non-object request")
        request_id = row.get("request_id")
        need(isinstance(request_id, str) and SAFE_ID_RE.fullmatch(request_id), f"{label} request id is unsafe")
        need(request_id not in mapped, f"{label} request id is duplicated")
        mapped[request_id] = row
    return rows, mapped


def _validate_source(base_tools: Any, analyzer: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest = read_json(SOURCE / "manifest.json", "five-position manifest")
    status = read_json(SOURCE / "status.json", "five-position source status")
    freeze = read_json(SOURCE / "freeze.json", "five-position freeze")
    need(isinstance(manifest, dict) and isinstance(status, dict) and isinstance(freeze, dict),
         "five-position source metadata is invalid")
    rows, requests = _request_maps(manifest, "five-position source")
    need(manifest.get("planned") == 5 and len(rows) == 5, "five-position manifest must contain exactly five slots")
    need(status.get("planned") == 5 and status.get("provider_requests") == 5,
         "five-position run does not have five recorded dispatches")
    need(status.get("response_count") == 5 and status.get("valid") == 5,
         "five-position run does not have five response receipts marked valid")
    need(status.get("state") == "INTERRUPTED", "source status changed; preserve and review its exact state")

    configuration = manifest.get("configuration", {})
    overrides = manifest.get("request_overrides", {})
    need(isinstance(configuration, dict) and isinstance(overrides, dict), "supplement configuration is invalid")
    need(configuration.get("temperature") == 0.5 and configuration.get("max_tokens") == 32768,
         "supplement temperature or token limit differs from the frozen protocol")
    need(configuration.get("stream") is False and configuration.get("tools") is False,
         "supplement stream/tool settings differ from the frozen protocol")
    need(overrides.get("thinking") == {"type": "enabled"} and overrides.get("reasoning_effort") == "low",
         "supplement reasoning override differs from the frozen request")
    need(manifest.get("proxy_honors_reasoning_setting_verified") is False,
         "proxy reasoning-setting verification boundary changed")

    base_manifest, base_analysis, base_summary, base_supplements, _ = _read_base(base_tools)
    base_requests, base_by_id = _request_maps(base_manifest, "prior public run")
    base_public = {row["request_id"]: row for row in base_requests}
    base_selected = {row["source_request_id"] for row in base_supplements.get("first_valid_per_original_position", [])}
    primary_valid_ids: set[str] = set()
    for request in base_requests:
        valid, _reason = base_tools._receipt_valid(analyzer, BASE, request)
        if valid:
            primary_valid_ids.add(request["request_id"])
    primary_selected = set(primary_valid_ids) | base_selected

    source_positions: set[str] = set()
    for request in rows:
        source_id = request.get("source_request_id")
        need(source_id in base_by_id, "completion request maps outside the original 84 positions")
        need(source_id not in source_positions, "completion supplement repeats an original position")
        need(source_id not in primary_selected, "completion request targets a position already valid at the prior cutoff")
        source_positions.add(source_id)
        primary_request = base_by_id[source_id]
        for key in ("transcript_id", "model", "condition", "replicate", "pair_id", "slot_order"):
            need(request.get(key) == primary_request.get(key), "completion request changes its original position")
        need(request.get("model") == "glm-5.3" and request.get("condition") == "blind",
             "completion supplement must remain within the specified GLM blind condition")
        need(request.get("prompt_sha256") == primary_request.get("prompt_sha256"),
             "completion supplement changes the exact frozen prompt hash")
        prompt_path = base_tools._safe_relpath(primary_request.get("prompt_path"), "base prompt path")
        prompt_file = BASE.joinpath(*prompt_path.parts)
        need(prompt_file.is_file() and base_tools._sha256_file(prompt_file) == request.get("prompt_sha256"),
             "completion prompt does not match one of the original 14 public prompt files")

    base_dispatches = base_tools._dispatch_rows(SOURCE, requests, RUN_NAME)
    need(set(base_dispatches) == set(requests), "five-position source does not contain five unique dispatch records")
    dispatches: dict[str, dict[str, Any]] = {}
    for path in (SOURCE / "dispatches").glob("*.json"):
        if not path.is_file():
            continue
        dispatch = read_json(path, "five-position dispatch record")
        need(isinstance(dispatch, dict), "five-position dispatch record is invalid")
        request_id = dispatch.get("request_id")
        need(request_id in requests and request_id not in dispatches,
             "five-position dispatch mapping is duplicated or unknown")
        need(set(dispatch).issubset({"request_id", "source_request_id", "prompt_sha256", "dispatched_utc", "reasoning_effort_requested"}),
             "five-position dispatch contains a field outside the publication whitelist")
        forbidden_keys(dispatch, "five-position dispatch")
        need(dispatch.get("reasoning_effort_requested") == "low", "five-position dispatch lost the requested low reasoning setting")
        dispatches[request_id] = dispatch
    need(set(dispatches) == set(requests), "five-position source does not contain five unique dispatch records")
    response_dir = SOURCE / "responses"
    response_files = {path.stem: path for path in response_dir.glob("*.json") if path.is_file()}
    need(set(response_files) == set(requests), "five-position source does not contain exactly five response receipts")
    for request_id, request in requests.items():
        dispatch = dispatches[request_id]
        receipt = read_json(response_files[request_id], "five-position response receipt")
        need(dispatch.get("source_request_id") == request.get("source_request_id"), "completion dispatch source mapping mismatch")
        need(dispatch.get("reasoning_effort_requested") == "low", "completion dispatch lost the requested low reasoning setting")
        need(receipt.get("source_request_id") == request.get("source_request_id"), "completion receipt source mapping mismatch")
        need(receipt.get("prompt_sha256") == request.get("prompt_sha256"), "completion receipt prompt hash mismatch")
        need(receipt.get("reasoning_effort_requested") == "low", "completion receipt lost the requested low reasoning setting")
        need(receipt.get("changed_configuration_supplement") is True,
             "completion receipt is missing its changed-configuration label")
        need(receipt.get("status") == "response_received" and receipt.get("parse_status") == "valid",
             "completion receipt is not recorded as a valid received response")
        need(receipt.get("finish_reason") == "stop", "completion receipt has an unexpected finish reason")
        observation, reason = analyzer._classify_receipt(response_files[request_id], request, SOURCE / "dispatches")
        need(observation is not None and reason is None, "a completion receipt is not valid under the unchanged strict parser")

    attestation = read_json(SOURCE / "completion_receipt.json", "root completion receipt")
    need(isinstance(attestation, dict), "root completion receipt is invalid")
    need(attestation.get("derived_completion") == "all_5_response_receipts_valid"
         and attestation.get("source_status") == "INTERRUPTED",
         "root completion receipt does not preserve the interrupted-source boundary")
    need((attestation.get("planned"), attestation.get("dispatch_count"), attestation.get("response_count"),
          attestation.get("valid")) == (5, 5, 5, 5),
         "root completion receipt does not attest five valid responses")
    need(attestation.get("model_requests_in_this_finalize") == 0
         and attestation.get("old_unknown_attempt_preserved") is True,
         "root completion receipt does not preserve the no-resend/unknown-attempt boundary")
    issue = attestation.get("engineering_issue")
    need(isinstance(issue, str) and "final_status_write_failed" in issue and "PermissionError" in issue,
         "root completion receipt does not document the final status-write failure")
    attested_hashes = attestation.get("source_artifact_hashes_lf")
    need(isinstance(attested_hashes, dict) and len(attested_hashes) == 13,
         "root completion receipt does not contain the expected source artifact hashes")
    need(all(isinstance(value, str) and SHA256_RE.fullmatch(value) for value in attested_hashes.values()),
         "root completion receipt contains a malformed source hash")
    expected_hashes = [
        base_tools._sha256_file(SOURCE / "manifest.json"),
        base_tools._sha256_file(SOURCE / "status.json"),
        base_tools._sha256_file(SOURCE / "freeze.json"),
        *(base_tools._sha256_file(SOURCE / "dispatches" / f"{request_id}.json") for request_id in requests),
        *(base_tools._sha256_file(response_files[request_id]) for request_id in requests),
    ]
    need(sorted(attested_hashes.values()) == sorted(expected_hashes),
         "root completion receipt hashes do not match the frozen source artifacts")
    frozen = base_tools._freeze_hashes(SOURCE, freeze, RUN_NAME)
    need("manifest.json" in frozen and len([k for k in frozen if k.startswith("prompts/")]) == 5,
         "completion freeze does not cover its manifest and five prompt files")
    return manifest, status, freeze, {"requests": requests, "dispatches": dispatches, "responses": response_files, "frozen": frozen}


def _configuration_view(manifest: dict[str, Any]) -> dict[str, Any]:
    if "configuration_delta" in manifest:
        return manifest["configuration_delta"]
    config = manifest["configuration"]
    override = manifest["request_overrides"]
    return {
        "model": "glm-5.3",
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
        "stream": config["stream"],
        "tools": config["tools"],
        "thinking": override["thinking"],
        "reasoning_effort": override["reasoning_effort"],
        "prompt_bytes_unchanged": True,
        "strict_original_parser_unchanged": True,
        "proxy_honors_reasoning_setting_verified": False,
        "interpretation": "changed-configuration engineering supplement; no controlled reasoning-effort effect is identified",
    }


def _public_manifest(manifest: dict[str, Any], base_manifest: dict[str, Any]) -> dict[str, Any]:
    _, base_by_id = _request_maps(base_manifest, "base public run")
    requests: list[dict[str, Any]] = []
    for row in manifest["requests"]:
        original = base_by_id[row["source_request_id"]]
        requests.append(
            {
                "request_id": row["request_id"],
                "source_request_id": row["source_request_id"],
                "transcript_id": row["transcript_id"],
                "model": row["model"],
                "condition": row["condition"],
                "replicate": row["replicate"],
                "pair_id": row["pair_id"],
                "slot_order": row["slot_order"],
                "prompt_sha256": row["prompt_sha256"],
                "base_prompt_path": "../go_frozen_replay_r0_20261008/" + original["prompt_path"].replace("\\", "/"),
                "max_tokens": row["max_tokens"],
                "reasoning_effort_requested": row["reasoning_effort_requested"],
            }
        )
    return {
        "schema_version": 1,
        "label": RUN_NAME,
        "source_status": "INTERRUPTED",
        "derived_completion": "all_5_response_receipts_valid",
        "configuration_delta": _configuration_view(manifest),
        "request_count": 5,
        "requests": requests,
    }


def _select_and_score(base_tools: Any, analyzer: Any, public_dir: Path, completion_manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    base_manifest = read_json(BASE / "manifest.json", "base manifest")
    base_analysis = read_json(BASE / "analysis.json", "base analysis")
    prior_status = read_json(BASE / "supplemental_status.json", "base supplemental status")
    primary_requests, primary_by_id = _request_maps(base_manifest, "base public run")
    current_requests, current_by_id = _request_maps(completion_manifest, "completion public run")
    new_receipts: dict[str, dict[str, Any]] = {}
    for request_id in current_by_id:
        new_receipts[request_id] = read_json(public_dir / "responses" / f"{request_id}.json", "public completion receipt")

    primary_valid: dict[str, dict[str, Any]] = {}
    for request in primary_requests:
        valid, _reason = base_tools._receipt_valid(analyzer, BASE, request)
        if valid:
            primary_valid[request["request_id"]] = {
                "source": "primary",
                "request_id": request["request_id"],
                "receipt_path": "../go_frozen_replay_r0_20261008/responses/" + request["request_id"] + ".json",
            }

    old_selected: dict[str, dict[str, Any]] = {}
    for item in prior_status.get("first_valid_per_original_position", []):
        source_id = item["source_request_id"]
        if source_id in primary_valid:
            continue
        old_selected[source_id] = {
            "source": item["selected_supplement"],
            "request_id": item["selected_request_id"],
            "receipt_path": "../go_frozen_replay_r0_20261008/supplements/"
            + item["selected_supplement"]
            + "/responses/"
            + item["selected_request_id"]
            + ".json",
        }

    new_selected: dict[str, dict[str, Any]] = {}
    for request_id, request in current_by_id.items():
        source_id = request["source_request_id"]
        if source_id in primary_valid or source_id in old_selected:
            continue
        receipt_path = public_dir / "responses" / f"{request_id}.json"
        observation, _reason = analyzer._classify_receipt(receipt_path, request, public_dir / "dispatches")
        if observation is not None:
            new_selected[source_id] = {
                "source": RUN_NAME,
                "request_id": request_id,
                "receipt_path": "responses/" + request_id + ".json",
            }

    selected: dict[str, dict[str, Any]] = {}
    for request_id in primary_by_id:
        if request_id in primary_valid:
            selected[request_id] = primary_valid[request_id]
        elif request_id in old_selected:
            selected[request_id] = old_selected[request_id]
        elif request_id in new_selected:
            selected[request_id] = new_selected[request_id]

    selection_rows = []
    for source_id, request in primary_by_id.items():
        item = selected.get(source_id)
        receipt = None
        if item is not None:
            receipt_path = public_dir / item["receipt_path"] if item["source"] == RUN_NAME else BASE / item["receipt_path"].replace("../go_frozen_replay_r0_20261008/", "")
            if item["source"] != RUN_NAME:
                receipt_path = BASE / item["receipt_path"].split("go_frozen_replay_r0_20261008/", 1)[1]
            receipt = read_json(receipt_path, "selected valid receipt")
        selection_rows.append(
            {
                "source_request_id": source_id,
                "valid_after_selection": item is not None,
                "selected_from": item["source"] if item else None,
                "selected_request_id": item["request_id"] if item else None,
                "receipt_path": item["receipt_path"] if item else None,
                "p_A": receipt.get("parsed", {}).get("p_A") if isinstance(receipt, dict) else None,
                "decision": receipt.get("parsed", {}).get("decision") if isinstance(receipt, dict) else None,
            }
        )

    weights = base_analysis["design"]["family_weights"]
    blind_requests = [q for q in primary_requests if q["model"] == "glm-5.3" and q["condition"] == "blind"]
    probabilities: list[float] = []
    decisions: Counter[str] = Counter()
    observed = 0.0
    valid_weight = 0.0
    coherent = 0
    primary_count = 0
    prior_supplement_count = 0
    new_count = 0
    for request in blind_requests:
        source_id = request["request_id"]
        item = selected.get(source_id)
        if item is None:
            continue
        if item["source"] == "primary":
            primary_count += 1
        elif item["source"] == RUN_NAME:
            new_count += 1
        else:
            prior_supplement_count += 1
        if item["source"] == RUN_NAME:
            receipt = new_receipts[item["request_id"]]
        else:
            rel = item["receipt_path"].split("go_frozen_replay_r0_20261008/", 1)[1]
            receipt = read_json(BASE / rel, "selected base receipt")
        parsed = receipt.get("parsed")
        need(isinstance(parsed, dict), "selected receipt is missing its strict parsed object")
        p_a = float(parsed["p_A"])
        decision = parsed["decision"]
        probabilities.append(p_a)
        decisions[str(decision)] += 1
        slot_weight = float(weights[request["transcript_id"]]) / 3.0
        valid_weight += slot_weight
        observed += slot_weight * (p_a - 0.5) ** 2
        coherent += int(decision in analyzer._minimizing_actions(p_a))

    planned = len(blind_requests)
    missing = planned - len(probabilities)
    missing_weight = max(0.0, 1.0 - valid_weight)
    complete = len(probabilities) == planned
    risk = {
        "complete": complete,
        "primary_metric": "family-equal-weight fixed-null excess Brier",
        "observed_contribution": round(observed, 12),
        "missing_slot_weight": round(missing_weight, 12),
        "completion_bounds": [round(observed, 12), round(observed + 0.25 * missing_weight, 12)],
        "risk": round(observed, 12) if complete else None,
    }
    probability_summary = {
        "n": len(probabilities),
        "mean": round(sum(probabilities) / len(probabilities), 12) if probabilities else None,
        "family_weighted_mean": round(sum(
            float(weights[q["transcript_id"]]) / 3.0
            * float((read_json(BASE / selected[q["request_id"]]["receipt_path"].split("go_frozen_replay_r0_20261008/", 1)[1], "selected base receipt")
                     if selected[q["request_id"]]["source"] != RUN_NAME
                     else new_receipts[selected[q["request_id"]]["request_id"]])["parsed"]["p_A"])
            for q in blind_requests if q["request_id"] in selected
        ) / valid_weight, 12) if probabilities and valid_weight else None,
        "minimum": min(probabilities) if probabilities else None,
        "maximum": max(probabilities) if probabilities else None,
        "exactly_half_count": sum(p == 0.5 for p in probabilities),
    }
    overlay = {
        "condition": "GLM-5.3 blind",
        "scope": "first-valid overlay; primary then supplement07 then supplement06 then supplement05_low",
        "planned_positions": planned,
        "valid_positions": len(probabilities),
        "missing_positions": missing,
        "selected_from": {
            "primary": primary_count,
            "prior_supplements": prior_supplement_count,
            "supplement05_low": new_count,
        },
        "risk_summary": risk,
        "probability_summary": probability_summary,
        "probability_counts": dict(sorted(Counter(str(value) for value in probabilities).items())),
        "action_counts": dict(sorted(decisions.items())),
        "coherent_actions": coherent,
        "incoherent_actions": len(probabilities) - coherent,
    }
    return {"schema_version": 1, "selection_order": ["primary", "supplement07", "supplement06", RUN_NAME], "positions": selection_rows}, {
        "schema_version": 1,
        "snapshot_date": SNAPSHOT_DATE,
        "registered_primary_analysis": {
            "planned": 84,
            "valid": 77,
            "state": "ALL_84_ATTEMPTED",
            "unchanged": True,
            "analysis_path": "../go_frozen_replay_r0_20261008/analysis.json",
            "summary_path": "../go_frozen_replay_r0_20261008/summary.json",
        },
        "completion_supplement": {
            "planned": 5,
            "dispatches": 5,
            "response_receipts": 5,
            "valid_response_receipts": 5,
            "source_status": "INTERRUPTED",
            "derived_status": "all_5_response_receipts_valid",
            "final_status_write_failed": True,
            "status_failure_class": "PermissionError",
            "root_verified_process_alive": False,
            "position_results": {},
        },
        "distinct_position_overlay": {
            "primary_valid_positions": 77,
            "prior_supplement_valid_positions": 2,
            "new_supplement_valid_positions": 5,
            "distinct_valid_positions": sum(1 for row in selection_rows if row["valid_after_selection"]),
            "remaining_positions_without_valid_response": sum(1 for row in selection_rows if not row["valid_after_selection"]),
            "selection_rule": "First valid response per original position in order: primary, supplement07, supplement06, supplement05_low. Earlier dispatched requests without responses remain separate unknown attempts.",
        },
        "glm_blind_first_valid_overlay": overlay,
        "configuration_boundary": _configuration_view(completion_manifest),
        "notes": [
            "The 84-position registered primary run remains 77/84; 84/84 refers only to distinct positions with a valid answer after additive supplements.",
            "Low reasoning is a changed-configuration engineering supplement. The proxy's compliance with the requested reasoning setting was not independently verified.",
            "No causal or controlled reasoning-effort effect is identified; hidden reasoning is not stored.",
        ],
    }


def _source_receipt_summary(run: Path, requests: dict[str, dict[str, Any]], responses: dict[str, Path]) -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    parse_counts: Counter[str] = Counter()
    finish_counts: Counter[str] = Counter()
    returned_models: Counter[str] = Counter()
    decisions: Counter[str] = Counter()
    probabilities: Counter[str] = Counter()
    completion_tokens = 0
    for request_id, path in responses.items():
        receipt = read_json(path, "completion response")
        status_counts[str(receipt.get("status"))] += 1
        parse_counts[str(receipt.get("parse_status"))] += 1
        finish_counts[str(receipt.get("finish_reason"))] += 1
        returned_models[str(receipt.get("returned_model"))] += 1
        parsed = receipt.get("parsed")
        if isinstance(parsed, dict):
            decisions[str(parsed.get("decision"))] += 1
            probabilities[str(parsed.get("p_A"))] += 1
        usage = receipt.get("usage")
        if isinstance(usage, dict) and isinstance(usage.get("completion_tokens"), int):
            completion_tokens += usage["completion_tokens"]
    return {
        "receipt_status_counts": dict(sorted(status_counts.items())),
        "parse_status_counts": dict(sorted(parse_counts.items())),
        "finish_reason_counts": dict(sorted(finish_counts.items())),
        "returned_model_counts": dict(sorted(returned_models.items())),
        "parsed_decision_counts": dict(sorted(decisions.items())),
        "parsed_probability_counts": dict(sorted(probabilities.items())),
        "reported_completion_tokens": completion_tokens,
    }


def _provenance(base_tools: Any, manifest_path: Path, status_path: Path, freeze: dict[str, Any], freeze_path: Path,
                dispatches: dict[str, dict[str, Any]], receipts: dict[str, Path]) -> dict[str, Any]:
    frozen_hashes = base_tools._freeze_hashes(SOURCE, freeze, RUN_NAME)
    prior = freeze.get("prior_artifact_hashes", {})
    need(isinstance(prior, dict), "completion prior-artifact hashes are malformed")
    prior_json = json.dumps(prior, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    completion_attestation = SOURCE / "completion_receipt.json"
    return {
        "schema_version": 1,
        "snapshot_date": SNAPSHOT_DATE,
        "source_label": RUN_NAME,
        "source_manifest_sha256lf": base_tools._sha256_file(manifest_path),
        "source_status_sha256lf": base_tools._sha256_file(status_path),
        "source_freeze_sha256lf": base_tools._sha256_file(freeze_path),
        "frozen_content_hashes": frozen_hashes,
        "protocol_sha256": freeze.get("protocol_sha256"),
        "runner_sha256": freeze.get("runner_sha256"),
        "prior_artifact_hash_manifest_sha256lf": base_tools._sha256_bytes(prior_json.encode("utf-8")),
        "prior_artifact_group_count": len(prior),
        "source_dispatch_hashes_sha256lf": {
            request_id: base_tools._sha256_file(SOURCE / "dispatches" / f"{request_id}.json") for request_id in sorted(dispatches)
        },
        "source_response_hashes_sha256lf": {
            request_id: base_tools._sha256_file(path) for request_id, path in sorted(receipts.items())
        },
        "root_completion_receipt_sha256lf": base_tools._sha256_file(completion_attestation) if completion_attestation.is_file() else None,
        "public_source_paths_included": False,
        "credential_or_environment_reads": 0,
        "network_or_model_calls": 0,
    }


def _readme() -> str:
    return """# R0 five-position low-reasoning completion supplement

This is an additive, changed-configuration engineering supplement to the [79/84 cutoff snapshot](../go_frozen_replay_r0_20261008/summary.json). It preserves that snapshot's registered analysis and exact primary receipts. The five requests reused the original prompts, temperature, model, token limit, strict parser, and 120-word reason cap; they requested `thinking.type=enabled` and `reasoning_effort=low`. The proxy's handling of that request was not independently verified, so this does not identify a controlled reasoning-effort effect.

The source status remains `INTERRUPTED` because its final status update failed. This package records the derived state separately: all five dispatches have valid response receipts. The new replies are five `ABSTAIN` decisions at p_A=0.5. A first-valid-per-position overlay covers 84/84 distinct positions, with GLM-5.3 blind at 21/21. That overlay does not mean the registered primary run completed successfully; its original result remains 77/84. Any earlier dispatched request without a receipt stays an unknown historical attempt and is not replaced by the new reply.

## Reading route

1. [Prior cutoff summary](../go_frozen_replay_r0_20261008/summary.json) and [unchanged primary analysis](../go_frozen_replay_r0_20261008/analysis.json).
2. [Completion summary and GLM blind overlay](summary.json).
3. [Per-position first-valid selection](selection.json) and [five-request configuration/prompt mapping](completion_manifest.json).
4. [Five allowlisted dispatches](dispatches/) and [five exact visible-response receipts](responses/).
5. [Sanitized completion/status provenance](completion_status.json) and [source hashes](provenance.json).

From the repository root, `python -X utf8 -B scripts/publish_frozen_replay_r0_completion.py` audits this package. The script uses only Python's standard library and local frozen public records; it makes no network/model calls and does not require the private source run. `SHA256SUMS.txt` contains SHA-256LF hashes for every published file except itself.
"""


def _write_hashes(root: Path, base_tools: Any) -> None:
    base_tools._write_content_hashes(root)


def _export_to(stage: Path, base_tools: Any, analyzer: Any) -> dict[str, Any]:
    base_manifest, _base_analysis, base_summary, _prior_supplements, _ = _read_base(base_tools)
    manifest, status, freeze, source_rows = _validate_source(base_tools, analyzer)
    public_manifest = _public_manifest(manifest, base_manifest)
    request_rows = source_rows["requests"]
    dispatches = source_rows["dispatches"]
    response_paths = source_rows["responses"]

    for request_id, dispatch in dispatches.items():
        dispatch_public = {
            key: dispatch[key]
            for key in ("request_id", "source_request_id", "prompt_sha256", "dispatched_utc", "reasoning_effort_requested")
            if key in dispatch
        }
        base_tools._write_json_lf(stage / "dispatches" / f"{request_id}.json", dispatch_public)
        receipt = read_json(response_paths[request_id], "completion source receipt")
        base_tools._write_json_lf(stage / "responses" / f"{request_id}.json", safe_receipt(receipt, "completion source receipt"))

    completion_status = {
        "schema_version": 1,
        "source_status": status["state"],
        "planned": status["planned"],
        "provider_requests": status["provider_requests"],
        "response_count": status["response_count"],
        "valid_count_in_source_status": status["valid"],
        "derived_completion": "all_5_response_receipts_valid",
        "final_status_write_failed": True,
        "status_write_failure_class": "PermissionError",
        "root_verified_process_alive": False,
        "process_state_basis": "root-verified operating-system snapshot; process identifier omitted",
        "source_status_file_unchanged": True,
    }
    public_json(stage / "completion_manifest.json", public_manifest, base_tools)
    public_json(stage / "completion_status.json", completion_status, base_tools)
    provenance = _provenance(base_tools, SOURCE / "manifest.json", SOURCE / "status.json", freeze,
                             SOURCE / "freeze.json", dispatches, response_paths)
    public_json(stage / "provenance.json", provenance, base_tools)
    selection, summary = _select_and_score(base_tools, analyzer, stage, public_manifest)
    receipt_stats = _source_receipt_summary(SOURCE, request_rows, response_paths)
    summary["completion_supplement"]["position_results"] = receipt_stats
    base_valid_count = base_summary["registered_primary_analysis"]["valid_responses"]
    prior_valid = base_summary["supplemental_cutoff"]["distinct_valid_primary_positions_after_first_valid_selection"] - base_valid_count
    summary["distinct_position_overlay"]["prior_supplement_valid_positions"] = prior_valid
    summary["distinct_position_overlay"]["new_supplement_valid_positions"] = sum(
        1 for row in selection["positions"] if row["selected_from"] == RUN_NAME
    )
    public_json(stage / "selection.json", selection, base_tools)
    public_json(stage / "summary.json", summary, base_tools)
    base_tools._write_lf(stage / "README.md", _readme())
    _write_hashes(stage, base_tools)
    return _audit(stage, base_tools, analyzer)


def _audit(root: Path, base_tools: Any, analyzer: Any) -> dict[str, Any]:
    base_manifest, _base_analysis, base_summary, _prior_status, _ = _read_base(base_tools)
    file_count = base_tools._audit_content_hashes(root)
    manifest = read_json(root / "completion_manifest.json", "public completion manifest")
    status = read_json(root / "completion_status.json", "public completion status")
    provenance = read_json(root / "provenance.json", "public completion provenance")
    selection = read_json(root / "selection.json", "public position selection")
    summary = read_json(root / "summary.json", "public completion summary")
    for label, obj in (("completion manifest", manifest), ("completion status", status),
                       ("completion provenance", provenance), ("position selection", selection),
                       ("completion summary", summary)):
        forbidden_keys(obj, label)

    rows, requests = _request_maps(manifest, "public completion manifest")
    need(len(rows) == 5 and manifest.get("request_count") == 5, "public completion manifest must contain five requests")
    need(status.get("source_status") == "INTERRUPTED", "public package must preserve the raw interrupted source status")
    need(status.get("derived_completion") == "all_5_response_receipts_valid", "public derived completion state is missing")
    need(status.get("final_status_write_failed") is True, "public package omitted the failed final status-write boundary")
    need(status.get("root_verified_process_alive") is False, "public package omitted the root process-state snapshot")
    need(provenance.get("public_source_paths_included") is False, "public provenance includes private source locations")
    expected_delta = {
        "model": "glm-5.3",
        "temperature": 0.5,
        "max_tokens": 32768,
        "stream": False,
        "tools": False,
        "thinking": {"type": "enabled"},
        "reasoning_effort": "low",
        "prompt_bytes_unchanged": True,
        "strict_original_parser_unchanged": True,
        "proxy_honors_reasoning_setting_verified": False,
        "interpretation": "changed-configuration engineering supplement; no controlled reasoning-effort effect is identified",
    }
    need(manifest.get("configuration_delta") == expected_delta,
         "public completion package changed its declared configuration boundary")

    base_requests, base_by_id = _request_maps(base_manifest, "base public run")
    prompt_files = {}
    for path in (BASE / "prompts").rglob("*"):
        if path.is_file():
            prompt_files[path.relative_to(BASE).as_posix()] = base_tools._sha256_file(path)
    response_names = {path.name for path in (root / "responses").glob("*.json") if path.is_file()}
    dispatch_names = {path.name for path in (root / "dispatches").glob("*.json") if path.is_file()}
    expected_names = {request_id + ".json" for request_id in requests}
    need(response_names == expected_names and dispatch_names == expected_names,
         "public completion package must preserve exactly five receipts and five dispatches")

    for request_id, request in requests.items():
        source_id = request.get("source_request_id")
        need(source_id in base_by_id, "public completion request maps outside the original 84 slots")
        original = base_by_id[source_id]
        need(request.get("model") == original.get("model") == "glm-5.3", "public completion model changed")
        need(request.get("condition") == original.get("condition") == "blind", "public completion condition changed")
        need(request.get("prompt_sha256") == original.get("prompt_sha256"), "public completion prompt hash changed")
        need(request.get("max_tokens") == 32768 and request.get("reasoning_effort_requested") == "low",
             "public completion request configuration changed")
        prompt_path = original["prompt_path"]
        need(prompt_files.get(prompt_path) == request.get("prompt_sha256"), "public completion prompt is not one of the exact 14 base prompts")
        dispatch = read_json(root / "dispatches" / f"{request_id}.json", "public completion dispatch")
        need(dispatch.get("request_id") == request_id and dispatch.get("source_request_id") == source_id,
             "public completion dispatch mapping mismatch")
        need(dispatch.get("prompt_sha256") == request.get("prompt_sha256"), "public completion dispatch hash mismatch")
        need(dispatch.get("reasoning_effort_requested") == "low", "public completion dispatch lost the low-reasoning request")
        receipt = read_json(root / "responses" / f"{request_id}.json", "public completion receipt")
        need(set(receipt).issubset(COMPLETION_RECEIPT_FIELDS), "public completion receipt contains a non-whitelisted field")
        need(receipt.get("request_id") == request_id and receipt.get("source_request_id") == source_id,
             "public completion response mapping mismatch")
        need(receipt.get("prompt_sha256") == request.get("prompt_sha256"), "public completion response prompt hash mismatch")
        need(receipt.get("status") == "response_received" and receipt.get("parse_status") == "valid"
             and receipt.get("finish_reason") == "stop" and receipt.get("reasoning_effort_requested") == "low"
             and receipt.get("changed_configuration_supplement") is True,
             "public completion response status/configuration boundary changed")
        observation, reason = analyzer._classify_receipt(root / "responses" / f"{request_id}.json", request, root / "dispatches")
        need(observation is not None and reason is None, "public completion response is not valid under the original strict parser")

    recomputed_selection, recomputed_summary = _select_and_score(base_tools, analyzer, root, manifest)
    need(selection == recomputed_selection, "public first-valid selection does not reproduce from the public records")
    public_receipts = {request_id: read_json(root / "responses" / f"{request_id}.json", "public completion receipt")
                       for request_id in requests}
    stats = _source_receipt_summary(root, requests, {request_id: root / "responses" / f"{request_id}.json" for request_id in requests})
    recomputed_summary["completion_supplement"]["position_results"] = stats
    base_valid_count = base_summary["registered_primary_analysis"]["valid_responses"]
    prior_valid = base_summary["supplemental_cutoff"]["distinct_valid_primary_positions_after_first_valid_selection"] - base_valid_count
    recomputed_summary["distinct_position_overlay"]["prior_supplement_valid_positions"] = prior_valid
    recomputed_summary["distinct_position_overlay"]["new_supplement_valid_positions"] = sum(
        1 for row in selection["positions"] if row["selected_from"] == RUN_NAME
    )
    need(summary == recomputed_summary, "public completion summary does not reproduce from the public records")
    need(summary["registered_primary_analysis"]["valid"] == 77 and summary["registered_primary_analysis"]["unchanged"] is True,
         "public completion package changed the registered primary result")
    need(summary["distinct_position_overlay"]["distinct_valid_positions"] == 84
         and summary["distinct_position_overlay"]["remaining_positions_without_valid_response"] == 0,
         "public completion package does not cover the expected 84 distinct positions")
    overlay = summary["glm_blind_first_valid_overlay"]
    need(overlay["planned_positions"] == 21 and overlay["valid_positions"] == 21 and overlay["risk_summary"]["complete"] is True,
         "public GLM blind overlay is not a complete 21-position conditional view")
    need(overlay["risk_summary"]["risk"] == 0.011041666667
         and overlay["risk_summary"]["completion_bounds"] == [0.011041666667, 0.011041666667],
         "public GLM blind overlay risk does not match the complete first-valid calculation")
    need(overlay["action_counts"] == {"A": 1, "ABSTAIN": 17, "B": 3}
         and overlay["probability_summary"]["n"] == 21
         and overlay["probability_summary"]["exactly_half_count"] == 16
         and overlay["probability_counts"] == {"0.15": 1, "0.2": 2, "0.5": 16, "0.55": 1, "0.8": 1},
         "public GLM blind overlay response counts do not match the selected receipts")
    need(summary["completion_supplement"]["position_results"]["reported_completion_tokens"] == 1246,
         "public completion token total does not match the five receipts")
    return {"hashed_files": file_count, "primary_valid": 77, "new_valid": 5,
            "distinct_positions": summary["distinct_position_overlay"]["distinct_valid_positions"],
            "glm_blind_risk": overlay["risk_summary"]["risk"]}


def _export_once(base_tools: Any, analyzer: Any) -> dict[str, Any]:
    need(not PUBLIC.exists(), "completion export already exists; --export never overwrites")
    need(PARENT.is_dir(), "published_runs directory is missing")
    stage = Path(tempfile.mkdtemp(prefix=".go_frozen_replay_r0_completion_20261008-", dir=PARENT))
    try:
        result = _export_to(stage, base_tools, analyzer)
        need(not PUBLIC.exists(), "completion export appeared during creation; refusing to replace it")
        stage.rename(PUBLIC)
    except Exception:
        need(stage.resolve().parent == PARENT.resolve() and stage.name.startswith(".go_frozen_replay_r0_completion_20261008-"),
             "temporary export path failed its cleanup boundary check")
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", action="store_true", help="create the completion add-on once; refuse overwrite")
    parser.add_argument("--audit", action="store_true", help="audit the existing public add-on (default)")
    args = parser.parse_args(argv)
    if args.export and args.audit:
        parser.error("choose either --export or --audit")
    try:
        base_tools, analyzer = helpers()
        if args.export:
            result = _export_once(base_tools, analyzer)
            print("EXPORT_OK completion add-on created; "
                  f"hashed_files={result['hashed_files']} primary_valid=77/84 "
                  f"new_valid={result['new_valid']} distinct_positions={result['distinct_positions']} "
                  f"glm_blind_risk={result['glm_blind_risk']}")
        else:
            need(PUBLIC.is_dir(), "completion public directory is missing; use --export once after source completion")
            result = _audit(PUBLIC, base_tools, analyzer)
            print("AUDIT_OK completion add-on verified; "
                  f"hashed_files={result['hashed_files']} primary_valid=77/84 "
                  f"new_valid={result['new_valid']} distinct_positions={result['distinct_positions']} "
                  f"glm_blind_risk={result['glm_blind_risk']}")
    except PublishError as exc:
        print(f"publication error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"publication error: {type(exc).__name__}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
