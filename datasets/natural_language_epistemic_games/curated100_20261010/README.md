# Who Really Knows? — 100 个来源世界资料库

本批按用户 2026-10-10 的决定，将资料规模定为 **100 个不同来源世界，总量包含可复用旧题**。这是自然语言研究材料库，不是已经完成的 100 场对话，也不是 100 个已认证 iid 测试样本。当前范围为离线编写、整合和检查，不启动付费 API 或发布。

## 从这里开始

1. [目录](CATALOG.md)：全部 100 个世界及来源、分组、标注状态。
2. [规模与分析边界](CORPUS_PLAN.json)：30 个旧世界、24 个已有开发世界、46 个新候选世界。
3. [旧题清点](LEGACY_INVENTORY.md)与[完整旧来源](LEGACY_INVENTORY.json)：保留 30 个原 case 家族及其版本，附原始位置。
4. [新题编写规范](AUTHORING.md)与 `new_worlds/NL025.json`–`NL070.json`：完整来源、来源支持与缺口标注。
5. [材料复核](MATERIAL_REVIEW.md)、[离线检查](audit.json)与[内容清单](manifest.json)：复核范围、数量、来源溯源、哈希和初始角色投影；不证明零标注错误或统计独立。
6. [共同实验配置](../dev24_20261010/EXPERIMENT_CONFIG.json)与[共同角色提示](../dev24_20261010/PROMPT_MODULES.json)：Qwen3.8-Max ↔ GLM-5.3；同局 Speakers 同模型、独立会话；冻结权重。

`worlds.jsonl` 是生成的统一 Host-only 材料文件，每行一个世界，包含完整来源与版本信息；**不得将整行交给角色**。角色消息只能使用下面的字段白名单投影命令。它会保留 Reader 的来源访问，同时去除 Bluffer/Judge 的来源、标注与出处信息。

目录标题可能概括私人资料中的事件或结果，因此也属于 Host 标签，不进入角色消息。三个角色统一看到通用 topic 和 `public_context`；Reader 另外获得来源标题及原文。旧库的公共背景原样保留，其历史披露量可能不同，不能据此称全部世界的公共信息量已经匹配。

## 计数与复用

- 30 个旧家族包括 N01–N12、S01–S02、EB01–EB06、SQ01–SQ04、CS01–CS06。座位、方向、策略、重试、replay、假来源与反事实版本均不增加世界数。
- 原 24 个开发世界原样引用，保留原始清单和哈希，不覆盖已有证据。
- 新增 46 个世界属于 `candidate_test`：尚未用模型回答调整材料或提示。它们仍需语义资格检查、分组审阅和采集前冻结，不能提前宣称是最终确认性测试集。
- 30 个旧世界在本库保留完整 source 与谱系，可找到的原格式 analyst notes、host map 或问题记录同时保留在 `legacy_evaluation`。这些历史标注尚未规范到新 schema；反事实插入版本的答案不能误当作遗漏版本的答案。

旧来源可以在共同协议下重新采集新对话，但历史 Arena/OpenCode 结果不能直接混成同一实验。旧世界、开发世界和新世界分别报告；重复调用和回合是嵌套观测。将同一事实骨架继续改写时，归入同一家族。当前 family/case 谱系不保证不同世界独立或同分布。

## 离线复现

从仓库根目录运行，仅使用 Python 标准库，不联网、不读密钥、不发送模型请求：

```text
python -X utf8 -B scripts/build_natural_language_corpus100.py audit
python -X utf8 -B scripts/test_natural_language_corpus100.py
python -X utf8 -B scripts/build_natural_language_corpus100.py packet --world CW001 --role judge
python -X utf8 -B scripts/build_natural_language_corpus100.py packet --world CW025 --role reader
python -X utf8 -B scripts/build_natural_language_corpus100.py packet --world CW071 --role bluffer --strategy boundary_aware
```

生成本批目录、JSONL、审计与哈希清单：

```text
python -X utf8 -B scripts/build_natural_language_corpus100.py build
```

初始消息投影不是对局 runner，逐轮私有记忆、概率更新、失败恢复与停止路由尚未在本任务实现或执行。正式采集前需要冻结条件矩阵、世界分组、主要终点、推理与总费用预算；当前统一配置的服务端默认推理政策不代表两模型内部计算量相等。
