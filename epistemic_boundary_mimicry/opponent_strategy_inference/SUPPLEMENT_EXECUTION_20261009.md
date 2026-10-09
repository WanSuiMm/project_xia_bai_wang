# OSI48 补跑启动快照

2026-10-09。用户要求补全缺失项，并明确取消本次 GitHub 上传。本页记录启动核验时刻，不代表整批已经完成。

## 已验证的启动状态

- 保留恢复批次 `_02` 的两条严格有效 Qwen 回复，没有重跑它们。
- 按原排程冻结其余 46 个位置；提示词和模型参数保持不变，见[补跑修订](SUPPLEMENT_PROTOCOL_20261009.md)。
- 第一条补跑为 `OSI_GLM_REFRESHED_H4_ONESA_R2`，HTTP 200，返回模型 `glm-5.3`，结束原因 `stop`，严格解析有效。
- 该条报告 `p_A=0.5`、`ABSTAIN`；usage 为 input 626、output 261、total 887 tokens。它与该格 oracle 一致，但不构成完整历史反转／重置效应。
- 一次启动核验时：补跑已派发 2 条，收到 1 条有效回复，连同保留结果共 **3/48 有效**；第二条补跑正在进行。
- 后台 worker 存活，启动收据中的 manifest SHA-256 与冻结 manifest 一致。主机、PID、会话映射与启动日志仅保存在忽略的私有运行目录。

其余 45 条由同一顺序 worker 继续派发。没有新 Speaker、额外重复、模型回退或 GitHub 上传。接口错误和截断按补跑修订停止；无效的最终回答不按正确答案修补。

## 本地入口

运行目录：`epistemic_boundary_mimicry/runs/opencode_go_20261009_opponent_strategy_inference48_supplement01`。

worker 结束时运行一次离线合并分析，产物位于该目录的 `analysis/completion_summary.json` 与 `analysis/RESULTS.md`。它把保留的两条回复与补跑位置合并为原定 48 个格，并另报全部物理尝试数。原始计费失败与 GLM 无效收据保留。

```text
python -X utf8 -B scripts/analyze_opponent_strategy_completion.py
```

该命令只重建本次补跑的派生分析，不发送 API 请求。没有创建监控或循环轮询；本页是历史启动快照，最终状态以实际收据和合并分析为准。
