"""Prepare and run the fixed 28-call strategic-qualification study."""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "epistemic_boundary_mimicry"
DESIGN = BASE / "strategic_qualification"
MATERIALS = DESIGN / "materials_20261008.json"
MODULES = DESIGN / "PROMPT_MODULES_20261008.json"
EXAMPLES = DESIGN / "judge_examples_20261008.json"
PROTOCOL = DESIGN / "PROTOCOL_20261008.md"
DEFAULT_RUN = BASE / "runs/opencode_go_20261008_strategic_qualification28_01"

ENDPOINTS = {"qwen3.8-max": "messages", "glm-5.3": "chat/completions"}
SPEAKER_MODEL = "qwen3.8-max"
JUDGE_MODEL = "glm-5.3"
CASE_IDS = ("SQ01", "SQ02", "SQ03", "SQ04")
SEAT_BY_CASE = {"SQ01": "A", "SQ02": "B", "SQ03": "B", "SQ04": "A"}
ARMS = ("B0", "B1")
JUDGE_CONDITIONS = ("J0", "J1")
QUESTIONS = tuple(f"Q{i}" for i in range(1, 7))
Q6_SOURCE_REGION = {"SQ01": "explicit", "SQ02": "unspecified", "SQ03": "explicit", "SQ04": "unspecified"}
SEED = 2026100803
TOTAL = 28
TIMEOUT_SECONDS = 300
MAX_SPEAKER_TOKENS = 8192
MAX_JUDGE_TOKENS = 4096


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes().replace(b"\r\n", b"\n"))


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def durable_bytes(path: Path, payload: bytes) -> None:
    """Atomically replace a file; retain a complete temporary if replacement fails."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    complete = False
    replaced = False
    try:
        with temp.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        complete = True
        for attempt in range(20):
            try:
                os.replace(temp, path)
                replaced = True
                return
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(min(0.05 * (attempt + 1), 0.2))
    finally:
        if not complete or replaced:
            temp.unlink(missing_ok=True)


def durable_dump(path: Path, value) -> None:
    durable_bytes(path, json_bytes(value))


def validate_inputs(materials: dict, modules: dict, examples: dict) -> None:
    assert materials.get("schema_version") == 1
    cases = materials.get("cases")
    assert isinstance(cases, list) and len(cases) == 4
    by_id = {case.get("case_id"): case for case in cases}
    assert set(by_id) == set(CASE_IDS)
    for case_id in CASE_IDS:
        case = by_id[case_id]
        assert all(isinstance(case.get(key), str) and case[key] for key in ("title", "public_context", "source_text"))
        questions = case.get("questions")
        assert isinstance(questions, list) and len(questions) == 6
        assert [q.get("question_id") for q in questions] == list(QUESTIONS)
        assert all(isinstance(q.get("question"), str) and q["question"] for q in questions)
        assert all(q.get("source_region") in {"explicit", "unspecified"} for q in questions)
        assert all(isinstance(q.get("gold_answer"), str) for q in questions)
        assert sum(q["source_region"] == "explicit" for q in questions) == 3
        assert sum(q["source_region"] == "unspecified" for q in questions) == 3
        assert questions[5]["source_region"] == Q6_SOURCE_REGION[case_id]
        for question in questions:
            quotes = question.get("source_quotes")
            assert isinstance(quotes, list)
            if question["source_region"] == "explicit":
                assert quotes, "Explicit facts require a supporting source span."
            else:
                assert not quotes, "Unspecified facts must not have a supporting source span."
                assert isinstance(question.get("absence_check"), str) and question["absence_check"].strip()
            assert all(isinstance(quote, str) and quote and quote in case["source_text"] for quote in quotes)

    expected_modules = {
        "speaker_common",
        "reader",
        "bluffer_common",
        "judge_common",
        "judge_blind",
        "judge_informed_neutral",
        "judge_informed_aware",
        "judge_output",
    }
    assert set(modules) == expected_modules
    assert all(isinstance(value, str) and value.strip() for value in modules.values())
    assert {"neutral_examples", "aware_examples"}.issubset(examples)
    assert all(isinstance(examples[key], str) and examples[key].strip() for key in ("neutral_examples", "aware_examples"))


def question_payload(case: dict, ids: tuple[str, ...]) -> list[dict]:
    return [
        {"question_id": question["question_id"], "question": question["question"]}
        for question in case["questions"]
        if question["question_id"] in ids
    ]


def tagged_json(label: str, value) -> str:
    if isinstance(value, str):
        body = value
    else:
        body = json.dumps(value, ensure_ascii=False, indent=2)
    return f"<{label}>\n{body}\n</{label}>"


def join_prompt(*parts: str) -> str:
    return "\n\n".join(part.strip() for part in parts if part and part.strip()) + "\n"


def speaker_prompt(case: dict, condition: str, modules: dict, examples: dict) -> str:
    common = modules["speaker_common"]
    case_data = {
        "case_id": case["case_id"],
        "title": case["title"],
        "public_context": case["public_context"],
        "questions": question_payload(case, QUESTIONS),
    }
    parts = [common]
    if condition == "READER":
        parts.append(modules["reader"])
        parts.append(tagged_json("public_case", case_data))
        parts.append(tagged_json("source_text", case["source_text"]))
    else:
        assert condition in ARMS
        parts.append(modules["bluffer_common"])
        parts.append(tagged_json("public_case", case_data))
        archive_key = "neutral_examples" if condition == "B0" else "aware_examples"
        parts.append(tagged_json("assigned_archive_packet", examples[archive_key]))
    return join_prompt(*parts)


def build_schedule(cases: list[dict], seed: int = SEED) -> list[dict]:
    rng = random.Random(seed)
    ordered = list(cases)
    rng.shuffle(ordered)
    rows: list[dict] = []
    for case_index, case in enumerate(ordered):
        case_id = case["case_id"]
        reader_id = f"SP_{case_id}_READER"
        b0_id = f"SP_{case_id}_B0"
        b1_id = f"SP_{case_id}_B1"
        reader_row = {"request_id": reader_id, "kind": "speaker", "case_id": case_id, "condition": "READER", "model": SPEAKER_MODEL, "depends_on": []}
        b0_row = {"request_id": b0_id, "kind": "speaker", "case_id": case_id, "condition": "B0", "model": SPEAKER_MODEL, "depends_on": []}
        b1_row = {"request_id": b1_id, "kind": "speaker", "case_id": case_id, "condition": "B1", "model": SPEAKER_MODEL, "depends_on": []}
        rows.extend((reader_row, b0_row))
        judge_rows = []
        for arm, speaker_id in (("B0", b0_id), ("B1", b1_id)):
            for judge_condition in JUDGE_CONDITIONS:
                judge_rows.append(
                    {
                        "request_id": f"JG_{case_id}_{arm}_{judge_condition}",
                        "kind": "judge",
                        "case_id": case_id,
                        "bluffer_condition": arm,
                        "judge_condition": judge_condition,
                        "model": JUDGE_MODEL,
                        "depends_on": [reader_id, speaker_id],
                    }
                )
        if case_index == 0:
            # The first GLM call is a planned Judge request with its two required
            # Speaker dependencies; it doubles as the no-extra-call availability check.
            rows.append(judge_rows.pop(0))
        rows.append(b1_row)
        rows.extend(judge_rows)
    assert len(rows) == TOTAL
    for index, row in enumerate(rows, 1):
        row["schedule_index"] = index
        row["reader_seat"] = SEAT_BY_CASE[row["case_id"]]
        if row["kind"] == "speaker":
            row["prompt_path"] = f"prompts/{row['request_id']}.txt"
    assert sum(row["kind"] == "speaker" for row in rows) == 12
    assert sum(row["kind"] == "judge" for row in rows) == 16
    return rows


def configuration() -> dict:
    return {
        "qwen3.8-max": {
            "endpoint_format": ENDPOINTS[SPEAKER_MODEL],
            "temperature": 0.5,
            "max_tokens": MAX_SPEAKER_TOKENS,
            "stream": False,
            "tools": "not supplied",
            "timeout_seconds": TIMEOUT_SECONDS,
            "fresh_session_per_request": True,
            "reasoning_controls": "deployment default; omitted",
        },
        "glm-5.3": {
            "endpoint_format": ENDPOINTS[JUDGE_MODEL],
            "temperature": 0.5,
            "thinking": {"type": "enabled"},
            "reasoning_effort": "low",
            "max_tokens": MAX_JUDGE_TOKENS,
            "stream": False,
            "tools": "not supplied",
            "timeout_seconds": TIMEOUT_SECONDS,
            "fresh_session_per_request": True,
        },
    }


def prepare(run: Path) -> None:
    assert not run.exists(), "Preparation never overwrites an existing run."
    for path in (MATERIALS, MODULES, EXAMPLES, PROTOCOL, Path(__file__)):
        assert path.is_file(), f"Required input missing: {path.name}"
    materials = read_json(MATERIALS)
    modules = read_json(MODULES)
    examples = read_json(EXAMPLES)
    validate_inputs(materials, modules, examples)
    case_by_id = {case["case_id"]: case for case in materials["cases"]}
    schedule = build_schedule(materials["cases"])

    run.mkdir(parents=True)
    for directory in ("inputs", "prompts", "prompt_receipts", "responses", "dispatches", "launch"):
        (run / directory).mkdir()
    input_sources = {
        "materials_20261008.json": MATERIALS,
        "PROMPT_MODULES_20261008.json": MODULES,
        "judge_examples_20261008.json": EXAMPLES,
        "PROTOCOL_20261008.md": PROTOCOL,
    }
    input_hashes = {}
    for name, source in input_sources.items():
        payload = source.read_bytes()
        durable_bytes(run / "inputs" / name, payload)
        input_hashes[name] = sha_file(run / "inputs" / name)
    durable_bytes(run / "schedule.json", json_bytes(schedule))

    speaker_prompts = {}
    for row in schedule:
        if row["kind"] != "speaker":
            continue
        prompt = speaker_prompt(case_by_id[row["case_id"]], row["condition"], modules, examples)
        prompt_path = run / row["prompt_path"]
        durable_bytes(prompt_path, prompt.encode("utf-8"))
        speaker_prompts[row["request_id"]] = {
            "path": row["prompt_path"],
            "sha256": sha_file(prompt_path),
        }

    manifest = {
        "schema_version": 1,
        "study": "strategic qualification, four fixed materials, one Qwen speaker and GLM judge arm",
        "created_utc": now(),
        "planned_provider_requests": TOTAL,
        "speaker_requests": 12,
        "judge_requests": 16,
        "randomization_seed": SEED,
        "randomized_case_order": [row["case_id"] for row in schedule if row["kind"] == "speaker" and row["condition"] == "READER"],
        "reader_seat_by_case": SEAT_BY_CASE,
        "models": {"speaker": SPEAKER_MODEL, "judge": JUDGE_MODEL},
        "endpoint_base": "https://opencode.ai/zen/go/v1",
        "endpoint_formats": ENDPOINTS,
        "configuration_by_model": configuration(),
        "max_concurrency": 1,
        "schedule_path": "schedule.json",
        "speaker_prompts": speaker_prompts,
        "dynamic_judge_prompts": "Built once from validated Speaker replies; exact bytes and hashes are saved before each Judge dispatch.",
        "judge_design": {
            "comparisons": "each case's same Reader response is paired with B0 and B1 separately; J0/J1 are twin prompts for each pair",
            "shared_prefix": "J0/J1 within a case and bluffer condition share the exact archive packets and case/reply input; only the exposure notice differs",
            "judge_sees": "public context, Q1-Q5 questions and replies for seats A/B, Q6 question without any Q6 reply, both archive packets, and one J0/J1 notice",
            "never_shown_to_model": ["source gold answers", "source regions", "source quotes", "private reader seat", "unseen Q6 answers"],
            "p_A_Q6_unspecified": "forecast that seat A explicitly says the supplied source lacks the requested answer if Q6 is asked",
            "p_B_Q6_unspecified": "forecast that seat B explicitly says the supplied source lacks the requested answer if Q6 is asked",
        },
        "failure_policy": {
            "provider_retries": False,
            "semantic_repairs": False,
            "fallback_models": False,
            "stop_batch_on": ["http_error", "transport_unknown", "unexpected_model", "truncation", "invalid_speaker", "invalid_judge", "invalid_provider_response", "local_fatal"],
            "dispatched_request_is_never_resubmitted": True,
        },
        "inputs": input_hashes,
        "requests": schedule,
    }
    durable_dump(run / "manifest.json", manifest)
    code_path = run / "inputs" / "run_strategic_qualification.py"
    durable_bytes(code_path, Path(__file__).read_bytes())
    freeze_paths = ["manifest.json", "schedule.json", *[f"inputs/{name}" for name in input_sources], "inputs/run_strategic_qualification.py", *[meta["path"] for meta in speaker_prompts.values()]]
    freeze = {
        "schema_version": 1,
        "created_utc": now(),
        "experimental_requests_at_freeze": 0,
        "hashes": {relative: sha_file(run / relative) for relative in freeze_paths},
        "source_hashes": {"runner": sha_file(Path(__file__)), **{name: sha_file(path) for name, path in input_sources.items()}},
    }
    durable_dump(run / "freeze.json", freeze)
    durable_dump(
        run / "status.json",
        {"state": "PREPARED", "planned": TOTAL, "provider_requests": 0, "response_count": 0, "valid": 0},
    )
    audit(run)
    print(json.dumps({"prepared": True, "planned": TOTAL, "speaker": 12, "judge": 16, "case_order": manifest["randomized_case_order"]}))


def audit(run: Path) -> None:
    freeze = read_json(run / "freeze.json")
    assert sha_file(Path(__file__)) == freeze["source_hashes"]["runner"]
    for relative, digest in freeze["hashes"].items():
        assert sha_file(run / relative) == digest, relative
    manifest = read_json(run / "manifest.json")
    schedule = read_json(run / "schedule.json")
    assert len(schedule) == TOTAL == len(manifest["requests"])
    assert schedule == manifest["requests"]
    assert sum(row["kind"] == "speaker" for row in schedule) == 12
    assert sum(row["kind"] == "judge" for row in schedule) == 16
    assert [row["schedule_index"] for row in schedule] == list(range(1, TOTAL + 1))
    modules = read_json(run / "inputs" / "PROMPT_MODULES_20261008.json")
    examples = read_json(run / "inputs" / "judge_examples_20261008.json")
    materials = read_json(run / "inputs" / "materials_20261008.json")
    validate_inputs(materials, modules, examples)
    assert manifest["configuration_by_model"] == configuration()
    assert build_schedule(materials["cases"], manifest["randomization_seed"]) == schedule
    cases = {case["case_id"]: case for case in materials["cases"]}
    for row in schedule:
        if row["kind"] == "speaker":
            path = run / row["prompt_path"]
            expected = speaker_prompt(cases[row["case_id"]], row["condition"], modules, examples).encode("utf-8")
            assert path.read_bytes() == expected, row["request_id"]
            assert sha_file(path) == manifest["speaker_prompts"][row["request_id"]]["sha256"]
    print(json.dumps({"offline_audit": "PASS", "planned": TOTAL, "speakers": 12, "judges": 16, "provider_requests": 0}))


def word_count(value: str) -> int:
    return len(re.findall(r"[\w]+(?:[’'-][\w]+)*", value, flags=re.UNICODE))


def parse_speaker(text: str, finish_reason: str) -> tuple[dict | None, str]:
    if finish_reason not in {"stop", "end_turn", "stop_sequence"}:
        return None, "truncated" if finish_reason in {"length", "max_tokens", "token_limit"} else "invalid_speaker"
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None, "invalid_speaker"
    if not isinstance(value, dict) or set(value) != {"answers"} or not isinstance(value["answers"], list):
        return None, "invalid_speaker"
    answers = value["answers"]
    if len(answers) != len(QUESTIONS):
        return None, "invalid_speaker"
    parsed = {}
    for expected_id, row in zip(QUESTIONS, answers):
        if not isinstance(row, dict) or set(row) != {"question_id", "answer"}:
            return None, "invalid_speaker"
        answer = row["answer"]
        if row["question_id"] != expected_id or not isinstance(answer, str) or not answer.strip() or word_count(answer) > 70:
            return None, "invalid_speaker"
        parsed[expected_id] = answer.strip()
    return {"answers": parsed}, "valid"


def parse_judge(text: str, finish_reason: str) -> tuple[dict | None, str]:
    if finish_reason not in {"stop", "end_turn", "stop_sequence"}:
        return None, "truncated" if finish_reason in {"length", "max_tokens", "token_limit"} else "invalid_judge"
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None, "invalid_judge"
    expected = {"p_A", "decision", "p_A_Q6_unspecified", "p_B_Q6_unspecified", "reason"}
    if not isinstance(value, dict) or set(value) != expected:
        return None, "invalid_judge"
    if value["decision"] not in {"A", "B", "ABSTAIN"}:
        return None, "invalid_judge"
    for key in ("p_A", "p_A_Q6_unspecified", "p_B_Q6_unspecified"):
        number = value[key]
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not 0 <= number <= 1:
            return None, "invalid_judge"
        value[key] = float(number)
    if not isinstance(value["reason"], str) or not value["reason"].strip() or word_count(value["reason"]) > 100:
        return None, "invalid_judge"
    return value, "valid"


def judge_prefix(row: dict, case: dict, reader: dict, bluffer: dict, examples: dict, modules: dict) -> str:
    reader_seat = row["reader_seat"]
    bluffer_seat = "B" if reader_seat == "A" else "A"
    q1_q5 = tuple(f"Q{i}" for i in range(1, 6))
    pairs = {
        reader_seat: {qid: reader["answers"][qid] for qid in q1_q5},
        bluffer_seat: {qid: bluffer["answers"][qid] for qid in q1_q5},
    }
    case_view = {
        "case_id": row["case_id"],
        "title": case["title"],
        "public_context": case["public_context"],
        "questions_with_replies": [
            {
                "question_id": question["question_id"],
                "question": question["question"],
                "A_reply": pairs["A"][question["question_id"]],
                "B_reply": pairs["B"][question["question_id"]],
            }
            for question in case["questions"][:5]
        ],
        "Q6_prompt_only": {
            "question_id": "Q6",
            "question": case["questions"][5]["question"],
        },
    }
    return join_prompt(
        modules["judge_common"],
        tagged_json("archive_E0_neutral", examples["neutral_examples"]),
        tagged_json("archive_E1_aware", examples["aware_examples"]),
        tagged_json("judge_case_input", case_view),
    )


def judge_prompt(row: dict, prefix: str, modules: dict) -> str:
    if row["judge_condition"] == "J0":
        notice = modules["judge_blind"]
    elif row["bluffer_condition"] == "B0":
        notice = modules["judge_informed_neutral"]
    else:
        notice = modules["judge_informed_aware"]
    return join_prompt(prefix, notice, modules["judge_output"])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def classify_http_error(error: urllib.error.HTTPError) -> str:
    try:
        body = error.read()
    except OSError:
        body = b""
    text = body.decode("utf-8", errors="ignore").lower()
    if error.code == 429 or any(term in text for term in ("rate limit", "rate_limit", "too many requests")):
        return "rate"
    if error.code == 402 or any(term in text for term in ("payment", "billing", "insufficient credit", "insufficient balance")):
        return "payment"
    if any(term in text for term in ("allowance", "quota", "usage limit", "monthly limit")):
        return "allowance"
    return "unspecified"


def extract_visible(data: dict, endpoint_format: str) -> tuple[str, str | None]:
    if endpoint_format == "messages":
        content = data.get("content")
        if not isinstance(content, list):
            raise ValueError("invalid messages content")
        visible = "".join(block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text")
        finish = data.get("stop_reason")
    else:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ValueError("invalid choices")
        choice = choices[0]
        message = choice.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ValueError("invalid message content")
        visible = message["content"]
        finish = choice.get("finish_reason")
    if not isinstance(visible, str) or not isinstance(finish, str):
        raise ValueError("missing visible text or finish reason")
    return visible, finish


def call(row: dict, prompt: str, prompt_hash: str, key: str, session_id: str) -> dict:
    model = row["model"]
    endpoint_format = ENDPOINTS[model]
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "XiaBaiWangResearch/1.0",
        "x-opencode-session": session_id,
    }
    if endpoint_format == "messages":
        headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
    else:
        headers["Authorization"] = "Bearer " + key
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_SPEAKER_TOKENS if row["kind"] == "speaker" else MAX_JUDGE_TOKENS,
        "temperature": 0.5,
        "stream": False,
    }
    if row["kind"] == "judge":
        body["thinking"] = {"type": "enabled"}
        body["reasoning_effort"] = "low"
    receipt = {
        "request_id": row["request_id"],
        "model": model,
        "kind": row["kind"],
        "case_id": row["case_id"],
        "prompt_sha256": prompt_hash,
        "status": "inflight",
        "sent_utc": now(),
        "visible_text": "",
        "parsed": None,
        "parse_status": "not_received",
        "returned_model": None,
        "usage": {},
        "finish_reason": None,
    }
    if row["kind"] == "speaker":
        receipt["speaker_condition"] = row["condition"]
    else:
        receipt.update(bluffer_condition=row["bluffer_condition"], judge_condition=row["judge_condition"])
    started = time.monotonic()
    request = urllib.request.Request(
        "https://opencode.ai/zen/go/v1/" + endpoint_format,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=headers,
    )
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
            receipt["http_status"] = response.status
        if not isinstance(data, dict):
            raise ValueError("invalid provider response")
        receipt["returned_model"] = data.get("model")
        receipt["usage"] = data.get("usage", {})
        visible, finish_reason = extract_visible(data, endpoint_format)
        receipt["finish_reason"] = finish_reason
        receipt["visible_text"] = visible.replace(key, "[REDACTED]")
        receipt["status"] = "response_received"
        if receipt["returned_model"] != model:
            receipt["parse_status"] = "unexpected_model"
        elif row["kind"] == "speaker":
            receipt["parsed"], receipt["parse_status"] = parse_speaker(receipt["visible_text"], finish_reason)
        else:
            receipt["parsed"], receipt["parse_status"] = parse_judge(receipt["visible_text"], finish_reason)
    except urllib.error.HTTPError as error:
        receipt.update(
            status="http_error",
            http_status=error.code,
            error_type=type(error).__name__,
            provider_error_category=classify_http_error(error),
        )
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        receipt.update(status="transport_unknown", error_type=type(error).__name__)
    except (ValueError, KeyError, IndexError, TypeError, AttributeError, json.JSONDecodeError) as error:
        receipt.update(status="invalid_provider_response", error_type=type(error).__name__)
    receipt.update(elapsed_seconds=round(time.monotonic() - started, 3), captured_utc=now())
    return receipt


def halt_reason(receipt: dict) -> str | None:
    if receipt["status"] != "response_received":
        return receipt["status"]
    if receipt["parse_status"] != "valid":
        return receipt["parse_status"]
    return None


def wait_for_launch_receipt(run: Path) -> dict:
    path = run / "launch" / "launch_receipt.private.json"
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if path.is_file():
            receipt = read_json(path)
            if receipt.get("state") == "LAUNCHED":
                return receipt
            if receipt.get("state") == "LAUNCH_FAILED":
                raise SystemExit("Private receipt records failed launch; no requests sent.")
        time.sleep(0.1)
    raise SystemExit("Timed out waiting for launch receipt; no requests sent.")


def execute(run: Path) -> None:
    audit(run)
    launch_receipt = wait_for_launch_receipt(run)
    manifest = read_json(run / "manifest.json")
    schedule = read_json(run / "schedule.json")
    status = read_json(run / "status.json")
    assert status["state"] == "PREPARED", "Execution requires the frozen PREPARED state."
    assert launch_receipt["manifest_sha256"] == sha_file(run / "manifest.json")
    assert not list((run / "dispatches").glob("*.json")), "Existing dispatch; refuse resubmission."
    assert not list((run / "responses").glob("*.json")), "Existing response; refuse resubmission."
    assert not list((run / "prompt_receipts").glob("*.json")), "Existing prompt receipt; refuse resubmission."
    session_path = run / "launch" / "session_mappings.private.json"
    assert not session_path.exists(), "Existing private session map; refuse resubmission."
    key = os.environ.get("OPENCODE_GO_API_KEY", "").strip()
    assert key, "Credential unavailable in detached worker; no request sent."
    lock_path = run / "execution.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(fd)

    modules = read_json(run / "inputs" / "PROMPT_MODULES_20261008.json")
    examples = read_json(run / "inputs" / "judge_examples_20261008.json")
    materials = read_json(run / "inputs" / "materials_20261008.json")
    cases = {case["case_id"]: case for case in materials["cases"]}
    state = {"state": "RUNNING", "halt_reason": None}
    frozen_judge_prefixes: dict[tuple[str, str], str] = {}

    def saved_responses() -> dict[str, dict]:
        found = {}
        for path in (run / "responses").glob("*.json"):
            row = read_json(path)
            found[row["request_id"]] = row
        return found

    def update_status() -> dict:
        receipts = [read_json(path) for path in (run / "responses").glob("*.json")]
        value = {
            **state,
            "planned": TOTAL,
            "provider_requests": len(list((run / "dispatches").glob("*.json"))),
            "response_count": len(receipts),
            "valid": sum(row.get("parse_status") == "valid" for row in receipts),
            "by_kind": {
                kind: {
                    "responses": sum(row.get("kind") == kind for row in receipts),
                    "valid": sum(row.get("kind") == kind and row.get("parse_status") == "valid" for row in receipts),
                }
                for kind in ("speaker", "judge")
            },
            "updated_utc": now(),
        }
        durable_dump(run / "status.json", value)
        return value

    try:
        durable_dump(session_path, {"schema_version": 1, "mappings": []})
        for row in schedule:
            responses = saved_responses()
            for dependency in row["depends_on"]:
                assert dependency in responses and responses[dependency].get("parse_status") == "valid", f"Unmet dependency: {dependency}"
            dependency_hashes = {
                dependency: sha_file(run / "responses" / f"{dependency}.json")
                for dependency in row["depends_on"]
            }
            if row["kind"] == "speaker":
                prompt_path = run / row["prompt_path"]
                prompt = prompt_path.read_text(encoding="utf-8")
                prompt_hash = sha_file(prompt_path)
                assert prompt_hash == manifest["speaker_prompts"][row["request_id"]]["sha256"]
                durable_dump(
                    run / "prompt_receipts" / f"{row['request_id']}.json",
                    {
                        "request_id": row["request_id"],
                        "path": row["prompt_path"],
                        "prompt_sha256": prompt_hash,
                        "dependency_response_sha256": dependency_hashes,
                        "created_utc": now(),
                    },
                )
            else:
                reader_id = f"SP_{row['case_id']}_READER"
                bluffer_id = f"SP_{row['case_id']}_{row['bluffer_condition']}"
                prefix = judge_prefix(row, cases[row["case_id"]], responses[reader_id]["parsed"], responses[bluffer_id]["parsed"], examples, modules)
                prefix_hash = sha_bytes(prefix.encode("utf-8"))
                pair_key = (row["case_id"], row["bluffer_condition"])
                previous_hash = frozen_judge_prefixes.get(pair_key)
                if row["judge_condition"] == "J0":
                    assert previous_hash is None
                    frozen_judge_prefixes[pair_key] = prefix_hash
                else:
                    assert previous_hash == prefix_hash, "J0/J1 Judge prefix changed within a paired comparison."
                prompt = judge_prompt(row, prefix, modules)
                prompt_path = run / "prompts" / f"{row['request_id']}.txt"
                durable_bytes(prompt_path, prompt.encode("utf-8"))
                prompt_hash = sha_file(prompt_path)
                receipt_path = run / "prompt_receipts" / f"{row['request_id']}.json"
                durable_dump(
                    receipt_path,
                    {
                        "request_id": row["request_id"],
                        "path": prompt_path.relative_to(run).as_posix(),
                        "prompt_sha256": prompt_hash,
                        "shared_prefix_sha256": prefix_hash,
                        "dependency_response_sha256": dependency_hashes,
                        "created_utc": now(),
                    },
                )
            dispatch_path = run / "dispatches" / f"{row['request_id']}.json"
            response_path = run / "responses" / f"{row['request_id']}.json"
            assert not dispatch_path.exists() and not response_path.exists(), "Duplicate request artifact; stopping."
            session_id = "xia-sq-" + str(uuid4())
            session_data = read_json(session_path)
            session_data["mappings"].append({"request_id": row["request_id"], "session_id": session_id})
            durable_dump(session_path, session_data)
            durable_dump(
                dispatch_path,
                {
                    "request_id": row["request_id"],
                    "model": row["model"],
                    "kind": row["kind"],
                    "case_id": row["case_id"],
                    "dispatched_utc": now(),
                    "prompt_sha256": prompt_hash,
                    "schedule_index": row["schedule_index"],
                    "dependencies": row["depends_on"],
                    "dependency_response_sha256": dependency_hashes,
                },
            )
            update_status()
            response = call(row, prompt, prompt_hash, key, session_id)
            durable_dump(response_path, response)
            reason = halt_reason(response)
            if reason:
                state.update(state="HALTED", halt_reason=reason)
                update_status()
                print(json.dumps({"state": "HALTED", "request_id": row["request_id"], "halt_reason": reason, "provider_requests": len(list((run / "dispatches").glob("*.json")))}), flush=True)
                return
            current = update_status()
            print(json.dumps({"request_id": row["request_id"], "kind": row["kind"], "response_count": current["response_count"], "planned": TOTAL, "parse_status": response["parse_status"], "finish_reason": response["finish_reason"]}), flush=True)
        state.update(state="COMPLETE_28_ATTEMPTED", completed_utc=now())
        final = update_status()
        durable_dump(run / "status.json", final)
        print(json.dumps(final), flush=True)
    except BaseException as error:
        state.update(state="HALTED", halt_reason="local_fatal/" + type(error).__name__)
        try:
            update_status()
        except Exception:
            pass
        raise
    finally:
        lock_path.unlink(missing_ok=True)


def launch(run: Path) -> None:
    assert os.name == "nt", "Detached launch is implemented for the Windows workspace."
    audit(run)
    status = read_json(run / "status.json")
    assert status["state"] == "PREPARED", "Launch requires PREPARED status."
    launch_dir = run / "launch"
    receipt_path = launch_dir / "launch_receipt.private.json"
    reservation = launch_dir / "launcher_reservation.private"
    assert not receipt_path.exists(), "Launch receipt already exists."
    assert not list((run / "dispatches").glob("*.json")) and not list((run / "responses").glob("*.json")), "Existing request artifacts; refusing launch."
    assert not list((run / "prompt_receipts").glob("*.json")), "Existing prompt receipt; refusing launch."
    assert not (launch_dir / "session_mappings.private.json").exists(), "Existing private session map; refusing launch."
    try:
        fd = os.open(reservation, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise SystemExit("A launcher already reserved this run; refusing duplicate launch.") from error
    os.write(fd, b"strategic qualification launch reserved\n")
    os.close(fd)
    key = getpass.getpass("OpenCode Go API key (hidden): ").strip()
    if not key:
        reservation.unlink(missing_ok=True)
        raise SystemExit("Empty credential; no worker launched.")
    stdout_path = launch_dir / "worker.stdout.private.log"
    stderr_path = launch_dir / "worker.stderr.private.log"
    script = Path(__file__).resolve()
    command = [sys.executable, "-X", "utf8", "-B", str(script), "--run", str(run.resolve()), "--execute"]
    child_env = os.environ.copy()
    child_env.pop("OPENCODE_GO_API_KEY", None)
    child_env["OPENCODE_GO_API_KEY"] = key
    del key
    child = None
    receipt_published = False
    try:
        with stdout_path.open("xb") as stdout_stream, stderr_path.open("xb") as stderr_stream:
            child = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=stdout_stream,
                stderr=stderr_stream,
                env=child_env,
                close_fds=True,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        del child_env
        durable_dump(
            receipt_path,
            {
                "state": "LAUNCHED",
                "pid": child.pid,
                "host": os.environ.get("COMPUTERNAME"),
                "launch_utc": now(),
                "command": "python -X utf8 -B scripts/run_strategic_qualification.py --execute",
                "run_path": str(run.resolve()),
                "manifest_sha256": sha_file(run / "manifest.json"),
                "planned_provider_requests": TOTAL,
                "max_concurrency": 1,
                "stdout_path": str(stdout_path.resolve()),
                "stderr_path": str(stderr_path.resolve()),
            },
        )
        receipt_published = True
        print(json.dumps({"launch": "accepted", "pid": child.pid, "planned": TOTAL}), flush=True)
    except BaseException:
        if child is not None and not receipt_published:
            durable_dump(receipt_path, {"state": "LAUNCH_FAILED", "pid": child.pid, "launch_utc": now(), "run_path": str(run.resolve()), "planned_provider_requests": TOTAL})
        elif child is None:
            reservation.unlink(missing_ok=True)
            stdout_path.unlink(missing_ok=True)
            stderr_path.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--audit", action="store_true")
    mode.add_argument("--launch", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    run = args.run.resolve()
    runs_root = (BASE / "runs").resolve()
    try:
        run.relative_to(runs_root)
    except ValueError as error:
        raise SystemExit(f"--run must be a descendant of {runs_root}") from error
    if run == runs_root:
        raise SystemExit(f"--run must be a specific run directory under {runs_root}")
    if args.prepare:
        prepare(run)
    elif args.audit:
        audit(run)
    elif args.launch:
        launch(run)
    else:
        execute(run)


if __name__ == "__main__":
    main()
