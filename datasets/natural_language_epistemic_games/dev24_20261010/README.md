# Who Really Knows? — 自然语言开发资料集

**状态：资料编写与离线检查；尚未采集 Reader–Bluffer–Judge 对话。** 所有内容为新创作的虚构资料，语言为英语。开发材料允许公开阅读；未来确认性测试资料必须另建、隔离并在生成对话前冻结。

研究问题：没有私人来源的战略智能体能在多大程度上模拟真正的来源访问？主动质询如何改变可见信息，裁判能否利用这些信息？不微调，不用程序化二值回答替代自然语言交互。

## 从这里开始

1. [研究设计与边界](DESIGN.md)：完整目标、首批材料的作用、评价与识别限制。
2. [资料目录](CATALOG.md)：24 个开发世界，8 个领域，各 3 份资料。
3. [调查者资料册](CASEBOOK.md)：完整 source 与评估记录；**不得整本或整份 world JSON 发给游戏角色**。
4. [共同配置](EXPERIMENT_CONFIG.json)与[角色提示](PROMPT_MODULES.json)：Qwen/GLM 双向、同局同模型 Speakers、独立会话、共同预算与损失。配置为待接口核验的执行草案，没有发送请求。
5. [机器可读审计](audit.json)与[内容哈希](manifest.json)：结构、证据原文匹配、覆盖和角色信息路由，不替代语义复核。
6. [语义复核记录](SEMANTIC_REVIEW.md)：AI 交叉检查发现并修正的来源关系、公共背景泄漏与数学例子问题；尚未进行独立人工资格评审。

每个 `worlds/NLxxx.json` 包含公共背景、350–550 词私人资料，以及仅供实验者使用的来源支持、明确否定、推断、未说明候选与跨事实问题。后两类问题是评估/干预候选，不限制 Judge 自由提问。

## 离线使用

从仓库根目录运行，仅需 Python 标准库，不联网、不读取 key、不调用模型：

```text
python -X utf8 -B scripts/build_natural_language_dataset.py audit
python -X utf8 -B scripts/test_natural_language_dataset.py
python -X utf8 -B scripts/build_natural_language_dataset.py packet --world NL001 --role judge
python -X utf8 -B scripts/build_natural_language_dataset.py packet --world NL001 --role reader
python -X utf8 -B scripts/build_natural_language_dataset.py packet --world NL001 --role bluffer --strategy boundary_aware
```

`packet` 输出的是初始模型消息，不是 API 请求；没有配置任何发送入口。Reader 只收到公共背景与 source，Bluffer 与 Judge 不收到 source，所有角色都不收到评估记录。实际对话和私有记忆的逐轮路由由后续 collection runner 实现；当前投影检查不代表运行时已经验证。

一次性交付的材料与目录可以通过以下命令重新构建；这会更新本目录生成的开发报告，不触碰任何旧实验：

```text
python -X utf8 -B scripts/build_natural_language_dataset.py build
```

**规模边界：** 24 是本批创作世界数，不是确认性样本量，也不是统计独立性的证明。正式目标约 200–300 个世界仍需按效应目标、开发集方差与实际完整对局成本冻结。扩展应增加制度、关系、事件与证据结构，而不只是重命名。
