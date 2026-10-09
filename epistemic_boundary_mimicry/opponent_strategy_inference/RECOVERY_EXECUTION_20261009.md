# OSI48：新凭据恢复的启动核验

核验时间：2026-10-09 18:28:53（Asia/Shanghai）。这是一次启动快照，后续状态以新运行的收据为准，不是完整结果。

用户提供替换凭据后，按[凭据恢复修订](CREDENTIAL_RECOVERY_20261009.md)建立独立新运行 opencode_go_20261009_opponent_strategy_inference48_02。原运行的一条 HTTP 403/payment 错误、零模型回答和 47 个未发送位置保持不变，见[原截止记录](RESULTS_20261009.md)。

## 已核实的启动状态

| 项目 | 核验快照 |
|---|---:|
| 新批次计划请求 | 48 |
| 已派发 | 2 |
| 已收到模型回答 | 1 |
| 严格／接受有效回答 | 1 / 1 |
| 首条 HTTP 状态 | 200 |
| 首条实际模型 | qwen3.8-max |
| 首条结束原因 | end_turn |
| Worker | 存活、RUNNING |
| 私有启动收据 | 已保存 |
| Manifest 哈希绑定 | 匹配 |

首条请求 OSI_QWEN_PERSISTENT_H7_ONESB_R2 是原来仅有 HTTP 错误的位置；本次收到严格有效 JSON。它计入新批次 48 次，不另作额外付费 smoke。新凭据已实际通过 Qwen 接口；这次快照尚不声称所有请求或另一模型已经完成。

新旧两批的 schedule 和 48 条提示词逐字节一致。只替换鉴权输入；模型、温度、推理参数、输出上限、解析和分析规则均不变。新冻结包同时绑定恢复修订和隐藏输入启动器。替换凭据只经 getpass 和子进程环境传递，没有写入文件、命令参数或持久凭据设置。

核验在与启动器相同的权限环境中完成，保存为新运行下 launch/dispatch_verification_elevated.private.json。较早普通权限检查未能看见 worker 的 PID；该快照保留，不据此判定 worker 已退出。

这是派发及接口成功的证据，不是历史反转、精确后验恢复或全批完成的科学结论。Worker 在有限排程结束后自行生成 analysis/summary.json 和 analysis/RESULTS.md；不增加重复调用或后台监控。

## 入口

新运行的离线审计：

    python -X utf8 -B scripts/run_opponent_strategy_inference.py --run epistemic_boundary_mimicry/runs/opencode_go_20261009_opponent_strategy_inference48_02 --audit

运行结束后离线分析：

    python -X utf8 -B scripts/analyze_opponent_strategy_inference.py --run epistemic_boundary_mimicry/runs/opencode_go_20261009_opponent_strategy_inference48_02

收据和启动记录均在 Git 忽略的 runs 目录内。当前任务没有 GitHub 上传。
