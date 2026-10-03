# 瞎掰王：Who Really Knows?

2026-10-03 最新交付：[Naturalistic Study 1：9 个已完成配置](naturalistic_study_1/SNAPSHOT_RESULTS.md) → [协议](naturalistic_study_1/PROTOCOL.md) → [脱敏提示词与回复](naturalistic_study_1/published_runs/nine_completed_20261003/README.md)。两个同模型 Speaker 中只有一个看过新资料，Judge 自由审问，主持人不提供真值。9 个配置覆盖 5 份资料，最终判断均正确，追问 1–6 次；部分回答透露资料缺失线索，不能据此宣称稳定识骗能力。原计划 24 个，用户已改为完成 12 个即停；此快照尚缺 3 个完成配置。平台缺失另列，剩余新题资料不公开。

下面是此前各轮实验，证据和结论保持原样。

上一轮：[v0.4 Active Verification 结果](v0_4_active/RESULTS.md) → [协议](v0_4_active/PROTOCOL.md) → [脱敏证据](v0_4_active/published_runs/arena_20261003_active01/README.md)。固定 GLM-5.2 (max) 生成双方回答，Gemini-3.8-Flash-high 主动选择验证、依据主持人真值更新并停止。六题均尝试，四题得到完整双方回答，6/18 裁判轨迹完成；平台缺失单列，不计为模型答错。旧版本结果保持原样。

用可控制的合成卡片游戏研究：模型能否分辨谁最初获得了完整定义，以及独立核验是否改变判断。2026-10-02 的 Arena Direct pilot 完成 3 道正式题；另一题受匿名模型干预污染并停止。完整题中，无核验的新裁判正确 1/3，有核验的新裁判正确 3/3。结果仅支持小样本探索观察，不是 ToM 结论或模型排名。

同日获授权的 grounded-card 后续小试单独记录：[数学](v0_2_math/RESULTS.md)、[其他四领域](v0_2_other/RESULTS.md) 及 [解释与平台恢复限制](v0_2_other/INTERPRETATION.md)。它们包含不完整配对，不并入上面的 v0.1 统计。新增提示词、原始回复和操作事件的脱敏副本分别在 [数学证据](v0_2_math/published_runs/arena_20261002_selvar_pair01/README.md) 与 [其他领域证据](v0_2_other/published_runs/arena_20261002_other_pairs01/README.md)；先读结果，日志仅作二级证据。

2026-10-03 最新 H2 资格检查：[中性补跑与强调版比较](v0_3_h2/RETRY_RESULTS.md)。同一对话，中性补跑 p(A)=50%，强调版 10%；旧中性 N 的 10% 未粗略复现，不能把差值归因于题面强调。原超时截止记录、补跑修订和三份脱敏收据分别保留；本次没有 H1 或额外变体调用。

## 从这里开始

1. [最新自然审问结果](naturalistic_study_1/SNAPSHOT_RESULTS.md)：9 个配置、实际成本与线索限制。
2. [自然审问协议](naturalistic_study_1/PROTOCOL.md) 和 [采集范围调整](naturalistic_study_1/COLLECTION_SCOPE.md)。
3. [自然审问公开证据](naturalistic_study_1/published_runs/nine_completed_20261003/README.md)：逐条提示词和回复，仅作二级证据。
4. [增量审阅交接](GPT_HANDOFF.md)：本次变化及旧实验不变的结论。

以下是 v0.1 的历史阅读路线：

1. [RESULTS.md](RESULTS.md)：本次真实结果、覆盖率、污染和结论边界。
2. [GPT_CONTEXT.md](GPT_CONTEXT.md)：任务定义、模型角色、源码与证据入口。
3. [运行过程](xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/published_runs/arena_20261002_direct_pilot01/README.md)：采集、平台干预、纠错与公开副本说明。
4. [冻结协议](xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/docs/01_SPEC.md) 与 [提示词模板](xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/prompts/templates/README.md)。

仓库包含源码、测试、22 个冻结案例、角色提示词，以及 67 条实际发送提示词和 66 条已保存 JSON 回复（含练习及污染题）。完整页面回复另外保存在公开日志中。原始日志是二级证据，先读汇总；日志包含主持人答案，不能整份发给被测模型。

## 本地使用与复核

Python 3.10+；分析仅依赖标准库。JavaScript 测试和采集辅助器另需 Node.js（在 PATH 上）。主持人 HTML 不需要安装依赖，也不会自动操作 Arena。

复核最新公开快照：`python -X utf8 -B scripts/analyze_naturalistic_snapshot.py`。无需 Arena 登录或本机原始记录，不产生模型调用。采集辅助器 [naturalistic_arena_operator.mjs](scripts/naturalistic_arena_operator.mjs) 只接受外部提供的浏览器 SDK 和冻结 bundle，不会自行启动浏览器。

```powershell
cd xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1
python -X utf8 -B -m unittest discover -s tests -p "test_*.py" -v
node tests/test_console.js
python -X utf8 -B tools/analyze.py --input published_runs/arena_20261002_direct_pilot01/logs --out ../../_verification/results
```

离线主持入口：[START_HERE.html](xia_bai_wang_pilot_v0_1/xia_bai_wang_pilot_v0_1/START_HERE.html)。浏览器运行需下载仓库后打开 HTML。逐题备用提示词在 `prompts/ready/`，动态质询的实际发送版本在本次 `published_runs/.../logs/*.json` 的 `sent_prompts` 字段。

本仓库保留原项目目录结构。`runs/` 是本机原始证据，Git 排除；`published_runs/` 是提示词与回复不改字的公开副本，已移除私有会话链接、账户截图和机器路径。旧包中“没有真实模型数据”的说明只描述初始冻结交付，当前结果以本页及 RESULTS 为准。
