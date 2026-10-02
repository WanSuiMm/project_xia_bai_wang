# Arena pilot01：过程与实际提示词

完整结果先读仓库根目录 [RESULTS.md](../../../../RESULTS.md)。这是 2026-10-02 真实 UI pilot 的公开副本：D01 练习完成，P01/P02/P04 完整，P03 受污染后停止。没有为 GitHub 发布重跑任何模型请求。

## 过程

1. 登录与验证最初多次失败；用户恢复浏览器后，开始实际采集。技术失败保留在 D01 事件中，不当作模型答案。
2. 固定 Direct 显示模型 `claude-sonnet-5-5-high` 和 `gemini-3.8-flash-high`。每题说话人 A/B、交互裁判、N、E 均分开会话；冻结序列控制开场、每轮回答、N/E 的先后。
3. 本地 `operator_capture.py` 只在 loopback 提供记录表单，用冻结 `Core.buildPrompt` 产生下一条提示词并核验发送收据；它不调用 Arena API、不自动控制浏览器。实际发送和读取通过 Arena UI 完成。
4. D01 跑完 14 步，不进入正式统计。P01 跑完 14 步。P02 的匿名比较候选单独保留并跳过，随后采集恢复后标为固定模型的回复；14 步完成。
5. P03 第二轮 B 出现匿名候选，一条被误当作固定模型回复进入 P2。后续发现后，整题标记 `unexpected_model_change`，停止，不归入 clean 分析。第三轮误抓上一轮文字，未发给裁判；canonical raw 移除错误，`capture_errors` 保存原样。匿名候选保留，不按内容挑选。
6. P04 两次生成界面卡住，重载后读取服务端已有回复，没有重新生成；14 步完成。模型字数和 JSON 外说明的偏离原样保留。
7. 逐条核验 67 条提示词收据、完整题 JSON 与完整页面回复，运行原分析器。发布时对私有会话链接、账户截图、机器路径做脱敏；`raw` 与 `sent_prompts` 文本完全不变。

## 证据入口

- [run_status.json](run_status.json)：已完成和仍缺失的步骤。
- [results/report.md](results/report.md)：按原分析器生成的结果，包含 all-recorded 和 clean 两种口径。
- [capture_audit.json](capture_audit.json)：提示词匹配、重复、完整性、字数和格式偏离。
- [publication_manifest.json](publication_manifest.json)：每条 prompt/reply 的 SHA-256，确保脱敏未改正文。
- [logs/](logs/)：实际发送的 `sent_prompts`、评分 JSON `raw`、完整渲染回复 `rendered_full_by_step`/`rendered_sessions`、平台事件与纠错证据。先读上述小文件，再打开原始日志。
- [direct_battle_D01.json](direct_battle_D01.json)：练习阶段额外匿名候选，不是固定模型正式回复。

时间元数据是操作者采集/保存时间，不是可精确推断的模型生成时间；后续全文补存会更新保存时间。后台温度、工具与真实模型部署身份未经验证。

## 代码与复核

从冻结包目录运行：

```powershell
python -X utf8 -B published_runs/arena_20261002_direct_pilot01/audit_capture.py
python -X utf8 -B tools/analyze.py --input published_runs/arena_20261002_direct_pilot01/logs --out ../../_verification/results
```

上述 audit 会写回公开副本的派生核验字段；只读审阅请直接读 capture_audit.json。本地新采集需 Python 与 PATH 中的 Node.js，可运行 `python -X utf8 -B published_runs/arena_20261002_direct_pilot01/operator_capture.py`，打开它输出的 loopback 地址。此脚本按运行记录设计，只开放 D01、P01–P04，现有提示词/回复拒绝替换。

冻结通用模板在 `../../prompts/templates/`，逐题开场提示词在 `../../prompts/ready/`。主持人私有答案是合成游戏内容，随代码公开，但不能整份提供给被测角色。
