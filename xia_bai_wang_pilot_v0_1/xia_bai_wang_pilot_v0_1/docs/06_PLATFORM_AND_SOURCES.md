# Arena 使用与来源核验

核验日期：2026-10-02。以下只核验平台相关信息，不把前文聊天中的模型发布时间、限免截止、会议奖项或论文争议当作已核验事实。本包不依赖这些说法。

## 模式

Arena 官方说明 Direct 可以手选模型，Agent 则有 web search、bash 等工具。官方 Max 介绍还明确包含搜索能力。因此 **Direct 不等于天然无工具**，不能根据页面没展示浏览过程就证明 tool-free。选固定文本模型，避开 Max/自动路由/Search/Agent；后台不可观测项记录为 unknown。

- [A1] Model selector — https://help.arena.ai/articles/1858200927-arena-experiments-new-model-selector
- [A2] Agent Mode — https://help.arena.ai/articles/5432423882-how-to-use-agent-mode
- [A3] Multimodal Max — https://arena.ai/blog/multimodal-max

## 使用限制

Arena 条款 §5 包含自动访问、自动查询、抓取和榜单操纵方面的限制；§3.3.5 还对欺骗性内容作宽泛限制。本包只有本地整理和手动提示词，不做爬取、网页操作或限流绕过；提示词明确是所有参与者知情的虚构游戏。这并不等于获得了平台对本研究的特别授权。遇到拒绝不要绕过；批量收集、发布第三方输出或扩大研究前应核对适用条款/取得所需许可。

- [A4] Terms of Use — https://help.arena.ai/articles/5629909088-terms-of-use
- [A5] Rate limits — https://help.arena.ai/articles/8931786544-arena-how-to-rate-limit

## 隐私

官方 FAQ 明确 Direct 的 prompts 也会被收集用于研究。隐私政策说明用户内容可能与模型提供方共享或公开。本包只含合成案例；不要发送私人材料，也不要把上线后的案例仍视为保密确认集。

- [A6] FAQ — https://arena.ai/faq
- [A7] Privacy — https://help.arena.ai/articles/3765052346-privacy-policy

## 本包的可靠性范围

数据的唯一真值来自本包可复核的生成过程；不可辨识性论证为本包的形式化推导。没有引用未实际核验的 Decrypto/ACL 具体结论来证明本方案的新颖性，也没有声称完成文献穷尽检索。

本包不复用商业桌游题卡、图片或品牌素材；“瞎掰王”只用于说明灵感来源。模型可用性以运行时界面为准；没有验证 Sonnet 5.5 或任何具体名称此刻可用。
