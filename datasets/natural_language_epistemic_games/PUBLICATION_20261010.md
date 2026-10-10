# 100 世界资料库公开交付

用户在资料建设完成后授权将本批材料、代码、配置和离线检查上传到现有项目 GitHub。此前各材料快照里的“本任务未发布”与 `publication_authorized_by_this_file=false` 描述编写时的范围；本次单独授权不更改这些冻结字节，也不授权付费实验。

## 先读什么

1. [100 世界目录](curated100_20261010/CATALOG.md)和[资料说明](curated100_20261010/README.md)。
2. [复核范围与修正](curated100_20261010/MATERIAL_REVIEW.md)、[小型审计](curated100_20261010/audit.json)、[哈希清单](curated100_20261010/manifest.json)。
3. [共同配置](dev24_20261010/EXPERIMENT_CONFIG.json)与[角色提示](dev24_20261010/PROMPT_MODULES.json)。
4. 需要逐题证据时再读 `worlds.jsonl`、单世界 JSON、旧来源清点和开发资料册。不要把包含 Host 标注的完整记录交给游戏角色。

## 本批包含什么

| 项目 | 已完成状态 |
|---|---|
| 来源世界 | 100：30 旧世界、24 已有开发世界、46 新候选世界 |
| 领域与正文 | 19 个领域；代表来源共 36,160 英文词 |
| 同家族版本 | 另保留 12 份版本；不增加世界数 |
| 标注 | 70 个世界使用统一 S/N/I/U/C schema；30 个旧世界尚待规范，26 个保留可找到的原格式标注 |
| 来源保真 | 42 份旧来源与原始 JSON 字段相等；已有 24 个世界的文件哈希保持不变 |
| 初始角色投影 | 700 次；隐藏目录标题、Host 标注、版本与出处，Reader 额外获得来源 |
| 行为采集 | 本次新增模型请求 0，新增对话 0 |

所有资料为合成自然语言材料。本批允许在公开固定集合上设计未来配对研究；公开本身不证明材料曾被任何模型训练使用。`candidate_test` 是新材料的创作分组，不能在公开后据此声称它们是保密、未曝光的确认性 holdout。独立性、分组及泛化范围需要单独论证。旧 Arena 与 OpenCode 结果保持各自历史协议身份。

本次只交付源材料及离线工具。仍未实现或运行完整多轮 collection runner，尚未核验当前模型接口和实际推理设置，也没有冻结付费采集规模。Qwen3.8-Max ↔ GLM-5.3 使用共同任务、采样和输出控制；服务端默认推理不代表隐藏计算量相等。

## 离线复现

从仓库根目录运行，需要 Python 3.9 或更新版本的标准库，不需要 API key，不联网，不调用模型：

```text
python -X utf8 -B scripts/verify_natural_language_publication.py
python -X utf8 -B scripts/build_natural_language_corpus100.py audit
python -X utf8 -B scripts/test_natural_language_corpus100.py
python -X utf8 -B scripts/test_natural_language_dataset.py
python -X utf8 -B scripts/build_natural_language_corpus100.py packet --world CW025 --role judge
```

构建脚本的 `build` 子命令可以重建派生目录和 JSONL；阅读与验证无需重新生成冻结快照。仓库包含构建所需的旧来源字段、原开发 manifest、共同配置和两个构建模块。Git 属性针对本批哈希绑定文件保留原始字节，避免 Windows 换行转换破坏验证。

[发布清单](publication_manifest_20261010.json)在原 100 世界 manifest 的 99 个输入之外，另外绑定原开发 manifest、测试、发布验证器和附带文档等实际依赖。它不改写原材料清单；验证器检查两套原始哈希，并从仓库内来源重新计算目录记录与审计后同保存快照比较。

本次未包含凭据、账户或会话链接、私有调用目录、隐藏推理、机器启动记录及无关论文修改。当前提交与上一交付的最小差异及 reviewer 问题见仓库根目录 `GPT_HANDOFF.md`。
