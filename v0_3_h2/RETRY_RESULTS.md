# H2 题面呈现资格检查

本报告使用用户明确授权的中性版一次补跑，与原已保存强调版比较。原资格检查和超时收据未覆盖；见 [补跑修订](RETRY_PROTOCOL.md)。两条件发送时序不同，保留这一操作偏差。
状态：`complete`；判读：`HISTORICAL_PATTERN_NOT_ROUGHLY_REPRODUCED`。历史 N 的 p(A)=0.10；A 实际知情，B 的候选规则依赖重音。

|条件|p(A)|选择|信息不足|采集状态|
|---|---:|---|---|---|
|neutral|0.5|A|True|completed|
|salient|0.1|B|False|completed|

差值 p(A)_salient − p(A)_neutral = `-0.4`；预期方向为负。阈值仅是事前资格判读规则，不是显著性标准。

**neutral 的原始短理由**：No independent host observations are provided to verify check outcomes. Both speakers propose coherent, plausible phonological rules that respect all public card constraints and apply them consistently across all rounds without deduction errors. In the absence of verified facts, there is insufficient evidence to distinguish the informed speaker.

**salient 的原始短理由**：Speaker B's lenition rule crucially uses the stress and syllable boundary mechanics defined on the card. Furthermore, Q1 and Q3 form an initial versus intervocalic voicing minimal pair (/k/ to /g/). Speaker A confabulates nonexistent syllable boundaries within syllables (e.g., between /k/ and /e/ in /ˈo.ke.pi/).

中性提示词与历史 N 逐字一致。强调条件只将原有重音/音节记法及固定输入两句移至音段清单前，并调整分段；原有词语集合、整份对话及题面外的指令完全相同。A 的原始音节边界措辞错误没有修改。

共三次发送，中性版原尝试超时，本报告采用补跑；采样参数和后台部署不受控，不能区分呈现作用与采样波动。若低概率接近零，向 B 移动也有地板限制。不能确认 task-designer modeling、总体效应或 H1。本轮到此停止，不追加措辞、镜像条件或重复调用。

完整冻结设计见 [PROTOCOL.md](PROTOCOL.md)、[bundle.json](bundle.json)；精确提示词见 [neutral_prompt.txt](neutral_prompt.txt)、[salient_prompt.txt](salient_prompt.txt)。原始 DOM 与会话信息在 Git 排除的本地 run；脱敏研究收据见 [原资格检查](published_runs/h2_qualification01/README.md) 和 [中性补跑](published_runs/h2_neutral_retry01/README.md)，账户、会话与完整页面不公开。

复核：从仓库根目录运行 `python -X utf8 -B scripts/analyze_h2_probe.py --neutral-retry`。
