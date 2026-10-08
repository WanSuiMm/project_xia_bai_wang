"""Offline strict analysis for the frozen 16-call opponent-model replay."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "epistemic_boundary_mimicry"
DEFAULT_RUN = BASE / "runs/opencode_go_20261008_opponent_model16_02"
SOURCE = BASE / "published_runs/go_strategic_qualification28_20261008"
CODING = BASE / "strategic_qualification/analysis_20261008/answer_coding.json"
CASES = tuple(f"SQ{i:02d}" for i in range(1, 5))
ARMS, REPEATS = ("B0", "B1"), (1, 2)
QUESTIONS = tuple(f"Q{i}" for i in range(1, 7))
VALID_FINISHES = {"stop", "end_turn", "stop_sequence"}
TRUNCATED_FINISHES = {"length", "max_tokens", "token_limit"}
CODING_SHA = "686f33feae2078acfe8f01ff74cbfe825d1957f814ab98e9f455ff6a6e53bddb"
SOURCE_REL = Path("epistemic_boundary_mimicry/published_runs/go_strategic_qualification28_20261008")


class AuditError(RuntimeError):
    pass


def sha(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"Cannot read {path.name}: {exc}") from exc


def safe(root, relative):
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise AuditError(f"Frozen path escapes its root: {relative}") from exc
    return path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def words(text):
    return len(re.findall(r"[\w]+(?:[’'-][\w]+)*", text, flags=re.UNICODE))


def parse_forecast(text, finish):
    if finish not in VALID_FINISHES:
        return None, "truncated" if finish in TRUNCATED_FINISHES else "invalid_forecast"
    try:
        value = json.loads(text, object_pairs_hook=unique_object)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None, "invalid_forecast"
    if not isinstance(value, dict) or set(value) != {"predictions", "reason"}:
        return None, "invalid_forecast"
    predictions = value["predictions"]
    if not isinstance(predictions, list) or len(predictions) != 6:
        return None, "invalid_forecast"
    clean = []
    for expected, row in zip(QUESTIONS, predictions):
        if not isinstance(row, dict) or set(row) != {"question_id", "p_explicit_source_silence"}:
            return None, "invalid_forecast"
        p = row["p_explicit_source_silence"]
        if row["question_id"] != expected or isinstance(p, bool) or not isinstance(p, (int, float)):
            return None, "invalid_forecast"
        if not math.isfinite(p) or not 0 <= p <= 1:
            return None, "invalid_forecast"
        clean.append({"question_id": expected, "p_explicit_source_silence": float(p)})
    reason = value["reason"]
    if not isinstance(reason, str) or not reason.strip() or words(reason) > 100:
        return None, "invalid_forecast"
    return {"predictions": clean, "reason": reason}, "valid"


def parse_speaker(text, finish):
    if finish not in VALID_FINISHES:
        raise AuditError("Frozen SQ28 target has a non-complete finish reason.")
    try:
        value = json.loads(text, object_pairs_hook=unique_object)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AuditError("Frozen SQ28 target is not strict JSON.") from exc
    if not isinstance(value, dict) or set(value) != {"answers"} or not isinstance(value["answers"], list) or len(value["answers"]) != 6:
        raise AuditError("Frozen SQ28 target does not have six answers.")
    answers = {}
    for expected, row in zip(QUESTIONS, value["answers"]):
        if not isinstance(row, dict) or set(row) != {"question_id", "answer"} or row["question_id"] != expected:
            raise AuditError("Frozen SQ28 target has an invalid question sequence.")
        answer = row["answer"]
        if not isinstance(answer, str) or not answer.strip() or words(answer) > 70:
            raise AuditError("Frozen SQ28 target has an invalid answer.")
        answers[expected] = answer.strip()
    return {"answers": answers}


def request_id(case, arm, repeat):
    return f"OM_{case}_{arm}_R{repeat}"


def check_hashes(root, hashes, label):
    if not isinstance(hashes, dict):
        raise AuditError(f"{label} is not a path-to-hash mapping.")
    for rel, digest in hashes.items():
        path = safe(root, rel) if isinstance(rel, str) else None
        if path is None or not isinstance(digest, str) or not path.is_file() or sha(path) != digest:
            raise AuditError(f"{label} hash mismatch: {rel}")


def audit_run(run):
    run = run.resolve()
    try:
        run.relative_to((BASE / "runs").resolve())
    except ValueError as exc:
        raise AuditError("--run must be beneath epistemic_boundary_mimicry/runs.") from exc
    if run == (BASE / "runs").resolve():
        raise AuditError("--run must name a specific run directory.")
    freeze, manifest = load(run / "freeze.json"), load(run / "manifest.json")
    schedule, status = load(run / "schedule.json"), load(run / "status.json")
    if not isinstance(schedule, list) or len(schedule) != 16:
        raise AuditError("Schedule must contain 16 requests.")
    if (manifest.get("schema_version"), manifest.get("study_id"), manifest.get("planned_provider_requests"),
            manifest.get("model"), manifest.get("randomization_seed")) != (1, "opponent_model16_20261008", 16, "glm-5.3", 2026100804):
        raise AuditError("Manifest identity, size, model or randomization seed mismatch.")
    config = {"endpoint": "chat/completions", "model": "glm-5.3", "temperature": 0.5, "max_tokens": 4096,
              "thinking": {"type": "enabled"}, "reasoning_effort": "low", "stream": False, "tools": None,
              "timeout_seconds": 300, "max_concurrency": 1}
    if manifest.get("configuration") != config or manifest.get("requests") != schedule:
        raise AuditError("Manifest config/requests disagree with the frozen protocol or schedule.")
    expected = {request_id(c, a, r) for c in CASES for a in ARMS for r in REPEATS}
    rows, indexes = {}, []
    for row in schedule:
        rid = row.get("request_id", "")
        match = re.fullmatch(r"OM_(SQ0[1-4])_(B[01])_R([12])", rid)
        if not match or rid in rows:
            raise AuditError(f"Invalid or duplicate schedule ID: {rid}")
        case, arm, rep = match.group(1), match.group(2), int(match.group(3))
        if (row.get("kind"), row.get("model"), row.get("case_id"), row.get("bluffer_condition"),
                row.get("judge_condition"), row.get("repeat")) != ("judge", "glm-5.3", case, arm, "FORECAST", rep):
            raise AuditError(f"Schedule metadata mismatch: {rid}")
        index = row.get("schedule_index")
        if isinstance(index, bool) or not isinstance(index, int) or index not in range(1, 17):
            raise AuditError(f"Invalid schedule index: {rid}")
        indexes.append(index)
        rows[rid] = row
    if set(rows) != expected or sorted(indexes) != list(range(1, 17)):
        raise AuditError("The schedule does not cover each expected ID/index exactly once.")
    blocks = [(c, a) for c in CASES for a in ARMS]
    random.Random(2026100804).shuffle(blocks)
    order = [request_id(c, a, r) for r, seq in ((1, blocks), (2, list(reversed(blocks)))) for c, a in seq]
    if [r["request_id"] for r in sorted(schedule, key=lambda x: x["schedule_index"])] != order:
        raise AuditError("Schedule order does not match the frozen seed/reverse-repeat design.")
    for c in CASES:
        for a in ARMS:
            x, y = rows[request_id(c, a, 1)], rows[request_id(c, a, 2)]
            if (x.get("prompt_sha256"), x.get("source_target_prompt_sha256")) != (y.get("prompt_sha256"), y.get("source_target_prompt_sha256")):
                raise AuditError(f"Repeats do not share identical prompts: {c}/{a}")

    if freeze.get("schema_version") != 1 or freeze.get("experimental_requests_at_freeze") != 0:
        raise AuditError("Freeze receipt does not attest to zero calls before freeze.")
    check_hashes(run, freeze.get("hashes"), "Run freeze")
    required = {"manifest.json", "schedule.json", "inputs/answer_coding.json", "inputs/materials_20261008.json",
                "inputs/PROTOCOL_20261008.md", "inputs/PROMPT_MODULES_20261008.json",
                "inputs/run_opponent_model_replay.py", "inputs/run_strategic_qualification.py"}
    required.update(row.get("prompt_path") for row in schedule)
    for c in CASES:
        for a in ARMS:
            required.update({f"inputs/sq28/prompts/SP_{c}_{a}.txt", f"inputs/sq28/responses/SP_{c}_{a}.json"})
    if not required <= set(freeze["hashes"]):
        raise AuditError("Freeze omits required inputs, prompts, manifest or schedule.")

    runner = ROOT / "scripts/run_opponent_model_replay.py"
    transport = ROOT / "scripts/run_strategic_qualification.py"
    if freeze.get("source_hashes") != {"runner": sha(runner), "transport_helper": sha(transport)}:
        raise AuditError("Current runner/transport sources differ from the freeze receipt.")
    sources = manifest.get("source_artifacts")
    check_hashes(ROOT, sources, "Source artifact")
    source_freeze = load(SOURCE / "freeze.json")
    check_hashes(SOURCE, source_freeze.get("hashes"), "Original SQ28 freeze")
    if isinstance(source_freeze.get("public_copy_hashes"), dict):
        check_hashes(SOURCE, source_freeze["public_copy_hashes"], "Original SQ28 public-copy")

    coding_rel = CODING.relative_to(ROOT).as_posix()
    material_rel = (SOURCE_REL / "inputs/materials_20261008.json").as_posix()
    protocol_rel = "epistemic_boundary_mimicry/opponent_model_replay/PROTOCOL_20261008.md"
    modules_rel = "epistemic_boundary_mimicry/opponent_model_replay/PROMPT_MODULES_20261008.json"
    runner_rel, transport_rel = "scripts/run_opponent_model_replay.py", "scripts/run_strategic_qualification.py"
    original = {}
    for c in CASES:
        for a in ARMS:
            tag = f"SP_{c}_{a}"
            original[c, a, "prompt"] = (SOURCE_REL / "prompts" / f"{tag}.txt").as_posix()
            original[c, a, "response"] = (SOURCE_REL / "responses" / f"{tag}.json").as_posix()
    needed = {coding_rel, material_rel, protocol_rel, modules_rel, runner_rel, transport_rel, *original.values()}
    if not needed <= set(sources):
        raise AuditError("Manifest source_artifacts omits a frozen dependency.")
    for rel, copy in ((coding_rel, run / "inputs/answer_coding.json"), (material_rel, run / "inputs/materials_20261008.json"),
                      (protocol_rel, run / "inputs/PROTOCOL_20261008.md"), (modules_rel, run / "inputs/PROMPT_MODULES_20261008.json"),
                      (runner_rel, run / "inputs/run_opponent_model_replay.py"),
                      (transport_rel, run / "inputs/run_strategic_qualification.py")):
        if sha(copy) != sources[rel]:
            raise AuditError(f"Frozen input copy differs from source: {rel}")
    if sha(CODING) != CODING_SHA or sources[coding_rel] != CODING_SHA:
        raise AuditError("The exact frozen SQ28 coding hash changed.")

    source_answers, source_hashes = {}, {}
    for (c, a, kind), rel in original.items():
        source_path = safe(ROOT, rel)
        digest = sources[rel]
        old_rel = f"{kind}s/SP_{c}_{a}.{'txt' if kind == 'prompt' else 'json'}"
        if source_freeze.get("hashes", {}).get(old_rel) != digest:
            raise AuditError(f"Original SQ28 freeze hash mismatch: {old_rel}")
        copy = run / "inputs/sq28" / ("prompts" if kind == "prompt" else "responses") / source_path.name
        if not copy.is_file() or sha(copy) != digest:
            raise AuditError(f"Frozen run copy differs from original {kind}: {c}/{a}")
        if kind == "response":
            rec = load(source_path)
            if (rec.get("request_id"), rec.get("model"), rec.get("kind"), rec.get("case_id"), rec.get("speaker_condition"),
                    rec.get("returned_model"), rec.get("status"), rec.get("http_status")) != (
                    f"SP_{c}_{a}", "qwen3.8-max", "speaker", c, a, "qwen3.8-max", "response_received", 200):
                raise AuditError(f"Original SQ28 response metadata mismatch: {c}/{a}")
            prompt_rel = original[c, a, "prompt"]
            if rec.get("prompt_sha256") != sources[prompt_rel]:
                raise AuditError(f"Original SQ28 response prompt hash mismatch: {c}/{a}")
            parsed = parse_speaker(rec.get("visible_text"), rec.get("finish_reason"))
            if rec.get("parsed") != parsed or rec.get("parse_status") != "valid":
                raise AuditError(f"Original SQ28 strict parse mismatch: {c}/{a}")
            source_answers[c, a], source_hashes[f"{c}_{a}"] = parsed["answers"], digest

    coding = load(CODING)
    outcomes = {}
    for rec in coding.get("records", []):
        if not isinstance(rec, dict) or rec.get("role") not in ARMS:
            continue
        c, a, q = rec.get("case_id"), rec.get("role"), rec.get("question_id")
        key = (c, a, q)
        if c not in CASES or q not in QUESTIONS or key in outcomes or rec.get("condition") != a:
            raise AuditError("Invalid/duplicate B0/B1 coding row.")
        region, y = rec.get("source_region"), rec.get("source_silence_admission")
        if region not in {"explicit", "unspecified"} or (y is not None and (isinstance(y, bool) or not isinstance(y, int) or y not in (0, 1))):
            raise AuditError(f"Invalid frozen coding value: {c}/{a}/{q}")
        if rec.get("answer") != source_answers[c, a][q]:
            raise AuditError(f"Coded answer differs from the exact original response: {c}/{a}/{q}")
        outcomes[key] = {"y": y, "region": region}
    expected_outcomes = {(c, a, q) for c in CASES for a in ARMS for q in QUESTIONS}
    if set(outcomes) != expected_outcomes or len(outcomes) != 48:
        raise AuditError("Coding must match the exact 48 B0/B1 answer events.")
    if [key for key, row in outcomes.items() if row["y"] is None] != [("SQ02", "B1", "Q6")]:
        raise AuditError("Preserve the sole unresolved SQ02/B1/Q6 coding.")
    if any(outcomes[c, "B0", q]["region"] != outcomes[c, "B1", q]["region"] for c in CASES for q in QUESTIONS):
        raise AuditError("Source-region metadata differs across conditions for a target question.")

    for rid, row in rows.items():
        prompt = safe(run, row.get("prompt_path", ""))
        target_rel = original[row["case_id"], row["bluffer_condition"], "prompt"]
        if not prompt.is_file() or sha(prompt) != row.get("prompt_sha256"):
            raise AuditError(f"Forecast prompt hash mismatch: {rid}")
        if row.get("source_target_prompt_sha256") != sources[target_rel]:
            raise AuditError(f"Target prompt binding mismatch: {rid}")

    responses = {p.stem: p for p in (run / "responses").glob("*.json")} if (run / "responses").is_dir() else {}
    dispatches = {p.stem: p for p in (run / "dispatches").glob("*.json")} if (run / "dispatches").is_dir() else {}
    if (set(responses) | set(dispatches)) - set(rows):
        raise AuditError("Run has a response or dispatch outside the frozen schedule.")
    valid, issues, runner_valid = {}, [], 0
    for rid, row in rows.items():
        dp, rp = dispatches.get(rid), responses.get(rid)
        if rp and not dp:
            raise AuditError(f"Response has no dispatch receipt: {rid}")
        if not dp:
            continue
        d = load(dp)
        dkeys = ("request_id", "model", "case_id", "bluffer_condition", "repeat", "schedule_index", "prompt_sha256", "source_target_prompt_sha256")
        if tuple(d.get(k) for k in dkeys) != (rid, row["model"], row["case_id"], row["bluffer_condition"], row["repeat"], row["schedule_index"], row["prompt_sha256"], row["source_target_prompt_sha256"]):
            raise AuditError(f"Dispatch metadata mismatch: {rid}")
        if not rp:
            continue
        rec = load(rp)
        meta = ("request_id", "model", "kind", "case_id", "bluffer_condition", "judge_condition", "repeat")
        wanted = (rid, "glm-5.3", "judge", row["case_id"], row["bluffer_condition"], "FORECAST", row["repeat"])
        if tuple(rec.get(k) for k in meta) != wanted or rec.get("prompt_sha256") != row["prompt_sha256"]:
            raise AuditError(f"Response metadata/prompt hash mismatch: {rid}")
        if rec.get("returned_model") != "glm-5.3" or rec.get("status") != "response_received":
            issues.append(f"{rid}: response status/model excluded from scoring")
            continue
        parsed, parse_status = parse_forecast(rec.get("visible_text"), rec.get("finish_reason"))
        runner_valid += rec.get("parse_status") == "valid"
        if (rec.get("parse_status"), rec.get("parsed")) != (parse_status, parsed):
            if parse_status != "valid" and rec.get("parse_status") == "valid" and parsed is None:
                issues.append(f"{rid}: strict analyzer rejected runner-accepted JSON; excluded without repair")
                continue
            raise AuditError(f"Raw strict parse disagrees with response receipt: {rid}")
        if parse_status != "valid" or rec.get("http_status") != 200:
            issues.append(f"{rid}: strict parse/HTTP status excluded from scoring")
            continue
        valid[rid] = {item["question_id"]: item["p_explicit_source_silence"] for item in parsed["predictions"]}

    counts = {"planned": 16, "provider_requests": len(dispatches), "response_count": len(responses), "valid": runner_valid}
    if any(status.get(k) is not None and status[k] != v for k, v in counts.items()):
        raise AuditError("status.json counts disagree with the receipts.")
    execution = {"state": status.get("state"), "planned": 16, "dispatched": len(dispatches),
                 "response_receipts": len(responses), "runner_parse_valid": runner_valid, "strict_valid": len(valid),
                 "missing_dispatch_ids": sorted(set(rows) - set(dispatches)),
                 "dispatched_without_response_ids": sorted(set(dispatches) - set(responses)), "issues": issues}
    return run, rows, valid, outcomes, source_hashes, sha(CODING), execution


def avg(values):
    return sum(values) / len(values) if values else None


def family_metrics(case, arm, forecasts, outcomes, resolve=None):
    events = []
    for q in QUESTIONS:
        y = outcomes[case, arm, q]["y"]
        y = resolve if y is None else y
        ps = [forecasts.get(request_id(case, arm, r), {}).get(q) for r in REPEATS]
        ps = [p for p in ps if p is not None]
        events.append({"question_id": q, "source_region": outcomes[case, arm, q]["region"],
                       "label": y, "repeat_count": len(ps), "repeat_probabilities": ps, "p_mean_repeats": avg(ps),
                       "mean_repeat_brier": avg([(p - y) ** 2 for p in ps]) if ps and y is not None else None})
    forecasts_only = [e["p_mean_repeats"] for e in events if e["p_mean_repeats"] is not None]
    scored = [e for e in events if e["p_mean_repeats"] is not None and e["label"] is not None]
    return {
        "case_id": case, "condition": arm, "events": events,
        "forecast_event_coverage": len(forecasts_only),
        "forecast_repeat_coverage": sum(e["repeat_count"] for e in events),
        "mean_forecast_over_available_questions": avg(forecasts_only),
        "scoreable_event_coverage": len(scored),
        "mean_signed_probability_error": avg([e["p_mean_repeats"] - e["label"] for e in scored]),
        "observed_admission_fraction": avg([e["label"] for e in scored]),
        "mean_per_repeat_brier": avg([e["mean_repeat_brier"] for e in scored]),
        "brier_of_mean_probability": avg([(e["p_mean_repeats"] - e["label"]) ** 2 for e in scored]),
        "repeat_dispersion_mean_absolute_difference": avg([abs(e["repeat_probabilities"][0] - e["repeat_probabilities"][1]) for e in events if e["repeat_count"] == 2]),
        "repeat_dispersion_event_count": sum(e["repeat_count"] == 2 for e in events),
    }


def equal_family(rows, metric):
    values = {r["case_id"]: r[metric] for r in rows if r.get(metric) is not None}
    return {"mean": avg(list(values.values())), "n_families": len(values), "by_family": values}


def complete_forecasts(case, arm, forecasts):
    return all(request_id(case, arm, r) in forecasts for r in REPEATS)


def paired_summary(cases, metrics):
    names = ("forecast_delta", "admission_fraction_delta", "repeat_brier_delta", "mean_probability_brier_delta")
    out = {}
    for name in names:
        by_case = {}
        for case in cases:
            left = {e["question_id"]: e for e in metrics["B0"][case]["events"]}
            right = {e["question_id"]: e for e in metrics["B1"][case]["events"]}
            deltas = []
            for q in QUESTIONS:
                a, b = left[q], right[q]
                if a["p_mean_repeats"] is None or b["p_mean_repeats"] is None or a["label"] is None or b["label"] is None:
                    continue
                if name == "forecast_delta": delta = b["p_mean_repeats"] - a["p_mean_repeats"]
                elif name == "admission_fraction_delta": delta = b["label"] - a["label"]
                elif name == "repeat_brier_delta": delta = b["mean_repeat_brier"] - a["mean_repeat_brier"]
                else: delta = (b["p_mean_repeats"] - b["label"]) ** 2 - (a["p_mean_repeats"] - a["label"]) ** 2
                deltas.append(delta)
            if deltas: by_case[case] = avg(deltas)
        out[name] = {"equal_family_mean": avg(list(by_case.values())), "n_families": len(by_case), "by_family": by_case}
    return out


def forecast_delta_only(cases, family):
    by_case = {}
    for c in cases:
        b0 = {e["question_id"]: e["p_mean_repeats"] for e in family["B0"][c]["events"]}
        b1 = {e["question_id"]: e["p_mean_repeats"] for e in family["B1"][c]["events"]}
        d = [b1[q] - b0[q] for q in QUESTIONS if b0[q] is not None and b1[q] is not None]
        if d: by_case[c] = avg(d)
    return {"equal_family_mean_probability_change": avg(list(by_case.values())), "n_families": len(by_case), "by_family": by_case}


def metric_events(events):
    p = [e["p_mean_repeats"] for e in events if e["p_mean_repeats"] is not None]
    scored = [e for e in events if e["p_mean_repeats"] is not None and e["label"] is not None]
    return {"mean_forecast": avg(p), "observed_admission_fraction": avg([e["label"] for e in scored]),
            "mean_signed_probability_error": avg([e["p_mean_repeats"] - e["label"] for e in scored]),
            "mean_per_repeat_brier": avg([e["mean_repeat_brier"] for e in scored]),
            "brier_of_mean_probability": avg([(e["p_mean_repeats"] - e["label"]) ** 2 for e in scored])}


def region_summary(family):
    out = {}
    metric_names = ("mean_forecast", "observed_admission_fraction", "mean_signed_probability_error", "mean_per_repeat_brier", "brier_of_mean_probability")
    for region in ("explicit", "unspecified"):
        counts = {c: sum(e["source_region"] == region for e in family["B0"][c]["events"]) for c in CASES}
        available, eligible = {}, {a: {} for a in ARMS}
        for arm in ARMS:
            all_events, label_n, forecast_n = [], 0, 0
            for c in CASES:
                es = [e for e in family[arm][c]["events"] if e["source_region"] == region]
                all_events.extend(es)
                label_n += sum(e["label"] is not None for e in es)
                forecast_n += sum(e["p_mean_repeats"] is not None for e in es)
                if es and all(e["label"] is not None and e["p_mean_repeats"] is not None and e["repeat_count"] == 2 for e in es):
                    eligible[arm][c] = metric_events(es)
            scored = [e for e in all_events if e["label"] is not None and e["p_mean_repeats"] is not None]
            n_source = sum(counts.values())
            available[arm] = {"source_events": n_source, "label_available_events": label_n,
                              "forecast_available_events": forecast_n, "scored_available_events": len(scored),
                              "scored_coverage": len(scored) / n_source if n_source else None,
                              "pooled_available_event_forecast": avg([e["p_mean_repeats"] for e in all_events if e["p_mean_repeats"] is not None]),
                              "pooled_available_event_brier": avg([e["mean_repeat_brier"] for e in scored])}
        paired = sorted(eligible["B0"].keys() & eligible["B1"].keys())
        deltas = {}
        for metric in metric_names:
            vals = {c: eligible["B1"][c][metric] - eligible["B0"][c][metric] for c in paired
                    if eligible["B0"][c][metric] is not None and eligible["B1"][c][metric] is not None}
            deltas[metric + "_b1_minus_b0"] = {"equal_family_mean": avg(list(vals.values())), "n_families": len(vals), "by_family": vals}
        out[region] = {"source_events_per_condition_by_family": counts, "source_region_share_of_distinct_case_questions": sum(counts.values()) / 24,
                       "available_event_descriptives_pooled_across_events": available,
                       "primary_complete_region_families": {a: {"families": eligible[a], "equal_family_mean": {
                           m: {"mean": avg([v[m] for v in eligible[a].values() if v[m] is not None]),
                               "n_families": sum(v[m] is not None for v in eligible[a].values())} for m in metric_names}} for a in ARMS},
                       "paired_complete_region_families": paired, "paired_b1_minus_b0": deltas}
    return out


def build_analysis(audit):
    run, rows, forecasts, outcomes, source_hashes, coding_hash, execution = audit
    family = {a: {c: family_metrics(c, a, forecasts, outcomes) for c in CASES} for a in ARMS}
    calls = []
    for rid, row in sorted(rows.items(), key=lambda pair: pair[1]["schedule_index"]):
        ps = forecasts.get(rid)
        scored = [(p, outcomes[row["case_id"], row["bluffer_condition"], q]["y"]) for q, p in (ps or {}).items()
                  if outcomes[row["case_id"], row["bluffer_condition"], q]["y"] is not None]
        calls.append({"request_id": rid, "case_id": row["case_id"], "condition": row["bluffer_condition"],
                      "repeat": row["repeat"], "valid_forecast": ps is not None,
                      "mean_forecast_over_six_questions": avg(list(ps.values())) if ps else None,
                      "scoreable_questions": len(scored), "label_coverage_of_six": len(scored) / 6 if ps else 0.0,
                      "mean_signed_probability_error": avg([p - y for p, y in scored]),
                      "mean_brier_over_scoreable_labels": avg([(p - y) ** 2 for p, y in scored])})
    forecast_complete = sorted(c for c in CASES if all(complete_forecasts(c, a, forecasts) for a in ARMS))
    b0_complete = sorted(c for c in CASES if complete_forecasts(c, "B0", forecasts) and all(outcomes[c, "B0", q]["y"] is not None for q in QUESTIONS))
    b1_complete = sorted(c for c in CASES if complete_forecasts(c, "B1", forecasts) and all(outcomes[c, "B1", q]["y"] is not None for q in QUESTIONS))
    paired_complete = sorted(set(b0_complete) & set(b1_complete))
    primary = {"all_family_forecast_probabilities_independent_of_label_coverage": {
                   "families": forecast_complete,
                   "by_condition_equal_family_question_mean": {a: equal_family([family[a][c] for c in forecast_complete], "mean_forecast_over_available_questions") for a in ARMS},
                   "paired_b1_minus_b0_probability_change": forecast_delta_only(forecast_complete, family)},
               "label_complete_families": sorted(c for c in CASES if all(outcomes[c, a, q]["y"] is not None for a in ARMS for q in QUESTIONS)),
               "by_condition": {a: {"families": b0_complete if a == "B0" else b1_complete,
                   "equal_family_mean": {m: equal_family([family[a][c] for c in (b0_complete if a == "B0" else b1_complete)], m)
                       for m in ("mean_forecast_over_available_questions", "mean_signed_probability_error", "observed_admission_fraction", "mean_per_repeat_brier", "brier_of_mean_probability", "repeat_dispersion_mean_absolute_difference")}} for a in ARMS},
               "paired_primary_families": paired_complete, "paired_b1_minus_b0": paired_summary(paired_complete, family),
               "source_region_strata": region_summary(family)}
    sensitivity = {}
    for resolve in (0, 1):
        resolved = {a: {c: family_metrics(c, a, forecasts, outcomes, resolve) for c in CASES} for a in ARMS}
        complete = [c for c in CASES if all(complete_forecasts(c, a, forecasts) for a in ARMS)]
        sensitivity[str(resolve)] = {"resolved_null_as": resolve, "families_with_both_repeats_valid": complete,
            "equal_family_metrics": {a: {m: equal_family([resolved[a][c] for c in complete], m) for m in
                ("mean_forecast_over_available_questions", "mean_signed_probability_error", "observed_admission_fraction", "mean_per_repeat_brier", "brier_of_mean_probability", "repeat_dispersion_mean_absolute_difference")} for a in ARMS},
            "paired_b1_minus_b0": paired_summary(complete, resolved), "family_condition": resolved,
            "source_region_strata": region_summary(resolved)}
    coverage = {"scheduled_calls": 16, "strict_valid_forecast_calls": len(forecasts), "historical_target_events": 48,
                "clear_labels": sum(e["y"] is not None for e in outcomes.values()),
                "unresolved_labels_preserved": ["SQ02/B1/Q6"],
                "historical_explicit_question_share": sum(outcomes[c, "B0", q]["region"] == "explicit" for c in CASES for q in QUESTIONS) / 24}
    return {"schema_version": 1, "study_id": "opponent_model16_20261008", "run_id": run.name,
            "execution": execution, "provenance": {"analyzer_sha256_lf": sha(Path(__file__)), "coding_sha256_lf": coding_hash,
                "original_target_response_sha256_lf": source_hashes}, "coverage": coverage, "per_call": calls,
            "family_condition_after_repeat_averaging": family, "primary_six_question_complete_case": primary,
            "null_resolution_sensitivity_descriptive_only": sensitivity,
            "interpretation_limits": [
                "Independent material-family N is four; calls, predictions and answer units are not independent actor outcomes.",
                "Observed fractions describe these fixed Speaker outputs, not known true conditional behavior probabilities.",
                "Repeat dispersion describes Judge sampling variability for fixed target answers only.",
                "Source-region labels are historical analysis metadata and were not shown to the forecaster.",
                "This hypothesis-guided retrospective replay does not establish population calibration, a stable strategic prior, an internal opponent model or a causal explanation."]}


def fmt(value):
    return "—" if value is None else f"{value:.4f}"


def markdown_report(summary):
    primary = summary["primary_six_question_complete_case"]
    pred = primary["all_family_forecast_probabilities_independent_of_label_coverage"]
    lines = ["# Opponent-model replay analysis", "", f"Run `{summary['run_id']}`: {summary['execution']['strict_valid']}/16 strict-valid forecasts; {summary['execution']['dispatched']}/16 dispatched.",
             "", "## Forecast probabilities independent of label coverage", "",
             "| Condition | Complete families | Equal-family mean forecast |", "|---|---:|---:|"]
    for a in ARMS:
        m = pred["by_condition_equal_family_question_mean"][a]
        lines.append(f"| {a} | {m['n_families']} | {fmt(m['mean'])} |")
    change = pred["paired_b1_minus_b0_probability_change"]
    lines.extend(["", f"Paired B1−B0 forecast change: {fmt(change['equal_family_mean_probability_change'])} across {change['n_families']} complete forecast families.",
                  "", "## Six-question complete-case outcomes", "", "| Condition | Families | Mean forecast | Mean signed error | Admission fraction | Mean-repeat Brier | Brier of mean probability |", "|---|---:|---:|---:|---:|---:|---:|"])
    for a in ARMS:
        vals = primary["by_condition"][a]["equal_family_mean"]
        m = vals["mean_forecast_over_available_questions"]
        names = ("mean_signed_probability_error", "observed_admission_fraction", "mean_per_repeat_brier", "brier_of_mean_probability")
        lines.append("| " + " | ".join([a, str(m["n_families"]), fmt(m["mean"]), *(fmt(vals[n]["mean"]) for n in names)]) + " |")
    lines.extend(["", "Paired B1−B0 complete-case deltas:"])
    for k, label in (("forecast_delta", "Forecast"), ("admission_fraction_delta", "Admission fraction"), ("repeat_brier_delta", "Mean-repeat Brier"), ("mean_probability_brier_delta", "Brier of mean probability")):
        x = primary["paired_b1_minus_b0"][k]
        lines.append(f"- {label}: {fmt(x['equal_family_mean'])} across {x['n_families']} families.")
    lines.extend(["", "## Null sensitivity", "", "| B1 Q6 resolved as | B1 signed error | B1 mean-repeat Brier | B1−B0 Brier change |", "|---|---:|---:|---:|"])
    for r in ("0", "1"):
        x = summary["null_resolution_sensitivity_descriptive_only"][r]
        b1, delta = x["equal_family_metrics"]["B1"], x["paired_b1_minus_b0"]
        lines.append(f"| {r} | {fmt(b1['mean_signed_probability_error']['mean'])} | {fmt(b1['mean_per_repeat_brier']['mean'])} | {fmt(delta['repeat_brier_delta']['equal_family_mean'])} |")
    lines.extend(["", "## Source-region strata", "", "Available-event figures are pooled descriptive coverage; primary results use complete regions within family, then equal family weighting."])
    for region, x in primary["source_region_strata"].items():
        b0 = x["primary_complete_region_families"]["B0"]["equal_family_mean"]
        b1 = x["primary_complete_region_families"]["B1"]["equal_family_mean"]
        paired = x["paired_b1_minus_b0"]
        av = x["available_event_descriptives_pooled_across_events"]
        lines.append(f"- {region}: available scored B0/B1={av['B0']['scored_available_events']}/{av['B0']['source_events']}, {av['B1']['scored_available_events']}/{av['B1']['source_events']}; complete-family n={b0['mean_forecast']['n_families']}/{b1['mean_forecast']['n_families']}; paired n={paired['mean_forecast_b1_minus_b0']['n_families']}; forecast delta={fmt(paired['mean_forecast_b1_minus_b0']['equal_family_mean'])}; Brier delta={fmt(paired['mean_per_repeat_brier_b1_minus_b0']['equal_family_mean'])}.")
    lines.extend(["", "## Interpretation limits", ""])
    lines.extend(f"- {limit}" for limit in summary["interpretation_limits"])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--write", action="store_true", help="write once to analysis/ after the complete-run gate")
    parser.add_argument("--output-name", default="analysis", help="new run-local analysis directory; existing output is never overwritten")
    args = parser.parse_args(argv)
    try:
        summary = build_analysis(audit_run(args.run))
        payload = json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.write:
            if args.run.resolve() != DEFAULT_RUN.resolve():
                raise AuditError("--write is restricted to the reviewed recovery run ending in `_02`.")
            e, c = summary["execution"], summary["coverage"]
            if (e["state"] != "COMPLETE_16_ATTEMPTED" or e["dispatched"] != 16 or e["response_receipts"] != 16
                    or e["strict_valid"] != 16 or e["issues"] or e["missing_dispatch_ids"] or e["dispatched_without_response_ids"]):
                raise AuditError("Write-once output requires 16 dispatches, receipts and strict-valid forecasts.")
            if c["historical_target_events"] != 48 or c["clear_labels"] != 47 or c["unresolved_labels_preserved"] != ["SQ02/B1/Q6"]:
                raise AuditError("Write-once output requires exact 48-event coding and its single unresolved label.")
            if not re.fullmatch(r"[A-Za-z0-9_-]+", args.output_name):
                raise AuditError("--output-name must be a single alphanumeric directory name.")
            report = markdown_report(summary)
            dest = args.run.resolve() / args.output_name
            if dest.exists():
                raise AuditError("Write-once output refused because analysis/ already exists.")
            dest.mkdir()
            (dest / "summary.json").write_text(payload, encoding="utf-8", newline="\n")
            (dest / "RESULTS.md").write_text(report, encoding="utf-8", newline="\n")
            print(f"Wrote {dest / 'summary.json'} and {dest / 'RESULTS.md'}")
        else:
            sys.stdout.write(payload)
    except (AuditError, OSError, TypeError, ValueError) as exc:
        print(f"analysis error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
