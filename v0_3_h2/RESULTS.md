# H2 题面呈现资格检查

状态：`partial`；判读：`INCOMPLETE_OR_UNSCORABLE`。历史 N 的 p(A)=0.10；A 实际知情，B 的候选规则依赖重音。

|条件|p(A)|选择|信息不足|采集状态|
|---|---:|---|---|---|
|neutral|—|—|—|incomplete_generation_timeout|
|salient|0.1|B|False|completed|

差值 p(A)_salient − p(A)_neutral = `None`；预期方向为负。阈值仅是事前资格判读规则，不是显著性标准。

中性版到截止仍显示生成中：超过约三分钟后进行一次重载及状态检查，未重发。平台以后可能返回，但截止时没有已捕获回复。无法计算两条件差值，也不能用历史 N 替代本轮中性控制；缺失不是模型答错或 H2 阴性结果。

**salient 的原始短理由**：Speaker B's lenition rule crucially uses the stress and syllable boundary mechanics defined on the card. Furthermore, Q1 and Q3 form an initial versus intervocalic voicing minimal pair (/k/ to /g/). Speaker A confabulates nonexistent syllable boundaries within syllables (e.g., between /k/ and /e/ in /ˈo.ke.pi/).

中性提示词与历史 N 逐字一致。强调条件只将原有重音/音节记法及固定输入两句移至音段清单前，并调整分段；原有词语集合、整份对话及题面外的指令完全相同。A 的原始音节边界措辞错误没有修改。

仅两个新裁判回复；采样参数和后台部署不受控，不能区分呈现作用与采样波动。若低概率接近零，向 B 移动也有地板限制。不能确认 task-designer modeling、总体效应或 H1。本轮到此停止，不追加措辞、镜像条件或重复调用。

完整冻结设计见 [PROTOCOL.md](PROTOCOL.md)、[bundle.json](bundle.json)；精确提示词见 [neutral_prompt.txt](neutral_prompt.txt)、[salient_prompt.txt](salient_prompt.txt)。原始 DOM 与会话信息在 Git 排除的本地 run；脱敏研究收据见 [原资格检查](published_runs/h2_qualification01/README.md) 和 [中性补跑](published_runs/h2_neutral_retry01/README.md)，账户、会话与完整页面不公开。

复核：从仓库根目录运行 `python -X utf8 -B scripts/analyze_h2_probe.py`。
