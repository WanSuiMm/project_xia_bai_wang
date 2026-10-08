# 瞎掰王：Who Really Knows?

2026-10-08 战略边界 qualification：[主要结果](epistemic_boundary_mimicry/strategic_qualification/DELIVERY_20261008.md) → [完整离线分析](epistemic_boundary_mimicry/strategic_qualification/analysis_20261008/RESULTS.md) → [冻结协议](epistemic_boundary_mimicry/strategic_qualification/PROTOCOL_20261008.md) → [完整公开证据](epistemic_boundary_mimicry/published_runs/go_strategic_qualification28_20261008/README.md)。四份新资料，Qwen Speakers → GLM Judge，28/28 有效。历史裁判评价暴露没有诱发清楚的所问细节边界模仿；告知暴露条件后身份正确从 2/8 到 5/8，但 B1 被遮住回答的预测未改善。只作四材料探索性结论，不证明高阶 ToM 或自由追问收益。公开复核不调用模型、不需要 key；旧 audit/R0 证据不变。

2026-10-08 R0 replay 交付：[原始结果与补跑完成](epistemic_boundary_mimicry/replay_r0/DELIVERY_20261008.md) → [补跑完成汇总](epistemic_boundary_mimicry/published_runs/go_frozen_replay_r0_completion_20261008/README.md) → [原始注册证据](epistemic_boundary_mimicry/published_runs/go_frozen_replay_r0_20261008/README.md)。原始 84 次均已尝试，77 次有效；此前补跑新增两条，本次低推理补跑五条全部有效，跨尝试 84/84 个位置已有有效回复。五条请求的参数变化单列，原始缺失分析与全部失败保留。两个模型 Informed 的 42/42 次全部 `.5` 并弃权；Blind 也多数弃权，Qwen 偏离集中于 EB05，不能宣称普遍或显著收益。离线公开复核：`python -X utf8 -B scripts/publish_frozen_replay_r0.py` 和 `python -X utf8 -B scripts/publish_frozen_replay_r0_completion.py`，不调用模型、不需要 key。以下各 dated snapshot 是较早阶段的证据。

2026-10-07 全量旧记录审计：[主要发现](epistemic_boundary_mimicry/analysis/claim_audit_20261007/RESULTS.md) → [审计协议](epistemic_boundary_mimicry/analysis/claim_audit_20261007/PROTOCOL.md) → [理论／证据边界](epistemic_boundary_mimicry/analysis/claim_audit_20261007/THEORY_EVIDENCE_MAP.md)。全部 13 条 API 轨迹的 107 次回答按 1,952 个句／分句单元覆盖，另审查全部 57 个问题、12 个终局理由的 72 个单元；保留旧标注，并纠正部分跨轮引用。这里不是独立原子断言样本、人工可靠性检验或机制确认。仅做离线审计，实验 API 调用为零。复核：`python -X utf8 -B scripts/audit_claim_corpus.py`。

2026-10-05 离线语料复用：[分析报告](epistemic_boundary_mimicry/analysis/offline_coding_20261005/RESULTS.md) → [冻结编码规则](epistemic_boundary_mimicry/analysis/CODEBOOK_20261005.md) → [固定复核集合](epistemic_boundary_mimicry/analysis/offline_coding_20261005/REPLAY_COHORT.md)。覆盖 API 阶段 13 条轨迹、107 次回答、57 次追问；7 条完整 Frozen 对话准备为终局盲复核输入，未按输赢筛选。模型辅助首轮标注，不是独立人工双编码或确认性实验；来源一致性与目标可识别性分别评价。未新增实验 API 调用，未补跑第四场。复核：`python -X utf8 -B scripts/audit_offline_coding.py`。

2026-10-05 措辞独立 Frozen 快照：[结果](epistemic_boundary_mimicry/SURFACE_DIVERSE_FROZEN_RESULTS.md) → [协议](epistemic_boundary_mimicry/SURFACE_DIVERSE_FROZEN_PROTOCOL.md) → [可见证据](epistemic_boundary_mimicry/published_runs/go_surface_diverse_cutoff_20261005/README.md)。2 个新背景 × Qwen／GLM 双向，完成 3／4 场，均选择 Speaker（6／2／4 次追问）；第四场第 6 问等待 B 回答时达到预设额度保护，无终局。随机目标不可当作真实性评分；与此前模板资料的弃权差异不是受控因果效应。复核：`python -X utf8 -B scripts/publish_surface_diverse_frozen.py`。

2026-10-04 两道新题 Frozen 完成：[结果](epistemic_boundary_mimicry/FROZEN_PAIR_RESULTS.md) → [可见证据](epistemic_boundary_mimicry/published_runs/go_frozen_pair_completed_20261004/README.md)。生态题追问 4 次后弃权（保留缺引号失败，单字符修复后继承历史）；考古题追问 3 次后弃权，无修复。Qwen Readers → GLM Judge；有限资料同模板生成，冻结资料／座位后独立随机指定目标，裁判不知道该机制。仅两条探索轨迹，不证明稳定识别真实性。复核：`python -X utf8 -B scripts/publish_boundary_frozen_pair.py`。

2026-10-04 新生态题 Frozen：[失败截止](epistemic_boundary_mimicry/FRESH_FROZEN_RESULTS.md) → [协议](epistemic_boundary_mimicry/FRESH_FROZEN_PROTOCOL.md) → [完整可见记录](epistemic_boundary_mimicry/published_runs/go_fresh_frozen_cutoff_20261004/README.md)。完成 3 次追问后，裁判第 4 问的 JSON 字符串未闭合；无终局，不计选对／选错／弃权。不是额度限制。原可见文本保留且未转发。复核：`python -X utf8 -B scripts/publish_boundary_fresh_frozen.py`。此前七个终局不变。

2026-10-04 第二题三场结果：[汇总](epistemic_boundary_mimicry/CASE02_RESULTS.md) → [协议](epistemic_boundary_mimicry/CASE02_API_PROTOCOL.md) → [公开对话](epistemic_boundary_mimicry/published_runs/go_case02_three_20261004/README.md)。Qwen speakers → GLM Judge：Strong 与 Boundary-aware 均追问 3 次选对（.70／.95）；Frozen 追问 9 次选 A（.70），仅匹配随机目标，不证明真实性识别。Strong 原额度 429 截止及保持历史的一次终局补请求都保留；反向尚未启动。两份题目背景、七个终局不是七个独立任务；无条件效应或排名结论。复核：`python -X utf8 -B scripts/publish_boundary_case2.py`。

2026-10-04 前四个 API 配置均有终局：[汇总](epistemic_boundary_mimicry/RESULTS.md)。新增[反向 Boundary-aware](epistemic_boundary_mimicry/REVERSE_RECOVERY_RESULTS.md)：GLM speakers → Qwen Judge，追问 2 次选 A（.78），目标读者 B，判断错误；[完整可见证据](epistemic_boundary_mimicry/published_runs/go_reverse_recovery_20261004/README.md)。原空 READY 失败保留，修订为 Judge 首问、私有初始化合并进 Speaker 首答后重新开始。四场共用一份背景，协议混合，不能估计条件效应或排名。复核：`python -X utf8 -B scripts/publish_boundary_reverse.py`。

2026-10-04 Frozen 负控制补跑完成：[结果](epistemic_boundary_mimicry/FROZEN_RECOVERY_RESULTS.md) → [脱敏完整对话](epistemic_boundary_mimicry/published_runs/go_frozen_recovery_20261004/README.md)。GLM 裁判追问 4 次后弃权：双方各有有限资料，但没有证据把任何一方绑定到主持人指定目标。原两问后的 JSON 换行失败保留；修订解析后继承原回答继续，未重生成。单场符合不可识别控制的预期，不是统计证明；与前两场快照分开。复核：`python -X utf8 -B scripts/publish_boundary_frozen.py`。

2026-10-04 API 试跑：[Epistemic Boundary Mimicry 结果](epistemic_boundary_mimicry/RESULTS.md) → [API 协议](epistemic_boundary_mimicry/API_PROTOCOL.md) → [两场提示词与可见回复](epistemic_boundary_mimicry/published_runs/go_two_completed_20261004/README.md)。Qwen3.8 Max speakers → GLM-5.3 Judge：Strong 追问 3 次选错，Boundary-aware 追问 8 次选对。同一份资料，另外两场因格式／空可见回复未完成；不是条件效应、模型排名或与旧 Arena 结果的受控比较。复核：`python -X utf8 -B scripts/analyze_boundary_go_snapshot.py`。

2026-10-04 完成更新：[全部 8 个配置的结果](strategic_bluff_pilot/COMPLETED_RESULTS.md)。最后两场已补完：strong 追问 7 次后选 B（0.78），natural 看完开场直接选 A（0.99），均正确。合计 natural 4/4、strong 4/4，但只有两份独立资料，且最后两场按用户要求取消提问次数上限；这是带修订的补跑汇总，不是同一固定协议的八次完整复现。先读结果，再看 [补跑和取消上限修订](strategic_bluff_pilot/COMPLETION04_PROTOCOL.md) 与 [八场公开收据](strategic_bluff_pilot/published_runs/eight_completed_20261004/README.md)。复核：`python -X utf8 -B scripts/analyze_strategic_snapshot.py --completed`。早期六场快照保持原样。

2026-10-04 最新交付：[natural / strong 策略瞎掰小试](strategic_bluff_pilot/SNAPSHOT_RESULTS.md)。Claude Sonnet 5 High 与 Gemini 3.1 Pro Preview 双向审问；8 个配置已有 6 个完整终局，natural 和 strong 各 3 场且均判断正确，追问 1–4 次。只有两份独立资料，经过失败后补跑，不能据此估计指令效应或稳定识骗能力。两项缺失单列，首次截止和各次恢复记录保留；发布包含提示词、原始可见回复、源码及公开复核脚本。

2026-10-03 最新交付：[Naturalistic Study 1：9 个已完成配置](naturalistic_study_1/SNAPSHOT_RESULTS.md) → [协议](naturalistic_study_1/PROTOCOL.md) → [脱敏提示词与回复](naturalistic_study_1/published_runs/nine_completed_20261003/README.md)。两个同模型 Speaker 中只有一个看过新资料，Judge 自由审问，主持人不提供真值。9 个配置覆盖 5 份资料，最终判断均正确，追问 1–6 次；部分回答透露资料缺失线索，不能据此宣称稳定识骗能力。原计划 24 个，用户已改为完成 12 个即停；此快照尚缺 3 个完成配置。平台缺失另列，剩余新题资料不公开。

下面是此前各轮实验，证据和结论保持原样。

上一轮：[v0.4 Active Verification 结果](v0_4_active/RESULTS.md) → [协议](v0_4_active/PROTOCOL.md) → [脱敏证据](v0_4_active/published_runs/arena_20261003_active01/README.md)。固定 GLM-5.2 (max) 生成双方回答，Gemini-3.8-Flash-high 主动选择验证、依据主持人真值更新并停止。六题均尝试，四题得到完整双方回答，6/18 裁判轨迹完成；平台缺失单列，不计为模型答错。旧版本结果保持原样。

用可控制的合成卡片游戏研究：模型能否分辨谁最初获得了完整定义，以及独立核验是否改变判断。2026-10-02 的 Arena Direct pilot 完成 3 道正式题；另一题受匿名模型干预污染并停止。完整题中，无核验的新裁判正确 1/3，有核验的新裁判正确 3/3。结果仅支持小样本探索观察，不是 ToM 结论或模型排名。

同日获授权的 grounded-card 后续小试单独记录：[数学](v0_2_math/RESULTS.md)、[其他四领域](v0_2_other/RESULTS.md) 及 [解释与平台恢复限制](v0_2_other/INTERPRETATION.md)。它们包含不完整配对，不并入上面的 v0.1 统计。新增提示词、原始回复和操作事件的脱敏副本分别在 [数学证据](v0_2_math/published_runs/arena_20261002_selvar_pair01/README.md) 与 [其他领域证据](v0_2_other/published_runs/arena_20261002_other_pairs01/README.md)；先读结果，日志仅作二级证据。

2026-10-03 最新 H2 资格检查：[中性补跑与强调版比较](v0_3_h2/RETRY_RESULTS.md)。同一对话，中性补跑 p(A)=50%，强调版 10%；旧中性 N 的 10% 未粗略复现，不能把差值归因于题面强调。原超时截止记录、补跑修订和三份脱敏收据分别保留；本次没有 H1 或额外变体调用。

## 从这里开始

1. [SQ28 当前结果](epistemic_boundary_mimicry/strategic_qualification/DELIVERY_20261008.md)：四份新资料、边界模仿未清楚出现，以及身份判断与回答预测的区别。
2. [完整分析](epistemic_boundary_mimicry/strategic_qualification/analysis_20261008/RESULTS.md) 与 [冻结协议](epistemic_boundary_mimicry/strategic_qualification/PROTOCOL_20261008.md)：先看汇总，精确回复是二级证据。
3. [公开包](epistemic_boundary_mimicry/published_runs/go_strategic_qualification28_20261008/README.md) 与 [增量交接](GPT_HANDOFF.md)：可复核收据、代码和审阅问题。
4. [R0 replay 交付](epistemic_boundary_mimicry/replay_r0/DELIVERY_20261008.md) 与 [旧全量审计](epistemic_boundary_mimicry/analysis/claim_audit_20261007/RESULTS.md)：此前独立阶段的证据保持不变。

以下是 v0.1 的历史阅读路线：

1. [RESULTS.md](RESULTS.md)：本次真实结果、覆盖率、污染和结论边界。
2. [GPT_CONTEXT.md](GPT_CONTEXT.md)：任务定义、模型角色、源码与证据入口。
3. [运行过程](xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/published_runs/arena_20261002_direct_pilot01/README.md)：采集、平台干预、纠错与公开副本说明。
4. [冻结协议](xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/docs/01_SPEC.md) 与 [提示词模板](xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/prompts/templates/README.md)。

仓库包含源码、测试、22 个冻结案例、角色提示词，以及 67 条实际发送提示词和 66 条已保存 JSON 回复（含练习及污染题）。完整页面回复另外保存在公开日志中。原始日志是二级证据，先读汇总；日志包含主持人答案，不能整份发给被测模型。

## 本地使用与复核

Python 3.10+；分析仅依赖标准库。JavaScript 测试和采集辅助器另需 Node.js（在 PATH 上）。主持人 HTML 不需要安装依赖，也不会自动操作 Arena。

复核最新公开快照：`python -X utf8 -B scripts/analyze_strategic_snapshot.py`。无需 Arena 登录或本机原始记录，不产生模型调用。此前九场快照仍可用 `scripts/analyze_naturalistic_snapshot.py` 复核。采集辅助器 [naturalistic_arena_operator.mjs](scripts/naturalistic_arena_operator.mjs) 只接受外部提供的浏览器 SDK 和冻结 bundle，不会自行启动浏览器。

```powershell
cd xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1
python -X utf8 -B -m unittest discover -s tests -p "test_*.py" -v
node tests/test_console.js
python -X utf8 -B tools/analyze.py --input published_runs/arena_20261002_direct_pilot01/logs --out ../../_verification/results
```

离线主持入口：[START_HERE.html](xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/START_HERE.html)。浏览器运行需下载仓库后打开 HTML。逐题备用提示词在 `prompts/ready/`，动态质询的实际发送版本在本次 `published_runs/.../logs/*.json` 的 `sent_prompts` 字段。

本仓库保留原项目目录结构。`runs/` 是本机原始证据，Git 排除；`published_runs/` 是提示词与回复不改字的公开副本，已移除私有会话链接、账户截图和机器路径。旧包中“没有真实模型数据”的说明只描述初始冻结交付，当前结果以本页及 RESULTS 为准。
