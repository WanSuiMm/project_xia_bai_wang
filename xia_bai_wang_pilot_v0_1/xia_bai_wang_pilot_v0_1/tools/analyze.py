#!/usr/bin/env python3
"""Analyze manually recorded XBW pilot logs. Standard library only; no model/network calls."""
from __future__ import annotations
import argparse
import json
import math
import random
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASES = ('P0', 'P1', 'P2', 'P3', 'N', 'E')
HARD_FLAGS = {'private_leak', 'model_identity_leak', 'cross_speaker_leak',
              'tool_use_observed', 'unexpected_model_change', 'question_protocol_breach'}


def parse_object(raw: str) -> dict[str, Any]:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError('missing response')
    text = raw.strip()
    if text.startswith('```'):
        first = text.find('\n')
        if first != -1:
            text = text[first + 1:]
        if text.rstrip().endswith('```'):
            text = text.rstrip()[:-3].strip()
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        a, b = text.find('{'), text.rfind('}')
        if a < 0 or b < a:
            raise ValueError('no JSON object in response') from None
        try:
            value = json.loads(text[a:b + 1])
        except (json.JSONDecodeError, ValueError):
            raise ValueError('malformed JSON; no values imputed') from None
    if not isinstance(value, dict):
        raise ValueError('response is not a JSON object')
    return value


def parse_judge(raw: str) -> dict[str, Any]:
    x = parse_object(raw)
    p = x.get('p_informed_A')
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError('p_informed_A is not a finite probability')
    if x.get('pick') not in ('A', 'B'):
        raise ValueError('pick is not A or B')
    if (p > 0.5 and x['pick'] != 'A') or (p < 0.5 and x['pick'] != 'B'):
        raise ValueError('pick contradicts probability; not repaired')
    if not isinstance(x.get('insufficient_evidence'), bool) or not isinstance(x.get('reason'), str):
        raise ValueError('missing evidence flag or reason')
    return x


def parse_checks(raw: str, case: dict[str, Any]) -> dict[str, str]:
    x = parse_object(raw)
    if not isinstance(x.get('explanation'), str) or not x['explanation'].strip():
        raise ValueError('missing explanation')
    checks = x.get('checks')
    if not isinstance(checks, dict):
        raise ValueError('missing check commitments')
    for q in case['check_ids']:
        if checks.get(q) not in ('PASS', 'FAIL'):
            raise ValueError('missing or invalid check ' + q)
    return {q: checks[q] for q in case['check_ids']}


def diagnostic(case: dict[str, Any], raw: dict[str, str]) -> dict[str, Any]:
    try:
        checks = {s: parse_checks(raw.get('opening_' + s, ''), case) for s in ('A', 'B')}
    except ValueError as e:
        return {'status': 'unscorable', 'error': str(e)}
    matches = {s: all(checks[s][q] == case['gold'][q] for q in case['check_ids']) for s in ('A', 'B')}
    k = case['informed_seat']
    b = 'B' if k == 'A' else 'A'
    status = 'knower_commitment_error' if not matches[k] else ('collision' if matches[b] else 'distinguishing')
    return {'status': status, 'matches': matches,
            'correct_check_counts': {s: sum(checks[s][q] == case['gold'][q] for q in case['check_ids']) for s in ('A', 'B')}}


def wilson(successes: int, n: int, z: float = 1.959963984540054) -> list[float] | None:
    if n == 0:
        return None
    p = successes / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n))/den
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return [max(0., center-half), min(1., center+half)]


def bootstrap_ci(values: list[float], seed: int = 1352, resamples: int = 10000) -> list[float] | None:
    """Descriptive percentile interval over paired case-level differences, not turns."""
    if len(values) < 2:
        return None
    rng = random.Random(seed)
    n = len(values)
    samples = sorted(sum(values[rng.randrange(n)] for _ in range(n))/n for _ in range(resamples))
    return [samples[int(0.025*(resamples-1))], samples[int(0.975*(resamples-1))]]


def analyze_record(rec: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    raw = rec.get('raw', {})
    if not isinstance(raw, dict):
        raise ValueError(f'{case["case_id"]}: raw must be an object')
    flags = sorted(set(rec.get('issue_flags', [])))
    metadata = rec.get('metadata', {})
    if metadata.get('tools_status') == 'tool_use_observed' and 'tool_use_observed' not in flags:
        flags.append('tool_use_observed')
    points: dict[str, Any] = {}
    for phase in PHASES:
        try:
            x = parse_judge(raw.get('judge_' + phase, ''))
            p = float(x['p_informed_A'])
            y = 1 if case['informed_seat'] == 'A' else 0
            points[phase] = {'valid': True, 'p_A': p, 'p_K': p if y else 1-p,
                             'pick': x['pick'], 'correct': int(x['pick'] == case['informed_seat']),
                             'brier': (p-y)**2, 'confidence': max(p, 1-p),
                             'insufficient_evidence': x['insufficient_evidence'], 'reason': x['reason']}
        except ValueError as e:
            points[phase] = {'valid': False, 'error': str(e)}
    required = ['opening_A', 'opening_B'] + ['judge_' + p for p in PHASES] + [f'answer_{n}_{s}' for n in range(1, 4) for s in ('A', 'B')]
    missing = [k for k in required if not isinstance(raw.get(k), str) or not raw[k].strip()]
    warnings = []
    if any(e.get('type') == 'raw_response_replaced' for e in rec.get('events', []) if isinstance(e, dict)):
        warnings.append('raw response was replaced; inspect preserved before/after event history')
    if not metadata.get('speaker_model') or not metadata.get('judge_model'):
        warnings.append('model identity metadata missing')
    if rec.get('status') == 'completed' and missing:
        warnings.append('marked completed but responses are missing')
    return {'case_id': case['case_id'], 'run_id': rec.get('run_id'), 'config': case['config'],
            'informed_seat': case['informed_seat'], 'status': rec.get('status', 'unknown'),
            'complete_responses': not missing, 'missing_steps': missing,
            'metadata': metadata, 'issue_flags': flags, 'warnings': warnings,
            'clean': not (set(flags) & HARD_FLAGS), 'diagnostic': diagnostic(case, raw),
            'points': points, 'notes': rec.get('notes', '')}


def stage_summary(rows: list[dict[str, Any]], phase: str) -> dict[str, Any]:
    valid = [r['points'][phase] for r in rows if r['points'][phase]['valid']]
    n = len(valid)
    wins = sum(x['correct'] for x in valid)
    return {'attempted_cases': len(rows), 'scorable_n': n, 'unscorable_n': len(rows)-n,
            'correct': wins, 'accuracy': wins/n if n else None, 'wilson_95': wilson(wins, n),
            'mean_brier': statistics.mean(x['brier'] for x in valid) if n else None,
            'mean_confidence': statistics.mean(x['confidence'] for x in valid) if n else None,
            'insufficient_evidence_count': sum(x['insufficient_evidence'] for x in valid)}


def paired_summary(rows: list[dict[str, Any]], before: str, after: str) -> dict[str, Any]:
    pairs = [(r['points'][before], r['points'][after]) for r in rows if r['points'][before]['valid'] and r['points'][after]['valid']]
    delta = [b['correct']-a['correct'] for a,b in pairs]
    return {'before': before, 'after': after, 'paired_n': len(pairs),
            'wrong_to_right': sum(a['correct']==0 and b['correct']==1 for a,b in pairs),
            'right_to_wrong': sum(a['correct']==1 and b['correct']==0 for a,b in pairs),
            'delta_accuracy': statistics.mean(delta) if delta else None,
            'descriptive_paired_bootstrap_95': bootstrap_ci(delta),
            'delta_brier': statistics.mean(b['brier']-a['brier'] for a,b in pairs) if pairs else None,
            'delta_p_K': statistics.mean(b['p_K']-a['p_K'] for a,b in pairs) if pairs else None,
            'case_ids': [r['case_id'] for r in rows if r['points'][before]['valid'] and r['points'][after]['valid']]}


def summarize(rows: list[dict[str, Any]], skipped: list[dict[str, Any]]) -> dict[str, Any]:
    clean = [r for r in rows if r['clean']]
    diag = [r for r in clean if r['diagnostic']['status'] == 'distinguishing']
    return {'protocol_version': '0.1.0', 'main_case_records': len(rows), 'complete_case_records': sum(r['complete_responses'] for r in rows),
            'clean_case_records': len(clean), 'skipped_records': skipped,
            'diagnostic_counts_all': dict(Counter(r['diagnostic']['status'] for r in rows)),
            'diagnostic_counts_clean': dict(Counter(r['diagnostic']['status'] for r in clean)),
            'issue_flag_counts': dict(Counter(flag for r in rows for flag in r['issue_flags'])),
            'all_recorded_stages': {p: stage_summary(rows, p) for p in PHASES},
            'clean_stages': {p: stage_summary(clean, p) for p in PHASES},
            'clean_pairs': {'dialogue_P3_minus_P0': paired_summary(clean, 'P0', 'P3'),
                            'evidence_E_minus_N': paired_summary(clean, 'N', 'E')},
            'distinguishing_clean_subset': {'n': len(diag), 'stages': {p: stage_summary(diag, p) for p in ('N','E')},
                                             'evidence_E_minus_N': paired_summary(diag, 'N', 'E')},
            'by_config_descriptive_not_ranking': {cfg: {'n': len(rr := [r for r in clean if r['config']==cfg]),
                  'speaker_models': sorted({r['metadata'].get('speaker_model','unknown') for r in rr}),
                  'judge_models': sorted({r['metadata'].get('judge_model','unknown') for r in rr}),
                  'stages': {p: stage_summary(rr, p) for p in PHASES}} for cfg in ('R1','R2')},
            'caution': 'Exploratory small sample. Stages are repeated measurements. Lack of information is not a ToM failure. No unseen model results imputed.'}


def load_records(path: Path, cases: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    files = [path] if path.is_file() else sorted(path.glob('*.json'))
    rows, skipped, seen = [], [], {}
    for file in files:
        try:
            obj = json.loads(file.read_text(encoding='utf-8-sig'))
        except (OSError, json.JSONDecodeError) as e:
            raise ValueError(f'Cannot read {file}: {e}') from e
        records = obj.get('records', []) if isinstance(obj, dict) and obj.get('schema_version')=='xbw.pilot.export/0.1' else [obj]
        if not isinstance(records, list):
            raise ValueError(f'{file}: invalid export records')
        for rec in records:
            if not isinstance(rec, dict) or rec.get('schema_version') != 'xbw.pilot.record/0.1':
                raise ValueError(f'{file}: not an XBW record or export. Do not mix analysis outputs into logs.')
            cid = rec.get('case_id')
            if cid not in cases:
                raise ValueError(f'{file}: unknown case {cid}')
            case = cases[cid]
            if rec.get('case_sha256') != case['case_sha256']:
                raise ValueError(f'{file}: frozen case hash mismatch for {cid}')
            if rec.get('demo'):
                skipped.append({'case_id': cid, 'reason': 'explicit demonstration, not a model run'}); continue
            if case['split'] != 'main':
                skipped.append({'case_id': cid, 'reason': 'practice case'}); continue
            if rec.get('status') == 'not_started' and not any(str(v).strip() for v in rec.get('raw', {}).values()):
                skipped.append({'case_id': cid, 'reason': 'not started'}); continue
            if cid in seen:
                raise ValueError(f'Duplicate main case {cid} in {seen[cid]} and {file}. Keep one prespecified run; do not combine single-case and aggregate exports or pick the best repeat.')
            seen[cid] = str(file)
            rows.append(analyze_record(rec, case))
    return sorted(rows, key=lambda r: r['case_id']), skipped


def pct(x: float | None) -> str:
    return '—' if x is None else f'{100*x:.1f}%'

def num(x: float | None) -> str:
    return '—' if x is None else f'{x:.3f}'

def ci(x: list[float] | None) -> str:
    return '—' if x is None else f'[{100*x[0]:.1f}%, {100*x[1]:.1f}%]'


def render_report(s: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    out = ['# 瞎掰王 pilot 分析', '', '**这是探索性记录，不是模型排行榜。**', '',
           f'正式案例记录：{s["main_case_records"]}；14 步均有回复：{s["complete_case_records"]}；未标重大污染的案例：{s["clean_case_records"]}。',
           f'练习/示例/未开始而跳过的记录：{len(s["skipped_records"])}。', '',
           '没有回复的阶段不补为错误；格式无法评分时报告覆盖率。重大污染按预定义标记单独处理，原始记录仍保留。', '',
           '## 全部正式记录：覆盖率与阶段结果', '',
           '| 阶段 | 可评分/已记录案例 | 正确率 | Wilson 95% | Brier（越低越好） | 平均自报置信度 | 信息不足次数 |',
           '|---|---:|---:|---|---:|---:|---:|']
    for phase,x in s['all_recorded_stages'].items():
        out.append(f'| {phase} | {x["scorable_n"]}/{x["attempted_cases"]} | {pct(x["accuracy"])} | {ci(x["wilson_95"])} | {num(x["mean_brier"])} | {pct(x["mean_confidence"])} | {x["insufficient_evidence_count"]} |')
    out += ['', '## 核验是否真正可区分', '', '全部正式记录：`'+json.dumps(s['diagnostic_counts_all'], ensure_ascii=False)+'`。',
            '未标重大污染记录：`'+json.dumps(s['diagnostic_counts_clean'], ensure_ascii=False)+'`。', '',
            '`distinguishing` 才表示 K 的原始三个承诺全对、B 至少一个错；collision、K 错误和不可评分不算成 Judge 的证据使用失败。', '',
            '## 未标重大污染记录的成对变化', '', '| 比较 | 成对案例 | 改对 | 改错 | 准确率变化 | 描述性成对 bootstrap 95% | Brier 变化 |', '|---|---:|---:|---:|---:|---|---:|']
    pairs=[('P3 − P0',s['clean_pairs']['dialogue_P3_minus_P0']),('E − N（全部 clean）',s['clean_pairs']['evidence_E_minus_N']),('E − N（可区分子集）',s['distinguishing_clean_subset']['evidence_E_minus_N'])]
    for name,x in pairs:
        out.append(f'| {name} | {x["paired_n"]} | {x["wrong_to_right"]} | {x["right_to_wrong"]} | {pct(x["delta_accuracy"])} | {ci(x["descriptive_paired_bootstrap_95"])} | {num(x["delta_brier"])} |')
    d=s['distinguishing_clean_subset']
    out += ['', f'可区分 clean 子集共 {d["n"]} 题；N 正确率 {pct(d["stages"]["N"]["accuracy"])}，E 正确率 {pct(d["stages"]["E"]["accuracy"])}。',
            '一致性规则在该子集可识别正确角色，是由子集定义保证的正对照，不是本研究测得的某个真实模型成绩。', '',
            '## 配置记录（不单独归因为 judge 能力）', '']
    for cfg,x in s['by_config_descriptive_not_ranking'].items():
        out += [f'**{cfg}**：{x["n"]} clean cases；speakers=`{", ".join(x["speaker_models"] or ["未记录"])}`；judges=`{", ".join(x["judge_models"] or ["未记录"])}`。']
        if len(x['speaker_models'])>1 or len(x['judge_models'])>1:
            out += ['警告：该配置包含不止一种实际模型名称，必须分版本核对，不能默认为单一部署。']
    out += ['', '## 偏离与缺失', '', '`'+json.dumps(s['issue_flag_counts'], ensure_ascii=False)+'`', '']
    for r in rows:
        details=[]
        if r['warnings']: details+=r['warnings']
        if r['missing_steps']:details+=['缺失：'+', '.join(r['missing_steps'])]
        if r['issue_flags']:details+=['标记：'+', '.join(r['issue_flags'])]
        if details:out.append(f'- {r["case_id"]}：'+ '; '.join(details))
    out += ['', '## 结论边界', '',
            'P0/P3 接近随机并不证明 ToM 失败；缺少可识别信息时可能合理。P3/P0 同时改变了对话量和交互，不能直接解释为主动质询的独立因果效应。N/E 使用同一对话，核验项在回复前固定。',
            '同一 case 的各阶段是重复测量；bootstrap 以 case 的成对差值重采样。小样本区间只是描述，不代替独立确认。概率是模型自报。',
            '下一步请结合 docs/05_INTERPRETATION.md，读完整原文并选一个竞争解释做干预。不要只挑最离谱的错误，也不要将此结果外推到未测试模型。', '']
    if not rows:
        out += ['**目前没有正式模型实验数据。此报告没有模型能力结论。**', '']
    return '\n'.join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, default=ROOT/'logs', help='Directory of JSON logs or one JSON export')
    p.add_argument('--out', type=Path, default=ROOT/'results', help='Output directory (keep separate from input)')
    args = p.parse_args(argv)
    if not args.input.exists():
        p.error('Input does not exist')
    if args.input.is_dir() and args.out.resolve() == args.input.resolve():
        p.error('Output must differ from input to avoid mixing summaries with raw logs')
    try:
        cases = {c['case_id']: c for c in json.loads((ROOT/'data/HOST_ONLY/cases.json').read_text(encoding='utf-8'))}
        rows, skipped = load_records(args.input, cases)
        s = summarize(rows, skipped)
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out/'summary.json').write_text(json.dumps(s, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
        (args.out/'per_case.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
        (args.out/'report.md').write_text(render_report(s,rows),encoding='utf-8')
    except (ValueError, OSError, KeyError) as e:
        print('Analysis stopped: '+str(e), file=sys.stderr)
        return 2
    print(f'Analyzed {len(rows)} main cases; skipped {len(skipped)} practice/demo/not-started records. Output: {args.out}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
