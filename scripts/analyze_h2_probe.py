"""Audit two frozen presentation prompts and report a qualification, not an effect estimate."""
from pathlib import Path
import hashlib
import json
import argparse

ROOT = Path(__file__).resolve().parents[1]/'v0_3_h2'
RUN = ROOT/'runs/h2_qualification01'
if not RUN.exists():
    RUN = ROOT/'published_runs/h2_qualification01'
RETRY_RUN = ROOT/'runs/h2_neutral_retry01'
if not RETRY_RUN.exists():
    RETRY_RUN = ROOT/'published_runs/h2_neutral_retry01'

def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()

def main(neutral_retry=False):
    bundle=json.loads((ROOT/'bundle.json').read_text(encoding='utf-8'))
    rows={}
    for arm in bundle['send_order']:
        path=RUN/(arm+'.json')
        if neutral_retry and arm=='neutral':
            path=RETRY_RUN/'neutral.json'
        if not path.exists():
            rows[arm]={'status':'missing','p_A':None,'pick':None}
            continue
        r=json.loads(path.read_text(encoding='utf-8'))
        assert r['prompt']==bundle['arms'][arm]['prompt']
        assert digest(r['prompt'])==bundle['arms'][arm]['prompt_sha256']
        row={'status':r['status'],'p_A':None,'pick':None}
        if r.get('raw'):
            assert r['visible_model']==bundle['model']
            parsed=json.loads(r['raw'])
            p=parsed['p_informed_A']
            assert type(p) in (int,float) and 0<=p<=1
            assert parsed['pick'] in ['A','B']
            assert (p==0.5 or parsed['pick']==('A' if p>0.5 else 'B'))
            assert type(parsed['insufficient_evidence']) is bool
            assert parsed['question'] is None
            row.update(p_A=p,pick=parsed['pick'],insufficient_evidence=parsed['insufficient_evidence'],reason=parsed['reason'],reason_words=len(parsed['reason'].split()),raw_sha256=digest(r['raw']))
        rows[arm]=row
    p_n,p_s=rows['neutral']['p_A'],rows['salient']['p_A']
    delta=None
    verdict='INCOMPLETE_OR_UNSCORABLE'
    if p_n is not None and p_s is not None:
        delta=round(p_s-p_n,12)
        threshold=bundle['decision']['material_shift_absolute']
        if p_n>bundle['decision']['neutral_replication_max_p_A']:
            verdict='HISTORICAL_PATTERN_NOT_ROUGHLY_REPRODUCED'
        elif delta<=-threshold:
            verdict='DIRECTIONAL_QUALIFICATION_SIGNAL'
        elif delta>=threshold:
            verdict='OPPOSITE_DIRECTION'
        else:
            verdict='NO_MATERIAL_DIRECTIONAL_SIGNAL'
    result={'status':'complete' if delta is not None else 'partial','receipt_audit':'passed','historical_p_A':bundle['historical_p_A'],'arms':rows,'delta_p_A':delta,'qualification_verdict':verdict,'claim_boundary':'One transcript, one fresh response per arm. No separation of presentation effect from sampling noise; no mechanism or population inference.'}
    result['neutral_attempt']='user_authorized_retry01' if neutral_retry else 'original_attempt'
    output_prefix='RETRY_' if neutral_retry else ''
    (ROOT/('retry_analysis.json' if neutral_retry else 'analysis.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# H2 题面呈现资格检查','',f"状态：`{result['status']}`；判读：`{verdict}`。历史 N 的 p(A)=0.10；A 实际知情，B 的候选规则依赖重音。",'', '|条件|p(A)|选择|信息不足|采集状态|','|---|---:|---|---|---|']
    for arm,row in rows.items():
        lines.append(f"|{arm}|{row['p_A'] if row['p_A'] is not None else '—'}|{row['pick'] or '—'}|{row.get('insufficient_evidence','—')}|{row['status']}|")
    lines += ['',f'差值 p(A)_salient − p(A)_neutral = `{delta}`；预期方向为负。阈值仅是事前资格判读规则，不是显著性标准。','']
    if delta is None:
        lines += ['中性版到截止仍显示生成中：超过约三分钟后进行一次重载及状态检查，未重发。平台以后可能返回，但截止时没有已捕获回复。无法计算两条件差值，也不能用历史 N 替代本轮中性控制；缺失不是模型答错或 H2 阴性结果。','']
    for arm,row in rows.items():
        if row.get('reason'):
            lines += [f"**{arm} 的原始短理由**：{row['reason']}",'']
    lines += ['中性提示词与历史 N 逐字一致。强调条件只将原有重音/音节记法及固定输入两句移至音段清单前，并调整分段；原有词语集合、整份对话及题面外的指令完全相同。A 的原始音节边界措辞错误没有修改。','', '仅两个新裁判回复；采样参数和后台部署不受控，不能区分呈现作用与采样波动。若低概率接近零，向 B 移动也有地板限制。不能确认 task-designer modeling、总体效应或 H1。本轮到此停止，不追加措辞、镜像条件或重复调用。','', '完整冻结设计见 [PROTOCOL.md](PROTOCOL.md)、[bundle.json](bundle.json)；精确提示词见 [neutral_prompt.txt](neutral_prompt.txt)、[salient_prompt.txt](salient_prompt.txt)。原始 DOM 与会话信息在 Git 排除的本地 run；本次结果未自动推送 GitHub。','', '复核：从仓库根目录运行 `python -X utf8 -B scripts/analyze_h2_probe.py`。']
    lines=[line.replace('本次结果未自动推送 GitHub。','脱敏研究收据见 [原资格检查](published_runs/h2_qualification01/README.md) 和 [中性补跑](published_runs/h2_neutral_retry01/README.md)，账户、会话与完整页面不公开。') for line in lines]
    if neutral_retry:
        lines.insert(2,'本报告使用用户明确授权的中性版一次补跑，与原已保存强调版比较。原资格检查和超时收据未覆盖；见 [补跑修订](RETRY_PROTOCOL.md)。两条件发送时序不同，保留这一操作偏差。')
        lines=[line.replace('仅两个新裁判回复；','共三次发送，中性版原尝试超时，本报告采用补跑；').replace('超过约三分钟后','补跑超过约五分钟后').replace('scripts/analyze_h2_probe.py`','scripts/analyze_h2_probe.py --neutral-retry`') for line in lines]
    (ROOT/(output_prefix+'RESULTS.md')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--neutral-retry',action='store_true',help='Use the explicitly authorized neutral retry without replacing original evidence')
    main(parser.parse_args().neutral_retry)
