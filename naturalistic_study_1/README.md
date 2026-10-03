# Naturalistic Study 1

研究问题：模型在看不到新资料时，如何通过自由对话判断哪位 Speaker 最初看过它？两个同模型、独立会话的 Speaker 中，一个获得完整虚构资料，另一个只获得公开背景并尝试表现得知情。Judge 自选对象、问题和停止时机，最多十次 ASK；Host 只转述回答，不提供真值。

当前公开快照：**9 个已完成配置，覆盖 5 份资料，最终判断 9/9 正确，追问 1–6 次**。这是完成子集的描述，不能推断总体准确率或审问收益。部分未看资料的 Speaker 透露缺少资料的线索，细节丰富度也可能成为简单线索。原计划 24 个配置；用户改为完成 12 个即停，目前还差 3 个。采集等待用户完成人机验证，没有后台监控。

阅读顺序：

1. [快照结果](SNAPSHOT_RESULTS.md) 与 [机器可读汇总](snapshot_analysis.json)。
2. [原始协议](PROTOCOL.md)、[串行续跑规则](RESUME_PROTOCOL.md)、[范围调整](COLLECTION_SCOPE.md)。
3. [公开证据](published_runs/nine_completed_20261003/README.md)：提示词、完整可见回复、角色席位和尝试状态。不要先读全部日志。
4. 历史记录：[最初速率限制截止](RESULTS.md)、[串行续跑](RESUME_RESULTS.md)、[单独授权的 N02 恢复](RECOVERY_RESULTS.md)。历史截止中的“尚未公开”仅描述当时状态。

公开 `bundle.json` 只包含 N01–N05 五份已完成题目的 source、背景和分析备注，不是完整原始冻结 bundle。其余新题继续本地保密。资料由 Codex 与受限子任务助手起草，是虚构游戏资料，不是现实研究发现。只有 Knower 收到 source；Bluffer 和 Judge 不接收 source 或分析备注。公开记录包含所有席位的私有提示词，因此不能整份转交给被测角色。

从 GitHub 仓库根复核，无需 Arena 访问或原始本地记录：

```powershell
python -X utf8 -B scripts/analyze_naturalistic_snapshot.py
```

此命令仅依赖 Python 标准库，检查公开文件哈希、角色隔离、开场和追问转述、ASK 数及终局评分，重新生成快照汇总。会话恢复检查在本地保留原私有链接进行，公开收据不能重新核验会话链接。浏览器采集代码见 [operator](../scripts/naturalistic_arena_operator.mjs)；它需要调用方提供 Browser SDK、文件接口和原始冻结 bundle。其他本地准备/分析脚本要求完整本地材料，不能用这份公开子集重建全部 24 个配置。

没有 passive、人类、匹配 token、自模型或 actor–observer 对照。本次不作 interrogation 因果收益、模型排名或 ToM 机制结论。旧实验和原始失败尝试都保持独立记录。
