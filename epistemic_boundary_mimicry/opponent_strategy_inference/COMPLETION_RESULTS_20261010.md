# OSI48 完成结果：历史信息能被使用，错误仍然存在

2026-10-10。**48/48 个原定位置已有严格有效回复，共 51 次物理请求。** 这是保留 46 条有效回答后、按缺失位置补齐两条的修订汇总，**不是原始 4096-token GLM 配置的完整运行**。两条末尾补跑使用 16384-token 上限，参数变化和失败均单独保留。

先读本页，再读[原协议](PROTOCOL_20261009.md)、[理论与精确后验](THEORY_V2_20261009.md)、[两条输出预算修订](TAIL_COMPLETION_PROTOCOL_20261010.md)，最后查[公开证据与离线复现](../published_runs/go_opponent_strategy_inference48_completion_20261010/README.md)。[论文初稿](../../paper/draft_20261009/PAPER_V1.md)整合各阶段证据；此前 JES32 的失败结论不变。

## 这次问的是什么

当前 A/B 的四项回答固定为一方 `1111`、另一方 `0000`。Reader 的来源由四个独立公平 bit 构成；non-reader 在一局中用同一个未知倾向参数回答。Judge 看到八条身份已知的旧 non-reader 回答，并被明确告知：当前倾向与旧倾向延续（Persistent），还是重新独立抽取（Refreshed）。

当历史中 1 的次数为 1、4、7 时，Persistent 下 `1111` 一方是 Reader 的理论概率分别为 `66/67`、`.5`、`1/67`；Refreshed 下均为 `.5`。这是给定模型族与采样规则的概率归因题，没有新 LLM Speaker，也没有自然语言自由追问。

## 注册指标

下表按每个模型／条件的 12 个选定刺激格等权计算。动作符合是相对已知后验及损失函数的最优动作，不是验证了实际身份标签。

| 模型 | 条件 | 严格有效 | 后验 MSE ↓ | 最优动作符合 | 后验误差 ≤ 1e-4 | 超额预期决策损失 ↓ |
|---|---|---:|---:|---:|---:|---:|
| GLM-5.3 | Persistent | 12/12 | .07029953 | 10/12 | 9/12 | .16169154 |
| GLM-5.3 | Refreshed | 12/12 | 0 | 12/12 | 12/12 | 0 |
| Qwen3.8 Max | Persistent | 12/12 | .000005783 | 12/12 | 11/12 | 0 |
| Qwen3.8 Max | Refreshed | 12/12 | 0 | 12/12 | 12/12 | 0 |

两模型的全部 **24 条 Refreshed 回复均为 `.5 / ABSTAIN`**，包括不对称的 1/8 和 7/8 历史。它们在这些明确告知重置的刺激上没有把旧历史当成当前身份线索。

| 模型 | Persistent 的历史反转 Δ | Refreshed 的 Δ | 两条件之差 | 与理论交互的绝对误差 |
|---|---:|---:|---:|---:|
| GLM-5.3 | .73864366 | 0 | .73864366 | .23150560 |
| Qwen3.8 Max | .96806664 | 0 | .96806664 | .00208261 |
| 理论目标 | .97014925 | 0 | .97014925 | 0 |

Δ 把报告统一为 `1111` 一方是 Reader 的概率，取历史 1/8 时的均值减去 7/8 时的均值。两模型在这个有限集合上都有预测方向的历史反转；Qwen 更接近数值目标，GLM 的均值被一个严重错误明显影响。没有新增总 PASS/FAIL 门槛。

## 保留的错误

所有严格有效但错误的回答都保留，没有重跑。

| 请求 | 报告 p_A | 理论 p_A | 动作 | 说明 |
|---|---:|---:|---|---|
| GLM / Persistent / H1 / ONESA / R1 | .0667 | .98507463 | B | 大幅后验错误，选择与 oracle 相反 |
| GLM / Persistent / H7 / ONESA / R1 | .0100 | .01492537 | B | 概率偏差，动作仍最优 |
| GLM / Persistent / H7 / ONESA / R2 | .0275 | .01492537 | B | 末尾预算修订补跑；概率偏差，动作仍最优 |
| Qwen / Persistent / H1 / ONESA / R2 | .97674419 | .98507463 | A | 概率偏差，动作仍最优 |

另有 GLM / Persistent / H7 / ONESB / R2 报告 `p_A=.9851`，却选择 **B**。概率在 1e-4 精度内符合 oracle，但该选择同时违反 oracle 最优动作和它自己报告的概率。因此后验误差与决策一致性必须分开报告。合计 46/48 个动作符合 oracle，47/48 个动作符合自身报告；44/48 个后验在 1e-4 内。

## 尝试记录与参数修订

| 批次 | 实际请求 | 严格有效回复 | 保留的失败 |
|---|---:|---:|---|
| 原始 01 | 1 | 0 | HTTP 403，payment 分类，无模型回答 |
| 凭据恢复 02 | 3 | 2 | 一条 GLM HTTP 200／ValueError；原始 envelope 已丢弃，具体原因未知 |
| 缺失补跑 01 | 45 | 44 | 一条 GLM `length`，4096 output tokens，无最终可见 JSON；最后一个位置未发送 |
| 末尾补跑 02 | 2 | 2 | 无新失败；两条 GLM 上限升至 16384 |
| 合计 | **51** | **48** | 三次失败均保留，与选择的 48 个格分开 |

22 条选定 GLM 回复使用 4096 上限，两条使用 16384；24 条 Qwen 回复使用 8192。末尾两条实际 output usage 为 358、575 tokens，不能据此证明“提高上限导致成功”，因为补跑也是新的随机调用。温度、模型、提示词、thinking/reasoning 请求参数及解析规则未变。原预算下的截止仍为 **46/48 有效，GLM Persistent 10/12**；其完整主指标没有被事后补权。

原始失败截止、恢复和启动快照均保留：[早期截止](CURRENT_RESULTS_20261009.md)、[凭据修订](CREDENTIAL_RECOVERY_20261009.md)、[46 位置补跑修订](SUPPLEMENT_PROTOCOL_20261009.md)、[启动快照](SUPPLEMENT_EXECUTION_20261009.md)。公开包提供全部 51 次安全收据、精确提示词、原始可见回复、逐格来源映射、代码与离线校验；不包含 key、账户／私有会话、主机路径、启动信息或隐藏 reasoning。

## 可以与不可以得出的结论

这些结果支持一个有限的行为判断：在给定策略族和历史生成机制时，模型的身份概率报告能随历史改变，并在明确重置条件下回到 `.5`。GLM 的严重后验错误及概率—动作冲突说明这种行为并不保证每次正确。

48 次选定调用对应 12 份不同可见提示词、两模型与两次重复，不是 48 个独立任务族。参数修订、每格仅两次调用及同一简化机制限制了推断。数值接近积分目标不证明内部实现了贝叶斯积分；本实验也没有检验真实 Bluffer 的策略学习、未知模型族推断、自然对话识骗或一般 Theory of Mind，更不构成模型能力排名。

## 离线复现

从 GitHub 仓库根运行，不需要 API key、不联网、不发送模型请求：

```text
python -X utf8 -B scripts/check_opponent_strategy_theory.py
python -X utf8 -B scripts/publish_opponent_strategy_completion.py --verify
```

先看汇总，再按请求 ID 查逐条证据。收集入口为 `scripts/run_opponent_strategy_inference.py`、`scripts/run_opponent_strategy_completion.py`、`scripts/complete_opponent_strategy_tail.py`；oracle 为 `run_opponent_strategy_inference.oracle`，注册指标为 `analyze_opponent_strategy_inference._cell`。
