# 瞎掰王：Who Really Knows?

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

1. [最新策略瞎掰结果](strategic_bluff_pilot/COMPLETED_RESULTS.md)：8 个终局及混合协议的结论边界。
2. [冻结协议](strategic_bluff_pilot/PROTOCOL.md)、[补跑修订](strategic_bluff_pilot/RETRY_PROTOCOL.md) 和 [取消上限修订](strategic_bluff_pilot/COMPLETION04_PROTOCOL.md)。
3. [公开提示词与回复](strategic_bluff_pilot/published_runs/eight_completed_20261004/README.md)：逐条原始可见回复，仅作二级证据。
4. [增量审阅交接](GPT_HANDOFF.md)：本次变化及旧实验不变的结论。

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
