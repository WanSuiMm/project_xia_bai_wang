"""Small offline invariants for the frozen OSI48 design and parser boundary."""
from __future__ import annotations

from collections import defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
import io
import json
from pathlib import Path
import tempfile
import unittest

import analyze_opponent_strategy_inference as analyzer
import run_joint_epistemic_supplement as formatting
import run_opponent_strategy_inference as study


class OracleTest(unittest.TestCase):
    def test_exact_history_oracle_and_seat_complement(self):
        expected_ones = {1: Fraction(66, 67), 4: Fraction(1, 2), 7: Fraction(1, 67)}
        for s, expected in expected_ones.items():
            with self.subTest(history_ones=s):
                a = study.oracle(s, "PERSISTENT", "A")
                b = study.oracle(s, "PERSISTENT", "B")
                self.assertEqual(a["posterior_A_exact"], str(expected))
                self.assertEqual(b["posterior_A_exact"], str(1 - expected))
                self.assertEqual(a["posterior_1111"], float(expected))
                self.assertAlmostEqual(a["posterior_A"] + b["posterior_A"], 1.0, places=15)

                refreshed_a = study.oracle(s, "REFRESHED", "A")
                refreshed_b = study.oracle(s, "REFRESHED", "B")
                self.assertEqual(refreshed_a["posterior_A_exact"], "1/2")
                self.assertEqual(refreshed_b["posterior_A_exact"], "1/2")
                self.assertEqual(refreshed_a["posterior_1111"], 0.5)


class FrozenDesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = study.schedule()
        cls.modules = study.read(study.DESIGN / "PROMPT_MODULES_20261009.json")
        cls.prompts = {row["request_id"]: study.make_prompt(row, cls.modules) for row in cls.rows}

    def test_schedule_has_48_unique_requests_and_two_independent_repeats(self):
        self.assertEqual(len(self.rows), 48)
        self.assertEqual(len({row["request_id"] for row in self.rows}), 48)
        slots = defaultdict(list)
        for row in self.rows:
            key = (row["model"], row["simulation_condition"], row["history_ones"], row["ones_seat"])
            slots[key].append(row["repeat"])
        self.assertEqual(len(slots), 2 * 2 * 3 * 2)
        self.assertTrue(all(sorted(repeats) == [1, 2] for repeats in slots.values()))

    def test_12_visible_prompts_are_byte_identical_across_models_and_repeats(self):
        by_prompt = defaultdict(list)
        for row in self.rows:
            by_prompt[self.prompts[row["request_id"]]].append(row)
        self.assertEqual(len(by_prompt), 12)
        for index, (prompt, rows) in enumerate(by_prompt.items()):
            with self.subTest(prompt_index=index):
                self.assertEqual(len(rows), 4)
                for model in study.MODELS:
                    self.assertEqual(
                        {row["repeat"] for row in rows if row["model"] == model}, {1, 2}
                    )
                for repeat in (1, 2):
                    self.assertEqual(
                        {row["model"] for row in rows if row["repeat"] == repeat},
                        set(study.MODELS),
                    )
                self.assertEqual(
                    len({(r["simulation_condition"], r["history_ones"], r["ones_seat"]) for r in rows}),
                    1,
                )

    def test_prompts_exclude_oracle_and_host_schedule_fields(self):
        private_names = (
            "posterior_A", "posterior_A_exact", "posterior_1111", "plugin_posterior_A",
            "schedule_index", "request_id", "history_ones", "prompt_path", "repeat",
        )
        private_values = (
            "66/67", "65/67", "1/67", "0.9961089494", "OSI_GLM_", "OSI_QWEN_",
            "glm-5.3", "qwen3.8-max", "UNKNOWN_PARAMETER_KNOWN_FAMILY",
        )
        for row in self.rows:
            prompt = self.prompts[row["request_id"]]
            for token in private_names + private_values:
                with self.subTest(request_id=row["request_id"], token=token):
                    self.assertNotIn(token, prompt)


class CompletionFormatTest(unittest.TestCase):
    def test_only_exact_redundant_trailer_is_accepted(self):
        parsed = {"p_A": 0.5, "decision": "ABSTAIN", "reason": "The evidence is balanced."}
        body = json.dumps(parsed, separators=(",", ":"))
        trailer = (
            "\n<|assistant|>_p_A:0.5\n"
            "decision:ABSTAIN\n"
            "reason:The evidence is balanced._"
        )
        accepted, status, exception = formatting.parse_completion(body + trailer, "stop")
        self.assertEqual((accepted, status, exception), (parsed, "valid", "identical_duplicate_trailer"))

        conflicting = trailer.replace("p_A:0.5", "p_A:0.6")
        rejected, reject_status, reject_exception = formatting.parse_completion(body + conflicting, "stop")
        self.assertIsNone(rejected)
        self.assertEqual(reject_status, "invalid_response")
        self.assertIsNone(reject_exception)


class AnalyzerFixtureTest(unittest.TestCase):
    def test_perfect_fixture_and_missing_cell_are_not_renormalized(self):
        with tempfile.TemporaryDirectory(prefix="osi48-offline-fixture-", dir=study.BASE / "runs") as temp:
            run = Path(temp) / "run"
            with redirect_stdout(io.StringIO()):
                study.prepare(run)

            for row in study.schedule():
                rid = row["request_id"]
                prompt_sha = study.sha(run / row["prompt_path"])
                parsed = {
                    "p_A": row["posterior_A"],
                    "decision": analyzer.action(row["posterior_A"]),
                    "reason": "The supplied sampling rules determine this posterior.",
                }
                visible = json.dumps(parsed, separators=(",", ":"))
                strict_value, strict_status = study.api.parse_response(visible, "stop")
                completion_value, completion_status, acceptance = formatting.parse_completion(visible, "stop")

                study.dump(run / f"dispatches/{rid}.json", row | {
                    "prompt_sha256": prompt_sha, "dispatched_utc": study.now(),
                })
                study.dump(run / f"prompt_receipts/{rid}.json", {
                    "request_id": rid, "prompt_sha256": prompt_sha, "created_utc": study.now(),
                })
                study.dump(run / f"responses/{rid}.json", {
                    **{key: row[key] for key in (
                        "request_id", "model", "kind", "case_id", "simulation_condition",
                        "bluffer_condition", "judge_condition",
                    )},
                    "status": "response_received", "http_status": 200,
                    "returned_model": row["model"], "prompt_sha256": prompt_sha,
                    "visible_text": visible, "finish_reason": "stop", "usage": {},
                    "parsed": strict_value, "parse_status": strict_status,
                    "completion_parsed": completion_value,
                    "completion_parse_status": completion_status,
                    "format_acceptance": acceptance,
                })

            study.status(run, "COMPLETE_48_ATTEMPTED")
            complete = analyzer.analyze(run, write=False)
            self.assertEqual((complete["completion"], complete["valid"], complete["strict_valid"]),
                             ("COMPLETE_VALID", 48, 48))
            self.assertEqual((complete["invalid"], complete["missing"]), (0, 0))
            self.assertTrue(all(cell["complete"] and cell["valid"] == 12 for cell in complete["cells"]))
            self.assertTrue(all(cell["posterior_mse"] == 0 for cell in complete["cells"]))
            self.assertTrue(all(abs(item["interaction"] - 65 / 67) < 1e-14
                                for item in complete["contrasts"]))

            missing_row = next(row for row in study.schedule()
                               if row["model"] == study.MODELS[0]
                               and row["simulation_condition"] == "PERSISTENT"
                               and row["history_ones"] == 1
                               and row["ones_seat"] == "A"
                               and row["repeat"] == 1)
            rid = missing_row["request_id"]
            for folder in ("responses", "dispatches", "prompt_receipts"):
                (run / f"{folder}/{rid}.json").unlink()

            partial = analyzer.analyze(run, write=False)
            self.assertEqual((partial["completion"], partial["valid"], partial["missing"]),
                             ("INCOMPLETE", 47, 1))
            affected = next(cell for cell in partial["cells"]
                            if cell["model"] == study.MODELS[0]
                            and cell["simulation_condition"] == "PERSISTENT")
            self.assertEqual((affected["complete"], affected["valid"], affected["posterior_mse"]),
                             (False, 11, None))
            self.assertIsNone(affected["history_delta"])
            affected_contrast = next(item for item in partial["contrasts"]
                                     if item["model"] == study.MODELS[0])
            self.assertFalse(affected_contrast["complete"])
            self.assertIsNone(affected_contrast["interaction"])
            unaffected = next(cell for cell in partial["cells"]
                              if cell["model"] == study.MODELS[1]
                              and cell["simulation_condition"] == "PERSISTENT")
            self.assertTrue(unaffected["complete"])
            self.assertEqual(unaffected["posterior_mse"], 0)


if __name__ == "__main__":
    unittest.main()
