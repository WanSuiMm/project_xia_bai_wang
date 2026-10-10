"""Offline source-world corpus assembly; no network, credentials or dispatch."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

import build_natural_language_dataset as development

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "datasets/natural_language_epistemic_games/curated100_20261010"
DEV = development.DATASET
NEW_DOMAINS = {
    "agriculture_food", "business_operations", "music_performance",
    "education_learning", "geography_navigation", "technology_archives",
    "public_services", "transport_logistics", "media_craft", "sport_leisure",
    "housing_design",
}
LEGACY_DOMAINS = {
    "N01": "civic_institutions", "N02": "civic_institutions", "N03": "archaeology_conservation",
    "N04": "ethnography_social", "N05": "ethnography_social", "N06": "ethnography_social",
    "N07": "ecology_fieldwork", "N08": "ecology_fieldwork", "N09": "materials_engineering",
    "N10": "mathematics_practice", "N11": "linguistics_fieldwork", "N12": "linguistics_fieldwork",
    "S01": "civic_institutions", "S02": "ecology_fieldwork",
    "EB01": "materials_engineering", "EB02": "civic_institutions", "EB03": "ecology_fieldwork",
    "EB04": "archaeology_conservation", "EB05": "civic_institutions", "EB06": "ecology_fieldwork",
    "SQ01": "civic_institutions", "SQ02": "ecology_fieldwork", "SQ03": "materials_engineering",
    "SQ04": "linguistics_fieldwork", "CS01": "civic_institutions", "CS02": "civic_institutions",
    "CS03": "ecology_fieldwork", "CS04": "materials_engineering", "CS05": "linguistics_fieldwork",
    "CS06": "mathematics_practice",
}


def read_json(path):
    return development.read_json(path)


def sha(path):
    return development.digest_bytes(Path(path).read_bytes())


def repository_path(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("reference escapes repository")
    return path


def reference_value(reference):
    """Resolve the limited original JSON locations recorded in the legacy inventory."""
    value = read_json(repository_path(reference["path"]))
    expression = reference["json_key"]
    token_pattern = r"([A-Za-z_][A-Za-z0-9_]*)|\[(\d+)\]|\[case_id=([^\]]+)\]"
    matches = list(re.finditer(token_pattern, expression))
    if re.sub(token_pattern, "", expression).replace(".", ""):
        raise ValueError("unsupported inventory reference expression")
    for match in matches:
        key, index, case_id = match.groups()
        if key is not None:
            value = value[key]
        elif index is not None:
            value = value[int(index)]
        else:
            candidates = [row for row in value if row.get("case_id") == case_id]
            if len(candidates) != 1:
                raise ValueError("ambiguous/missing original case")
            value = candidates[0]
    return value


def validate_new(world, filename):
    # Reuse the exact content checks without changing the frozen dev24 builder.
    shadow = dict(world)
    shadow["split"] = "development"
    shadow["domain"] = "civic_institutions"
    errors = development.validate_world(shadow, filename)
    if world.get("split") != "candidate_test":
        errors.append("new source must be candidate_test")
    if world.get("domain") not in NEW_DOMAINS:
        errors.append("unknown new-material domain")
    return errors


def common_modules():
    return read_json(DEV / "PROMPT_MODULES.json")


def role_packet(world, role, modules, strategy="matched_access", reader_style="matched_access", judge_policy="active"):
    # Catalog titles are host labels and can summarize a private finding.
    visible_world = dict(world)
    visible_world["title"] = "Fictional source dossier"
    return development.role_packet(visible_world, role, modules, strategy, reader_style, judge_policy)


def new_record(world, source_path, origin):
    record = dict(world)
    record.update({
        "corpus_id": f"CW{int(world['world_id'][2:]):03d}",
        "origin": origin,
        "material_reference": source_path.relative_to(ROOT).as_posix(),
        "material_sha256": sha(source_path),
        "source_variants": [],
        "annotation_status": "STRUCTURED_AUTHOR_ANNOTATIONS_NOT_HUMAN_QUALIFIED",
        "source_world_lineage": world["family_id"],
    })
    return record


def legacy_record(row, ordinal, inventory_path):
    parent_reference = dict(row["source_reference"])
    expression = parent_reference["json_key"]
    parent_reference["json_key"] = expression.rsplit(".", 1)[0] if "." in expression else ""
    original_node = reference_value(parent_reference)
    legacy_annotation_keys = ("analyst_notes", "host_map", "questions", "question", "gold_answer",
                              "insertion_sentence", "addition_sentence", "omission_check")
    original_annotations = {key: original_node[key] for key in legacy_annotation_keys if key in original_node}
    return {
        "corpus_id": f"CW{ordinal:03d}", "world_id": row["legacy_id"],
        "family_id": row["legacy_id"].lower(), "source_world_lineage": row["legacy_id"],
        "origin": "legacy_exploratory", "split": "exploratory_only",
        "language": "en", "synthetic": True, "domain": LEGACY_DOMAINS[row["original_ids"][0]],
        "original_domain": row["domain"],
        "title": row["title"], "source_title": row["title"],
        "public_context": row["public_context"], "source_text": row["source_text"],
        "source_variants": row["variants"], "original_ids": row["original_ids"],
        "material_reference": inventory_path.relative_to(ROOT).as_posix(),
        "material_sha256": sha(inventory_path), "source_reference": row["source_reference"],
        "evaluation": None, "authoring_note": (row["family_notes"] if isinstance(row["family_notes"], str)
                                                 else "; ".join(row["family_notes"])),
        "annotation_status": "LEGACY_ANNOTATION_NORMALIZATION_PENDING",
        "legacy_evaluation": original_annotations or None,
        "legacy_evaluation_reference": parent_reference,
        "legacy_evaluation_interpretation": "Original-format host notes only. Counterfactual insertion answers apply to the inserted version, not automatically to the canonical omission version.",
        "public_context_policy": "PRESERVED_ORIGINAL",
        "canonical_source_interpretation": "Representative source within this legacy case; not a historical target-identity assertion.",
    }


def collect(require_complete=True):
    errors, records = [], []
    plan = read_json(DATASET / "CORPUS_PLAN.json")
    if plan.get("user_selected_total_worlds") != 100 or plan.get("composition") != {
            "legacy_exploratory": 30, "existing_development": 24, "new_candidate_test": 46}:
        errors.append("unexpected selected corpus size/composition")
    if plan.get("dispatch_authorized_by_this_file") is not False:
        errors.append("corpus plan must not authorize paid dispatch")
    dev_manifest = read_json(DEV / "manifest.json")
    expected_dev_hashes = {w["world_id"]: w["sha256"] for w in dev_manifest["worlds"]}
    for path in sorted((DEV / "worlds").glob("NL*.json")):
        world = read_json(path)
        errors.extend(f"{path.name}: {e}" for e in development.validate_world(world, path.name))
        if sha(path) != expected_dev_hashes.get(world["world_id"]):
            errors.append(f"{path.name}: original development snapshot changed")
        records.append(new_record(world, path, "existing_development"))
    new_paths = sorted((DATASET / "new_worlds").glob("NL*.json"))
    if require_complete and {p.stem for p in new_paths} != {f"NL{i:03d}" for i in range(25, 71)}:
        errors.append("expected exactly new sources NL025–NL070")
    for path in new_paths:
        try:
            world = read_json(path)
        except (ValueError, OSError) as exc:
            errors.append(f"{path.name}: invalid JSON ({type(exc).__name__})")
            continue
        world_errors = validate_new(world, path.name)
        errors.extend(f"{path.name}: {e}" for e in world_errors)
        if world_errors:
            continue
        records.append(new_record(world, path, "new_candidate_test"))
    inventory_path = DATASET / "LEGACY_INVENTORY.json"
    inventory = read_json(inventory_path)
    legacy = inventory["worlds"]
    if len(legacy) != 30 or inventory.get("world_count") != 30:
        errors.append("expected thirty legacy source lineages")
    for ordinal, row in enumerate(legacy, start=71):
        if row.get("status") != "exploratory_only":
            errors.append(f"{row['legacy_id']}: historical source was promoted to test")
        for material in [row] + row["variants"]:
            try:
                original = reference_value(material["source_reference"])
                if original != material["source_text"]:
                    errors.append(f"{row['legacy_id']}: copied source differs from original")
            except (ValueError, KeyError, TypeError, IndexError, OSError) as exc:
                errors.append(f"{row['legacy_id']}: source reference {type(exc).__name__}")
        if not row["public_context"].strip() or development.word_count(row["source_text"]) < 150:
            errors.append(f"{row['legacy_id']}: missing/very short original material")
        records.append(legacy_record(row, ordinal, inventory_path))
    if len({r["corpus_id"] for r in records}) != len(records):
        errors.append("duplicate corpus identifier")
    if len({r["source_world_lineage"] for r in records}) != len(records):
        errors.append("duplicate declared source lineage")
    fingerprints = {}
    for row in records:
        normalized = re.sub(r"\s+", " ", row["source_text"]).strip().casefold()
        previous = fingerprints.setdefault(normalized, row["corpus_id"])
        if previous != row["corpus_id"]:
            errors.append(f"duplicate canonical source: {previous}/{row['corpus_id']}")
    if require_complete and len(records) != 100:
        errors.append("expected one hundred source worlds")
    config = read_json(DEV / "EXPERIMENT_CONFIG.json")
    errors.extend(development.validate_config(config))
    modules = common_modules()
    projections = 0
    for world in records:
        variants = [("reader", {"reader_style": s}) for s in modules["reader_styles"]]
        variants += [("bluffer", {"strategy": s}) for s in modules["bluffer_strategies"]]
        variants += [("judge", {"judge_policy": s}) for s in config["judge_policies"]]
        for role, kwargs in variants:
            visible = json.dumps(role_packet(world, role, modules, **kwargs), ensure_ascii=False)
            # Decode messages before searching, so escaped newlines cannot hide source text.
            content = "\n".join(m["content"] for m in json.loads(visible)["messages"])
            if (world["source_text"] in content) != (role == "reader"):
                errors.append(f"{world['corpus_id']}: wrong initial source projection")
            if (world["authoring_note"] and world["authoring_note"] in content) or world["material_reference"] in content:
                errors.append(f"{world['corpus_id']}: initial metadata projection leak")
            projections += 1
    words = [development.word_count(r["source_text"]) for r in records]
    summary = {
        "corpus_id": plan["corpus_id"], "selected_total": 100,
        "material_status": "CURATED_SOURCE_BANK_NOT_COLLECTED_DIALOGUES",
        "structural_status": "PASS" if not errors else "FAIL",
        "world_count": len(records), "composition": dict(Counter(r["origin"] for r in records)),
        "declared_lineages": len({r["source_world_lineage"] for r in records}),
        "independence_established": False, "probability_sample": False,
        "domain_counts": dict(sorted(Counter(r["domain"] for r in records).items())),
        "canonical_source_word_total": sum(words),
        "canonical_source_word_range": [min(words, default=0), max(words, default=0)],
        "retained_in_family_variants": sum(len(r["source_variants"]) for r in records),
        "structured_annotation_worlds": sum(r["evaluation"] is not None for r in records),
        "legacy_annotation_normalization_pending": sum(r["evaluation"] is None for r in records),
        "legacy_original_format_annotations_preserved": sum(r.get("legacy_evaluation") is not None for r in records if r["origin"] == "legacy_exploratory"),
        "initial_role_projection_checks": projections,
        "catalog_title_visibility": "HOST_ONLY_GENERIC_TOPIC_IN_ROLE_MESSAGES",
        "new_trajectory_count": 0, "provider_requests_in_this_task": 0,
        "runtime_router_verified": False, "provider_preflight": "PENDING",
        "configuration_path": plan["common_config_path"], "configuration_sha256": sha(DEV / "EXPERIMENT_CONFIG.json"),
        "prompt_path": plan["common_prompt_path"], "prompt_sha256": sha(DEV / "PROMPT_MODULES.json"),
        "errors": errors,
        "warnings": [
            "One hundred source worlds are not one hundred unseen confirmatory test samples.",
            "Declared lineage IDs and literal deduplication do not establish statistical independence.",
            "Legacy full source copies are verified; their annotations remain unnormalized.",
            "Historical endpoints remain separate from any future common-protocol collection.",
            "Initial role projections do not verify a multi-round collection runner.",
            "Provider-default reasoning does not guarantee equal internal compute.",
        ],
    }
    return summary, sorted(records, key=lambda r: r["corpus_id"])


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build():
    summary, records = collect()
    if summary["errors"]:
        return summary
    lines = ["# 100 个来源世界目录", "", "30 旧来源 + 24 已有开发来源 + 46 新候选来源；计数不包含同世界版本、重复或对局。", "",
             "新对话尚未采集。world lineage 不等于已认证的统计独立样本。", "",
             "| Corpus ID | 原 ID | 来源组 | 领域 | 资料 | 词数 | 标注状态 |", "|---|---|---|---|---|---:|---|"]
    for row in records:
        relative = Path(row["material_reference"]).relative_to("datasets/natural_language_epistemic_games")
        link = "../" + relative.as_posix()
        status = "新schema" if row["evaluation"] is not None else "旧标注待规范"
        lines.append(f"| {row['corpus_id']} | {row['world_id']} | {row['origin']} | {row['domain']} | [{row['title']}]({link}) | {development.word_count(row['source_text'])} | {status} |")
    (DATASET / "CATALOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (DATASET / "worlds.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for row in records:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_json(DATASET / "audit.json", summary)
    inputs = [DATASET / name for name in ("AUTHORING.md", "README.md", "CORPUS_PLAN.json", "LEGACY_INVENTORY.json", "LEGACY_INVENTORY.md", "MATERIAL_REVIEW.md")]
    inputs += [DEV / "EXPERIMENT_CONFIG.json", DEV / "PROMPT_MODULES.json", ROOT / "scripts/build_natural_language_dataset.py", Path(__file__)]
    inputs += sorted((DATASET / "new_worlds").glob("NL*.json")) + sorted((DEV / "worlds").glob("NL*.json"))
    for legacy in read_json(DATASET / "LEGACY_INVENTORY.json")["worlds"]:
        for item in [legacy] + legacy["variants"]:
            inputs.append(repository_path(item["source_reference"]["path"]))
    write_json(DATASET / "manifest.json", {
        "corpus_id": summary["corpus_id"], "date": "2026-10-10", "world_count": len(records),
        "status": "MATERIAL_SNAPSHOT_NOT_PREREGISTERED_COLLECTION",
        "inputs": {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(inputs))},
        "outputs": {name: sha(DATASET / name) for name in ("CATALOG.md", "worlds.jsonl", "audit.json")},
        "worlds": [{"corpus_id": r["corpus_id"], "source_world_lineage": r["source_world_lineage"],
                    "source_sha256": development.text_digest(r["source_text"]), "origin": r["origin"]} for r in records],
        "provider_requests": 0, "new_trajectories": 0,
    })
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    audit_parser = commands.add_parser("audit")
    audit_parser.add_argument("--allow-incomplete", action="store_true")
    commands.add_parser("build")
    packet = commands.add_parser("packet")
    packet.add_argument("--world", required=True)
    packet.add_argument("--role", choices=("reader", "bluffer", "judge"), required=True)
    packet.add_argument("--strategy", choices=("matched_access", "strong", "boundary_aware"), default="matched_access")
    packet.add_argument("--reader-style", choices=("matched_access", "source_faithful"), default="matched_access")
    packet.add_argument("--judge-policy", choices=("active", "nonadaptive"), default="active")
    args = parser.parse_args()
    if args.command == "build":
        result = build()
    else:
        summary, records = collect(require_complete=not getattr(args, "allow_incomplete", False))
        if args.command == "packet":
            if summary["errors"]:
                result = summary
            else:
                selected = [r for r in records if r["corpus_id"] == args.world]
                if len(selected) != 1:
                    parser.error("unknown corpus world")
                result = role_packet(selected[0], args.role, common_modules(), args.strategy, args.reader_style, args.judge_policy)
        else:
            result = summary
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("errors"):
        sys.exit(1)


if __name__ == "__main__":
    main()
