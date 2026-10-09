"""Offline checks for the narrow OSI48 envelope-handling repair."""
import unittest

import run_opponent_strategy_completion as completion


class EnvelopeTests(unittest.TestCase):
    def packet(self, content, finish="stop"):
        return {"model": "glm-5.3", "usage": {"completion_tokens": 4096},
                "choices": [{"finish_reason": finish, "message": {"content": content,
                              "reasoning_content": "This private field must never be retained."}}]}

    def test_null_content_at_limit_is_received_truncation(self):
        meta, diag = completion.decode_envelope(self.packet(None, "length"), "chat/completions")
        self.assertEqual(meta["finish_reason"], "length")
        self.assertEqual(meta["visible_text"], "")
        self.assertTrue(diag["null_content_at_token_limit"])
        self.assertEqual(completion.study.api.parse_response("", "length")[1], "truncated")
        self.assertNotIn("private field", str(meta) + str(diag))

    def test_bad_content_keeps_finish_and_usage(self):
        meta, diag = completion.decode_envelope(self.packet(None), "chat/completions")
        self.assertEqual(diag["failure_stage"], "message_content")
        self.assertEqual(meta["returned_model"], "glm-5.3")
        self.assertEqual(meta["usage"], {"completion_tokens": 4096})
        self.assertEqual(meta["finish_reason"], "stop")

    def test_text_blocks_only(self):
        meta, diag = completion.decode_envelope(self.packet([
            {"type": "text", "text": "a"}, {"type": "text", "text": "b"}]), "chat/completions")
        self.assertEqual(meta["visible_text"], "ab")
        self.assertIsNone(diag["failure_stage"])
        _, diag = completion.decode_envelope(self.packet([
            {"type": "thinking", "text": "private"}]), "chat/completions")
        self.assertEqual(diag["failure_stage"], "message_content")

    def test_missing_finish_is_not_invented(self):
        meta, diag = completion.decode_envelope(self.packet("{}", None), "chat/completions")
        self.assertEqual(diag["failure_stage"], "finish_reason")
        self.assertIsNone(meta["finish_reason"])

    def test_selection_preserves_valid_slots(self):
        retained, pending = completion.selection()
        self.assertEqual([r["schedule_index"] for r in retained], [1, 2])
        self.assertEqual([r["schedule_index"] for r in pending], list(range(3, 49)))


if __name__ == "__main__":
    unittest.main()
