# 《瞎掰王》的统计 ToM 形式化：来源模拟、交互可识别性与归因校准

**Statistical Theory of Epistemic Interrogation: Source Simulation, Identifiability, and Attribution Calibration**

- 版本：v1.0，2026-10-07。
- 证据基线：`WanSuiMm/project_xia_bai_wang`，提交 `af15fd160e070ec39bb6a60c2d4f64a3474fee8d`；重点依据全量 claim audit、理论—证据映射和七条 Frozen replay 队列。[A1–A4]
- 文档性质：研究形式化与实验设计稿，不是已完成的 confirmatory study，也不是已经冻结并执行的预注册协议。
- 本文未调用实验模型 API，未补跑旧游戏，未修改仓库。新增内容是定义、推导、有限空间数学检查和候选 replay 方案。
- 数学定位：使用经典统计决策、信息论、序贯检验及适当评分规则。下文完整给出主要推导；不主张这些不等式具有数学文献意义上的原创性。

> **论文要研究的不是一个模型“究竟有没有心灵”，而是：在一个明确的信息结构中，哪些关于他人信息访问的区分能够从交互行为中恢复；LLM 又会把哪些可见差异当成这样的证据。**

## 阅读路线

需要快速确定下一步，读第 0、1、9、10、13、14 节。需要理论正文，读第 2–8 节。需要解释为什么这是一个 ToM 研究范式而不只是猜硬币，读第 11、12、15 节。第 16 节逐项列出对前面讨论的必要修正。

---

## 0. 总结：哪些内容已经成立，哪些值得 replay，哪些暂时只作模型

本文把项目分成三个层次：

$$
\underbrace{\text{信息结构与允许的交互}}_{\text{实验者可定义、可证明}}
\longrightarrow
\underbrace{\text{实际问答与来源忠实性}}_{\text{已有 audit 可观察}}
\longrightarrow
\underbrace{\text{裁判的概率报告与决策}}_{\text{replay 可干预}}.
$$

这三个层次不能相互替代。对话中出现一个错误解释，不等于模型内部持有某种特定因果模型；一次正确选择不等于找到了有信息的问题；一个 Frozen 弃权不等于验证了互信息为零。

### 0.1 核心理论结果

| 编号 | 结果 | 最重要的含义 | 当前是否能直接用旧 replay 检验 |
|---|---|---|---|
| P1 | 交互等价类与结构可识别性 | 区分“目标定义可识别”与“有限数据可恢复” | 否；主要规范任务定义 |
| P2 | 二元检验的 TV—Bayes 风险等式 | 可见差异必须是身份条件分布差异 | 否；自然语言分布尚未估计 |
| P3 | 自适应信息分解、固定/随机预算下界 | 追问数量不能代替信息获取量 | 否；需响应核或受控小模型 |
| P4 | 来源模拟的轮数无关紧界 | 没收到原资料也可能模拟到任何追问都无法区分 | 否；需可控生成器与策略 |
| P5 | 复合假设与稳健性 | 分别会识别已知骗法，不等于有通用识骗器 | 否；作为泛化边界 |
| P6 | 随机目标的自适应 null | 目标不进入生成过程时，完整对话与目标独立 | 可检查协议；replay 测模型是否遵守其后果 |
| P7 | 选择性归因的紧界 | 弃权不能从零信息数据中筛出高准确率子集 | 可作评价准则，不能从小样本反推 TV |
| P8 | 后验、评分与采样方差分解 | 区分无根据概率偏移与生成不稳定性 | **是，主 replay 对象** |
| P9 | 已知噪声线索的后验不变性 | 区分使用真实证据与始终输出 0.5 | **是，优先补充** |
| P10 | 座位交换的奇偶分解 | 分离 A/B 标签偏好与跟随内容的偏好 | 是，机制定位补充 |
| P11 | 零即时信息问题的自适应收益 | 好问题可能只帮助选择下一问 | 不能由终局 replay 证明 |
| P12 | 共同迎合导致信息收缩 | 诱导出具体回答不等于获得诊断信息 | 需新的匹配 Speaker 干预 |

### 0.2 推荐的首个实验

只先做**固定七条 Frozen 对话的 Blind/Informed 终局 replay**，保留两个既有模型标签、独立重复、原始终局隔离；主终点是报告概率相对真实 null 后验的超额 Brier 风险，而不是随机目标命中率。后续用双向可靠线索与无对话基线检查“是否真的区分有信息/无信息”。不把所有候选实验同时启动。

### 0.3 本文的候选 thesis

> **Interactive epistemic attribution is a statistical identification problem. Observable differences in content, expression, or apparent provenance need not identify the target access relation. We use controlled information structures to distinguish the information present in a dialogue from the evidence attributed to it by language models.**

这是一项待用 replay 补强的研究纲领，不是已经得到的总体模型结论。

---

## 1. 审计后的事实基线

### 1.1 已有语料与独立性

全量 audit 覆盖 13 条 canonical API trajectories、107 次可见 Speaker 回答、57 个 ASK、12 个终局理由；材料来自 6 个 family。五条是 Strong/Boundary-aware 战略对话，八条是 Frozen，其中一条未完成。全部终局理由按 72 个操作性句/分句单元审阅；Speaker 回答按 1,952 个操作性单元覆盖。[A1]

这不是 1,952 个独立样本，也不是 107 个独立受试者。结构为：

$$
\text{family}\supset\text{trajectory}\supset\text{answer}\supset\text{coding unit}.
$$

同一 family 的不同方向、条件、recovery 前缀共享材料。模型调用重复可用于研究给定输入下的采样变动，但不会创造新材料 family。现有 six-family 语料也是便利性探索集合，不是自然场景的概率抽样。

### 1.2 审计支持的观察

**来源与自洽性。** Reader 总体贴近自己的资料，但复合单元中有未经来源明确支持的补全，且逐字引用存在误差。Bluffer-proxy 的 375 个单元中，72 个为 new detail、302 个为 consistent elaboration；本轮没有保守认定出由明确前后承诺确立的 revision/contradiction。这不是“Reader 零错误”或“Bluffer 绝无矛盾”。[A1]

**前提响应。** 严格筛选得到 11 个分组机会，来自五条轨迹但只有 EB01/EB02 两个 family。Reader 多拒绝将缺失项当作来源事实，Bluffer 多作具体来源式回答；普通细节请求和显式候选检查混杂，不能直接估计统一因果 uptake effect。[A1]

**裁判理由。** 审计最扎实的观察是：裁判将措辞接近公共背景、晚出现的细节、引用方式、文本组织等差异，推成缺乏支持的来源或目标身份判断。72 个理由单元中，24 个支持、34 个复合/歧义、9 个不受支持的推断、5 个与来源/对话冲突的误读；不能把这些计数直接称作总体理由错误率。[A1]

**问题依赖。** 57 个 ASK 中，28 个能链接到此前具体回答，28 个为一般/独立请求，1 个歧义。这证明存在可见的回答依赖，不证明追问带来因果正确率收益或正互信息增益。[A1]

### 1.3 最需要保留的审计区分

| 容易混淆的两个对象 | 正确区分 |
|---|---|
| 与 target source 不符 / 与自己之前回答矛盾 | 前者是 documentary mismatch，后者是 internal inconsistency |
| 没在初次概述出现 / 后来才编造 | 不完整概述允许后来披露原本存在的内容 |
| source 提到某张表 / 当前文档包含那张表 | 提及 artifact 不等于附带 artifact |
| 意义一致 / 逐字一致 | 引用漏词可以保留意义但破坏 verbatim fidelity |
| 文档确实更像原稿 / 它是随机 target | 真实的 provenance 差异也可能与 target 无关 |
| 裁判理由说明了什么 / 裁判内部实际如何计算 | 前者可观察，后者不能由理由文本直接识别 |

EB06 的 opening caution、EB02 漏写 `left`、EB05 的 public-brief alignment 是上述区分的具体证据，不应再被改写成“已经验证的内部机制”。[A1]

### 1.4 固定的终局 replay 队列

[A3] 固定了七条完整 Frozen 对话：

| ID | 原 ASK 数 | 材料 family |
|---|---:|---|
| EB01_D1_symmetric_frozen | 4 | EB01 |
| EB02_D1_symmetric_frozen | 9 | EB02 |
| EB03_D1_symmetric_frozen | 4 | EB03 |
| EB04_D1_symmetric_frozen | 3 | EB04 |
| EB05_D1_symmetric_frozen | 6 | EB05 |
| EB05_D2_symmetric_frozen | 2 | EB05 |
| EB06_D1_symmetric_frozen | 4 | EB06 |

EB06_D2 保留已发生的问答，但没有终局，不加入默认终局 replay 队列。七条来源于六个 family；原裁判六条为 GLM 标签、一条为 Qwen 标签，不能称原始设计是平衡跨模型研究。[A3]

**当前 audit 未建立：** persistent latent dossier、false-presupposition 的因果机制、active 相对 passive 的收益、文风的独立因果效应、模型总体排名，以及自然回答核的 TV/KL/MI 数值。[A1–A2]

---

## 2. 统一对象：不要把“知道”“拿过资料”“被指定为 target”合成一个变量

### 2.1 符号与约定

除特别说明外，对固定公共背景 $C=c$ 条件化；下式可省略 $c$。概率空间取标准 Borel 空间，使条件分布存在。涉及极小极大交换时先限定有限观察空间及闭凸紧集合。所有 KL 和互信息用自然对数，单位为 nats；需要 bits 时除以 $\ln 2$。

| 符号 | 定义 |
|---|---|
| $S_i$ | Speaker $i\in\{A,B\}$ 实际收到的有限文档，或空输入 |
| $A_i^{\rm access}$ | 是否实际获配某份来源的操作性访问事实 |
| $F_S$ | 文档明确表达的命题集合；不等于整个真实世界 |
| $G$ | 文体、表面来源、编辑结构等 nuisance/provenance 特征 |
| $K\in\{0,1\}$ | 待预测目标；固定 $K=1$ 表示 A，$K=0$ 表示 B |
| $\Theta$ | 完整建模状态，可包含来源、角色、策略类型与私人记忆 |
| $M$ | 实验生成机制；尤其包含 target 的指定规则 |
| $Q_t=(J_t,q_t)$ | 询问对象及问题文本，$J_t\in\{A,B,\mathrm{BOTH}\}$ |
| $Y_t$ | 本次收到的可见回答；BOTH 时为回答对 |
| $H_t$ | 截至 $t$ 的公共问答历史，不含私卡或隐藏 reasoning |
| $\pi$ | 裁判的提问、停止策略 |
| $\beta_i$ | Speaker 策略；可有私人状态，不假设完美忠实 |
| $\tau$ | 由裁判历史决定的停止时间 |
| $\hat p$ | 模型报告的 $P(K=1)$，不是直接读取的内部 posterior |
| $d$ | 最终动作 $A,B,\bot$，其中 $\bot$ 为弃权 |

### 2.2 原始访问任务与随机目标任务是两种实验

**战略访问任务。** 先决定谁收到 target source，再按访问条件生成行为。此时 $K$ 与来源分配、角色指令相关，可能通过行为产生身份信号；也可能被模拟消除。

**对称来源随机目标任务。** 两席各有一份来源，来源、座位、策略输入先固定；再独立抽签指定哪席是 target。该标签不改变任何可见或私有生成输入。这时预测的是一个随机指定关系，**不是谁有资料**，因为两席都有。

Strong 与 Boundary-aware 是不同策略提示条件；Frozen random-target 是识别性对照。三者不是已证明单调的“骗术强度轴”。

### 2.3 来源边界的非神秘定义

对一个已消歧命题 $\varphi$，定义相对文档的判定：

$$
\mathsf{Rel}_S(\varphi)\in\{+, -, ?, \mathrm{ambiguous}\}.
$$

其中 $+$ 为明确支持或在声明的推理规则下蕴涵，$-$ 为明确反驳，$?$ 为两者皆不成立，歧义单列。必须另记“明确写出”和“推导得到”；自然语言未消歧时不得强行套二值逻辑。

另定义说话者的**归属方式**：

$$
\mathsf{Attr}(\varphi,Y)\in\{
\text{source assertion},\text{qualified inference},
\text{hypothetical},\text{uncertainty/refusal}\}.
$$

可操作的 overclaim 是：命题无充分来源支持，却被作为来源事实断言。命题被 source 反驳和 source 沉默，应分别报告。“没有记录化验”不自动等于“化验没有发生”；“没有规定谁填写表格”不自动等于“任何人都可以填写”。

可定义可回答问题集：

$$
\mathcal A(S)=\{q:\text{来源及预先声明的推理规则确定该问题的答案}\}.
$$

这里的 epistemic boundary 指 $\mathcal A(S)$ 与其补集的区分。**没有给问题空间定义拓扑前，不写 $\partial\mathcal A(S)$ 为严格几何边界，更不将“边界几何”当已测物理对象。**

### 2.4 观察的是承诺约束，而不是隐藏文档

令 $\mathcal W$ 是允许的候选世界/资料集合，定义：

$$
\mathcal V_t=\{w\in\mathcal W:
 w\text{ 与 Speaker 截至 }t\text{ 的全部非假设性承诺相容}\}.
$$

在解释规则固定、没有撤回旧承诺的情况下，新增约束给出：

$$
\mathcal V_{t+1}\subseteq\mathcal V_t.
$$

$\mathcal V_t\neq\varnothing$ 只表示尚有一致解释，不证明模型内部真的存了 $w$。而 $\mathcal V_t=\varnothing$ 也要先排除措辞歧义、作用域变化与“计划/已执行”混淆；不能用与 target 不符替代这项检查。

---

## 3. 交互的统计实验与可识别性

### 3.1 生成过程

给定机制 $M$、状态 $\Theta$、Speaker 策略和裁判策略：

$$
Q_t\sim\pi_t(\cdot\mid H_{t-1}),\qquad
Y_t\sim W_{K,t}(\cdot\mid H_{t-1},Q_t).
\tag{3.1}
$$

$W_{K,t}$ 是将未观察的私卡与私人状态积分后的条件回答核，不要求跨轮独立。同一历史上的裁判选择核在两个假设下相同；这是“裁判没有额外 target 通道”的建模假设。

BOTH 不意味着两份回答在给定公共历史后无条件独立：它们可能共享材料结构或其他潜变量。因此将其作为联合 $Y_t$ 即可。

对固定策略 $\pi$，得到记录分布：

$$
P_k^{\pi,T}=\mathcal L(H_T\mid K=k,C,M).
$$

固定预算讨论最多 $T$ 次；允许提前停止时，以吸收符号 padding 到 $T$。完整序贯结果用停止记录 $H_\tau$。单个 ASK 可含多个子问题，所以理论“每步信息上限”必须明确适用于整个回答，而不是把 ASK 当等成本原子。

### 3.2 定义：交互等价

在同一协议和策略集合 $\Pi$ 下：

$$
\theta\sim_\Pi\theta'
\quad\Longleftrightarrow\quad
\mathcal L_\theta(H^\pi)=\mathcal L_{\theta'}(H^\pi)
\ \text{对所有 }\pi\in\Pi.
\tag{3.2}
$$

这里 $\theta$ 表示一个假设状态及其诱导的实验分布，不是一次实际生成的隐藏 token 串。

**P1：结构可识别性准则。** 定义实验映射

$$
\mathcal E(\theta)=\big(\mathcal L_\theta(H^\pi)\big)_{\pi\in\Pi}.
$$

一个目标属性 $g(\theta)$ 是 $\mathcal E(\theta)$ 的函数，当且仅当 $g$ 在每个 $\sim_\Pi$ 等价类上为常数。

**证明。** 若 $g=\bar g\circ\mathcal E$，相同实验映射给相同 $g$。反之，若每个纤维上 $g$ 恒定，则可在映射像上定义 $\bar g(\mathcal E(\theta))=g(\theta)$，且定义无歧义。此处是集合意义的因子分解；一般空间的可测性需另列条件。□

**不能从 P1 推出：** 单条有限对话能零错误恢复 $g$，或存在统一样本复杂度。以 $n$ 次 Bernoulli 观察为例，所有不同参数诱导不同分布，但 $1/2-\epsilon$ 与 $1/2+\epsilon$ 在固定 $n$、$\epsilon\to0$ 时可任意接近。没有 margin 就没有统一有限样本可靠性。

若 $\Pi_1\subseteq\Pi_2$，则 $\sim_{\Pi_2}$ 的分区细化 $\sim_{\Pi_1}$。这描述的是**最优可用信息**；真实 LLM 在更长文本、更大行动集下可能表现更差，不违反此结论。

### 3.3 P2：固定策略与最优策略的 Bayes 风险

等先验、必须二选一时，定义：

$$
\Delta_T^\pi=\operatorname{TV}(P_1^{\pi,T},P_0^{\pi,T}),
\qquad
\Delta_T^*=\sup_{\pi\in\Pi_T}\Delta_T^\pi.
$$

则：

$$
R_T^*(\pi)=\frac{1-\Delta_T^\pi}{2},\qquad
\inf_{\pi,d}P(d(H_T)\neq K)=\frac{1-\Delta_T^*}{2}.
\tag{3.3}
$$

**证明。** 对共同支配测度下密度 $p_1,p_0$，逐点选择密度较大的一类，风险为 $\frac12\int\min(p_1,p_0)=\frac12(1-\mathrm{TV})$。再对 $\pi$ 优化。□

式 (3.3) 假定这两个假设分布已知，并将最优判决能力与实际 LLM 区分。它不是“任意未知骗法下的 minimax 风险”，后者见第 6 节。TV/KL 检验联系见 [R2]。

### 3.4 信息获取量，而非再造一个含混的 capacity

固定先验后定义预算内最大可获取信息：

$$
\mathcal I_T^*=
\sup_{\pi\in\Pi_T}I(K;H_T\mid C,M).
\tag{3.4}
$$

$\mathcal I_T^*$ 可作为理论坐标，但不称为标准 Shannon channel capacity，因为没有对输入先验取上确界。若允许少用一次查询：

$$
0\le\mathcal I_T^*\le\mathcal I_{T+1}^*\le H(K\mid C,M).
$$

若 $K\to X\to H_T$ 在 $C,M$ 下构成 Markov 链，则：

$$
\mathcal I_T^*\le I(K;X\mid C,M).
\tag{3.5}
$$

右端可很松；若把 access flag 本身塞入 $X$，它可能包含全部身份信息，却不通过语言暴露。因此不把 $I(K;X)$ 称为“裁判必可提取的信息”，也不直接用它归一化计算能力评分。固定先验下 MI 与最小分类风险不是同一个目标函数。

---

## 4. 自适应信息分解与查询上下界

### 4.1 P3a：KL 与互信息链式分解

在式 (3.1) 的共同裁判核条件下：

$$
D_{\rm KL}(P_1^{\pi,T}\Vert P_0^{\pi,T})
=
\sum_{t=1}^T E_1\left[
D_{\rm KL}\big(W_{1,t}(\cdot\mid H_{t-1},Q_t)
\Vert W_{0,t}(\cdot\mid H_{t-1},Q_t)\big)
\right].
\tag{4.1}
$$

**证明。** 联合密度为 $\prod_t\pi_t(q_t\mid h_{t-1})W_{k,t}(y_t\mid h_{t-1},q_t)$。似然比中 $\pi_t$ 逐项消去，对数展开并在 $K=1$ 下取期望。有限 KL 情况可直接计算；无限情形按扩展值处理。□

互信息版本：

$$
I(K;H_T\mid C,M)
=
\sum_{t=1}^T I(K;Y_t\mid H_{t-1},Q_t,C,M).
\tag{4.2}
$$

原因是给定过去历史后 $I(K;Q_t\mid H_{t-1},C,M)=0$。这不表示问题“没有用”：问题决定后续回答核。

令当前 posterior 为 $p=P(K=1\mid h)$，则单步信息为加权 Jensen–Shannon 散度：

$$
\mathsf{IG}(h,q)=
pD_{\rm KL}(W_1\Vert\overline W)
+(1-p)D_{\rm KL}(W_0\Vert\overline W),
\quad\overline W=pW_1+(1-p)W_0.
\tag{4.3}
$$

这些是经典主动检验工具。[R1–R3] 我们没有从 28 个“相关追问”估计式 (4.3)。

### 4.2 P3b：固定预算下界

若对所有允许策略和所有可达历史，单步 KL 均至多 $\kappa$，则：

$$
D_{\rm KL}(P_1^{\pi,T}\Vert P_0^{\pi,T})\le T\kappa.
$$

Pinsker 与 Bretagnolle–Huber 的直接推论为：

$$
R_T^*\ge
\max\left\{
0,\frac{1-\sqrt{T\kappa/2}}2,
\frac{1-\sqrt{1-e^{-T\kappa}}}{2}
\right\}
\ge\frac14 e^{-T\kappa}.
\tag{4.4}
$$

最后一个较简单的界对 $\delta<1/4$ 给出必要条件：

$$
R_T^*\le\delta
\quad\Longrightarrow\quad
T\ge\frac{\log(1/(4\delta))}{\kappa}.
\tag{4.5}
$$

这里 $\kappa=0$ 时用零信息结论直接处理，而不是除以零。界的标准出处与相互关系见 [R2]。

### 4.3 一个可用的上界，但只在明确的小模型里

固定问题 $q$，每次从**独立重置的相同响应核**得到一个观察。令：

$$
\mathsf C(q)=
-\log\inf_{s\in[0,1]}\int w_1(y)^s w_0(y)^{1-s}dy.
$$

似然比分类器满足：

$$
R_T^*(q)\le\frac12e^{-T\mathsf C(q)}.
\tag{4.6}
$$

**证明。** $\min(a,b)\le a^sb^{1-s}$，对 $T$ 个乘积分布积分，再对 $s$ 最小化。□

自然多轮 bluff 往往改变私有承诺，反复同问也未必是独立样本。因此式 (4.6) 不可直接套入实际 ASK 数。它适合后续经过重置的单问题 probe，而不是用来声称“三次询问已有最优指数”。

### 4.4 P3c：自主停止的必要成本

在有限停止时间或有适当可积性的 a.s. 有限 $\tau$ 下，停止似然比与数据处理给出：

$$
E_1\sum_{t=1}^{\tau}d_t
\ge
\operatorname{kl}(P_1(E),P_0(E)),
\quad E\in\mathcal F_\tau,
\tag{4.7}
$$

其中 $d_t=D_{\rm KL}(W_{1,t}\Vert W_{0,t})$。可先对有界停止应用 (4.1)，再在合法极限条件下推广；相关 stopping-time change-of-measure 工具见 [R3, Lemma 1 / Appendix A]。

若每种身份下的错误概率至多 $\delta$、弃权概率至多 $b$，取 $E=\{d=A\}$。当 $1-b-\delta>\delta$ 且 $d_t\le\kappa$ 时：

$$
E_1\tau\ge
\frac{\operatorname{kl}(1-b-\delta,\delta)}{\kappa}.
\tag{4.8}
$$

这说明错误、弃权与查询成本之间存在约束；不是越多问越好，也不是一句“随时允许弃权”就绕过识别下界。实际可另外记录 token、时延和回答子问题数量，避免将一长串复合问题视为一个固定成本测量。

---

## 5. 来源模拟：对任意追问成立的识别上限

### 5.1 P4：source-simulation bound

固定公共背景。真来源 $S\sim D$，对手独立生成 $\widetilde S\sim Q$。假设给定各自文档后，两席按照同一来源条件响应规则回答；允许历史依赖、私人随机性与全文复述，但不能额外暴露文档是收到的还是自造的。

$$
(S_A,S_B)\mid K=1\sim D\otimes Q,\qquad
(S_A,S_B)\mid K=0\sim Q\otimes D.
$$

所有审问结果都来自同一个随机通道 $\mathcal M_\pi$：

$$
(S_A,S_B)\xrightarrow{\mathcal M_\pi}H_\tau.
$$

令 $\epsilon=\operatorname{TV}(D,Q)$，则对任意策略与合法停止：

$$
\operatorname{TV}(P_1^\pi,P_0^\pi)
\le 2\epsilon-\epsilon^2,
\qquad
R^*(\pi)\ge\frac{(1-\epsilon)^2}{2}.
\tag{5.1}
$$

**证明。** 通道数据处理先给
$\mathrm{TV}(P_1^\pi,P_0^\pi)\le\mathrm{TV}(D\otimes Q,Q\otimes D)$。设密度为 $d,q$，则

$$
\min\{d(x)q(y),q(x)d(y)\}
\ge\min\{d(x),q(x)\}\min\{d(y),q(y)\}.
$$

两边积分，重叠质量至少 $(1-\epsilon)^2$。再用 (3.3)。□

**紧性。** 取三个文档值 $s_c,s_0,s_1$，令：

$$
D=(1-\epsilon)\delta_{s_c}+\epsilon\delta_{s_0},\quad
Q=(1-\epsilon)\delta_{s_c}+\epsilon\delta_{s_1}.
$$

两种来源对分布仅在 $(s_c,s_c)$ 共享质量 $(1-\epsilon)^2$。允许完整呈现两份文档的通道可达到 (5.1)，因此这是给定 TV 条件的紧通用界。

KL 版本也直接成立：

$$
D_{\rm KL}(P_1^\pi\Vert P_0^\pi)
\le D_{\rm KL}(D\Vert Q)+D_{\rm KL}(Q\Vert D).
\tag{5.2}
$$

如果两侧不互相绝对连续，右端可能无穷，此时 TV 界仍然有意义。数据处理的基础见 [R4]；(5.1) 的证明与紧性构造是本文在该设定下的直接推导，不主张文献首次。

### 5.2 为什么不平凡于“随机 target 猜不出”

当 $Q=D$，即使现实中确实只有一席收到 Host 原始文件，另一席是自造文件，也仍有：

$$
R^*=1/2.
$$

这是**因果接收历史不同，但来源条件行为统计相同**，不依赖事后硬币标签。结论来自强假设，而不是当前模型测得的性能：原始来源分布、模拟来源分布和响应核均尚未在真实 LLM 中估计。

### 5.3 显式持有文档不是必要条件

如果在线策略在每个可达历史上都复现“先抽一个来源，再根据来源回答”的后验预测核：

$$
W_B(y\mid h,q)=\int R(y\mid s,h,q)\,\mu(ds\mid h),
\tag{5.3}
$$

且这些核来自同一个相容联合过程，那么归纳可得全部有限维对话分布相同。$\mu$ 必须随此前回答更新，不能每轮无条件重抽一个毫不相干的新来源。

因此：稳定承诺可以由预存文档实现，也可以由等价的预测过程实现。仅凭外部一致性无法证明 persistent latent dossier。这与 audit 的降级结论一致。[A1–A2]

### 5.4 近似模拟与累积误差

若两个候选过程的每个历史条件回答核 TV 至多 $e_t$，可用逐步最大耦合得到：

$$
\operatorname{TV}(P_1^{\pi,T},P_0^{\pi,T})
\le 1-\prod_{t=1}^T(1-e_t)
\le\sum_{t=1}^Te_t.
\tag{5.4}
$$

**证明思路。** 在两边历史尚相同时使用同一问题，并耦合本轮回答；保持相同的条件概率至少 $1-e_t$。记录最终不同的概率支配 TV。□

(5.4) 允许逐步近似误差累积；(5.1) 是来源级共同通道带来的、与轮数无关的上限。两者不能混为一个定理。增加询问有时会暴露模拟误差，但没有一般定理保证一定暴露。

---

## 6. 不知道对手是哪种策略：复合假设与 minimax

### 6.1 正确的极小极大对象

令 $\beta$ 为未知对手策略，完整误判风险为 $R(\pi,d,\beta)$。稳健风险应定义为：

$$
R_{\rm mm}(\mathcal B)=
\inf_{\pi,d}\sup_{\beta\in\mathcal B}R(\pi,d,\beta).
\tag{6.1}
$$

一般只能先得：

$$
R_{\rm mm}(\mathcal B)
\ge
\frac{1-\sup_\pi\inf_{\beta\in\mathcal B}
\operatorname{TV}(P_1^{\pi,\beta},P_0^{\pi,\beta})}{2}.
\tag{6.2}
$$

这是因为 $\inf_d\sup_\beta\ge\sup_\beta\inf_d$。右端容许针对每个已知 $\beta$ 选择最佳分类器；左端要求同一个裁判处理未知 $\beta$。**除非另证极小极大条件，不能把 (6.2) 写成等式。**

策略集合包含 $\mathcal B_1\subseteq\mathcal B_2$ 时，$R_{\rm mm}(\mathcal B_1)\le R_{\rm mm}(\mathcal B_2)$。但两份不同 prompt 不构成经证明的策略集合包含关系，不能据此预言 Boundary-aware 一定比 Strong 更难。

### 6.2 P5：凸包距离决定一个标准稳健检验问题

固定 $\pi$，在有限记录空间内考虑两组允许分布 $\mathcal P_0,\mathcal P_1$。这里允许 Nature 在两个假设下分别选择最坏分布，而不是要求共享同一个 nuisance 参数。令 $\phi(h)$ 为选择 1 的概率：

$$
R_{\rm sep}=\inf_\phi\frac12\left[
\sup_{P\in\mathcal P_0}E_P\phi+
\sup_{Q\in\mathcal P_1}E_Q(1-\phi)\right].
$$

令 $\mathcal C_k=\overline{\operatorname{conv}}(\mathcal P_k)$。有限维紧凸情形：

$$
R_{\rm sep}=\frac12\left[
1-\inf_{P\in\mathcal C_0,Q\in\mathcal C_1}\operatorname{TV}(P,Q)
\right].
\tag{6.3}
$$

**证明。** 线性期望在原集合与其闭凸包上有相同上确界。损失关于 $\phi$ 和 $(P,Q)$ 双线性，有限维 minimax 交换后，对固定 $(P,Q)$ 用 (3.3)。[R5] □

**例。** $\mathcal P_0=\{\delta_0,\delta_1\}$，$\mathcal P_1=\{(\delta_0+\delta_1)/2\}$。每个已知 $P\in\mathcal P_0$ 与唯一 $Q$ 的 TV 为 $1/2$，两两最佳正确率为 $3/4$。但 $Q\in\mathcal C_0$，所以统一稳健风险为 $1/2$。

**ToM 含义。** 对已知“谨慎读者”“健谈读者”分别有用的判断规则，不一定能应付未知风格混合。所谓 reliable knowledge signature 必须声明对哪一组 Reader/Bluffer 策略成立。

---

## 7. Frozen null：不可识别的是指定关系，不是文档内容

### 7.1 P6：任意自适应交互与停止均不产生 target 信息

令 $X$ 包含已冻结的来源、座位、角色输入、公共背景以及不含 target 的环境设置；令 $U$ 包含所有后续随机性。假设：

$$
K\sim\mathrm{Bernoulli}(1/2),\qquad
K\perp(X,U),
\qquad
H_\tau=F_\pi(X,U).
\tag{7.1}
$$

这里还要求停止规则、模型路由、错误恢复、预算中止及日志选择不使用 target。则：

$$
K\perp H_\tau,\qquad
P(K=1\mid H_\tau)=1/2\quad\text{a.s.},
\qquad I(K;H_\tau)=0.
\tag{7.2}
$$

**证明。** 对任意历史事件 $B$：

$$
P(K=k,H_\tau\in B)
=P(K=k)P(F_\pi(X,U)\in B).
$$

这是独立变量经过可测映射后的独立性。也可逐轮归纳共同回答核，或用 (4.1)。□

“a.s.” 不能随意写成对概率零历史也无条件成立的“所有 H”；条件概率只在相关分布下几乎处处定义。

**实现层注意。** 式 (7.1) 是生成机制的独立性假设，不是从某次固定 seed 的轨迹中估出来的事实。“不同 seed/不同编号”本身不构成随机独立性证明；必须检查 label 是否进入来源构造、条件路由、恢复和筛选。新 replay 也可以明确设为“对已经固定的同一记录重新独立指定 target”的任务，并对该新标签解析评分；这样需明示估计对象已经是新 designation，而非声称复原原始接收历史。

### 7.2 三个不需要的假设

P6 不要求两份资料逐字平行，不要求它们 IID，也不要求 Reader 完美忠实。只要 target 独立且不进入生成过程，即使一份来源更完整、一席回答更差，也仍然没有关于随机指定关系的信息。

同样，完整引用私卡内容不破坏 P6。全文可以彻底暴露两个 $S_i$，但不暴露随后独立抽取的 $K$。这不代表全文重现对原始战略访问任务一定无用；两个任务不同。

### 7.3 选择与缺失会不会破坏 null？

若纳入事件 $E$ 只依赖 $(X,U,H)$，则：

$$
K\perp H\mid E.
\tag{7.3}
$$

因此，target-blind 的完整性选择可以保留 null。**但它会改变被分析对话的行为分布**，例如偏向更短、更便宜的轨迹，所以仍不能估计自然总体的弃权率。

若按“裁判猜对”“高置信错误”等依赖 $K$ 的事件选择，(7.3) 不再自动成立。不能挑选命中案例再声称 null 后验仍然 0.5。固定七条 replay 的规则是纳入所有完整 Frozen，不按原终局筛选。[A3]

### 7.4 近似 null 的容差

若只能证明 $I(K;H)\le\varepsilon$ nats，而非严格独立，令真实后验为 $p^*(H)$。则：

$$
I(K;H)=E\,\operatorname{kl}(p^*(H),1/2)
\ge2E\left(p^*(H)-1/2\right)^2.
$$

所以：

$$
E\left(p^*(H)-1/2\right)^2\le\varepsilon/2.
\tag{7.4}
$$

这是近似独立时的平均容差，不是每条记录的逐点界。当前原始自然语言实验没有测出这样的 $\varepsilon$；精确 null 应由生成协议保证，而不是由小样本不显著推断。

---

## 8. 文本来源信息与 target 信息：何时可以从一个推到另一个

### 8.1 基本条件不能省略

若 $K\to G\to H$ 构成 Markov 链，即 $K\perp H\mid G$，则数据处理给出：

$$
I(K;H)\le I(K;G).
\tag{8.1}
$$

仅有 $K\perp G$ 不够推出 $K\perp H$：$H$ 可能另有直接 target 通道。例如 $H=K$，无论 $G$ 是什么独立噪声，$H$ 都完全揭示 $K$。

Frozen 中更强的 (7.1) 排除了全部 target 通道，因此文风、引用误差、推断得到的 lineage 统统不能关联随机目标。

如果另建模型 $G=K\oplus N$，其中 $K$ 均衡、$N\sim\mathrm{Bernoulli}(e)$ 独立、$e\le1/2$，且 $H$ 只通过 $G$ 获得 target 信息，那么即使完全恢复 $G$，正确率也至多 $1-e$。这需要对称噪声通道条件；仅给总体 $P(G=K)$ 一项，不能一般性推出最优准确率上界。

### 8.2 为什么 Blind 的有偏判断不必是“明知违反概率论”

假设某一可见特征 $G\in\{A,B\}$ 表示“更像原始材料的一方”。考虑两种机制：

- $M_0$：来源和行为生成后，target 与 $G$ 独立随机；
- $M_1$：来源和行为仍照原方式生成，但 Host 将 $G$ 指向的一方指定为 target。

两种机制可以有完全相同的 $H$ 边缘分布，却有不同 $P(K\mid H,M)$。不知道机制时，仅靠对话未必能区分它们。

以一个说明性的主观混合模型为例，若裁判假定 $P(M_1)=\lambda$，两个机制有相同 $H$ 分布，则：

$$
\widetilde P(K=1\mid H)
=\frac{1-\lambda}{2}+\lambda\widetilde P(G=A\mid H).
\tag{8.2}
$$

若它认为 A 几乎确定更“原始”，就报告 $(1+\lambda)/2$。这可以解释为什么措辞和文档结构会影响 target 判断，但**不是从概率报告中识别出的真实心理参数**。许多不同策略都可产生相同报告。

因此：

$$
\text{Blind 的 null 偏离}
\neq
\text{Informed 条件下无视明确独立性}.
$$

前者是相对真实 DGP 的归因误差；后者才是对已告知规范后验的违反。Audit 的终局裁判不知道随机机制，所以不能倒推成 informed-null reasoning failure。[A1–A3]

### 8.3 Replay 可检验的最窄问题

> 在完全相同的社会对话证据上，明确披露 target 的独立生成机制，是否改变 LLM 的概率报告和决策？

这检验的是**机制信息对报告行为的影响**。即使观察到显著变化，也不能单凭这一点证明模型内部真的在做 Bayesian model averaging；也可能是规则识别、提示遵从或其他可观察等价实现。

### 8.4 表面改写与信息等价

若 $K\perp(H,U_R)$，且改写 $H'=g(H,U_R)$ 不使用 target，则 $K\perp H'$。这说明重排、改写不会从精确 null 中创造 target 信息。该结论只需要独立性，不要求重写具有语言学意义上的完美语义等价。

但若要把**行为变化因果归于文风本身**，仍需匹配事实、限定词、推理需求和资料 framing。既有 parallel 与 surface-diverse 不是这样的同事实对照。静态改写对话也不是重新生成 source 后的主动交互。Blackwell 的实验比较提供区分信息结构与决策表现的经典语言；不应把任意两种互动文档都称为相互 garbling。[R7]

---

## 9. 选择性归因：概率、弃权与成本必须分开

### 9.1 P7：准确率—覆盖率紧界

对固定策略生成的 $P_1,P_0$，等先验，令：

$$
c=P(d\neq\bot),\quad
 a=P(d=K\mid d\neq\bot),\quad
 \Delta=\operatorname{TV}(P_1,P_0).
$$

当 $c>0$ 时：

$$
\boxed{|c(2a-1)|\le\Delta.}
\tag{9.1}
$$

特别地：

$$
a\le\min\left(1,\frac12+\frac{\Delta}{2c}\right).
\tag{9.2}
$$

**证明。** 给定 $h$ 的选择 A、B 概率为 $u_A(h),u_B(h)$，且 $u_A+u_B\le1$。则：

$$
P(\text{correct})-P(\text{wrong})
=\frac12\int(p_1-p_0)(u_A-u_B).
$$

其绝对值至多 $\frac12\int|p_1-p_0|=\Delta$。左侧为 $c(2a-1)$。□

**紧性。** 概率 $\Delta$ 时观察完全揭示身份，概率 $1-\Delta$ 时观察两类相同。若 $c\le\Delta$，只在揭示性事件中抽样作答可得 $a=1$；若 $c>\Delta$，再在无信息事件中作答可达到 (9.2)。

**null 推论。** $\Delta=0$ 时，只要回答，条件准确率仍为 $1/2$。不能通过高置信筛选、复杂理由或选择性弃权，从真正零信息记录里提取一个高准确率子集。有限样本命中率当然可以偏离 $1/2$，所以要区分理论值与样本波动。

### 9.2 弃权是否理性取决于损失，而不是动作名

定义损失：正确 0、错误 1、弃权 $\ell_\bot\in(0,1/2)$。给定真实 posterior $p$：

$$
L(A;p)=1-p,\quad L(B;p)=p,\quad L(\bot;p)=\ell_\bot.
$$

最优动作选择最小者：

$$
\bot\text{ 最优}\iff\ell_\bot\le\min(p,1-p).
\tag{9.3}
$$

边界相等时有并列最优。若规定 $\ell_\bot=0.25$，null 下弃权严格优于选择；有 $r=0.8$ 的可靠线索时，选择线索指向一方严格优于弃权。若没有声明损失，不能把任何强制猜测都称为“不理性”。

### 9.3 分离报告与动作

对模型报告 $\hat p$，定义报告—动作不一致损失：

$$
\mathsf{Incoherence}(d,\hat p)
=L(d;\hat p)-\min_{d'}L(d';\hat p).
\tag{9.4}
$$

对已知真实后验 $p^*$，定义实际决策 regret：

$$
\mathsf{Regret}(d;p^*)
=L(d;p^*)-\min_{d'}L(d';p^*).
\tag{9.5}
$$

二者不同。例如模型报 0.8 并选 A，动作对自身报告相容，但在真实 $p^*=0.5$ 的 informed null 中仍有正 regret。相反，模型报 0.5 却选 A，是报告正确、动作没有遵守给定 reject option。

---

## 10. 后验报告的统计学：Replay 的主要理论与可测结果

### 10.1 概率报告的完整行为分布

固定模型部署 $m$、对话 $h$、条件 $z$ 与其他固定输入。新会话的输出服从某个未知分布：

$$
(\hat p,d,R_{\rm text},V)\sim
\mathcal Q_m(\cdot\mid h,z),
\tag{10.1}
$$

其中 $R_{\rm text}$ 是可见理由，$V$ 是格式/可用性状态。不假设 $\hat p$ 正态分布，也不假设它就是模型内部信念。可先用重复调用的经验分布估计均值、方差、动作频率和无效回复比例。

### 10.2 P8a：适当评分与解析边缘化

已知 oracle posterior $p^*$ 时，binary Brier loss：

$$
L_B(p,K)=(p-K)^2.
$$

对 $K\sim\mathrm{Bernoulli}(p^*)$ 取条件期望：

$$
E[L_B(p,K)]
=p^*(1-p^*)+(p-p^*)^2.
\tag{10.2}
$$

因此超额风险恰为：

$$
\boxed{O_B(p;p^*)=(p-p^*)^2.}
\tag{10.3}
$$

log loss 的超额风险为：

$$
O_{\log}(p;p^*)=
\operatorname{kl}(p^*,p).
\tag{10.4}
$$

严格适当评分的通用理论见 [R6]；(10.2) 是直接展开。主分析使用 Brier，避免日志边界数值问题。若报告 $p=0,1$ 而 $0<p^*<1$，真实 log loss 为无穷；若展示时用 $\epsilon=10^{-6}$ 截断，必须预先声明为 capped display/sensitivity，保留原始数值。

精确 Frozen 下 $p^*=1/2$，可以不依赖那一次随机标签的偶然取值：

$$
\frac12(p-0)^2+\frac12(p-1)^2
=\frac14+(p-1/2)^2.
\tag{10.5}
$$

这是对已知随机性求条件期望，不是把一条记录伪装成两个独立样本。在 Blind 条件，它仍是相对真实机制的风险，但不自动等于违反裁判已知规则。

### 10.3 P8b：系统性偏差与解码方差

对固定 $(m,h,z)$，令：

$$
\mu=E\hat p,\qquad v=\operatorname{Var}(\hat p).
$$

则：

$$
\boxed{E(\hat p-p^*)^2=(\mu-p^*)^2+v.}
\tag{10.6}
$$

这是部署时的单次预测风险分解。一次样本偏离 $p^*$ 既可能是均值偏差，也可能是随机波动；不能从一次报告确定来源。

若有 $R\ge2$ 次独立重复，$z_r=\hat p_r-p^*$，则：

$$
\widehat B=
\frac{1}{R(R-1)}\sum_{r\ne s}z_rz_s
=(\bar p-p^*)^2-\frac{s_p^2}{R},
\quad E\widehat B=(\mu-p^*)^2.
\tag{10.7}
$$

其中 $s_p^2$ 为分母 $R-1$ 的样本方差。有限样本下 $\widehat B$ 可为负，不截断它后再声称无偏；直接展示均值、方差和估计不确定性。少量重复不能精确恢复全分布。

### 10.4 P8c：真正 posterior 的鞅结构，以及 prefix replay 的限制

同一真实信息过程下：

$$
p_t^*=P(K=1\mid\mathcal F_t),\qquad
E[p_{t+1}^*\mid\mathcal F_t]=p_t^*.
\tag{10.8}
$$

这只要求条件期望，不要求单条有信息轨迹的后验单调。精确 null 更强：$p_t^*=1/2$ a.s. 对每个 $t$ 成立。

旧记录的 prefix replay 是让**不同新会话**看到 $h_t$，得到分布 $\mathcal Q_m(\hat p\mid h_t,z)$。它是截面证据量敏感性，不是原 Judge 内部 belief trajectory；不能直接检验一般的 martingale identity。

若相邻 prefix 调用独立，均值、方差为 $\mu_t,v_t$，则：

$$
E(\hat p_t-\hat p_{t-1})^2
=(\mu_t-\mu_{t-1})^2+v_t+v_{t-1}.
\tag{10.9}
$$

因此直接累加 $\sum_t|\hat p_t-\hat p_{t-1}|$ 会把采样波动计成“信念漂移”。若每个 prefix 有独立重复，令 $D_r=\hat p_{t,r}-\hat p_{t-1,r}$，可以用 $\sum_{r\ne s}D_rD_s/[R(R-1)]$ 无偏估计平方均值漂移。只在明确 null 或已知 oracle posterior 的条件下解释“无关证据的概率偏移”。

### 10.5 P9a：真实但有噪的 target 线索

避免“输出 0.5 就全部过关”，另加入独立线索：

$$
K\sim\mathrm{Bernoulli}(1/2),\quad
Z_{\rm cue}=K\oplus N,\quad
N\sim\mathrm{Bernoulli}(1-r),\quad r>1/2,
$$

且 $N$ 独立于 $(K,H)$，$H\perp K$。线索在对话冻结后产生，不交给旧 Speaker。于是 $H\perp(K,Z_{\rm cue})$，并有：

$$
p^*(Z_{\rm cue},H)=
\begin{cases}
r,&Z_{\rm cue}=1\text{（指向 A 席）},\\
1-r,&Z_{\rm cue}=0\text{（指向 B 席）}.
\end{cases}
\tag{10.10}
$$

**证明。** 对 $Z_{\rm cue}=1$，Bayes 公式给 $r/(r+1-r)=r$；$H$ 的独立因子消去。另一方向对称。□

关键是独立的 binary symmetric channel；只说“这个 clue 总体准确率 80%”并不足以在任意非均衡先验、非对称误差下推出 posterior 0.8。实验必须把生成规则讲全。

每条对话都做两个线索方向，避免根据原选择挑“冲突线索”。另加**同规则、同线索但不给对话**的基线，以分离基础概率理解与对话造成的变化。

### 10.6 P9b：方向偏移与线索利用的精确分解

固定对话和模型，设两个线索方向的平均报告为 $\mu_+,\mu_-$，oracle 分别为 $r,1-r$。定义：

$$
b_h=\frac{\mu_++\mu_--1}{2},\qquad
s_h=\frac{\mu_+-\mu_-}{2r-1}.
\tag{10.11}
$$

$b_h$ 是不随线索方向反转的偏移，$s_h$ 是在该可靠度下的方向响应增益。规范值为 $b_h=0,s_h=1$。令 $d_r=r-1/2$，则：

$$
\boxed{
\frac{(\mu_+-r)^2+(\mu_--(1-r))^2}{2}
=b_h^2+d_r^2(s_h-1)^2.
}
\tag{10.12}
$$

**证明。** 两方向误差分别为 $b_h+d_r(s_h-1)$ 和 $b_h-d_r(s_h-1)$，平方平均交叉项消去。□

若考虑单次调用风险，还需加上 $(v_++v_-)/2$。因此可严格区分：

- 总偏向某一席：$b_h\neq0$；
- 没有充分使用线索：$s_h<1$；
- 将噪声线索当确定事实：可能 $s_h>1$；
- 相同输入下不稳定：$v_+,v_-$ 较大。

例如始终报 0.5 时，$b_h=0,s_h=0$：null 全对不等于会利用信息。这项分解来自代数，直接可 replay，不需要对模型内部进行因果断言。单一 $r$ 只识别该点的方向增益，不是完整可靠度校准曲线。

### 10.7 P10：座位交换的可测结构

定义 $\sigma(h)$ 为对全部角色标签及其指代一致交换 A/B 的记录，保持文字内容、问答依赖与时间顺序。在可交换的 target 问题下，理想报告函数应满足：

$$
p(\sigma h)=1-p(h).
\tag{10.13}
$$

在 informed exact null 下，两边更应都为 0.5。对均值报告定义：

$$
b_{\rm even}(h)=\frac{\mu(h)+\mu(\sigma h)-1}{2},\qquad
b_{\rm odd}(h)=\frac{\mu(h)-\mu(\sigma h)}{2}.
\tag{10.14}
$$

则：

$$
\frac{(\mu(h)-1/2)^2+(\mu(\sigma h)-1/2)^2}{2}
=b_{\rm even}^2+b_{\rm odd}^2.
\tag{10.15}
$$

这能区分交换不变与交换反号的偏移。**不能自动将前者唯一命名为 seat bias、后者唯一命名为 content bias**：始终偏好首先发言者也可能落入交换反号部分。要再分离内容与出现位置，需要额外且语义合法的顺序干预。

交换必须覆盖问题内的 “Speaker A”、指向另一席的嵌入引用等；不得对普通词中字符 A/B 全局替换。修改后要人工核对指代。记录原始和交换 payload 的独立 hash；不得替换 source 中实体名称来制造新事实。

---

## 11. ToM 的策略结构与主动提问为何有价值

### 11.1 与 Decrypto 的关系

Decrypto 将游戏写为 RSA 式语用推断：说话者选择表达时兼顾合作听者理解和对手截获，听者反推这种表达策略。其 Appendix H 在所设模型内讨论了嵌套对他人信念的建模，以及不确定的 speaker model。[R9]

这里借鉴的是“给游戏明确的信息状态、策略与推断目标”，不是照搬某个结论为“任何成功神经网络都必须显式实现高阶 ToM”。本文不据游戏胜负判定模型内部是否存在心理状态模块。

### 11.2 一个用于解释策略行为的 level-k 模型

令 $b_J(k\mid h)$ 是一个裁判模型。有限候选回答集上，Speaker 的近似最佳反应可以写成：

$$
\beta_i(y\mid s,h,q;b_J)
\propto\beta_{i,0}(y\mid s,h,q)
\exp\{\lambda U_i(y;s,h,q,b_J)\}.
\tag{11.1}
$$

$U_i$ 可包含被选中概率、来源不忠实成本、与既有承诺冲突的成本。Reader 与 Bluffer 的信息输入不同，不必假设有不同神经架构。

在简化的一步诱导模型里，Bluffer 的效用项可含：

$$
U_B(y)\supset\log b_J(K=B\mid h\oplus(q,y)).
$$

一个战略感知 Judge 又对 $\beta_i$ 的可能类型积分：

$$
b_J(k\mid h)\propto P(k)
\int P(h\mid k,\beta)\,d\Lambda(\beta).
\tag{11.2}
$$

于是产生“我预测你如何预测我”的策略结构。它是一种解释与对照模型，不是从现有 audit 识别的内部算法。总赢分、specificity 或拒答频率均不足以唯一估计 $\lambda$、$\Lambda$ 或心智层级。

### 11.3 最优查询一般依赖联合 belief，不只依赖身份概率

若 $Z$ 表示资料类型、来源范围或对手策略类型，规划需要的状态是 $b_t(K,Z)$，而非仅 $p_t(K)$。以单位查询成本 $c_q$ 表示的有限时域 Bellman 形式为：

$$
V_t(b)=\min\left\{
L_{\rm stop}(b),
\inf_q\left[c_q+E_{Y\sim b,q}V_{t+1}(\mathcal B(b,q,Y))\right]
\right\}.
\tag{11.3}
$$

立即最大化 $I(K;Y\mid h,q)$ 只是贪心法。只有额外结构下才可能有一般保证；adaptive submodularity 是一种经典充分结构，而不是自然对话自动具备的性质。[R1,R8]

### 11.4 P11：无即时身份信息的问题可以带来严格自适应优势

设 $K,Z$ 为独立公平 bit。允许三个问题：

| 问题 | $Z=0$ | $Z=1$ |
|---|---|---|
| $q_{\rm scope}$ | 返回 0 | 返回 1 |
| $q_L$ | 返回 $K$ | 返回独立公平 bit |
| $q_R$ | 返回独立公平 bit | 返回 $K$ |

无关 bit 开局抽取，重复同问返回同一 bit，禁止把多个问题免费合成一次。

$$
I(K;Y_{\rm scope})=0,
\quad
I(K;Y_L)=I(K;Y_R)=\ln2-h(1/4)>0.
$$

先问 scope 再问相应诊断问题，两问零错误。先问 $q_L$ 或 $q_R$ 后，无论第二问选择哪个允许问题，最佳风险为 $1/4$。例如第二问 scope，一半情况下第一问是诊断问题，另一半只得到无关 bit；后一半只能猜。第二问另一方向时，答案相同时识别，答案相反时两个解释对称，风险同样 $1/4$。

推广：$Z$ 均匀于 $\{1,\ldots,m\}$，只有 $q_Z$ 回答 $K$，其余返回开局固定的独立噪声；scope 返回 $Z$。自适应仍只需两问。任何事先固定的 $T$ 个问题至多覆盖 $T$ 个诊断位置，因此：

$$
R_T^{\rm nonadaptive}\ge
\frac12(1-T/m)_+.
\tag{11.4}
$$

这是限定查询模型中的严格差距，不是对自然语言自由 ASK 的无条件下界。它说明“先问这份资料覆盖什么”可能有未来工具价值，而不是证明现有 28 个依赖性追问已经具有这种价值。

### 11.5 Replay 与 active ToM 的边界

固定终局 replay 能考察证据解释；它不能估计 (11.3) 的最优提问，也不能证明 (11.4) 在自然对话中出现。若要研究主动策略，需前瞻性随机化提问政策或在可计算小世界中比较查询成本。当前不把这一条另开为主项目。

---

## 12. 从 audit 到可操作的 Speaker 行为模型

### 12.1 缺失信息响应不是一个单一变量

将候选 $\varphi$ 分别标为：来源支持、来源反驳、来源沉默。另记问题属于：普通细节请求、显式是否出现的 recognition check、带肯定前提的问题、纯假设情景。把首次来源标为 Judge / 本席此前 / 另一席此前。

定义 uptake indicator 只针对具体行为：

$$
X=1\iff\text{本席将候选作为自己来源的事实接受}.
$$

讨论可能性、作为假设续写、明确拒绝、未回应分别保留，不全压成 $X=0$。若测二值响应，必须预先写明如何处理 ambiguous/missing。

### 12.2 一个诊断 probe 的 TV

固定来源、问题、历史与重置策略，假设观察到的二值响应满足：

$$
X_R\sim\mathrm{Bernoulli}(a_R),\qquad
X_B\sim\mathrm{Bernoulli}(a_B).
$$

则：

$$
\operatorname{TV}(\mathcal L(X_R),\mathcal L(X_B))=|a_R-a_B|.
\tag{12.1}
$$

这是对**已定义二值读出**的可分性，不是整段自然语言回答的 TV；经过编码的数据处理可丢掉其他信息。对同一游戏的两个回答不能随意当独立样本，多个历史条件的概率也不应直接合成一个 memoryless kernel。

当前 11 个分组机会只描述观察差异，不能估计随机化“诱导问法相对中性问法”的因果效应。真正的后续小实验应对同一来源、候选和角色在新会话中随机化问法，分别估计角色差异及问法交互；不要只挑已成功骗到人的前提。[A1]

### 12.3 P12：共同迎合可能消除身份信息

固定历史和语义问题。原始响应核为 $W_1,W_0$。若两类均以同一概率 $\rho$ 改用只依赖问题、与身份无关的迎合核 $C_q$：

$$
\widetilde W_k=(1-\rho)W_k+\rho C_q,
$$

则：

$$
\operatorname{TV}(\widetilde W_1,\widetilde W_0)
=(1-\rho)\operatorname{TV}(W_1,W_0),
\tag{12.2}
$$

$$
D_{\rm KL}(\widetilde W_1\Vert\widetilde W_0)
\le(1-\rho)D_{\rm KL}(W_1\Vert W_0).
\tag{12.3}
$$

**证明。** TV 直接相减；KL 用联合凸性，并利用 $D_{\rm KL}(C_q\Vert C_q)=0$。□ [R4]

所以设套“有效”不能只指模型顺着问题说出了更多细节；共同的顺从压力反而可能使两类更像。若两类的迎合概率不同，可以产生新信号，但不能再套 (12.2) 的共同系数。

### 12.4 与审计对应的目标层级

| 所观察对象 | 数学解释 | 不足以支持的更强解释 |
|---|---|---|
| Reader 未把缺失字段当 source fact | 一个相对来源的响应 | Reader 不会 hallucinate |
| Bluffer 延展既有故事 | 相容承诺约束 | 内部真的有 persistent dossier |
| 后问链接先前回答 | 历史条件策略 | 获取了正身份信息 |
| Judge 从少一个词推源文件衍生 | noisy observation 到 lineage 的推断 | 真正识别了文档生成历史 |
| Frozen 下根据文风选一席 | 相对随机指定规则的非规范归因 | Blind Judge 明知 null 仍故意忽视 |

这些是论文最有价值的“管中窥豹”：把行为放进一个有可观察量、有反例、有规范参照的模型，而不是替模型宣布一种内部心理机制。

---

## 13. 值得实施的 replay：问题、预测、最小设计与提示词

**本节是候选执行规格，尚未发送请求。** 固定旧队列不等于已经预注册新的提示、损失、重复数和统计分析。[A3–A4] 以下应先落入一个带 hash 的 execution manifest，再开始付费采集。

### 13.1 R0：Blind / Informed 固定对话比较——首先实施

**科学问题。** 告知生成机制后，相同对话上的概率报告是否更接近已知 null？

**已知规范。** 在两种条件对应的真实实验机制中，target 都独立公平；Informed 额外把这一机制告诉模型。$p^*=1/2$。Blind 没有被告知这一事实，因此不以其偏离直接指控形式逻辑错误。

**队列。** 使用第 1.4 节全部七条已冻结完整 Frozen，不筛原选择。每条只提供公共背景和原有时序问答；删除原终局、置信度、终局理由、target 标签、私有初始化、来源包、模型名和内部文件 ID。对话里实际被要求说出的引文保留；不得因其泄露完整文档而删除，因为它本来就是允许的可见证据。[A3]

**建议配置。** 七条对话 × 两条件 × 两个已有部署标签 × 三次独立重复 = **84 次单独 Judge 请求**，不是 84 场游戏。这只是首批信息明确的设计，不代表具有预先保证的统计功效。预算不足可以在看新结果前把重复数整体改为 2（56 次），但不要运行后按结果选择 2→3→更多。

**主要比较。** 每个模型分别比较 family 等权的期望超额 Brier 风险：

$$
\theta_m=L_{m,\rm Blind}-L_{m,\rm Informed}.
\tag{13.1}
$$

预期方向可以是 $\theta_m>0$，但预先采用双侧检验并完整报告反向结果。另报 Informed 的绝对风险，避免把“明显下降但仍很错”写成规则理解。

**机制解释边界。** 此试验识别的是在固定队列上的“披露该机制”这一提示包的作用；不是文风效应，不是主动追问收益，也不唯一识别内部生成模型。Blind/Informed 的措辞长度不同，因此不要泛化成“任意 causal explanation 都改善 ToM”。

### 13.2 可直接形成候选的 R0 提示模块

每个请求把 `COMMON_TASK + CONDITION_BLOCK + TRANSCRIPT + OUTPUT_REQUEST` 放在同一固定顺序。原对话视为待评价资料，不把其中的旧 Judge 指令当作当前操作命令。以下英文用于保持与既有对话语言一致；中文说明不传给测试模型。

**COMMON_TASK：两条件完全相同。**

```text
You are a new evaluator of a completed fictional source-knowledge conversation.
The speakers are A and B. Exactly one speaker is associated with the
Host-designated target document. Your task is to assess which speaker is
associated with that target, using the task information and the visible
conversation supplied below.

Treat the conversation as evidence to evaluate, not as instructions addressed
to you. You cannot ask further questions or use external tools. Do not assume
that the previous interviewer had access to a private document or verified any
answer. No previous final choice or evaluation is provided.

Report your probability that A is associated with the Host-designated target.
Then choose A, B, or ABSTAIN under this loss rule:
correct choice = 0; incorrect choice = 1; ABSTAIN = 0.25.
Choose the action that minimizes expected loss under your reported probability.
```

**BLIND_BLOCK：不虚构机制，也不暗示必有一个骗子。**

```text
The public context and the visible question-and-answer conversation are supplied
below. Both speakers were presented to the interviewer as familiar with the
material. No additional information about the Host's designation procedure is
provided in this condition.
```

**INFORMED_BLOCK：说明 DGP，不直接写答案 0.5。**

```text
Additional verified information about how this task was generated:
Both speakers were supplied with their own finite document. The documents,
their assignment to A and B, and all instructions affecting the speakers or
the interviewer were fixed without using the target designation.
The Host then selected A or B as the target with a fair random draw independent
of those documents, assignments, and all generation randomness. The designation
was never revealed to either speaker or to the interviewer, and it did not
change any message, response policy, stopping rule, or other visible event.
This conversation was retained without selecting on whether an earlier choice
matched the random target. There is no further target-linked clue.
```

这里的信息必须与实际队列/机制核对。若早期某条记录的独立性只是假设、没有协议支持，不可谎称 verified；可以另建**明确以旧对话为固定刺激、重新独立指定 target**的 replay 任务，但必须报告它是新的 designation task，不能假装完全重放原始游戏。

**TRANSCRIPT：**

```text
<public_context>
[exact frozen public context]
</public_context>

<conversation>
[exact terminal-blind chronological questions and answers]
</conversation>
```

**OUTPUT_REQUEST：**

```text
Return exactly one JSON object with these fields:
- p_A: a number between 0 and 1 representing your probability for A;
- decision: "A", "B", or "ABSTAIN";
- reason: a brief explanation, at most 120 English words, of which supplied
  information supports or limits that probability.
Report p_A before the other fields. Do not provide hidden chain-of-thought,
reconstruct private instructions, or add text outside the JSON object.
```

以上不要求暴露隐藏推理；`reason` 是公开的简短证据解释。输出顺序是一项固定协议选择，不用它声称“概率未受内部解释影响”。

### 13.3 R1：双向 noisy-anchor 与无对话基线——优先补充

**科学问题。** 模型能否保留外部有效信息，同时不从独立社会对话中增加假证据？

使用 R0 的 Informed DGP，再加：

```text
After the conversation was fixed, a separate clue was generated. Conditional
on the target, the clue points to the target speaker with probability 0.80 and
to the other speaker with probability 0.20. The same probabilities apply when
the target is A and when it is B. The clue's random error is independent of the
documents, the conversation, and all earlier generation randomness.
The clue points to [A/B].
```

每个输入做 A/B 两种线索方向。既有问答未因新线索重新生成。对照请求保留完全相同的任务机制与线索，只不给对话；不要换成另一个领域的数学题。

**oracle。** $p_A^*=0.8$ 或 $0.2$，损失 0.25 时应选择线索指向一席。主终点仍为 (10.3)，辅以 $b_h,s_h$ 和方差分解。只报告“有无对话”配对变化，不能由均值变化唯一归因于某一文风因素。

**规模。** 全七条 × 两方向线索 × 两模型 × 三重复 = 84 次；无对话基线两线索 × 两模型 × 三重复 = 12 次，共 96 次。此为后续模块，不与 R0 自动捆绑。规模按请求数而非价格报告，长记录和隐藏 reasoning 仍可能占用较多额度。

可以在运行前指定只用四条记录做较小机制资格检查，但选择规则必须独立于本模块新结果，并明确其覆盖不等于全队列。首版建议保留全队列，避免再产生人为挑选。

### 13.4 R2：座位交换——定位偏移而非追求翻转

对 R0 payload 完整执行 $\sigma$。计算 (10.14)，同时报告原始与交换的报告分布。这个模块回答“偏好如何随标签交换变化”，不单独证明文体因果效应。

若需要压缩预算，先对 R0 使用同样全队列；不根据最高置信度、最大错误或最漂亮翻转来选择交换对象。与原始请求不共享角色会话，防止显式记忆原决策。

### 13.5 R3：prefix replay——只在终局结果确实值得追时实施

对每条记录预先选定：第一轮完整问答、约一半完整轮数、最后一轮完整问答。重复位置合并。每个 prefix 都在新的 Informed 会话中评价，保持模板相同。

短 prefix 看不到后面事实，这是被操纵的证据量；不能把这些 prefixes 算成新的材料样本。检验绝对规范风险和均值随 prefix 的变化，并用 (10.9) 排除解码方差被当作动态漂移。不把不单调结果“修饰”成随时间累积，也不把多数前缀独立采样曲线称为原 Judge 的心智演化。

### 13.6 不应由 replay 承担的验证任务

| 想要的结论 | 为什么旧终局 replay 不够 | 真正需要什么 |
|---|---|---|
| 自由追问比 passive 更有效 | 问题轨迹已固定，缺少反事实策略 | 前瞻性策略随机化/匹配信息预算 |
| 来源生成分布的 TV 接近某个值 | 没有可估计的独立来源分布样本 | 受控有限来源生成器或可验证密度 |
| Boundary-aware 有稳定更强骗术 | 策略提示与回答采样不可简单排序 | 同来源、完整随机化策略对照 |
| 模型具有 persistent latent dossier | 外部过程可以有等价实现 | 新内部干预或限定表征假设 |
| 表面多样性导致 over-inference | 旧材料的内容、领域与 framing 都变化 | 同事实的双版本并前瞻性冻结 |
| 特有 ToM 缺陷而非一般概率缺陷 | 计算 0.5/0.8 可退化为概率题 | no-dialogue、有效线索，必要时再加匹配非社会控制 |

### 13.7 结果如何改变论文，而不是无论什么都宣布成功

| 结果形态 | 合理解释 | 仍缺什么 |
|---|---|---|
| Blind 偏移，Informed 回到 0.5；noisy-anchor 也正确 | 显式机制说明可以约束固定对话上的归因 | 不证明内部 Bayes 实现，未必有新认知缺陷 |
| Informed 仍偏移，但无对话线索也算错 | 可能含一般概率/指令理解问题 | 不能优先归因于社会证据 |
| 无对话线索正确，加入无关对话后系统偏移 | 支持对话对规范概率报告的干扰 | 尚需识别具体文本因素 |
| null 全报 0.5，线索也全报 0.5 | 保守或规则化默认，不是选择性利用信息 | 需要解释 cue underuse |
| 系统均值正确，方差较大 | 部署不稳定而非稳定的来源偏见 | 重复性与输出分布是主结果 |
| 全部条件包括有效线索都正确 | 该部署在此队列上通过这些控制 | 不能再制造一个“失败故事”；既有 audit 保持探索性 |

本项目不需要把每次输出都解释成理论成功，也不需要为了得到错误而无限改 prompt。

---

## 14. 新实验的统计规格：固定队列效应，不伪装总体推断

### 14.1 估计量与分母

设六个 family 为 $f=1,\dots,F$，$F=6$；family $f$ 有 $n_f$ 条 replay 记录。EB05 有两条，其余各一条。令：

$$
w_j=\frac{1}{Fn_{f(j)}},\quad \sum_jw_j=1.
$$

对模型 $m$、条件 $z$，定义固定队列风险：

$$
L^{\rm fix}_{m,z}
=\sum_{j=1}^7w_j\,
E_U\big[(\hat p_{j,m,z,U}-p^*_{j,z})^2\big].
\tag{14.1}
$$

使用所有独立重复的均值估计期望。每模型分别给表；若以两模型平均为单一主终点，必须在采集前明确，不在看完后选择最好方向。概率风险、动作频率、无效率分开报告。

### 14.2 有界风险的有限调用概率界

在 R0 中令：

$$
D_{jr}=(\hat p_{j,B,r}-1/2)^2-(\hat p_{j,I,r}-1/2)^2\in[-1/4,1/4],
\qquad
\widehat\theta=\sum_{j,r}a_{jr}D_{jr},\quad a_{jr}=w_j/R.
$$

若各新会话输出独立、部署稳定，则加权 Hoeffding 界给出：

$$
P(|\widehat\theta-\theta|\ge t)
\le 2\exp\left\{-\frac{8t^2}{\sum_{j,r}a_{jr}^2}\right\}.
\tag{14.2}
$$

**推导。** 每个加权变量的取值区间长度为 $a_{jr}/2$，代入独立有界和的 Hoeffding 不等式。[R10] □

本队列 $\sum_jw_j^2=11/72$。三次重复时 $\sum_{jr}a_{jr}^2=11/216$，分布无关 95% 半宽约为 **0.15324**。这相当宽，提醒我们 84 次请求不是自动拥有很强功效；结果是否精确还取决于实际方差与效应大小。此界只控制给定队列、稳定部署的调用随机性，不控制向未见世界的外推误差。

### 14.3 更适合小规模前瞻性比较的随机化

每个 `transcript × model × replicate` 建立两个新请求槽位，随机决定哪个先接受 Blind、哪个先接受 Informed。固定两个 payload，随机化配对内顺序，再平衡跨模型和跨 family 的执行批次。不要把所有 Blind 跑完再跑 Informed，以免条件与时间变化完全混杂。

可在明确的 no-interference/稳定请求槽位假设下，对配对内条件标签做 Fisher 型随机化检验，保留原 family 权重。它检验的是**这些固定刺激和请求槽位上的 sharp no-effect null**，不是总体“LLM 没有 ToM”零假设。对概率模型的采样分布解释，仍需声明调用独立性或其他稳定性假设。

给出每 family 的效应与 leave-one-family-out 敏感性；不要把 1,952 个标注单元送进普通独立样本检验。六个便利性 family 的 cluster bootstrap 也不是总体真实性保证。若两个模型的显著性都列为并列主要判断，预先处理两项多重比较，不在结果后挑一个。

### 14.4 固定重复数、停止与失败

三次独立重复是建议的基础重复，不是“足够证明稳定”的标准。预先冻结总请求数与预算上限；不得按 p 值、翻转、错误或成功追加。

格式无效、可见回答为空、截断、transport failure 和拒绝提供概率均单列。无效不等于 $\hat p=0.5$，预算中止不等于 ABSTAIN。保留原始所有响应，不用另一个模型修写概率或解释。

可采用“无自动语义重试；transport 未产生任何可见回答时按预先策略续发”的方案，但必须在执行 manifest 中选定具体规则；本稿不把历史的多种恢复办法自动推广成统一新协议。

若完整终点缺失，报告 valid-only 风险和缺失权重。针对 null Brier，若把未观察概率视为未知的 $[0,1]$ 值，则每个缺失分数在 $[0,1/4]$；用该范围给最乐观/最悲观完成敏感性区间，不用单值插补冒充真实结果。对 $p^*=0.8$，范围上界为 $0.64$，不能沿用 $1/4$。

### 14.5 API 参数与隐私记录

以下仅引用既有实验中记录过的设置，不宣称它们是当前所有服务的统一能力：模型标签 `glm-5.3`、`qwen3.8-max`，temperature 0.5，最大生成预算 32768，nonstreaming，不启用工具，reasoning 为部署默认。[A1–A3 及其链接的原始协议]

新 run 前记录实际可用 endpoint、返回 model ID、参数支持情况和版本/时间；同名部署不保证权重相同。不要仅为追求“看起来一致”强加接口不支持的 seed/effort 参数。相同 temperature 或 token ceiling 不意味着相同有效计算量。

每次保存：精确输入 hash、条件、角色、public payload、完整可见回复、usage、结束原因、失败类别、调用时间、解析器版本、独立会话标识的本地映射。身份 token、API 密钥、账号、session URL 和隐藏 reasoning 不发布，也不跨角色传递。

**这份文档不是调用权限。** 未获授权前只准备 manifest 和离线验证，不启动 API，不充值，不打开超额计费，不修改已冻结旧数据。

### 14.6 分析输出的最小集合

建议生成四张表，而不是几十个指标：

1. **覆盖表**：计划/成功/无效/缺失请求，逐模型与条件。
2. **主要风险表**：family 等权的 Blind/Informed 风险、差值、均值偏移及方差。
3. **线索利用表**：有无对话时 $b_h,s_h$、超额风险与决策 regret。
4. **证据理由表**：少量预先定义的理由标签，带可核对 span；明确是结果解释，不做内部机制证明。

旧 audit 表保留为探索语料；新 replay 表保留为固定刺激实验，不合并成一个“大样本游戏准确率”。

---

## 15. 论文结构与最可能产生的非平凡 ToM 结果

### 15.1 主文应少而有用，不把全部数学搬进去

**理论正文建议保留三块。**

- 目标与协议：操作性访问、随机指定及交互等价，说明什么是被估计的量。
- 一个实质限制：来源模拟的轮数无关紧界 (5.1)，加随机目标 corollary；区分因果接收史与可模拟行为。
- 一个评价结构：选择性归因界 (9.1)，以及规范概率评分、有效线索分解 (10.12)。

链式分解、固定预算与停止下界、稳健凸包、主动 scope 反例和迎合收缩放附录。它们指导解释，但当前自然语言数据没有识别其中全部参数。

### 15.2 三类值得写、但必须用不同证据支持的结果

**结果类型 A：可观察内容不等于可恢复身份。** 由 formal model 和模拟/随机目标结果支持；不是某一模型失败频率。需要把定理假设与实际实验协议一一对应。

**结果类型 B：在正确事实观察上进行错误目标归因。** 由逐项 audit 的来源与理由检查支持。它区别于普通事实 hallucination：一句“引用更精确”可以是真的，但并不能证明随机 target 在那一席。

**结果类型 C：有效信息与无关社会线索的选择性使用。** 由 R0/R1 及基线支持。若无对话时正确、有对话时偏移，便形成比“会不会说不知道”更具体的行为效应。若模型都遵守规范，则报告遵守，而不夸大成失败。

### 15.3 ToM 定位的边界

这里的 ToM 是**关于另一个 agent 信息访问、来源约束和策略性表达的功能性推断**。它不自动覆盖情绪识别、意图理解、错误信念的所有形式，更不证明具有人的心智结构。Decrypto 同样区分游戏/特定探针与广义 ToM 的外推。[R9]

Frozen 随机标签本身不是一个深刻的心理状态；它是检验“哪些线索能支持访问归因”的 null。项目的 ToM 意义来自将这个 null 与真实来源访问、策略性模仿、对他人知识的理由表达相接，而不是把猜隐藏硬币包装成心智理论。

### 15.4 当前可写的摘要骨架，不预写未知结果

> We study epistemic attribution in a conversational game where agents explain finite private sources and an interrogator infers source access. We formalize the setting as an adaptive statistical experiment, separating source-conditioned behavior from causal access history and independent target designation. An audit of existing interactions identifies cases where observable linguistic differences are extended into unsupported provenance or target inferences. We derive simulation and selective-attribution bounds and specify fixed-transcript experiments with known posterior targets. These experiments test whether language models distinguish target-identifying evidence from suggestive but ancillary conversational information.

其中 `specify` 只有实验真正执行后才能改成 `evaluate` 并填入结果。不要现在写“发现所有模型失败”“显著改善”或“证明高阶 ToM 机制”。

### 15.5 本文不承诺什么

经典数学工具可以为一篇 ToM/NLP 行为研究提供有效骨架，但“有定理”不保证发表，null 的简单推论也不能单独承担主要新颖性。论文的实质价值取决于任务区分是否有用、audit 是否可靠、replay 是否给出可复现且有排他性解释的行为结构，而不是定理编号多少。

---

## 16. 相比此前讨论，必须保留的数学修正

这些修正不改写历史结果；它们明确替换此前过强的理论表述。

| 先前容易写出的说法 | 本稿采用的精确版本 |
|---|---|
| 等价类上恒定 ⇔ 有限互动能恢复目标 | 仅是结构可识别/因子分解；有限样本误差和一致性另需条件 |
| $R_{mm}=(1-\sup_\pi\inf_\beta TV)/2$ 总成立 | 一般只有 (6.2) 的下界；统一判别器与 oracle 判别器不同 |
| $K\perp G$ 所以 $K\perp H$ | 还需排除其他通道，或声明 $K\perp H\mid G$；Frozen 用更强生成独立性 |
| $P(G=K)=r$ 所以最优准确率就是 $r$ | 需要等先验、对称独立噪声等条件，整体正确率一项不够 |
| 来源不同就必然可识别 | 必须是 target 条件分布不同；来源模拟可令 causal history 不可辨 |
| 没有实际文档就不能长期一致 | 正确的在线 posterior predictive 可以与预抽来源等价 |
| Strong→Boundary-aware→Frozen 是已证强度递增 | prompt 不保证策略集合包含；Frozen random-target 是不同信息结构 |
| 更多合法问题总提升实际 LLM 表现 | 只保证最优可获取信息不下降；实际策略可以退化 |
| 即时信息增益最大的问题就是最优首问 | 规划可先获取与目标独立、但决定后续诊断位置的 nuisance 信息 |
| 没有 topology 也可使用边界 $\partial\mathcal A$ | 先用可回答集合与来源关系；几何语言只是比喻 |
| confidence 是内部 posterior | 是被诱导出的报告变量；用行为分布建模，不直接读取心智 |
| informed-null 规则成立对所有任意 H | 条件概率 a.s. 成立；概率零历史及不可达历史另作处理 |
| null 下弃权永远“理性” | 需要给定错误/弃权损失，或者只描述动作不判断最优性 |
| prefix 单次报告变化就是信念累积 | fresh replay 是截面敏感性，变化还含生成方差 |
| 两次 A/B 交换就完全分离座位与内容 | 得到交换奇偶分解；出现次序等仍可能混杂 |
| replay 让 null 报 0.5 就验证 ToM | 至少要检查有效线索、无对话基线及任务理解 |
| 107 次回答就是样本量 107 | 有 family/trajectory/event 依赖，固定刺激效果与总体效果分开 |
| replay 在“验证信息论定理” | 定理靠证明；replay 检验模型行为是否符合定理给出的规范参照 |

---

## 17. 数学核对、证据路径与参考文献

### 17.1 本轮数学检查的范围

除正文证明外，用固定随机种子 `20261007` 在有限概率空间做了以下补充检查：

- 2,000 对随机六点分布检查来源模拟 TV 上限；另对七个 $\epsilon$ 点核对紧性构造。
- 2,000 组随机选择/弃权策略核对 $|c(2a-1)|\le\Delta$。
- 2,000 组概率核对 Brier 恒等式、双向线索分解与座位交换奇偶分解。
- 穷举 16 个隐状态以及全部两步分支策略：最优 scope-first 风险为 0；L-first、R-first 各为 0.25。
- 有限格点核对复合假设例子的 minimax 风险为 0.5（浮点表示为 0.49999999999999994）。
- 核对均值为 0.5、每次随机报告 0.2/0.8 的例子：超额 Brier 为 0.09，系统平方均值偏差为 0。
- 按本队列的 family 权重，核算三次重复时式 (14.2) 的 95% 半宽为 0.1532398454。

配套 `XiaBaiWang_math_checks.py` 只使用 Python 标准库；运行后输出数学检查摘要，不联网、不调用模型。

这些是数值/有限枚举检查，**不是 Lean 形式化证明，不是文献 novelty audit，也不是 LLM 实验**。数学通用性仍由列出的条件与证明承担。本轮没有重新运行项目全量语义 audit，也没有声称机械检查可保证每个自然语言标签正确。

### 17.2 内部证据参考

本文的观察和计数只引用以下冻结材料，不把后来研究计划当已完成结果。

- **[A1] 全量 claim audit，RESULTS.md。** 固定提交 `af15fd160e070ec39bb6a60c2d4f64a3474fee8d`。包含 Reader/Bluffer、前提响应、终局理由和 query adaptivity 的观察与限制。
  [打开审计报告](https://github.com/WanSuiMm/project_xia_bai_wang/blob/af15fd160e070ec39bb6a60c2d4f64a3474fee8d/epistemic_boundary_mimicry/analysis/claim_audit_20261007/RESULTS.md)
- **[A2] THEORY_EVIDENCE_MAP.md。** 同一固定提交。规定四个理论对象的假设、已有证据与未估参数。
  [打开理论—证据映射](https://github.com/WanSuiMm/project_xia_bai_wang/blob/af15fd160e070ec39bb6a60c2d4f64a3474fee8d/epistemic_boundary_mimicry/analysis/claim_audit_20261007/THEORY_EVIDENCE_MAP.md)
- **[A3] REPLAY_COHORT.md。** 同一固定提交，七条完整 Frozen 的不依结果筛选规则、终局清除和实验边界。
  [打开固定 replay 队列](https://github.com/WanSuiMm/project_xia_bai_wang/blob/af15fd160e070ec39bb6a60c2d4f64a3474fee8d/epistemic_boundary_mimicry/analysis/offline_coding_20261005/REPLAY_COHORT.md)
- **[A4] 用户提供附件 TRANSCRIPT_REUSE_ANALYSIS.md。** 2026-10-05 离线复用方案，53 行；本轮读取了完整附件。说明旧对话、终局 replay 与同事实呈现对照的不同估计对象。未为本地路径编造外部链接。

### 17.3 数学与 ToM 参考

下列链接本轮已核对标题或相关章节。本文只借用所需标准工具，不声称下列作者提出了本文特定游戏的全部推论。

- **[R1] Naghshvar, M.; Javidi, T. (2013). Active Sequential Hypothesis Testing.** *The Annals of Statistics*, 41(6), 2703–2738. DOI: `10.1214/13-AOS1144`。主动查询、动态规划、信息获取与可靠性的参照。
  [论文](https://arxiv.org/abs/1203.4626)
- **[R2] Canonne, C. L. (2022; revised 2023). A Short Note on an Inequality between KL and TV.** arXiv:2202.07198。Pinsker、Bretagnolle–Huber 及二元检验界。
  [论文](https://arxiv.org/html/2202.07198v2)
- **[R3] Kaufmann, E.; Cappé, O.; Garivier, A. (2016). On the Complexity of Best-Arm Identification in Multi-Armed Bandit Models.** *JMLR*, 17(1), 1–42。重点为 Lemma 1 和 Appendix A 的停止时间变换测度；本文的历史依赖核表达单独给出条件，不把所有模型假定成 bandit IID arms。
  [期刊页](https://www.jmlr.org/papers/v17/kaufman16a.html)
- **[R4] Makur, A.; Zheng, L. Linear Bounds between Contraction Coefficients for f-Divergences.** arXiv:1510.01844v4 (2018 version)。数据处理与散度收缩。注意这份 arXiv 的作者是 Makur/Zheng，不是其他常被引用的 SDPI 作者。
  [论文](https://arxiv.org/abs/1510.01844)
- **[R5] Sion, M. (1958). On General Minimax Theorems.** *Pacific Journal of Mathematics*, 8(1), 171–176。有限紧凸情形的交换基础。
  [期刊页](https://projecteuclid.org/journals/pacific-journal-of-mathematics/volume-8/issue-1/On-general-minimax-theorems/pjm/1103040253.full)
- **[R6] Gneiting, T.; Raftery, A. E. (2007). Strictly Proper Scoring Rules, Prediction, and Estimation.** *JASA*, 102(477), 359–378。概率报告的适当评分；本文 binary Brier 与分解均逐式推导。
  [论文](https://doi.org/10.1198/016214506000001437)
- **[R7] Blackwell, D. (1953). Equivalent Comparisons of Experiments.** *The Annals of Mathematical Statistics*, 24(2), 265–272。实验信息与决策价值的区分。
  [论文](https://projecteuclid.org/journals/annals-of-mathematical-statistics/volume-24/issue-2/Equivalent-Comparisons-of-Experiments/10.1214/aoms/1177729032.full)
- **[R8] Golovin, D.; Krause, A. Adaptive Submodularity: Theory and Applications in Active Learning and Stochastic Optimization.** arXiv:1003.3967v5。用于说明自适应贪心需要额外结构；本文 scope-first 反例是自行给出的有限模型。
  [论文](https://arxiv.org/abs/1003.3967)
- **[R9] Lupu, A.; Willi, T.; Foerster, J. The Decrypto Benchmark for Multi-Agent Reasoning and Theory of Mind.** arXiv:2506.20664，重点看 §2、§3.2、Appendix B/H。FAIR/Meta 与 Oxford 的游戏式 ToM 建模参照；本稿不依赖任何未经另核的会议届次或奖项。
  [全文](https://arxiv.org/html/2506.20664v1)
- **[R10] Hoeffding, W. (1963). Probability Inequalities for Sums of Bounded Random Variables.** *JASA*, 58(301), 13–30。独立有界变量的有限样本集中界。
  [论文](https://doi.org/10.1080/01621459.1963.10500830)

### 17.4 往仓库移交时的建议

建议将本文作为新的理论草稿存入 `epistemic_boundary_mimicry/theory/`，不要覆盖旧 audit 或原实验协议。另建 replay execution manifest，至少冻结：队列 hash、提示 hash、模型部署信息、loss、主要估计量、重复数、随机化顺序、失败规则和预算。此处仅建议位置，本轮没有上传或创建这些仓库路径。

---

## 最终工作判断

我们已有的不是“一个已被证明的 LLM 心理机制”，而是一个值得用统计学刻画的行为问题：**裁判如何从另一个 agent 的语言表现推断其信息访问，什么时候这种推断有证据，什么时候只是将可见差异赋予了过强的意义。**

经典数学已经足以给出三种有效约束：

$$
\boxed{\text{来源模拟限制原则上能识别什么}}
$$

$$
\boxed{\text{查询与选择性推断限制信息、成本和准确率如何交换}}
$$

$$
\boxed{\text{已知 DGP 与适当评分让 replay 有精确规范参照}}
$$

下一步最值得验证的不是定理本身，而是：**模型报告行为能否区分有效线索、无关社会文本与自身采样波动。** 这既接住了 audit，也保留了 ToM 研究的意义，而不需要人为制造新的数学语言。
