"""Checks for the two observed failures and source-isolated first-turn routing."""
import unittest
import run_boundary_go_recovery as recovery


class RecoveryTest(unittest.TestCase):
    def test_literal_newline_preserves_answer(self):
        raw = '{"reply":"first paragraph\n\nsecond paragraph"}'
        self.assertEqual(recovery.parse(raw), {'reply': 'first paragraph\n\nsecond paragraph'})
        with self.assertRaises(ValueError):
            recovery.parse('Some prose before {"ready":true}')
        with self.assertRaises(ValueError):
            recovery.parse('')

    def test_reverse_judge_first_private_initialization(self):
        r = {'id': recovery.REVERSE, 'messages': [], 'asks': 0}
        b = {'role_initial_prompts': {recovery.REVERSE: {
            'J': 'PUBLIC ONLY', 'A': 'PRIVATE A\nThere is no opening account. READY',
            'B': 'PRIVATE B\nThere is no opening account. READY'}}}
        self.assertEqual(recovery.next_turn(r, b), ('J', 1, 'PUBLIC ONLY'))
        r['messages'].append({'role': 'J', 'question_index': 1, 'reply': True,
            'parsed': {'action': 'ASK', 'target': 'BOTH', 'question': 'What happened?'}})
        r['asks'] = 1
        role, index, prompt = recovery.next_turn(r, b)
        self.assertEqual((role, index), ('A', 1))
        self.assertIn('PRIVATE A', prompt)
        self.assertNotIn('PRIVATE B', prompt)
        self.assertIn('What happened?', prompt)
        self.assertNotIn('return only {"ready":true}', prompt)


if __name__ == '__main__':
    unittest.main()
