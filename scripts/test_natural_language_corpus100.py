"""Offline safeguards for source provenance, world counting and role privacy."""
from __future__ import annotations

from copy import deepcopy
import json
import unittest

import build_natural_language_corpus100 as corpus
import build_natural_language_dataset as development


class CorpusSafeguards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory_path = corpus.DATASET / "LEGACY_INVENTORY.json"
        cls.inventory = corpus.read_json(cls.inventory_path)

    def test_all_legacy_canonical_and_variant_texts_match_original_artifacts(self):
        checked = 0
        for row in self.inventory["worlds"]:
            for variant in [row] + row["variants"]:
                self.assertEqual(corpus.reference_value(variant["source_reference"]), variant["source_text"])
                checked += 1
        self.assertEqual(checked, 42)

    def test_counterfactual_and_counterfeit_sources_do_not_add_worlds(self):
        self.assertEqual(len(self.inventory["worlds"]), 30)
        self.assertEqual(sum(len(row["variants"]) for row in self.inventory["worlds"]), 12)
        self.assertEqual(len({row["legacy_id"] for row in self.inventory["worlds"]}), 30)

    def test_original_development_snapshot_is_preserved(self):
        manifest = corpus.read_json(corpus.DEV / "manifest.json")
        for row in manifest["worlds"]:
            self.assertEqual(corpus.sha(corpus.DEV / row["path"]), row["sha256"])
        self.assertEqual(len(manifest["worlds"]), 24)

    def test_source_references_cannot_escape_repository(self):
        with self.assertRaises(ValueError):
            corpus.repository_path("../outside.json")

    def test_unrecognized_reference_expression_is_rejected(self):
        reference = dict(self.inventory["worlds"][0]["source_reference"])
        reference["json_key"] = "source_text[malformed]"
        with self.assertRaises(ValueError):
            corpus.reference_value(reference)

    def test_new_sources_cannot_be_silently_promoted_or_marked_development(self):
        world = deepcopy(corpus.read_json(corpus.DEV / "worlds/NL001.json"))
        world["split"] = "confirmatory_test"
        world["domain"] = "agriculture_food"
        self.assertIn("new source must be candidate_test", corpus.validate_new(world, "NL001.json"))

    def test_legacy_variants_and_provenance_never_enter_initial_role_messages(self):
        row = corpus.legacy_record(self.inventory["worlds"][0], 71, self.inventory_path)
        row["source_text"] = "PRIVATE_CANONICAL_SOURCE_CANARY"
        row["source_variants"] = [{"source_text": "PRIVATE_VARIANT_CANARY"}]
        row["authoring_note"] = "HOST_PROVENANCE_CANARY"
        row["material_reference"] = "HOST_PATH_CANARY"
        row["evaluation"] = {"answer": "HOST_ORACLE_CANARY"}
        row["legacy_evaluation"] = {"answer": "HOST_RAW_ANNOTATION_CANARY"}
        row["title"] = "HOST_CATALOG_TITLE_CANARY"
        for role in ("reader", "bluffer", "judge"):
            visible = json.dumps(corpus.role_packet(row, role, corpus.common_modules()))
            self.assertNotIn("PRIVATE_VARIANT_CANARY", visible)
            self.assertNotIn("HOST_", visible)
            self.assertEqual("PRIVATE_CANONICAL_SOURCE_CANARY" in visible, role == "reader")

    def test_common_config_is_the_same_reciprocal_config(self):
        plan = corpus.read_json(corpus.DATASET / "CORPUS_PLAN.json")
        config = corpus.read_json(corpus.repository_path(plan["common_config_path"]))
        self.assertEqual(development.validate_config(config), [])
        self.assertEqual(corpus.repository_path(plan["common_config_path"]), corpus.DEV / "EXPERIMENT_CONFIG.json")
        self.assertFalse(plan["dispatch_authorized_by_this_file"])


if __name__ == "__main__":
    unittest.main()
