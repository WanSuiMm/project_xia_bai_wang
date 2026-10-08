# Latest replay delivery：2026-10-08

See [R0 result and supplementary completion](epistemic_boundary_mimicry/replay_r0/DELIVERY_20261008.md), [original registered numerical results](epistemic_boundary_mimicry/replay_r0/RESULTS_20261007.md), and [completion evidence](epistemic_boundary_mimicry/published_runs/go_frozen_replay_r0_completion_20261008/README.md). Original 84 attempts yielded 77 valid replies; two earlier supplementary replies and five new low-reasoning replies cover all 84 original positions across attempts. The five new calls are all .5/ABSTAIN. Preserve their configuration change, previous unknown dispatches, and final status-file error separately. All 42 original Informed replies are .5/ABSTAIN. Blind is mostly null-consistent; Qwen's small effect is confined to EB05, and GLM primary missingness remains bounded rather than imputed. The mixed-configuration descriptive overlay gives GLM Blind risk .011042; it is not a replacement registered analysis, model ranking or interrogation experiment.

# Arena Direct pilot：2026-10-02

状态：**部分完成，有平台阻塞**。计划 D01 练习加 P01–P04；D01/P01/P02/P04 均完成 14 步，P03 保存 10 步后因匿名候选进入裁判上下文而停止。正式完整且未标重大污染的独立单位是 3 个 case，不是 42 条独立样本。

| 案例 | 配置 | 知情座位 | 回复数 | P0 / P3 / N / E 的 A 概率 | 状态 |
|---|---|---|---:|---|---|
| D01 | R1 | A | 14 | .75 / .75 / .50 / .98 | 练习，排除 |
| P01 | R1 | A | 14 | .50 / .50 / .50 / .95 | 完整 |
| P02 | R2 | A | 14 | .50 / .42 / .42 / .91 | 完整，有格式偏离 |
| P03 | R1 | B | 10 | .50 / — / — / — | 污染，排除 |
| P04 | R2 | B | 14 | .64 / .68 / .68 / .04 | 完整，有格式偏离 |

M1=`claude-sonnet-5-5-high`；M2=`gemini-3.8-flash-high`。R1：M1 两位说话人、M2 裁判；R2 相反。

三道完整题的 P0 正确 2/3，P3 与 N 正确 1/3，E 正确 3/3。N/E 的平均 Brier 约 0.350/0.004；E−N 描述性正确率变化 +66.7 个百分点，case 成对 bootstrap 95% 为 [0%,100%]。三题的冻结核验均真正可区分双方开场承诺。N 的所有裁判都声明证据不足，E 都声明证据足够。

不能据此推断 ToM 失败、主动质询的独立因果效应或模型优劣。配置同时改变了说话人与裁判；无核验的 forced pick 在 p=.5 时也会被评分，但不表示确定识别。未完成阶段不补为错误。

67 条发送提示词与冻结构造器完全一致；完整题 56 条 JSON（含练习）与补存的页面 JSON 一致。D01 B 开场 145 词；P02 P3 reason 52 词；P04 N reason 57 词。P02/P04 E 有 JSON 外说明，全文已保留。P03 的污染与采集错误没有隐去或重跑。

详细证据：[原分析报告](xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/published_runs/arena_20261002_direct_pilot01/results/report.md)、[采集核验](xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/published_runs/arena_20261002_direct_pilot01/capture_audit.json)、[公开日志](xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/published_runs/arena_20261002_direct_pilot01/logs/)、[完整性清单](xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/published_runs/arena_20261002_direct_pilot01/publication_manifest.json)。
