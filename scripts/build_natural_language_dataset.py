"""Offline development-material validation, documentation and role projection.

No network, credentials, provider clients, model calls or game execution.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "datasets/natural_language_epistemic_games/dev24_20261010"
DOMAINS = (
    "ecology_fieldwork", "materials_engineering", "archaeology_conservation",
    "civic_institutions", "ethnography_social", "linguistics_fieldwork",
    "mathematics_practice", "investigations_history",
)
WORLD_FIELDS = {
    "schema_version", "world_id", "family_id", "domain", "title", "split",
    "language", "synthetic", "public_context", "source_title", "source_text",
    "structure_tags", "authoring_note", "evaluation",
}
EVALUATION_FIELDS = {
    "supported_claims", "explicit_negatives", "licensed_inferences",
    "unspecified_probes", "consistency_questions",
}


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=no_duplicate_keys)


def word_count(text):
    return len(re.findall(r"\b[\w]+(?:[-'][\w]+)*\b", text))


def digest_bytes(data):
    return sha256(data).hexdigest()


def text_digest(text):
    return digest_bytes(text.encode("utf-8"))


def validate_world(world, filename=None):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    if not isinstance(world, dict):
        return ["world must be an object"]
    require(set(world) == WORLD_FIELDS, "unexpected or missing world fields")
    wid = world.get("world_id", "")
    require(isinstance(wid, str) and bool(re.fullmatch(r"NL\d{3}", wid)), "invalid world_id")
    if filename is not None:
        require(Path(filename).stem == wid, "filename/world_id mismatch")
    for key, expected in (("schema_version", "1.0"), ("split", "development"),
                          ("language", "en"), ("synthetic", True)):
        require(world.get(key) == expected, f"invalid {key}")
    require(world.get("domain") in DOMAINS, "unknown domain")
    family = world.get("family_id", "")
    require(isinstance(family, str) and bool(re.fullmatch(r"[a-z0-9_-]+", family)), "invalid family_id")
    for key in ("title", "source_title", "authoring_note", "public_context", "source_text"):
        require(isinstance(world.get(key), str) and bool(world[key].strip()), f"empty/non-text {key}")
    source = world.get("source_text", "")
    public = world.get("public_context", "")
    if not isinstance(source, str) or not isinstance(public, str):
        return errors
    require(350 <= word_count(source) <= 550, "source outside 350–550 words")
    require(40 <= word_count(public) <= 100, "public context outside 40–100 words")
    require(len(source.split("\n\n")) >= 4, "source needs natural paragraphs")
    tags = world.get("structure_tags")
    require(isinstance(tags, list) and len(tags) >= 2
            and all(isinstance(t, str) and t.strip() for t in tags), "invalid structure_tags")
    evaluation = world.get("evaluation")
    if not isinstance(evaluation, dict):
        return errors + ["evaluation must be an object"]
    require(set(evaluation) == EVALUATION_FIELDS, "unexpected/missing evaluation fields")
    sizes = {"supported_claims": 5, "explicit_negatives": 2,
             "licensed_inferences": 2, "unspecified_probes": 3,
             "consistency_questions": 2}
    prefixes = {"supported_claims": "S", "explicit_negatives": "N",
                "licensed_inferences": "I", "unspecified_probes": "U",
                "consistency_questions": "C"}
    fields = {
        "supported_claims": {"id", "claim", "evidence"},
        "explicit_negatives": {"id", "claim", "evidence"},
        "licensed_inferences": {"id", "claim", "premise_ids", "rationale"},
        "unspecified_probes": {"id", "neutral_question", "presupposition_question", "candidate_claim", "boundary_note"},
        "consistency_questions": {"id", "question", "target_claim_ids", "reference_answer"},
    }
    records = {}
    for group, minimum in sizes.items():
        rows = evaluation.get(group, [])
        if not isinstance(rows, list):
            errors.append(f"{group} must be a list")
            continue
        require(len(rows) >= minimum, f"too few {group}")
        for row in rows:
            if not isinstance(row, dict):
                errors.append(f"{group} contains non-object")
                continue
            require(set(row) == fields[group], f"unexpected/missing {group} record fields")
            rid = row.get("id", "")
            require(isinstance(rid, str) and bool(re.fullmatch(prefixes[group] + r"[1-9]\d*", rid)),
                    f"invalid {group} id")
            require(rid not in records, f"duplicate evaluation id {rid}")
            if not isinstance(rid, str):
                continue
            records[rid] = (group, row)
            for key, value in row.items():
                if key not in {"evidence", "premise_ids", "target_claim_ids"}:
                    require(isinstance(value, str) and bool(value.strip()), f"empty {rid}/{key}")
            if "evidence" in row:
                evidence = row["evidence"]
                require(isinstance(evidence, list) and len(evidence) > 0, f"missing evidence {rid}")
                if isinstance(evidence, list):
                    for span in evidence:
                        require(isinstance(span, str) and len(span) >= 12 and span in source,
                                f"nonliteral/short source evidence {rid}")
            if group == "unspecified_probes":
                require(row.get("neutral_question") != row.get("presupposition_question"),
                        f"identical probe pair {rid}")
    fact_ids = {rid for rid, (group, _) in records.items()
                if group in {"supported_claims", "explicit_negatives", "licensed_inferences"}}
    for rid, (group, row) in records.items():
        if group not in {"licensed_inferences", "consistency_questions"}:
            continue
        key = "premise_ids" if group == "licensed_inferences" else "target_claim_ids"
        references = row.get(key, [])
        require(isinstance(references, list) and len(references) >= (2 if group == "consistency_questions" else 1),
                f"too few references {rid}")
        if isinstance(references, list):
            require(all(isinstance(x, str) and x in fact_ids and x != rid for x in references),
                    f"invalid claim reference {rid}")
            if all(isinstance(x, str) for x in references):
                require(len(references) == len(set(references)), f"duplicate claim reference {rid}")
    # Detect unsupported circular inference chains, not just dangling references.
    visiting, visited = set(), set()

    def visit(rid):
        if rid in visiting:
            errors.append(f"circular inference at {rid}")
            return
        if rid in visited or rid not in records:
            return
        visiting.add(rid)
        group, row = records[rid]
        if group == "licensed_inferences" and isinstance(row.get("premise_ids"), list):
            for other in row["premise_ids"]:
                if isinstance(other, str):
                    visit(other)
        visiting.remove(rid)
        visited.add(rid)

    for rid in fact_ids:
        visit(rid)
    return errors


def validate_config(config):
    errors = []
    arms = config.get("arms", [])
    observed = {(a.get("reader_model"), a.get("bluffer_model"), a.get("judge_model")) for a in arms}
    expected = {("qwen3.8-max", "qwen3.8-max", "glm-5.3"),
                ("glm-5.3", "glm-5.3", "qwen3.8-max")}
    if observed != expected or len(arms) != 2:
        errors.append("configuration must contain exactly the reciprocal same-model Speaker arms")
    if config.get("model_weights") != "frozen_no_fine_tuning":
        errors.append("model weights must remain frozen")
    generation = config.get("shared_requested_generation", {})
    if generation.get("reasoning_policy") != "provider_default_for_both_models":
        errors.append("reasoning request policy must be common")
    if generation.get("explicit_reasoning_effort") is not None or generation.get("explicit_thinking") is not None:
        errors.append("asymmetric historical thinking/effort override is not allowed")
    if generation.get("temperature") != 0.5 or generation.get("max_output_tokens") != 16384:
        errors.append("unexpected shared sampling/output budget")
    adapters = config.get("provider_adapters", {})
    if any(adapters.get(model, {}).get("reasoning_fields") != "omit"
           for model in ("qwen3.8-max", "glm-5.3")):
        errors.append("both provider adapters must omit asymmetric reasoning overrides")
    roles = config.get("roles", {})
    if roles.get("reader_bluffer_same_model") is not True or roles.get("independent_sessions") is not True:
        errors.append("same-model Speakers must use independent sessions")
    if config.get("dispatch_authorized_by_this_file") is not False:
        errors.append("offline config must not authorize dispatch")
    if config.get("stopping", {}).get("max_ask_actions") is not None:
        errors.append("five-query or other fixed ASK cap must not be reintroduced")
    if config.get("stopping", {}).get("guard_is_voluntary_stop_or_abstention") is not False:
        errors.append("budget censoring must not be coded as a voluntary decision")
    if config.get("decision_loss") != {"correct": 0.0, "wrong": 1.0, "abstain": 0.25}:
        errors.append("decision loss mismatch")
    return errors


def role_packet(world, role, modules, strategy="matched_access", reader_style="matched_access", judge_policy="active"):
    if role not in {"reader", "bluffer", "judge"}:
        raise ValueError("unknown role")
    if strategy not in modules["bluffer_strategies"] or reader_style not in modules["reader_styles"]:
        raise ValueError("unknown instruction condition")
    if judge_policy not in {"active", "nonadaptive"}:
        raise ValueError("unknown judge policy")
    # Deliberate field allowlist. Neither evaluation nor metadata is serialized.
    public = f"Topic: {world['title']}\n\nShared public context:\n{world['public_context']}"
    if role == "judge":
        system = modules["judge_instruction"]
        system += "\n\n" + (modules["judge_action_format"] if judge_policy == "active"
                             else modules["nonadaptive_instruction"])
        user = public
    else:
        system = modules["shared_speaker_instruction"]
        if role == "reader":
            extra = modules["reader_styles"][reader_style]
            user = (public + "\n\n" + modules["reader_access_prefix"] + "\n"
                    + world["source_title"] + "\n\n" + world["source_text"])
        else:
            extra = modules["bluffer_strategies"][strategy]
            user = public + "\n\n" + modules["bluffer_access_notice"]
        if extra:
            system += "\n\n" + extra
    return {"messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}


def audit(dataset=DATASET, require_complete=True):
    errors, worlds = [], []
    for path in sorted((dataset / "worlds").glob("NL*.json")):
        try:
            world = read_json(path)
            errors.extend(f"{path.name}: {error}" for error in validate_world(world, path.name))
            worlds.append(world)
        except (ValueError, TypeError, KeyError) as exc:
            errors.append(f"{path.name}: {type(exc).__name__}: {exc}")
    if require_complete and {w.get("world_id") for w in worlds} != {f"NL{i:03d}" for i in range(1, 25)}:
        errors.append("expected exactly NL001–NL024")
    families = [w.get("family_id") for w in worlds]
    if len(families) != len(set(families)):
        errors.append("duplicate family_id in this development batch")
    sources = [text_digest(w.get("source_text", "")) for w in worlds]
    if len(sources) != len(set(sources)):
        errors.append("duplicate source text")
    domain_counts = Counter(w.get("domain") for w in worlds)
    if require_complete and dict(domain_counts) != {domain: 3 for domain in DOMAINS}:
        errors.append("expected three worlds per domain")
    modules = read_json(dataset / "PROMPT_MODULES.json")
    config = read_json(dataset / "EXPERIMENT_CONFIG.json")
    errors.extend(validate_config(config))
    projections = 0
    for world in worlds:
        if validate_world(world):
            continue
        variants = [("reader", {"reader_style": style}) for style in modules["reader_styles"]]
        variants += [("bluffer", {"strategy": s}) for s in modules["bluffer_strategies"]]
        variants += [("judge", {"judge_policy": p}) for p in config["judge_policies"]]
        for role, kwargs in variants:
            packet = role_packet(world, role, modules, **kwargs)
            visible = "\n".join(m["content"] for m in packet["messages"])
            has_source = world["source_text"] in visible
            if has_source != (role == "reader"):
                errors.append(f"{world['world_id']}: source routing failure for {role}")
            if world["authoring_note"] in visible or json.dumps(world["evaluation"], ensure_ascii=False) in visible:
                errors.append(f"{world['world_id']}: host metadata routing failure for {role}")
            projections += 1
    counts = Counter()
    for world in worlds:
        for key, rows in world.get("evaluation", {}).items():
            if isinstance(rows, list):
                counts[key] += len(rows)
    word_counts = [word_count(w.get("source_text", "")) for w in worlds]
    public_counts = [word_count(w.get("public_context", "")) for w in worlds]
    summary = {
        "dataset_id": "natural_language_epistemic_games_dev24_20261010",
        "material_status": "DEVELOPMENT_DRAFTS",
        "structural_status": "PASS" if not errors else "FAIL",
        "semantic_status": "AUTHOR_ANNOTATED_REQUIRES_INDEPENDENT_HUMAN_QUALIFICATION",
        "ai_cross_review_report": "SEMANTIC_REVIEW.md",
        "dialogue_collection_status": "NOT_COLLECTED",
        "provider_requests": 0,
        "fine_tuning_runs": 0,
        "world_count": len(worlds),
        "family_id_count": len(set(families)),
        "iid_qualification": False,
        "domain_counts": dict(sorted(domain_counts.items())),
        "source_word_total": sum(word_counts),
        "source_word_range": [min(word_counts, default=0), max(word_counts, default=0)],
        "public_word_range": [min(public_counts, default=0), max(public_counts, default=0)],
        "evaluation_record_counts": dict(counts),
        "initial_role_projection_checks": projections,
        "runtime_router_verified": False,
        "configuration_status": config["status"],
        "errors": errors,
        "warnings": ["No real multi-agent trajectories have been collected.",
                     "Exact source-span matching does not certify semantic support or unspecifiedness.",
                     "Development worlds cannot be relabeled as unseen confirmatory tests after inspection.",
                     "Unique family IDs and balanced domains do not establish independent sampling.",
                     "Provider-default reasoning is not equal internal compute; preflight remains pending."],
    }
    return summary, worlds


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build(dataset=DATASET):
    summary, worlds = audit(dataset)
    if summary["errors"]:
        return summary
    catalog = ["# 开发资料目录", "", "24 个新创作世界；全部 development，不是确认性测试数据或已完成对局。", "",
               "| ID | 领域 | 资料 | Source 词数 |", "|---|---|---|---:|"]
    book = ["# 调查者资料册：开发世界", "", "**Host-only：包含全部私人来源与评估记录。不得整本发送给游戏角色。**", "",
            "所有实体与记录均为虚构。结构校验与原文匹配不等于独立语义资格认证。", ""]
    files = []
    for world in worlds:
        wid = world["world_id"]
        catalog.append(f"| {wid} | {world['domain']} | [{world['title']}](worlds/{wid}.json) | {word_count(world['source_text'])} |")
        book.extend([f"## {wid} — {world['title']}", "", f"领域：{world['domain']}；分组：`{world['family_id']}`。", "",
                     "### 公共背景", "", world["public_context"], "", "### 私人来源", "",
                     f"**{world['source_title']}**", "", world["source_text"], "", "### Host-only 评估记录", ""])
        for group in ("supported_claims", "explicit_negatives", "licensed_inferences"):
            book.extend([f"**{group}**", ""])
            for row in world["evaluation"][group]:
                book.append(f"- `{row['id']}` {row['claim']}")
                if "evidence" in row:
                    for span in row["evidence"]:
                        book.append(f"  - 来源：{span}")
                else:
                    book.append(f"  - 前提：{', '.join(row['premise_ids'])}；{row['rationale']}")
            book.append("")
        book.extend(["**自然缺口与候选前提：不是 Judge 问题菜单**", ""])
        for row in world["evaluation"]["unspecified_probes"]:
            book.extend([f"- `{row['id']}` 中性：{row['neutral_question']}",
                         f"  - 候选前提：{row['presupposition_question']}",
                         f"  - 候选：{row['candidate_claim']}", f"  - 边界：{row['boundary_note']}"])
        book.extend(["", "**跨事实开放问题**", ""])
        for row in world["evaluation"]["consistency_questions"]:
            book.extend([f"- `{row['id']}` {row['question']}",
                         f"  - 关系：{', '.join(row['target_claim_ids'])}；{row['reference_answer']}"])
        book.append("")
        path = dataset / "worlds" / f"{wid}.json"
        files.append({"world_id": wid, "family_id": world["family_id"], "domain": world["domain"],
                      "path": path.relative_to(dataset).as_posix(), "sha256": digest_bytes(path.read_bytes()),
                      "source_sha256": text_digest(world["source_text"]),
                      "public_context_sha256": text_digest(world["public_context"])})
    (dataset / "CATALOG.md").write_text("\n".join(catalog) + "\n", encoding="utf-8")
    (dataset / "CASEBOOK.md").write_text("\n".join(book), encoding="utf-8")
    write_json(dataset / "audit.json", summary)
    bound = {name: digest_bytes((dataset / name).read_bytes()) for name in (
        "AUTHORING.md", "README.md", "DESIGN.md", "SEMANTIC_REVIEW.md", "EXPERIMENT_CONFIG.json", "PROMPT_MODULES.json")}
    write_json(dataset / "manifest.json", {
        "schema_version": "1.0", "dataset_id": summary["dataset_id"],
        "status": "DEVELOPMENT_MATERIAL_SNAPSHOT_NOT_PREREGISTERED_TEST",
        "date": "2026-10-10", "world_count": len(worlds),
        "input_hashes": bound, "worlds": files,
        "builder_path": "scripts/build_natural_language_dataset.py",
        "builder_sha256": digest_bytes(Path(__file__).read_bytes()),
        "provider_requests": 0, "dialogues": 0,
    })
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    audit_parser = commands.add_parser("audit")
    audit_parser.add_argument("--allow-incomplete", action="store_true")
    commands.add_parser("build")
    packet_parser = commands.add_parser("packet")
    packet_parser.add_argument("--world", required=True)
    packet_parser.add_argument("--role", choices=("reader", "bluffer", "judge"), required=True)
    packet_parser.add_argument("--strategy", choices=("matched_access", "strong", "boundary_aware"), default="matched_access")
    packet_parser.add_argument("--reader-style", choices=("matched_access", "source_faithful"), default="matched_access")
    packet_parser.add_argument("--judge-policy", choices=("active", "nonadaptive"), default="active")
    args = parser.parse_args()
    if args.command == "packet":
        if not re.fullmatch(r"NL\d{3}", args.world):
            parser.error("world must be an NLxxx identifier")
        world = read_json(DATASET / "worlds" / f"{args.world}.json")
        errors = validate_world(world)
        if errors:
            raise ValueError("invalid world: " + "; ".join(errors))
        result = role_packet(world, args.role, read_json(DATASET / "PROMPT_MODULES.json"),
                             args.strategy, args.reader_style, args.judge_policy)
    elif args.command == "build":
        result = build()
    else:
        result, _ = audit(require_complete=not args.allow_incomplete)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("errors"):
        sys.exit(1)


if __name__ == "__main__":
    main()
