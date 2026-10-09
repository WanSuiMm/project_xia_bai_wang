# When Can You Tell Who Knows? Strategic Simulation and Statistical Identifiability in Interactive Theory of Mind

**Research paper draft v1 — 10 October 2026**

This draft synthesizes evidence through 10 October 2026. OSI48 now has a 48/48 strict-valid completion overlay assembled from 51 physical attempts. The overlay uses mixed requested output ceilings: 22 GLM replies at 4096 tokens, two amended GLM tail replies at 16384, and 24 Qwen replies at 8192. The earlier unchanged-budget completion remains 46/48, with GLM/PERSISTENT at 10/12; all failed attempts are retained in the evidence record.

## Abstract

Interactive theory-of-mind tasks often ask a judge to infer which speaker had access to a private source. The answer depends on the full law of observable dialogue, not on whether one utterance sounds more specific, fluent, or source-like. We formulate access attribution as an adaptive statistical experiment and separate causal source access from an independently assigned target label. Under equal prior odds, the optimal forced-choice error is determined by the total-variation distance between the two target-conditioned transcript laws. If a no-access speaker simulates the source-conditioned response process closely, no adaptive questioning can recover the access relation reliably; if a target label is assigned independently of all dialogue generation, the transcript carries exactly zero information about that label.

A set of distinct experiments illustrates why these conditions matter. In a frozen random-target replay, the reported 42/42 informed responses had the exact null posterior, 0.5. In a genuine-access source-boundary manipulation, a small six-material screen showed no consistent improvement in judges' source attribution. A finite known-mechanism screen yielded 29 exact posterior reports and 31 loss-optimal actions across 32 analyzed slots, yet failed its preregistered weighted calibration gate. In OSI48, a 48-slot completion overlay under a specified Beta–Bernoulli opponent family produced exact 0.5/ABSTAIN reports in all refreshed cells and a positive history reversal in both models; persistent-condition posterior MSE was 0.07030 for GLM-5.3 and 5.78×10⁻⁶ for Qwen3.8 Max. The overlay combines requested GLM output ceilings of 4096 and 16384 tokens. These results describe finite, supplied-mechanism behavior and do not establish human-like belief, an internal inference algorithm, or general opponent modeling.

## 1. Introduction

Suppose two speakers answer questions about a private dossier. One received the dossier; the other may be guessing, strategically inventing, or reproducing its likely response pattern. A judge observes their answers and must decide who had access. This looks like a theory-of-mind task, but the observable question is statistical: do the two access conditions induce distinguishable distributions over the entire interaction?

The distinction matters because a transcript can be coherent without identifying its cause. A speaker may reproduce source facts without access, and an informed speaker may omit or distort them. Likewise, one detail that resembles a source does not by itself establish which speaker received it. Adaptive questions can expose a difference in response distributions, but they cannot reveal a target label that was kept out of every input, nor overcome exact distributional simulation.

We make three contributions. First, we state an identifiability framework in terms of adaptive transcript laws, separating source access, a random target designation, and the judge's reported probability and action. Second, we connect this framework to a source-simulation bound: when a no-access strategy draws an approximate source and uses the same response rule, the maximum information available from any adaptive interrogation is limited by the distance between the source and simulation distributions. Third, we organize a set of completed experiments by the estimand each can support. The results include a null-consistent frozen replay, a small genuine-access manipulation, strategic archive and notice screens, and a finite known-mechanism calibration task. These studies are not pooled because they use different target constructions, prompts, samples, and scoring rules.

Our central claim is deliberately narrow: **access is inferable only to the extent that access changes the joint law of observable responses under the allowed interaction policy.** We do not claim that an LLM has, or lacks, human-like mental states. We treat “theory of mind” here as functional inference about another agent's information access and strategic behavior under an explicit information structure.

## 2. Related work, bounded

Active sequential hypothesis testing studies how a decision maker should choose observations over time when evidence collection is adaptive and errors are costly. We use the same broad statistical perspective: questions and answers form a sequential experiment, and information is evaluated through the distributions they induce. Our focus is the identifiability of an access relation under strategic or source-simulating response kernels, rather than a new query-selection policy. [Naghshvar and Javidi (2013)](https://arxiv.org/abs/1203.4626) provide a standard reference for adaptive sensing and sequential decision limits.

Recent work also uses opponent simulation as an inference-time method for online strategic adaptation in repeated negotiation. [Liu et al. (2026)](https://proceedings.mlr.press/v306/liu26ef.html) learn an opponent model and simulate against it when selecting responses. Our question is complementary: when does a transcript support an inference about an agent's access or strategy, and when can a simulator reproduce the same observable law? The existence of a useful opponent model does not by itself establish that access is identifiable from its outputs. This short comparison is not intended as a survey of theory-of-mind benchmarks or strategic-agent methods.

## 3. Methods and estimands

### 3.1 Access, target designation, and the transcript

Let $K ∈ {A,B}$ denote the seat that is the target of an attribution. Let $S_A,S_B$ denote the documents actually received by the speakers, $C$ the public context, and $H_t$ the public question-answer history through turn $t$. A judge chooses a question from the prior history and receives a response generated by a history-dependent kernel. The complete interaction, including a stopping decision, is the transcript $H_τ$.

Two tasks that may look alike have different estimands:

1. **Access attribution:** a source is assigned to one speaker, and the question is whether the resulting source-conditioned response laws differ by seat.
2. **Random-target attribution:** sources, seats, and response inputs are fixed first; a target seat is then selected independently. The target label does not affect any answer. This tests whether a judge invents information about an arbitrary designation; it does not test which speaker actually received a source.

The reported probability $p̂$ and final action $d ∈ {A,B,⊥}$ are separate observables. For tasks that specify abstention loss, we use correct = 0, wrong = 1, and abstain = 0.25. Under a known posterior of 0.5, abstention minimizes expected loss. A probability report can still be wrong even when the eventual action happens to be optimal, so posterior scoring and action scoring are reported separately.

### 3.2 Completed evidence and analysis units

The evidence base contains several distinct designs. Natural-language transcript audits are used only as exploratory context. Their event counts and rationale codes are not independent trials and are not pooled with controlled replays. For controlled studies, we retain each protocol's own unit: authored material family, fixed mechanism stimulus, or replay slot. Multiple questions or repeated model outputs within a family do not turn that family into multiple independent materials.

The main controlled sources are:

- **Strategic qualification (SQ28):** four authored dossier families. A Qwen3.8 Max Reader and no-source Bluffers answered fixed questions. B0 Bluffers saw a neutral archive; B1 Bluffers saw authentic historical Judge-evaluation examples. Judges either were not told which archive the Bluffer had seen (J0) or were told (J1). The run produced 28 strict-valid replies: 12 Speaker and 16 Judge calls. The design tests bounded archive-exposure and notice manipulations, not adaptive interrogation.
- **Frozen replay (R0):** judges evaluated fixed dialogues under blind and informed prompts. The original registered run attempted 84 positions and had 77 valid replies overall. The delivery reports the informed stratum as 42/42 at the null posterior; it reports seven later valid completion replies separately, without replacing the original 77/84 analysis.
- **Counterfactual source-boundary manipulation (CSB30):** six materials contrast V0, where the queried detail is absent from the source, with V1, where a sentence adds it. In each family, separate Readers answer under V0 and V1; a fixed Bluffer answer is reused in independent single-package Judge decisions. Judges do not see the paired package or the source-version label.
- **Joint epistemic simulation (JES32):** a finite known mechanism generates two-query response packages. In MARGINAL, a Reader repeats a source bit while a non-Reader samples independently on the two questions, matching each one-question marginal but not the joint law. In JOINT, the non-Reader repeats one fair bit, matching the Reader's full two-question response law. Judges know the mechanism but receive no likelihood table or numeric posterior. This is a finite mechanism screen, not a natural-language Speaker experiment.
- **OSI48:** a frozen known-family, unknown-parameter extension described in Section 3.3. A 48/48 strict-valid completion overlay now fills every selected slot across 51 physical attempts, while preserving the original HTTP 403, recovery parse failure, and 4096-token truncation. Two final GLM calls used an amended 16384-token ceiling; the unchanged-budget completion remains 46/48, including 10/12 GLM/PERSISTENT slots [E8, E10, E11].

### 3.3 Frozen persistent-versus-refreshed mechanism study (OSI48)

The frozen OSI48 design comprised $3 × 2 × 2 × 2 × 2 = 48$ Judge calls: three archive histories, two history/current coupling conditions, two seat orders (which seat is observed as 1111), two Judge models (GLM-5.3 or Qwen3.8 Max), and two independent repeats. Each archive contains eight identity-confirmed non-Reader answers with no mapping to current A/B. The archive answers share one $b_{archive} ∼ Uniform[0,1]$; conditional on that rate, each answer is an independent Bernoulli draw. The history count $s$ is the number of ones among those eight answers, not the history length. The fixed histories are 00100000, 01101001, and 11011111, giving $s=1,4,7$.

In the current block, the Reader answers with four independent fair source bits. The Bluffer draws a continuous $b_{current} ∼ Uniform[0,1]$ and, conditional on it, answers independently as Bernoulli($b_{current}$) on each of four questions. Under PERSISTENT, $b_{current}=b_{archive}$. Under REFRESHED, $b_{current}$ is a new independent Uniform[0,1] draw, held fixed across the four current answers. Thus a shared rate creates marginal dependence among answers; it does not make the Bluffer repeat one binary value.

For the current packet A=1111, B=0000, the exact posterior that the 1111 seat is Reader is 66/67, 1/2, and 1/67 for $s=1,4,7$ under PERSISTENT, respectively, and 1/2 for every REFRESHED history. Swapping the seats complements $p_A$. The eight-answer history has no seat/name mapping, no identity label is sampled for scoring, and selecting these positive-probability packets supplies no additional identity clue. These are mechanism-derived targets, not observed model outputs [E6, E7].

**Completion record:** the original batch halted on its first HTTP 403/payment-category response, with no model answer and 47 requests unstarted. Credential-only recovery produced two valid Qwen replies and one invalid GLM response (`HTTP 200`, `ValueError`). The 46-slot supplement retained the two valid recovery replies for the merged view and dispatched 45 requests, receiving 44 additional valid replies and one GLM truncation at the 4096-token ceiling; one selected slot remained unstarted. The final two-slot completion retained the truncation record, retried that slot, and filled the unstarted slot using a GLM ceiling of 16384 tokens. The selected overlay therefore contains 48/48 strict-valid slot observations across 51 physical attempts: one original request, three recovery requests, 45 supplement requests, and two tail requests. It includes 22 GLM replies at 4096 tokens, two at 16384, and 24 Qwen replies at 8192. Only the requested GLM output ceiling changed for the two tail calls; prompts, models, temperature, reasoning controls, parser, and oracle stayed fixed. The unchanged-budget completion remains 46/48 valid, with GLM/PERSISTENT at 10/12; the amended overlay is reported separately because its GLM output ceiling is mixed [E11].

The registered endpoints are equal-stimulus summaries for these finite packets, with each model and coupling condition weighted separately. Posterior MSE/MAE, expected decision loss, action optimality, and history contrasts are now defined for all four model-by-condition cells. No identity label is sampled for scoring, and the replies are not evaluated against a realized Reader seat. The design samples no LLM Speaker: it measures reported posterior probabilities and actions for a supplied response family with an unknown scalar realization. It does not measure spontaneous strategic adaptation, an unknown strategy family, naturalistic interrogation, or general theory-of-mind capability [E6, E7, E11].

**Historical startup snapshot (18:28:53 Asia/Shanghai):** the recovery startup check recorded two dispatched requests, one strict-valid Qwen reply, and a live worker. This dated snapshot is retained as startup evidence. It predates the later cutoff and completion overlay documented in [E10] and [E11] [E9].

## 4. Statistical framework

For a fixed adaptive interrogation policy $π$, let

$$
P_k^{π,T} = Law(H_T | K=k,C,M),  k ∈ {0,1},
$$

be the law of the public transcript after at most $T$ turns under mechanism $M$. The response kernel may depend on the full history and may integrate over private documents, memory, and strategy state. We do not assume independent answers across turns.

### 4.1 Structural identifiability and finite-sample risk

Two states are interaction-equivalent under a policy class $Π$ when they induce the same transcript law for every policy in $Π$. A target attribute is structurally identifiable only if it is constant within every such equivalence class. This criterion says whether the attribute is in principle a function of the experiment; it does not say that one finite transcript recovers it with zero error.

With equal prior odds and forced binary decisions, the optimal Bayes risk for a fixed policy is

$$
R*(π) = (1 − TV(P₁^π,P₀^π))/2.
$$

Thus, language differences matter only insofar as they create differences between target-conditioned transcript laws. This is a standard binary-testing identity, not a claim of a new theorem.

### 4.2 Source simulation bounds identification

Consider an informed source $S ∼ D$ and a no-access simulator $Ŝ ∼ Q$. Assume the two speakers use the same source-conditioned response rule after receiving their respective documents, and all questioning and stopping operate through the resulting answers. If $TV(D,Q)=ε$, data processing yields, for every adaptive policy,

$$
TV(P₁^π,P₀^π) ≤ 2ε − ε².
$$

$$
R*(π) ≥ (1 − ε)²/2.
$$

The bound follows by comparing the swapped source assignments $D ⊗ Q$ and $Q ⊗ D$, then passing them through the common response-and-interrogation channel. When $D=Q$, access can differ causally while the full transcript law is identical, so no allowed interrogation can identify access above chance under equal priors. The assumptions are substantive: a simulator with a different response policy, or one that leaks an access flag, falls outside the result.

### 4.3 Random-target null and selective decisions

If $K ∼ Bernoulli(1/2)$ is sampled independently of sources, seats, prompts, routing, all response randomness, and target-blind stopping, then $H_τ$ is independent of $K$. Consequently $P(K=1 | H_τ)=1/2$ almost surely and $I(K;H_τ)=0$. This is a property guaranteed by the randomization protocol, not an empirical conclusion from a small sample. It applies to the random-target task; it must not be used to reinterpret genuine access-attribution experiments.

Selective actions also need a declared loss. With abstention cost 0.25, abstention is optimal whenever the true posterior lies between 0.25 and 0.75, including the exact random-target null. A judge's high-confidence rationale cannot create information absent from the transcript law. At the same time, finite-sample accuracy can depart from its theoretical value by chance; a handful of correct guesses is not evidence against the null.

These arguments use standard sequential testing and statistical decision tools. The paper's contribution is their application to explicit source-access and strategic-simulation mechanisms, together with an evidence program whose experiments keep different estimands separate.

### 4.4 Latent-strategy persistence and the value of history

Let an archived, identity-confirmed non-reader produce eight Bernoulli answers using one latent rate b drawn uniformly on [0,1]. Conditional on s observed ones, the posterior is Beta(1+s,9-s). If that same rate governs four current answers, the predictive probability of one specified ordered sequence with k ones is

$$
m_s(k)=\frac{\mathrm B(1+s+k,\,9-s+4-k)}{\mathrm B(1+s,\,9-s)}.
$$

For the fixed current packet A=1111, B=0000, the equal Reader likelihoods cancel and

$$
P(K=A\mid D_s,H)=\frac{m_s(0)}{m_s(0)+m_s(4)}.
$$

This yields 66/67, 1/2 and 1/67 for s=1,4,7. If the current rate is independently refreshed, the two extreme sequences each have predictive probability 1/5 and the posterior is 1/2 regardless of history. These identities are standard conjugate prediction; the prospective behavioral contrast is whether the model both transfers relevant history and suppresses its use after an explicit reset.

Integrating over the rate differs from substituting its posterior mean. The latter gives 256/257, 1/2 and 1/257, which preserves reversal and decisions but differs in probability strength. Output agreement with either calculation does not uniquely establish an internal algorithm.

The broader frozen theory [E7] also separates the full path law of a persistent latent strategy from that of a strategy independently redrawn at each answer. Its Bernoulli prior-averaged square-root risk rate requires positive, regular prior density near the Reader parameter. Near-indistinguishable prior mass produces that rate even for an oracle told the current rate; it is not solely an estimation penalty. These Bayes-average statements do not imply a minimax guarantee, and a fixed-question accumulation example does not by itself establish an advantage for adaptive questioning.

## 5. Results

### 5.1 A random-target replay produced a null-consistent informed response

The R0 delivery reports that all 42/42 Informed replies across GLM-5.3 and Qwen3.8 Max gave $p_A=0.5$ and abstained. Its original primary table reports 21/21 valid Informed replies for each model; separately, the full original run had 77 valid replies among 84 attempted positions. Seven later valid completion replies are retained separately and do not replace that original analysis. This is evidence that both deployments followed the stated null response on the fixed Informed replay, not that they carried out an internal Bayesian calculation or have generally calibrated beliefs [E2].

### 5.2 Genuine source access changed answers more clearly than Judge attribution

CSB30 achieved its operational manipulation checks: all six V0 Readers reported that the queried detail was absent from the source, all six V1 Readers gave the added value, and all six Strong Bluffers supplied a different unsupported value. The 30 calls were strict-valid with no retries. Yet the six Judges per condition did not show a consistent shift toward the Reader: mean $p_{Reader}$ was .425 in V0 and .433 in V1, a family-average change of +.008333. Across 12 decisions, one was correct, five wrong, and six were abstentions. These are six authored materials with one Judge sample per cell, so the result is a small qualification screen rather than a population effect [E3].

### 5.3 Strategic archive exposure and notice gave mixed, bounded evidence

In SQ28, the primary actor endpoint is admission on source-unspecified questions. B0 had no coded source-silence admissions on its 12 scoreable source-unspecified answers; B1 had none on its 11 scoreable answers, with SQ02/B1/Q6 unresolved. The explicit-question region was scored separately and also contained no Bluffer admissions. This screen therefore found no observed source-silence mimicry in that fixed sample; its model-assisted first-pass coding and four-family design do not establish a stable speaker policy.

For Judge identity scoring, the 16 responses yielded seven correct choices and nine wrong choices, with no abstentions. The overall realized-label Brier score was .364. Telling the Judge which archive the no-source Bluffer had seen (J1) was descriptively associated with a lower identity Brier score than the no-notice condition (J0), .249 versus .478 across eight calls per notice condition. The relevant independent materials remain four families, and no known Bayes-optimal posterior exists for this generated behavior setting; the contrast is not a calibration or causal population estimate [E4].

A retrospective OMC16 forecast replay used two Judge forecasts per family-condition on frozen Bluffer answers. Exposure to historical Judge-evaluation examples shifted the equal-family mean forecast of an explicit source-silence admission from .0373 to .1292. None of the selected frozen answers contained a clear admission, and one inherited label was unresolved. This is a prompt-conditioned expectation shift on selected outputs, not proof of an internal opponent model, a calibrated probability, or a general expectation about strategic agents [E5].

### 5.4 Known joint response laws exposed a calibration failure despite mostly correct actions

JES32 analyzed 32 fixed mechanism slots. Across those slots, models reported the exact mechanism posterior on 29/32 and selected a loss-optimal action on 31/32. The frozen qualification gate nevertheless failed: GLM-5.3/MARGINAL had weighted posterior squared error .018896605, above the predeclared .01 limit; the other three model-by-mechanism cells passed. The GLM errors included two imperfect probabilities with the correct action and one missed informative case that was incorrectly assigned $p_A=.5$ with abstention.

The aggregate draws on 33 physical attempts: two originally valid replies plus 30 supplemental replies fill the 32 analyzed slots, while one original reply with a duplicated JSON trailer remains invalid. This is not a clean 32-call original run, and the original incomplete record is preserved. The experiment used programmatic speakers and a finite enumeration; it evaluates whether a Judge can apply a known two-query mechanism, not whether an LLM Speaker naturally simulates a source's joint response law [E1].

### 5.5 OSI48: finite history-coupling endpoints on a mixed-budget overlay

All 48 prompts and the schedule were frozen before dispatch. The original batch's first request returned HTTP 403/payment-category error; the credential-only recovery retained two valid Qwen replies and one invalid GLM provider response (`HTTP 200`, `ValueError`). The 46-slot supplement added 44 valid replies, one GLM truncation at 4096 completion tokens, and one unstarted slot. A two-request amendment raised the GLM output ceiling to 16384 for those two slots, retaining the earlier truncation and filling the unstarted position. The selected overlay has 48/48 strict-valid observations across 51 physical attempts. It is a mixed-budget completion overlay: 22 GLM replies used a 4096-token ceiling, two used 16384, and 24 Qwen replies used 8192. Under the unchanged GLM ceiling, the prior completion was 46/48, including 10/12 valid GLM/PERSISTENT slots [E8, E10, E11].

The primary quantities are equal-stimulus posterior squared error for each model and coupling condition, plus the history reversal $Δ_c = mean(p_{1111} | s=1,c) - mean(p_{1111} | s=7,c)$. The registered persistent and refreshed targets are $65/67 ≈ .97015$ and 0. Table entries use strict-valid selected observations; calls are not independent games or a population sample.

| Model | Coupling | Valid slots | Posterior MSE | Posterior MAE | Expected loss / optimal loss | Oracle-optimal actions | Within $10^{-4}$ of target |
|---|---|---:|---:|---:|---:|---:|---:|
| GLM-5.3 | PERSISTENT | 12/12 | .070300 | .078002 | .254975 / .093284 | 10/12 | 9/12 |
| GLM-5.3 | REFRESHED | 12/12 | .000000 | .000000 | .250000 / .250000 | 12/12 | 12/12 |
| Qwen3.8 Max | PERSISTENT | 12/12 | .00000578 | .000694 | .093284 / .093284 | 12/12 | 11/12 |
| Qwen3.8 Max | REFRESHED | 12/12 | .000000 | .000000 | .250000 / .250000 | 12/12 | 12/12 |

Both models reported $p_A=.5$ and abstained in all 12 REFRESHED slots. For PERSISTENT, the mean probability assigned to the 1111 seat at $s=1,4,7$ was $.755475,.5,.016831$ for GLM-5.3 and $.982992,.5,.014925$ for Qwen3.8 Max. The observed reversals were .738644 and .968067, respectively, against the target .970149. Qwen's persistent posterior MSE was small and all 12 actions matched the oracle; GLM's persistent MSE was .070300, excess expected decision loss was .161692, and 10/12 actions were oracle-optimal. Three GLM and one Qwen persistent reports differed from the exact posterior by more than $10^{-4}$. One GLM reply reported $p_A=.9851$ but chose B; the largest GLM error reported .0667 when the target was .98507. The two remaining GLM deviations were .0100 versus $1/67$ and .0275 versus $1/67$.

These are finite prompted outputs, not evidence that either system internally integrated a Beta posterior. The posterior-mean plug-in comparator has the same action directions as exact integration, and matching observed probabilities does not identify the computation that produced them [E6, E7, E11]. OSI48 remains separate from JES32 because their mechanisms and estimands differ.

## 6. Discussion

The results expose three distinct ways that access attribution can fail or succeed. First, in a random-target replay, exact independence makes the posterior 0.5 by construction; the informed R0 responses were consistent with that benchmark. Second, when source access genuinely changes what a Reader can answer, the small CSB30 manipulation showed that the Judge did not reliably convert the changed answer into the correct source attribution. Third, with a known response mechanism, most JES32 actions were optimal, but one model-condition still missed a strict, preregistered posterior-risk threshold. Correct actions and calibrated probabilities are not interchangeable outcomes.

Strategic simulation changes what historical dialogue can tell us. If the same latent Bernoulli rate governs historical and current answers, history can update the judge's prediction of current behavior. If a new rate is drawn independently for the current game, the old history does not identify that draw under the specified mechanism. Thus, an answer's evidential value depends on the joint temporal law, not only on its current-turn marginal. In OSI48, both models produced the exact null posterior and abstention in all refreshed cells. Their persistent reversals differed: Qwen's .9681 was close to the .9701 target with low posterior error, while GLM's .7386 was accompanied by a substantially larger posterior MSE and two nonoptimal actions. This supports a bounded behavioral finding for the selected history/seat packets. It leaves internal computation unidentified, and does not establish a stable ability across prompts or models [E11].

This perspective also sharpens the interpretation of “who knows.” An access label is recoverable only when access changes observable behavior in a way the competing strategy cannot reproduce, or when additional assumptions restrict the simulator. A model can correctly describe the source, correctly predict an answer, and still lack evidence about which causal path produced it. Conversely, a response that is not literally copied can remain diagnostic if its joint distribution depends on access. In controlled tasks, the strongest conclusions therefore come from protocols that specify the latent mechanism, the target assignment, and the judge's loss.

The practical implication is to report a ladder of claims. A valid source manipulation establishes that the intended speaker conditions were realized. A known posterior test establishes performance on a bounded mechanism. A random-target null checks whether the judge invents access information where none exists. None alone demonstrates a general opponent model or human-like mental-state representation. Stronger ToM claims require repeated families, independently sampled speakers and judges, unknown or mixed strategies, and interventions that distinguish actual source conditioning from behaviorally equivalent simulation.

## 7. Limitations

The controlled samples are small and mostly use a few authored materials or enumerated response packages. Family-level summaries are descriptive, not population estimates. Repeated questions and calls within a dossier do not provide independent material replication. The results do not support model rankings or general claims about LLMs.

The natural-language transcript audits and semantic labels are exploratory. They are useful for identifying possible failure modes, such as over-reading style or public-context fit as source provenance, but they do not establish causal mechanisms, annotation reliability, or the frequency of these behaviors in a broader population. We do not pool them with the fixed-mechanism or random-target experiments.

The source-simulation result depends on a shared response channel after conditioning on source content. The relevant total-variation distance between real and simulated source distributions has not been estimated for natural LLM dialogue. The random-target null likewise depends on correct independence throughout assignment, generation, routing, stopping, and selection. Neither result can be transferred to a genuine-access task without matching its assumptions.

Finally, JES32 uses programmatic speakers, and OSI48 supplies a known Beta–Bernoulli family while hiding the scalar rate realization. JES32 has no LLM Speaker. OSI48's 48/48 selected completion overlay combines two requested GLM output ceilings; the unchanged-budget record remains 46/48, and the added ceiling does not establish equal internal reasoning effort. The study uses fixed positive-probability packets, two calls per cell, one model family per row, and no sampled identity label. Neither study tests whether a model learns an unknown strategy family or naturally maintains a persistent dossier. These experiments do not establish generic theory-of-mind competence or an internal inference algorithm. This paper is a research draft, not a submission-ready claim of general capability.

## 8. Evidence map

| Evidence | Observed result | Supported interpretation | Boundary |
|---|---|---|---|
| Formalization [E0] | Transcript-law identifiability, source-simulation bound, and random-target null under explicit assumptions | Access attribution is a property of the complete response law and information structure | These are mathematical consequences of the stated model; no novelty or natural-LLM validation claim |
| R0 frozen replay [E2] | Delivery reports 42/42 Informed replies at p_A=.5 with abstention; original run had 77/84 valid overall | Null-consistent output on this fixed replay | Later valid completion replies are separate from the original analysis; not a general calibration result |
| CSB30 [E3] | Source-boundary checks passed 6/6 families; V1−V0 mean p_Reader=+.008333 | Intended access manipulation changed Reader answers; Judge attribution showed no consistent direction | Six authored materials, one Judge sample per cell; not a population effect |
| SQ28 [E4] | 28/28 valid calls; 7 correct, 9 wrong; source-silence admission 0/12 for B0 and 0/11 for B1 on scoreable source-unspecified answers | Bounded strategic archive/notice screen with mixed Judge outcomes | Four families; one unresolved B1 event; coding is exploratory and no known Bayes posterior |
| OMC16 [E5] | Forecast mean .0373 to .1292 after historical archive exposure | Prompt-conditioned forecast shift on selected frozen answers | No clear observed admissions; not opponent-model validation or population calibration |
| JES32 [E1] | 29/32 exact posteriors, 31/32 optimal actions; frozen weighted-Brier gate FAIL at .018896605 vs .01 | Mostly correct finite-mechanism reasoning, with a material calibration miss in GLM/MARGINAL | 32 analyzed slots from 33 physical attempts; programmatic speakers; no generalization to natural conversation |
| OSI48 initial attempt [E6–E8] | 48 frozen slots; first request HTTP 403/payment-category error; 47 unstarted | Preserved delivery failure before a model answer | Historical attempt only; no model behavior was observed in that batch |
| OSI48 recovery startup [E9] | Dated 18:28:53 snapshot: 2 dispatched, 1 strict-valid Qwen reply, worker live | Startup and interface evidence at that time | Historical snapshot only; later results are recorded in E10 and E11 |
| OSI48 original and recovery cutoff [E10] | Original batch: one HTTP 403; recovery: three receipts, two valid Qwen replies and one invalid GLM HTTP 200/ValueError; four physical attempts total | Preserves the initial delivery and parsing failures | Historical cutoff; later supplement and amended tail are summarized separately in E11 |
| OSI48 mixed-budget completion overlay [E11] | 48/48 strict-valid selected slots across 51 physical attempts; GLM persistent MSE .070300, Qwen .00000578; both refreshed cells MSE 0; persistent history deltas .738644 and .968067 | Finite history-conditioned posterior/action behavior under the supplied Beta–Bernoulli family | Two GLM tail slots use 16384-token ceiling; unchanged-budget view remains 46/48; no generic ToM or internal-algorithm claim |

## References and evidence sources

### Literature

1. Naghshvar, Mohammad, and Tara Javidi. 2013. “Active Sequential Hypothesis Testing.” *The Annals of Statistics* 41(6): 2703–2738. [arXiv:1203.4626](https://arxiv.org/abs/1203.4626).
2. Liu, Xiangyu, Di Wang, Zhe Feng, and Aranyak Mehta. 2026. “Scaling Inference-Time Computation via Opponent Simulation: Enabling Online Strategic Adaptation in Repeated Negotiation.” *Proceedings of the 43rd International Conference on Machine Learning*, PMLR 306: 78681–78704. [Proceedings page](https://proceedings.mlr.press/v306/liu26ef.html).

### Project evidence

- [E0] [Statistical ToM formalization, 7 October 2026](../../XiaBaiWang_Statistical_ToM_Formalization_20261007.md).
- [E1] [JES32 results, 9 October 2026](../../epistemic_boundary_mimicry/joint_epistemic_simulation/RESULTS_20261009.md).
- [E2] [R0 replay delivery, 8 October 2026](../../epistemic_boundary_mimicry/replay_r0/DELIVERY_20261008.md).
- [E3] [CSB30 results, 8 October 2026](../../epistemic_boundary_mimicry/counterfactual_source_boundary/RESULTS_20261008.md).
- [E4] [Strategic qualification results, 8 October 2026](../../epistemic_boundary_mimicry/strategic_qualification/analysis_20261008/RESULTS.md).
- [E5] [OMC16 results, 8 October 2026](../../epistemic_boundary_mimicry/opponent_model_replay/RESULTS_20261008.md).
- [E6] [OSI48 protocol, 9 October 2026](../../epistemic_boundary_mimicry/opponent_strategy_inference/PROTOCOL_20261009.md).
- [E7] [OSI48 theory v2, 9 October 2026](../../epistemic_boundary_mimicry/opponent_strategy_inference/THEORY_V2_20261009.md).
- [E8] [OSI48 attempted launch and cutoff, 9 October 2026](../../epistemic_boundary_mimicry/opponent_strategy_inference/RESULTS_20261009.md).
- [E9] [OSI48 credential recovery startup, 9 October 2026](../../epistemic_boundary_mimicry/opponent_strategy_inference/RECOVERY_EXECUTION_20261009.md).
- [E10] [OSI48 current results and cutoff, 9 October 2026](../../epistemic_boundary_mimicry/opponent_strategy_inference/CURRENT_RESULTS_20261009.md).
- [E11] [OSI48 completion overlay, 10 October 2026](../../epistemic_boundary_mimicry/opponent_strategy_inference/COMPLETION_RESULTS_20261010.md); [sanitized public evidence package](../../epistemic_boundary_mimicry/published_runs/go_opponent_strategy_inference48_completion_20261010/README.md).
