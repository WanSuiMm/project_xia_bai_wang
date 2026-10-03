# v0.4 Active Verification

先读 [RESULTS.md](RESULTS.md)，再读 [PROTOCOL.md](PROTOCOL.md)。这轮只研究：模型会不会选择能区分双方的验证、使用真实结果更新判断，以及及时停止。H2 暂停。

角色固定：GLM-5.2 (max) 在隔离会话中生成 A/B；Gemini-3.8-Flash-high 当裁判；本地确定性代码当主持人。均使用 Arena Direct。每题双方只生成一次，预测冻结；裁判初始只看解释和输入菜单，每次验证才收到所选输入的双方预测与主持人真值。

六个新背景题，每题三次独立裁判会话。同题的三条轨迹共享双方回答，不能当作三个独立背景。原始证据在 Git 排除的 `runs/arena_20261003_active01/`；[脱敏公开证据](published_runs/arena_20261003_active01/README.md) 保留提示词和最终 JSON 回复。采集完成后按用户要求发布，旧版本证据不改写。

从仓库根目录复核：

```powershell
python -X utf8 -B scripts/analyze_active_verification.py
```

源码入口：[core.cjs](core.cjs) 的 `speakerPrompt`、`judgeInitial`、`judgeFollow` 生成提示词，`observation` 给出冻结预测和真值，`auditTrajectory` 检查逐步提示词及主持人结果。`../scripts/prepare_active_verification.py` 只用于首次冻结，已有 `bundle.json` 时拒绝覆盖；不要把完整 bundle、角色标签或全量日志发送给被测裁判。
