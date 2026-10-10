"""Verify the published source bank offline, without credentials or regeneration."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import build_natural_language_corpus100 as corpus

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "datasets/natural_language_epistemic_games"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    errors = []
    publication = read(BASE / "publication_manifest_20261010.json")
    for relative, expected in publication["files"].items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            errors.append(f"missing/outside repository: {relative}")
        elif digest(path) != expected:
            errors.append(f"publication hash: {relative}")
    material = read(corpus.DATASET / "manifest.json")
    for relative, expected in material["inputs"].items():
        if digest(ROOT / relative) != expected:
            errors.append(f"material input hash: {relative}")
    for name, expected in material["outputs"].items():
        if digest(corpus.DATASET / name) != expected:
            errors.append(f"material output hash: {name}")
    development = read(corpus.DEV / "manifest.json")
    for relative, expected in development["input_hashes"].items():
        if digest(corpus.DEV / relative) != expected:
            errors.append(f"development input hash: {relative}")
    if digest(ROOT / development["builder_path"]) != development["builder_sha256"]:
        errors.append("development builder hash")
    summary, rows = corpus.collect()
    errors.extend(summary["errors"])
    saved = [json.loads(line) for line in (corpus.DATASET / "worlds.jsonl").read_text(encoding="utf-8").splitlines()]
    if saved != rows or read(corpus.DATASET / "audit.json") != summary:
        errors.append("saved corpus/audit differs from offline reconstruction")
    result = {
        "status": "PASS" if not errors else "FAIL",
        "publication_files_verified": len(publication["files"]),
        "world_count": len(rows),
        "initial_role_projection_checks": summary["initial_role_projection_checks"],
        "provider_requests": 0,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(verify())
