"""Validate authoring materials and render a local reading route; no model calls."""
from pathlib import Path
import argparse
import hashlib
import json

BASE = Path(__file__).resolve().parents[1] / 'naturalistic_study_1'
DOMAINS = {'history_institutions': '历史 / 制度', 'anthropology_social': '人类学 / 社会制度',
           'science_nature': '科学 / 自然', 'math_language': '数学 / 语言'}


def digest(text):
    return hashlib.sha256(text.encode('utf8')).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write-index', action='store_true')
    args = ap.parse_args()
    cases, errors, counts = [], [], {d: 0 for d in DOMAINS}
    paths = sorted((BASE / 'cards').glob('N*.json'))
    expected = {f'N{i:02}' for i in range(1, 13)}
    for p in paths:
        c = json.loads(p.read_text(encoding='utf8'))
        for field in ['case_id', 'domain', 'title', 'public_context', 'source_title', 'source_text', 'analyst_notes']:
            if field not in c:
                errors.append(f'{p.name}: missing {field}')
        if p.stem != c['case_id']:
            errors.append(f'{p.name}: ID mismatch')
        if c['domain'] not in DOMAINS:
            errors.append(f'{p.name}: invalid domain')
        else:
            counts[c['domain']] += 1
        words = len(c['source_text'].split())
        public_words = len(c['public_context'].split())
        if not 200 <= words <= 400:
            errors.append(f'{p.name}: source words {words}')
        if not 45 <= public_words <= 75:
            errors.append(f'{p.name}: public words {public_words}')
        for key in ['core_facts', 'explicit_negations', 'source_boundaries', 'consistency_checks']:
            values = c['analyst_notes'].get(key)
            if not isinstance(values, list) or len(values) < 2 or not all(isinstance(x, str) and x for x in values):
                errors.append(f'{p.name}: inadequate analyst notes {key}')
        for banned in ['ANALYST NOTES', 'source_boundaries', 'informed_seat', 'PRIVATE REFERENCE CARD']:
            if banned in c['source_text'] or banned in c['public_context']:
                errors.append(f'{p.name}: role/analysis field leaked into source')
        cases.append(c)
    if {c['case_id'] for c in cases} != expected or len(cases) != 12:
        errors.append('Expected exactly N01–N12')
    if any(n != 3 for n in counts.values()):
        errors.append('Expected three cases per domain')
    if len({c['title'] for c in cases}) != len(cases):
        errors.append('Duplicate titles')
    report = {'state': 'MATERIALS_DRAFT', 'experimental_model_calls': 0, 'cases': len(cases), 'domain_counts': counts,
              'word_count_convention': 'Whitespace-separated English tokens; source excludes title and analyst notes.',
              'errors': errors, 'checks': [dict(case_id=c['case_id'], source_words=len(c['source_text'].split()),
                                            public_words=len(c['public_context'].split()),
                                            source_sha256=digest(c['source_text']), public_sha256=digest(c['public_context'])) for c in cases],
              'limits': 'Structural checks do not establish scientific realism, source/explanation consistency of future responses, difficulty matching or absence of stylistic cues. These are draft materials, not experimental evidence.'}
    if errors:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    if args.write_index:
        (BASE / 'materials_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        inventory = ['# 12 题总览', '', '状态：材料草案；尚未执行模型实验。每题双方看同一份公开介绍，仅 Knower 看完整 source。', '',
                     '| ID | 领域 | 实体 / 资料 | source 词数 |', '|---|---|---|---:|']
        book = ['# Naturalistic Study 1 — investigator source book', '',
                'Draft materials. Contains private sources: investigators only. Do not send this book or the full JSON files to game roles. Analyst notes remain in the individual JSON files and are not part of the source.', '']
        for c in cases:
            inventory.append(f"| [{c['case_id']}](cards/{c['case_id']}.json) | {DOMAINS[c['domain']]} | {c['title']} | {len(c['source_text'].split())} |")
            book += [f"## {c['case_id']} — {c['title']}", '', '### Shared public context', '', c['public_context'], '',
                     f"### Private source: {c['source_title']}", '', c['source_text'], '']
        (BASE / 'INVENTORY.md').write_text('\n'.join(inventory) + '\n', encoding='utf8')
        (BASE / 'CASEBOOK.md').write_text('\n'.join(book) + '\n', encoding='utf8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
