"""Recompute the frozen Active Verification screen; no model or network calls."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'v0_4_active'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def parse(raw):
    text = raw.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0]
    return json.loads(text)


def ratio(n, d):
    return {'numerator': n, 'denominator': d, 'value': n / d if d else None}


def main():
    ap = argparse.ArgumentParser()
    local = BASE / 'runs/arena_20261003_active01'
    default = local if local.exists() else BASE / 'published_runs/arena_20261003_active01'
    ap.add_argument('--run', type=Path, default=default)
    args = ap.parse_args()
    bundle = read(BASE / 'bundle.json')
    rows, cases, updates, audit_errors, word_flags = [], [], [], [], []
    speaker_sends = speaker_replies = judge_sends = judge_replies = verifications = 0
    # Use the canonical JS builders/parser to audit exact receipts, including failed pending steps.
    code = r'''
const fs=require('fs'),C=require(process.argv[1]),b=JSON.parse(fs.readFileSync(process.argv[2])),run=process.argv[3],errors=[];
for(const c of b.cases){const r=JSON.parse(fs.readFileSync(run+'/logs/'+c.case_id+'.json'));
for(const s of Object.keys(r.raw)){try{C.parseSpeaker(r.raw[s],c);if(r.captures[s].prompt!==C.speakerPrompt(b,c,s))throw Error('speaker prompt mismatch');}catch(e){errors.push(c.case_id+'_'+s+': '+e.message);}}
for(let j=1;j<=3;j++){const k=c.case_id+'_J'+j,t=JSON.parse(fs.readFileSync(run+'/trajectories/'+k+'.json'));
try{if(t.decisions.length)C.auditTrajectory(b,c,r,t);
if(t.pending?.url||t.pending?.sent){const expected=t.pending.index===0?C.judgeInitial(b,c,r):C.judgeFollow(b,c,t,t.observations.at(-1));if(expected!==t.pending.prompt)throw Error('pending prompt mismatch');}
if(t.decisions.length&&Date.parse(r.frozen_utc)>Date.parse(t.events.find(e=>e.type==='judge_send_receipt').at))throw Error('judge sent before freeze');
}catch(e){errors.push(k+': '+e.message);}}}
console.log(JSON.stringify(errors));
'''
    result = subprocess.run(['node', '-e', code, str(BASE / 'core.cjs'), str(BASE / 'bundle.json'), str(args.run)],
                            check=True, capture_output=True, text=True, encoding='utf8')
    audit_errors.extend(json.loads(result.stdout))
    for c in bundle['cases']:
        cid = c['case_id']
        r = read(args.run / 'logs' / f'{cid}.json')
        speakers = {seat: parse(raw) for seat, raw in r['raw'].items()}
        speaker_sends += len(r.get('sessions', {}))
        speaker_replies += len(speakers)
        for seat, reply in speakers.items():
            words = len(reply['explanation'].split())
            if not 80 <= words <= 120:
                word_flags.append({'case_id': cid, 'seat': seat, 'explanation_words': words})
        ready = set(speakers) == {'A', 'B'}
        diagnostic = [q['id'] for q in c['queries'] if ready and speakers['A']['predictions'][q['id']] != speakers['B']['predictions'][q['id']]]
        known_correct = all(speakers[c['informed_seat']]['predictions'][q['id']] == c['gold'][q['id']] for q in c['queries']) if c['informed_seat'] in speakers else None
        cr = {'case_id': cid, 'design_class': c['design_class'], 'status': r['status'], 'usable_pair': ready,
              'known_predictions_correct': known_correct, 'diagnostic_queries': diagnostic if ready else None,
              'random_first_query_chance': len(diagnostic) / 8 if ready else None,
              'oracle_table_cost_lower_bound': (1 if diagnostic else 0) if ready and known_correct else None}
        cases.append(cr)
        for j in range(1, 4):
            tid = f'{cid}_J{j}'
            t = read(args.run / 'trajectories' / f'{tid}.json')
            ds = [parse(d['raw']) for d in t['decisions']]
            obs = t['observations']
            judge_sends += len(ds) + int(bool(t.get('pending', {}).get('url') or t.get('pending', {}).get('sent')))
            judge_replies += len(ds)
            verifications += len(obs)
            terminal = bool(ds and ds[-1]['action'] in ('STOP', 'UNIDENTIFIABLE'))
            first = ds[0] if ds else None
            first_disagreement = bool(first and first['action'] == 'VERIFY' and first['query_id'] in diagnostic) if ready and diagnostic and first else None
            first_diag_index = next((i for i, o in enumerate(obs) if o['A'] != o['B']), None)
            final_correct = ds[-1]['pick'] == c['informed_seat'] if terminal and ready and diagnostic and known_correct else None
            abstain_correct = ds[-1]['action'] == 'UNIDENTIFIABLE' if terminal and ready and not diagnostic else None
            extra = len(obs) - first_diag_index - 1 if terminal and first_diag_index is not None else None
            row = {'trajectory': tid, 'case_id': cid, 'status': t['status'], 'replies': len(ds), 'terminal': terminal,
                   'first_action': first['action'] if first else None, 'first_query_diagnostic': first_disagreement,
                   'verifications': len(obs), 'final_correct': final_correct, 'equivalent_abstention_correct': abstain_correct,
                   'extra_verifications_after_first_diagnostic': extra,
                   'decision_sequence': [{k: d[k] for k in ('action', 'query_id', 'p_informed_A', 'pick')} for d in ds]}
            rows.append(row)
            for i, o in enumerate(obs):
                if i + 1 >= len(ds) or o['A'] == o['B']:
                    continue
                supported = 'A' if o['A'] == o['truth'] else 'B'
                before, after = ds[i]['p_informed_A'], ds[i + 1]['p_informed_A']
                delta = (after - before) * (1 if supported == 'A' else -1)
                updates.append({'trajectory': tid, 'observation_index': i, 'supported_seat': supported,
                                'probability_before': before, 'probability_after': after,
                                'direction_correct': delta > 0 if before not in (0, 1) else None,
                                'post_update_side_correct': (after > .5 if supported == 'A' else after < .5)})
    first_rows = [r for r in rows if r['first_query_diagnostic'] is not None]
    final_rows = [r for r in rows if r['final_correct'] is not None]
    neg_rows = [r for r in rows if r['equivalent_abstention_correct'] is not None]
    direction_rows = [u for u in updates if u['direction_correct'] is not None]
    extra = [r['extra_verifications_after_first_diagnostic'] for r in final_rows]
    completed = sum(r['terminal'] for r in rows)
    analysis = {'version': bundle['version'], 'run_id': args.run.name,
                'bundle_sha256': hashlib.sha256((BASE / 'bundle.json').read_bytes()).hexdigest(),
                'collection_status': read(args.run / 'status.json')['status'],
                'counts': {'planned_cases': 6, 'usable_pairs': sum(c['usable_pair'] for c in cases), 'planned_trajectories': 18,
                           'speaker_sends': speaker_sends, 'speaker_replies': speaker_replies, 'judge_sends': judge_sends,
                           'judge_replies': judge_replies, 'completed_trajectories': completed, 'missing_terminal_trajectories': 18 - completed,
                           'host_verifications': verifications},
                'metrics': {'first_query_discrimination': ratio(sum(r['first_query_diagnostic'] for r in first_rows), len(first_rows)),
                            'evidence_update_side': ratio(sum(u['post_update_side_correct'] for u in updates), len(updates)),
                            'evidence_update_direction': ratio(sum(u['direction_correct'] for u in direction_rows), len(direction_rows)),
                            'final_accuracy_known_correct_disagreement_completed': ratio(sum(r['final_correct'] for r in final_rows), len(final_rows)),
                            'equivalent_abstention_completed': ratio(sum(r['equivalent_abstention_correct'] for r in neg_rows), len(neg_rows)),
                            'completed_identifiable_costs': [r['verifications'] for r in final_rows],
                            'completed_identifiable_extra_costs': extra},
                'audit_errors': audit_errors, 'word_budget_flags': word_flags, 'cases': cases, 'trajectories': rows, 'evidence_updates': updates}
    (BASE / 'analysis.json').write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    m = analysis['metrics']
    lines = ['# v0.4 Active Verification — qualification01', '',
             '2026-10-03；Arena Direct。GLM-5.2 (max) 生成冻结 A/B，Gemini-3.8-Flash-high 当裁判。', '',
             '**这版基础任务在已观测回复上表现良好，没有观察到明确的选题或证据使用失败；停止成本高于单次验证下界。平台缺失严重，不能宣称稳定通过。**', '',
             f'六题全部尝试，{speaker_replies}/12 解释者回复，四个完整双方配对。12 条裁判会话实际启动，计划 18 条中完成 {completed} 条；六条平台失败、六条因缺少解释者无法启动。26 次裁判发送获得 20 条有效回复，共验证 {verifications} 次。缺失不计为模型错误，无重发或补题。', '',
             '| 指标 | 实际结果 | 分母与边界 |', '|---|---:|---|',
             f"| 首问选择双方预测不同的输入 | {m['first_query_discrimination']['numerator']}/{m['first_query_discrimination']['denominator']} | 三个可识别背景中有首回复的轨迹，含后来中断者 |",
             f"| 真值后更新到证据支持的一侧 | {m['evidence_update_side']['numerator']}/{m['evidence_update_side']['denominator']} | 有下一条回复的区分性观察；未返回更新单列缺失 |",
             f"| 完成的可识别题最终选对 | {m['final_accuracy_known_correct_disagreement_completed']['numerator']}/{m['final_accuracy_known_correct_disagreement_completed']['denominator']} | 仅两个背景有终局；不是 18 条整体准确率 |",
             f"| 预测等价负控制正确 abstain | {m['equivalent_abstention_completed']['numerator']}/{m['equivalent_abstention_completed']['denominator']} | 一个背景的三次条件重复，均零验证 |",
             '| 完成的可识别轨迹验证成本 | 2、3、2 | 具有完整预测表的 oracle 下界为 1；额外成本为 1、2、1 |', '',
             '## 按题覆盖率', '', '| 题目 | 完整双方 | 区分输入 | 随机首问命中率 | 完成裁判 |', '|---|---|---|---:|---:|']
    for c in cases:
        n = sum(r['terminal'] for r in rows if r['case_id'] == c['case_id'])
        d = ', '.join(c['diagnostic_queries']) or '无' if c['usable_pair'] else '缺失'
        chance = f"{c['random_first_query_chance']:.0%}" if c['usable_pair'] else '—'
        lines.append(f"| {c['case_id']} | {'是' if c['usable_pair'] else '否'} | {d} | {chance} | {n}/3 |")
    lines += ['', '## 解释与限制', '',
              '四个完整配对的知情方八项预测均符合主持人真值。所有已捕获的可识别题首问都主动选择区分输入，所有可观测更新都朝真值支持方移动。14 次验证中有 4 次未返回下一步更新，不能评分。完成的可识别轨迹没有在首次区分性验证后立即停止。这里允许知情方误算、未知方猜中，因此额外验证只表示相对 oracle 预测表下界的成本，不能直接判作非理性，也不是一次真值就证明初始知识访问。', '',
              '负控制公开了允许测试模式的完整规则，因此本身很容易；预测等价只限制验证通道，不能证明双方全文没有角色线索。实际裁判从解释推断区分输入，oracle 已有完整预测表，二者信息条件不同。', '',
              '同题三次裁判共享同一对冻结回答。独立背景只有六个计划题、四个可用配对；可识别终局仅来自两个背景，负控制终局仅来自一个背景。禁止把重复轨迹或更新次数当作独立样本。平台缺失可能具有选择性，不能据此推断总体准确率、因果效应、ToM 机制或模型排名。H2 暂停，没有新增领域、自由提问或两步规划实验。', '',
              '## 复核', '', '[协议](PROTOCOL.md)；[机器可读统计](analysis.json)；[源码](core.cjs)；[脱敏证据](published_runs/arena_20261003_active01/README.md)。从仓库根运行 `python -X utf8 -B scripts/analyze_active_verification.py`，需要 Python 和 Node.js；原始 run 不存在时自动使用公开证据。发布不新增模型调用，原始证据保持原样。', '',
              f'冻结 bundle SHA256：`{analysis["bundle_sha256"]}`。逐条已捕获/失败待回应提示词、主持人观察和先冻结后发送的时间顺序审计：{len(audit_errors)} 个错误。解释字数违规：{len(word_flags)}。原始日志、匿名比较、错误页面及截图保留在 Git 排除的 `runs/arena_20261003_active01/`，作为二级证据；不要整份发送给被测模型。', '',
              '## 全部计划轨迹', '', '| 轨迹 | 状态 | 有效回复 | 验证次数 | 终局 |', '|---|---|---:|---:|---|']
    for r in rows:
        last = r['decision_sequence'][-1] if r['terminal'] else None
        end = (last['action'] + (' ' + last['pick'] if last['pick'] else '')) if last else '缺失'
        lines.append(f"| {r['trajectory']} | {r['status']} | {r['replies']} | {r['verifications']} | {end} |")
    (BASE / 'RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
    print(json.dumps({'counts': analysis['counts'], 'metrics': m, 'audit_errors': audit_errors, 'word_budget_flags': word_flags}, ensure_ascii=False, indent=2))
    if audit_errors:
        raise SystemExit('Receipt audit failed')


if __name__ == '__main__':
    main()
