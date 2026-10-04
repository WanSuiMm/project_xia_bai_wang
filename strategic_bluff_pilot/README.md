# Natural versus strong strategic bluff

已全部补完：[8 个终局结果](COMPLETED_RESULTS.md) → [最后两场及取消上限修订](COMPLETION04_PROTOCOL.md) → [完整公开收据](published_runs/eight_completed_20261004/README.md)。natural 和 strong 各 4 场，均判断正确；最后两场的次数限制已取消，分别 7 次追问和 0 次追问后自行停止。两份独立资料、失败后的补跑和协议修改限制结论。复核：`python -X utf8 -B scripts/analyze_strategic_snapshot.py --completed`。早期快照和失败记录保留。

2026-10-04 公开快照：8 个配置已有 **6 个完整终局**，natural 和 strong 各 3 场且均判断正确；另外两项缺少终局。阅读顺序：[结果与限制](SNAPSHOT_RESULTS.md) → [冻结协议](PROTOCOL.md) → [补跑修订](RETRY_PROTOCOL.md) → [逐场提示词与原始可见回复](published_runs/six_completed_20261004/README.md)。从仓库根运行 `python -X utf8 -B scripts/analyze_strategic_snapshot.py`，仅依赖标准库和公开文件，无需登录或本机私有记录，不产生模型调用。公开 bundle 含资料和答案标签，不能整份发给被测角色。下面保留早期采集截止说明，不能当作当前进度。

用户随后授权继续六个失败配置，见 [补跑协议](RETRY_PROTOCOL.md) 和 [补跑进度](RETRY_RESULTS.md)。补跑使用原资料与配置、全新独立会话，保留第一次截止记录。当前 5/6 已尝试，S01 两场 strong 完成且均正确（1 次和 4 次追问）；S02 两个 Claude Speaker 配置再次受截断／报错影响，Gemini natural 的裁判在实际 reCAPTCHA 处待恢复，最后一个 strong 配置未开始。普通错误的相同提示词重试单独记载。下段统计仅描述第一次截止，不是合并补跑后的进度。

本轮已停止采集：8/8 场均尝试，2/8 场完成，保存 26/32 条完整回复，另保留 3 条截断输出；3 条裁判回复因平台／验证问题缺失。两个完整终局都属于 S01 的 natural 条件，分别追问一次和两次后正确判断。strong 条件没有终局，四个 natural/strong 配对全部不完整，结论是 `NO_COMPLETE_PAIRS`，不能估计条件差异。具体线索和资料一致性限制见 [观察](OBSERVATIONS.md)。无待处理模型请求，也没有后台监控。

用户于 2026-10-03 授权的新 8 场资格小试：2 份全新资料 × Claude Sonnet 5 High / Gemini 3.1 Pro Preview 两个方向 × natural / strong 两种 Bluffer 指令。只改变 Bluffer 指令套装，Knower 和 Judge 指令保持一致；配对席位相同，每场独立会话，不复用开场。

先读 [冻结协议](PROTOCOL.md)，再读 [当前结果](RESULTS.md)。种子借用制度和鱼类斑纹资料、完整冻结 bundle 和原始收据保存在本地，未公开。旧自然审问研究的九个已完成配置不并入这轮，也不作为新条件的因果对照。

从仓库根运行 `python -X utf8 -B scripts/analyze_strategic_bluff.py` 复核当前本地记录；分析只读收据，没有模型调用。`scripts/prepare_strategic_bluff.py` 只准备首次冻结，拒绝覆盖已有运行。浏览器采集辅助器接受 studyDir 参数区分新旧研究，并仅对 strong 条件的未知情 Speaker 使用强指令。

目标是检查强策略指令是否实际改变 bluff 行为及判断，不能将小样本差异归因于 post-training、稳定 ToM 或审问因果收益。没有后台监控，不自动扩大场数或推送私有新材料。
