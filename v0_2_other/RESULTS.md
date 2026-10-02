# 其他领域 pilot01：实际结果

2026-10-02。状态 `partial`；正式回复 46/112；完整背景 pairs 0/4。

固定 Direct UI：Claude Sonnet 5.5 high 两位隔离解释者；Gemini 3.8 Flash high 交互及独立 N/E 裁判。UI 标签不验证后台部署和采样参数。

概率均表示真实知情者的概率；不是所有版本都以 A 为知情者。N 只见完整对话，E 额外见三个真实检查。

|版本|知情座位|回复|P0|P1|P2|P3|N|E|初始承诺诊断|状态|
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
|L01V1|A|14/14|50%|50%|50%|50%|10%|99%|distinguishing|completed|
|L01V2|A|1/14|—|—|—|—|—|—|unscorable|blocked_platform_generation|
|E01V1|B|1/14|—|—|—|—|—|—|unscorable|blocked_platform_session_loss|
|E01V2|B|14/14|80%|80%|85%|90%|80%|85%|collision|completed|
|T01V1|A|14/14|80%|90%|95%|96%|95%|99%|distinguishing|completed|
|T01V2|B|2/14|—|—|—|—|—|—|distinguishing|blocked_platform_session_loss|
|H01V1|B|0/14|—|—|—|—|—|—|unscorable|blocked_platform_generation|
|H01V2|A|0/14|—|—|—|—|—|—|unscorable|blocked_platform_generation|

`collision` 表示未知情者三个初始承诺也全对；`knower_commitment_error` 表示知情者至少一项错误；这些不能当作明确区分的 E 正对照。缺失项不计作模型答错。

## Public-only prior

- L01: `completed`；原始 JSON：`{"p_pass":[0.2,0.1,0.3],"insufficient_evidence":true,"reason":"The private rule is not identified. Consonant inventory has no /tʃ/, so Q2's palatalization outcome is unlikely under a rule limited to ancestor segments. Lenition-style voicing (k>g) is plausible intervocalically, favoring Q3 slightly over Q1's word-initial context. All of these are priors, not evidence."}`
  格式偏差：['p_pass_array_not_keyed']；保留原文，不补造具名概率字段。
- E01: `completed`；原始 JSON：`{"p_pass":[0.01,0.45,0.45],"insufficient_evidence":true,"reason":"Moisture alone is stated to supply neither cue, so Q1 should fail. The private report fixes the cue as freeze-thaw or smoke, and the public card does not say which. Q2 and Q3 are probably mutually exclusive, so each is near even odds. A both-cues-work case is possible but less likely."}`
  格式偏差：['p_pass_array_not_keyed']；保留原文，不补造具名概率字段。
- T01: `completed`；原始 JSON：`{"p_pass":[0.1,0.12,0.15],"insufficient_evidence":true,"reason":"The sampled private facts about Taluma are not identified. The card says marriage is negotiated separately from age-grade ceremonies, so Q1 is unlikely. Q2 is a narrow, specific right (speak but not vote). Q3 is a specific duty. Both have low priors, and the herd-management context makes Q3 only slightly more plausible."}`
  格式偏差：['p_pass_array_not_keyed']；保留原文，不补造具名概率字段。
- H01: `completed`；原始 JSON：`{"p_pass":{"Q1":0.12,"Q2":0.15,"Q3":0.6},"insufficient_evidence":true,"reason":"The private card is not identified. The baseline stipulates that guild weighmasters had no pre-assessment certification authority, which suggests the Compact might add it, so Q3 is the likeliest PASS. Tariff cuts and a transfer of clearance authority are less suggested by the public card."}`

## 偏差与证据

原样构建提示词、捕获副本和可见固定模型审计：`passed`。三轮内部提问及多次回复不是独立统计样本。

- L01V1: 1 次匿名比较平台干预，详情见本地日志；不能描述为无干预运行。
- E01V2: 1 次匿名比较平台干预，详情见本地日志；不能描述为无干预运行。
- T01V1: 2 次匿名比较平台干预，详情见本地日志；不能描述为无干预运行。
- T01V1/opening_A: explanation 141 词，预算 100–140；保留原文。
- T01V1/answer_1_A: answer 101 词，预算 60–100；保留原文。

四组是人类学 Taluma、历史 Varen、生态 Orava、语言学 Serevic 的合成配对卡，不能作为现实民族志、史料、植物实验或语言史事实。完整规则及冻结设计见 [PROTOCOL.md](PROTOCOL.md) 和 [bundle.json](bundle.json)；规范化统计与逐裁判理由见 [analysis.json](analysis.json)。逐例解释及操作恢复见 [INTERPRETATION.md](INTERPRETATION.md)。

原始回复、完整 DOM、失败收据、可见模型及会话地址保存在 Git 排除的 `runs/arena_20261002_other_pairs01/`，脱敏后的提示词、原始回复与操作事件见 [公开证据副本](published_runs/arena_20261002_other_pairs01/README.md)，页面与会话信息不公开。数学与 v0.1 原始证据保持分开。

从仓库根目录重做本地审计和表格：`python -X utf8 -B scripts/analyze_other_pilots.py`，然后 `python -X utf8 -B scripts/render_other_results.py`；没有本地原始 run 时自动使用公开证据副本。

这是发现性小试。无总体准确率、模型排名、一般 ToM 或 grounding/主动质询因果效应结论。
