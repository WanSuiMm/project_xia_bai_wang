"""Decision-relevant offline checks for role privacy and dataset/config safety."""
from __future__ import annotations

from copy import deepcopy
import json
import unittest

import build_natural_language_dataset as dataset


class RolePrivacyTests(unittest.TestCase):
    def setUp(self):
        self.modules = dataset.read_json(dataset.DATASET / "PROMPT_MODULES.json")
        self.world = {
            "title": "Public topic", "public_context": "Shared general background.",
            "source_title": "Private source", "source_text": "PRIVATE_SOURCE_CANARY_731",
            "evaluation": {"secret_answer": "HOST_ONLY_ORACLE_CANARY_928"},
            "family_id": "HOST_ONLY_FAMILY_CANARY_427", "authoring_note": "HOST_ONLY_AUTHOR_CANARY_821",
        }

    def test_reader_receives_source_but_never_host_annotations(self):
        for style in self.modules["reader_styles"]:
            text = json.dumps(dataset.role_packet(self.world, "reader", self.modules, reader_style=style))
            self.assertIn("PRIVATE_SOURCE_CANARY_731", text)
            self.assertNotIn("HOST_ONLY_", text)

    def test_no_bluffer_strategy_receives_source_or_oracle(self):
        for strategy in self.modules["bluffer_strategies"]:
            text = json.dumps(dataset.role_packet(self.world, "bluffer", self.modules, strategy=strategy))
            self.assertNotIn("PRIVATE_SOURCE_CANARY_731", text)
            self.assertNotIn("HOST_ONLY_", text)

    def test_no_judge_policy_receives_source_or_oracle(self):
        for policy in ("active", "nonadaptive"):
            text = json.dumps(dataset.role_packet(self.world, "judge", self.modules, judge_policy=policy))
            self.assertNotIn("PRIVATE_SOURCE_CANARY_731", text)
            self.assertNotIn("HOST_ONLY_", text)

    def test_matched_access_uses_identical_speaker_system_instruction(self):
        reader = dataset.role_packet(self.world, "reader", self.modules)
        bluffer = dataset.role_packet(self.world, "bluffer", self.modules)
        self.assertEqual(reader["messages"][0], bluffer["messages"][0])

    def test_unknown_conditions_are_rejected(self):
        for kwargs in ({"strategy": "invented"}, {"reader_style": "invented"}, {"judge_policy": "invented"}):
            with self.assertRaises(ValueError):
                dataset.role_packet(self.world, "judge", self.modules, **kwargs)


class ConfigSafetyTests(unittest.TestCase):
    def setUp(self):
        self.config = dataset.read_json(dataset.DATASET / "EXPERIMENT_CONFIG.json")

    def test_reciprocal_config_has_no_historical_low_effort_override(self):
        self.assertEqual(dataset.validate_config(self.config), [])
        altered = deepcopy(self.config)
        altered["shared_requested_generation"]["explicit_reasoning_effort"] = "low"
        self.assertTrue(dataset.validate_config(altered))

    def test_cross_model_speaker_mismatch_is_rejected(self):
        altered = deepcopy(self.config)
        altered["arms"][0]["bluffer_model"] = "glm-5.3"
        self.assertTrue(dataset.validate_config(altered))

    def test_adapter_cannot_restore_an_asymmetric_reasoning_override(self):
        altered = deepcopy(self.config)
        altered["provider_adapters"]["glm-5.3"]["reasoning_fields"] = "reasoning_effort=low"
        self.assertTrue(dataset.validate_config(altered))

    def test_shared_speaker_session_is_rejected(self):
        altered = deepcopy(self.config)
        altered["roles"]["independent_sessions"] = False
        self.assertTrue(dataset.validate_config(altered))

    def test_dispatch_and_budget_censoring_cannot_be_silently_reclassified(self):
        altered = deepcopy(self.config)
        altered["dispatch_authorized_by_this_file"] = True
        altered["stopping"]["guard_is_voluntary_stop_or_abstention"] = True
        self.assertGreaterEqual(len(dataset.validate_config(altered)), 2)

    def test_duplicate_json_key_is_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"source_text":"first","source_text":"second"}', object_pairs_hook=dataset.no_duplicate_keys)


if __name__ == "__main__":
    unittest.main()
