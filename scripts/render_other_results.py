"""Render the small canonical table from audited JSON, including missing runs."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / 'v0_2_other'
RUN = ROOT / 'runs/arena_20261002_other_pairs01'
if not RUN.exists():
    RUN = ROOT / 'published_runs/arena_20261002_other_pairs01'

def main():
    data = json.loads((ROOT/'analysis.json').read_text(encoding='utf-8'))
    priors = []
    for prefix in ['L01', 'E01', 'T01', 'H01']:
        path = RUN/('prior_'+prefix+'.json')
        if path.exists():
            rec = json.loads(path.read_text(encoding='utf-8'))
            priors.append((prefix, rec.get('status', 'unknown'), rec.get('raw'), rec.get('issue_flags', [])))
    lines = ['# 其他领域 pilot01：实际结果', '', f"2026-10-02。状态 `{data['status']}`；正式回复 {data['completed_game_replies']}/112；完整背景 pairs {data['complete_background_pairs']}/4。", '', '固定 Direct UI：Claude Sonnet 5.5 high 两位隔离解释者；Gemini 3.8 Flash high 交互及独立 N/E 裁判。UI 标签不验证后台部署和采样参数。', '', '概率均表示真实知情者的概率；不是所有版本都以 A 为知情者。N 只见完整对话，E 额外见三个真实检查。', '', '|版本|知情座位|回复|P0|P1|P2|P3|N|E|初始承诺诊断|状态|', '|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|']
    for row in data['cases']:
        stages = row['stages']
        vals = [f"{100*stages[s]['p_informed']:.0f}%" if s in stages else '—' for s in ['P0','P1','P2','P3','N','E']]
        lines.append('|'+ '|'.join([row['case'], row.get('informed_seat','—'), str(row['replies'])+'/14'] + vals + [row.get('diagnostic',{}).get('status','—'), row['status']])+'|')
    lines += ['', '`collision` 表示未知情者三个初始承诺也全对；`knower_commitment_error` 表示知情者至少一项错误；这些不能当作明确区分的 E 正对照。缺失项不计作模型答错。', '', '## Public-only prior', '']
    for prefix, status, raw, flags in priors:
        lines.append(f'- {prefix}: `{status}`；'+(f'原始 JSON：`{json.dumps(json.loads(raw), ensure_ascii=False, separators=(",", ":"))}`' if raw else '无已保存回复。'))
        if flags:
            lines.append(f'  格式偏差：{flags}；保留原文，不补造具名概率字段。')
    lines += ['', '## 偏差与证据', '', f"原样构建提示词、捕获副本和可见固定模型审计：`{data['receipt_audit']}`。三轮内部提问及多次回复不是独立统计样本。", '']
    for row in data['cases']:
        if row.get('platform_interventions'):
            lines.append(f"- {row['case']}: {row['platform_interventions']} 次匿名比较平台干预，详情见本地日志；不能描述为无干预运行。")
        if row.get('issue_flags'):
            lines.append(f"- {row['case']}: 标记 {row['issue_flags']}。")
    for item in data['deviations']:
        lines.append(f"- {item['case']}/{item['step']}: {item['field']} {item['words']} 词，预算 {item['allowed'][0]}–{item['allowed'][1]}；保留原文。")
    lines += ['', '四组是人类学 Taluma、历史 Varen、生态 Orava、语言学 Serevic 的合成配对卡，不能作为现实民族志、史料、植物实验或语言史事实。完整规则及冻结设计见 [PROTOCOL.md](PROTOCOL.md) 和 [bundle.json](bundle.json)；规范化统计与逐裁判理由见 [analysis.json](analysis.json)。逐例解释及操作恢复见 [INTERPRETATION.md](INTERPRETATION.md)。', '', '原始回复、完整 DOM、失败收据、可见模型及会话地址保存在 Git 排除的 `runs/arena_20261002_other_pairs01/`，不包含在公开概要中。本轮未推送 GitHub。数学与 v0.1 原始证据保持分开。', '', '从仓库根目录重做本地审计和表格：`python -X utf8 -B scripts/analyze_other_pilots.py`，然后 `python -X utf8 -B scripts/render_other_results.py`；需要本地原始 run。', '', '这是发现性小试。无总体准确率、模型排名、一般 ToM 或 grounding/主动质询因果效应结论。']
    lines = [line.replace('不包含在公开概要中。本轮未推送 GitHub。', '脱敏后的提示词、原始回复与操作事件见 [公开证据副本](published_runs/arena_20261002_other_pairs01/README.md)，页面与会话信息不公开。').replace('；需要本地原始 run。', '；没有本地原始 run 时自动使用公开证据副本。') for line in lines]
    (ROOT/'RESULTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')

if __name__ == '__main__':
    main()
