# autonomy-five-channel

**Autonomy as Determination by One's Own Normative Structure: A White-Box-First Five-Channel Audit Framework with Axioms and Conditional Theorems**

Wen Hu<sup>1,2</sup> and Gong Zhang<sup>1,2</sup> — <sup>1</sup>College of Electronic and Information Engineering, Nanjing University of Aeronautics and Astronautics, Nanjing, China; <sup>2</sup>Jiangsu Yunhefeng Intelligent Technology Co., Ltd., Nanjing, China — `huwen@nuaa.edu.cn`; `gzhang@nuaa.edu.cn`

**R23 public source synchronization, 2026-11-24.** Paper: [`latex/main.pdf`](latex/main.pdf) (**101 pages**, **6 figures**, **115 cited references**) · [Gitee mirror](https://gitee.com/jiangsu-yunhefeng-intelligent/autonomy-five-channel) · [Release and provenance notes](RELEASE_NOTES.md)

[![Historical Zenodo concept DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23608751.svg)](https://doi.org/10.5281/zenodo.23608751) — this DOI archives the historical `v1.0-r10` release. **The present editorial revision is frozen by immutable tag `v1.6-r23` with manifest `sim/runs/20261124_r23/validation.json`. R22's full two-environment numerical replay record (`sim/runs/20261123_r22/validation.json`) and all earlier tags through `v1.5-r22` are retained, including the recorded R18 failure. A version DOI requires actual Zenodo archiving of the current tag and is not yet minted; the historical concept DOI does not cover R23.**

---

## What R23 changes

R23 is the acceptance-stage **editorial finalization** of R22. It makes no change to theory, proofs, estimands, certificates, detection, estimators, simulation code, tests, numerical artifacts, negative controls, or R11--R22 historical evidence. The accepted A/B/C matched-method analysis and its noncausal interpretation are retained verbatim in substance.

- **Explicit external-validity boundary:** the abstract, introduction, and conclusion now position the work as a conditional conceptual and mathematical audit framework with executable model checks, not a deployment-ready tool or cross-substrate measurement standard. It claims no cross-substrate construct validity, universal interval coverage, statistical consistency, or external validation of real-LLM or human autonomy. Independent substrates, domain SESOI/power, external execution, and independent-investigator replication remain outstanding.
- **Article dehistoricized:** current rules and findings replace R17--R22 repair-sequence narration. The complete R11--R22 supersession history remains in `sim/CRITERION_VERSION_MAP.md`, `RELEASE_NOTES.md`, and read-only provenance/failure records.
- **Public technical supplement:** `sim/runs/20261124_r23/TECHNICAL_SUPPLEMENT.md` preserves the old estimator table, historical quantitative anchors, log-domain bookkeeping shares, older weight batteries, X5-c protocol details, registry arithmetic, log-field schema, and R18 numerical-failure explanation. Content is relocated, not deleted or upgraded.
- **Honest compression:** the paper decreases from 105 to **101 pages**, with 6 figures and 115 cited references unchanged. Font, geometry, bibliography size, and figure scaling were not used to reduce pages. Current native, detection, A/B/C, multi-seed, counterexample, and limitation content remains in the article.
- **Editorial-source validation:** R23 compares against the R22 public baseline and fails if numerical source/tests/artifacts or historical runs changed. Two clean environments run **429/429 tests** and stable statistical/joint replays; frozen grids receive read-only integrity/anchor checks. R22's completed full-grid two-environment validation is inherited, not misrepresented as a new R23 full-grid run. The paper is independently rebuilt with bibliography, text, font, metadata, and overfull gates.
- **Publication boundary:** tag `v1.6-r23`; no formal Release or version DOI is claimed. The two validation environments are same-platform thread/hash variants, not independent-investigator or cross-platform replication.

## What R22 changed (scientific content retained by R23)

R22 addresses the R21 review's remaining identifiability problem. R21 compared A (basic share-conditional) with C (percentile joint), which also differed in interval construction and bootstrap stream. R22 withdraws the interpretations "A misses / C covers -> conditional-design effect" and "both miss -> plug-in-bias effect". The detection rule, three-state sensitivity, estimator, formal R21 certificate, and historical evidence are unchanged.

- **Matched A/B/C on common replicates:** A = basic-share-conditional (the certificate construction); B = percentile-share-conditional composite (only the share varies, all other channels fixed at the original points); C = percentile-joint composite (all data-estimated channels recomputed, structural goal fixed). B/C is a matched-replicate, matched-percentile channel-propagation contrast; A/B is an interval-construction contrast; A/C remains mixed. All are artifact-level supplementary diagnostics, not certificate semantics or a formal bias decomposition.
- **Descriptive rather than causal attribution:** `undercoverage_attribution` is replaced by `descriptive_interval_method_contrast`, with complete 2x2 miss/miss, miss/cover, cover/miss, cover/cover counts for A/B, B/C, and A/C. A-miss/C-cover is a combined construction+conditioning difference; both-miss can reflect source-share bias, other-channel error, or construction and receives no single-cause attribution.
- **Full-grid findings (16 seeds per cell):** at n=2048, A/B/C coverage is RNI 4/5/16, NRI 16/0/0, order-average 8/8/15; at n=8192 it is RNI 0/2/14, NRI 16/0/0, order-average 1/1/13. At n=8192, B/C gives 12 B-miss/C-cover, 2 both-miss, 2 both-cover (RNI) and 12/3/1 (order-average). NRI has 16 A-cover/B-miss cells at each n, directly showing the construction contrast. The original certificate-A results are separately reproduced (RNI 4/16 -> 0/16; order-average 8/16 -> 2/16); matched order-average A at n=8192 is 1/16, not the original 2/16, because the streams differ.
- **Exact R21 reproduction and independent bias evaluation:** C reproduces R21's joint bounds/mean/SE exactly. Matched A does not replace the formal certificate's original A; the R22 baseline certificate is field-for-field identical to R21. Plug-in bias/RMSE are reported separately by exact-truth multi-seed simulation, never inferred from both-miss cells. NRI remains INDETERMINATE with a logical envelope; basic-A inclusion is not statistical recovery.
- **Hardened replay and test governance:** no empirical error threshold is a software pass condition. Audit hashes cover exact integer resampling indices and platform-independent common masks, not native floating-point outputs. Top-level/table and C-alias consistency is checked; joint/matched bootstrap counts must agree; synthetic non-full-mask tests independently verify B. **429/429 tests pass.** Paper: 105 pages, 6 figures, 115 references; the authors chose no R22 page cap.

## What R21 changed (historical; attribution superseded by R22)

R21 is a small revision addressing the R20 review, which confirmed that the four R20 fixes were substantive and that no new foundational theory/implementation problem remained. The two remaining items were statistical-naming precision and coverage-interpretation completeness. R21 closes them WITHOUT changing the detection rule, the three-state sensitivity system, the estimator, the predeclared grid, or the historical archive.

- **Share-conditional composite intervals disclosed (priority):** the above-detection-limit composite sampling interval propagates ONLY the source-share basic bootstrap interval; the execution/epistemic/reflection channels are fixed at their plug-in/structural points. It is therefore a SHARE-CONDITIONAL composite sampling interval, not a full joint-uncertainty interval. R21 renames its kind to SHARE_CONDITIONAL_SAMPLING_BASIC_BOOTSTRAP, adds a `conditioning_scope` field to every interval-mode composite interval, and a certificate-level `composite_interval_conditioning` policy declaring the design and its two under-coverage causes. The share's own interval keeps SAMPLING_BASIC_BOOTSTRAP (unconditional). The propagated bounds are numerically identical to R20 (only the kind/scope changed).
- **Coverage semantics separated (priority):** logical-envelope anchor containment (NRI 16/16) is a CONTAINMENT DIAGNOSTIC, not statistical coverage; share-conditional sampling coverage (RNI 0/16 at n=8192) is conditional on the other channels being fixed at points. The two are reported in separate columns and NEVER combined into one rate or compared as estimator quality ("NRI containment 16/16 > RNI coverage 0/16" is not "NRI estimated more reliably").
- **Joint trajectory bootstrap (supplementary diagnostic):** a trajectory-block bootstrap recomputes ALL operating-side channels from the same resampled batch (within-batch covariance preserved) and the execution channel from the independent stream (stratified by sequence), then the composite per convention; the percentile-95 interval is a genuine joint composite sampling interval. Per-trajectory sufficient statistics plus a small Blahut--Arimoto capacity value make it efficient and deterministic (cross-environment float diff 0). It is an ARTIFACT-LEVEL diagnostic, NOT the certificate's reported semantics, and does NOT remove plug-in bias.
- **Superseded R21 attribution:** R21 originally interpreted A-miss/C-cover cells as conditional-design attributable and both-miss cells as residual plug-in bias. R22 withdraws that identification because basic/percentile construction and bootstrap streams also differed. The numerical R21 artifacts remain read-only and byte-identical; only the causal interpretation is withdrawn. R22 supplies matched A/B/C descriptive contrasts instead.
- **Paper:** 105 pages (R20 was 103; the reviewer-required additions net ~+2 pages after honest compression of ~60 lines; the authors accepted 105 to preserve evidence detail, no formatting tricks). 115 references, 6 figures, 406/406 tests.

## What R20 changes

R20 is a small-to-medium revision addressing the R19 review, which confirmed that the R18 cross-environment replay problem was substantively repaired and that the core theory issues (execution channel, historical provenance, certificate profile) should no longer be rejection reasons. The remaining problems were the executability of the near-zero detection rule, the statistical meaning of interval sensitivity, and tests coupled to expected empirical outcomes. R20 closes them without rewriting the theory or historical evidence.

- **Data-driven near-zero detection inside the formal certificate (priority):** the R19 below-limit annotation was triggered by the exact share (known only in the white-box fixture) and lived outside the certificate; on this instance the sampled share and its percentile interval both lie ABOVE the limit, so no data-driven rule reproduces the oracle classification. R20 declares one executable rule BEFORE the study outcomes: plug-in share + bootstrap percentile interval -> basic bias-corrected interval [2p-q97.5, 2p-q2.5] clipped to [0,1] -> three-state classification against the inherited post hoc frozen limit (upper<limit: DATA_BELOW_LIMIT; lower>limit: DATA_ABOVE_LIMIT; otherwise INDETERMINATE_NEAR_ZERO). Every L1/L2 convention in the certificate carries convention_status, share_interval, composite_interval (with kinds), detection limit + rule/value provenance, and diagnostic plug-in outputs. The truth-triggered rule is explicitly labeled ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE. The sampled baseline certificate is INTERVAL-valued (no point export); its overall range is the hull of the reported convention intervals. The honest data verdict for the near-zero NRI convention at n=8192 is INDETERMINATE, reported as a conservative logical envelope [0, 0.1324]; the plug-in 0.1478 is a labeled diagnostic, not the reported semantics.
- **Three-state interval sensitivity (priority):** confirmed sensitive (minimum possible convention separation exceeds the threshold) / no confirmed sensitivity (worst-case spread within threshold) / indeterminate (overlapping intervals) / not evaluable (zero total flow or unknown inputs). Identical wide intervals are NEVER read as agreement; the midpoint spread is retained only as a descriptive statistic; flags fire only on confirmed separation, and absence of a flag means "no confirmed sensitivity detected", not agreement.
- **Real interval propagation with declared kinds (priority):** sampling certificates propagate the actual bias-corrected bootstrap share intervals, not degenerate [s,s] points. Every interval carries a kind (POINT_EXACT / LOGICAL_ENVELOPE / SAMPLING_* / SENSITIVITY / MODEL_SELECTION); logical envelopes are explicitly NOT confidence intervals; monotone endpoint propagation is an envelope guarantee for the given inputs, not automatically a full statistical uncertainty interval.
- **Test decoupling (priority):** software correctness tests check formulas, structures, boundaries, analytic anchors, numerical stability, and governance only. The R19 empirical expectations (NRI error must exceed 0.05, bias correction must improve RMSE, intervals must not cover the truth) were removed from validators/tests and replaced by explicitly labeled snapshot regressions on the frozen artifacts (which remain byte-identical and replayable). A future improved estimator must not fail validation for recovering the endpoint better.
- **Predeclared detection-rule study:** 16 independent seeds x {2048, 8192} x 200 bootstrap resamples, frozen in source before outcomes. Findings (descriptive): NRI is INDETERMINATE in 16/16 seeds at both sample sizes, with zero false-below/false-above classifications and 16/16 conservative-envelope coverage; ABOVE-limit conventions are correctly classified but their sampling intervals under-cover the exact composites because plug-in bias dominates. Indeterminate is an honest outcome, not a failure; this is reporting governance, not a consistency guarantee or power claim.

## What R19 changes

R19 is a medium revision addressing the R18 review (no new foundational math error found): cross-environment replay repair (canonicalized capacity input, immutable-input evidence binding, per-field tolerances; failure record retained), layer-aware degradation-complete certificates, corrected state_autonomy_RNI, sampled convention disclosure + 8-seed study, decomposed sensitivity, post hoc frozen threshold provenance, sampled negative controls. (R19's oracle-triggered detection and midpoint sensitivity semantics are superseded by R20; its artifacts are retained read-only and byte-identical.)

## What R18 changes

R18 is a focused local revision addressing the R17 review, which confirmed that the R16 core defects were already repaired in R17. It does not rewrite the theory or historical evidence. (R18's point-valued L2 certificate is retained as a compatibility layer; its joint-audit cross-environment replay failure is recorded and superseded by R19.)

- **Full-profile certificates:** the R18 schema (`r18_guards.py`) makes the profile-first principle machine-checked. Mandatory fields carry the complete layer-applicable channel vector (value/state/interval/protocol version), the goal structural point and IRL interval, the execution open-loop horizon, the reflection three factors with logged event counts, the registered RNI/NRI/order-average shares with every flow term and alternative semantic partition, the aggregation weights, and the recomputed composite under each convention with its range. When the composite spread across order conventions or semantic partitions exceeds the preregistered internal threshold (0.05, an engineering threshold, not a domain SESOI), the certificate must carry `ORDER_SENSITIVE`/`MODEL_SENSITIVE`, a scalar-export warning, and a sensitivity-qualified grade. A near-one RNI share with a near-zero NRI share cannot be exported as a single unflagged positive scalar.
- **Joint-log end-to-end native audit:** the R17-native compositional fixture is superseded (read-only, not rewritten) by `native_joint_audit.py`, which estimates every operating-side estimand from one joint trajectory-log batch of a single registered \(T=3\) SCM under one log schema. Execution is audited on a separate precommitted open-loop intervention stream from the same environment law, as the estimand requires. The paper now reports the convention composites directly: RNI \(0.4608565\), NRI \(0.0003908\), order-average \(0.4011989\), alternative partition \(\approx0.4608565\); composite range \([0.0003908,0.4608565]\). Internal concept validation only.
- **Open-loop output conventions:** the zero-MI quantifier is support-relative for a fixed precommitted distribution (a point-mass distribution is always zero); capacity mode quantifies over sequences assignable positive probability by some admissible distribution. The terminal-observation estimand (normalized \(0.2655022\) for a two-step BSC at error \(0.1\)) is kept separate from the whole-observation-sequence Kronecker object (\(0.5310044\)).
- **Weight sensitivity terminology:** exact log-domain simplex bounds and halfspaces are an exact sensitivity characterization, not robustness evidence; 17 of 22 unique finite historical contrasts are weight-dependent. The closed simplex (zero vertices) is a sensitivity relaxation; the representation theorem and certificate weights use strictly positive interior weights.
- **External protocol precision:** equivalence is decided by TOST (two one-sided \(\alpha=0.05\) tests, equivalently a 90% two-sided interval inside the frozen margins); non-inferiority directions are explicit (\(\delta_{BA}=BA_{full}-BA_{reduced}\) upper bound \(<\Delta_{BA,NI}\); \(\delta_{Brier}=Brier_{full}-Brier_{reduced}\) lower bound \(>-\Delta_{Brier,NI}\)). Engineering margins are frozen; a domain-justified SESOI, power analysis, and external execution remain pending.

## What R17 changes

R17 is a major revision addressing the R16 review without rewriting historical evidence.

- **Open-loop execution repair:** multi-step \(A_{\mathrm{exec}}\) now optimizes precommitted open-loop action-sequence distributions under intervention kernels. A feedback-copy counterexample shows ordinary reactive MI can score 0.5 while open-loop capacity is zero. EXEC-1/ENV-0 are explicitly \(n=1\) open-loop special cases.
- **Co-primary current/history outputs:** certificates carry `current_structural_profile` and `historical_formation_profile`. A fixed-point goal implant can leave \(A_{\mathrm{goal}}=1\) and current channels unchanged while historical formation records surgery. Lambda time origins distinguish audit-time removal from original-implant prevention.
- **R17-native end-to-end benchmark:** one registered \(T=3\) reactive SCM with action-dependent environment, N/R/I roles, resource/defense split, structural goal point and IRL interval, reflection events, and explicit XOR endorsement SCM. Execution is audited separately by \(n=2\) open-loop interventions. Reports exact truth, seeded sampling errors, bootstrap/Wilson intervals, alternative semantic partition, surgery/decoupling negative controls, and R17 certificates. Internal concept validation only.
- **Weight-simplex bookkeeping bounds:** exact log-domain bounds and pairwise damage halfspaces replace a few alternative weights as the primary robustness check. Among 22 unique finite historical contrasts, 17 are weight-dependent. Log-damage shares are bookkeeping under the selected geometric aggregator, not causal attribution or ratio-scale effects.
- **Claim contraction:** T2 is single-channel insufficiency, not exactly-five minimality; T3/T8 are design propositions and T5 zero-factor bookkeeping. C1 uses a local OU premise, C2 states the [0,1] truncation convention, and T1d's Le Cam bound does not depend on finite verification capacity.
- **External equivalence design:** the unexecuted protocol now freezes equivalence/non-inferiority margins, an independent downstream Brier outcome, nested instance-level validation, and independent-investigator reimplementation requirements. Non-significance is not equivalence.

The R16 ordered-attribution, certificate, interval, non-finite, and replay repairs remain in force; see the historical R16 section in `RELEASE_NOTES.md`.

## Historical R16 changes

R16 closed the R15 re-review without rewriting historical evidence.

- **Ordered source attribution:** the L1+ \(R\to N\to I\) decomposition is explicitly an **ordered residual-attribution axiom**, not a unique causal decomposition. Reports require reverse NRI and an I-last two-order Shapley-style sensitivity descriptor when \(R,N\) are nondegenerate. The \(N/R/I\) semantic partition is registered before scoring; alternative partitions are sensitivity arms. PID remains a comparator, not a silent replacement estimand. Pure-random zero claims are RNI-specific: with \(N=R\) and \(A=R\), the RNI normative share is 0 but NRI is 1.
- **Executable order and closed-loop guards:** the one-step OR law gives normative shares `0.6163114534` (RNI), `0.3836885466` (NRI), and `0.5` (order average). Exact \(T=2\) enumeration covers pure-random, pure-normative, and mixed feedback policies, joint-DI chain identities, mediated external influence, and direct bypass. The mixed XOR model changes its ordered normative share from 1 to 0; the I-last average is 0.5.
- **Route B scaling:** homogeneity now explicitly gives \(\varphi(z+st')=\varphi(z)+t'\) before \(q=st'\) yields \(\varphi(z+q)=\varphi(z)+q/s\). The regression derives this from the actual homogeneous function rather than restating the incorrect unscaled intermediate equation.
- **T2 interval and finite-value discipline:** identified-goal intervals use endpoint order, \(l_1\ge l_0\) **and** \(u_1\ge u_0\). Stronger cross-world guarantees require \(\ell_1\ge u_0\) or a registered coupling. NaN and either infinity fail closed, including NaN→NaN.
- **Certificate schema and evidence axes:** `registration_completeness` is distinct from `mechanism_evidence`. Complete registration without an SCM audit is `REGISTERED_COMPLETE`, not `SCM_AUDITED`. R16 certificates require schema/origin/goal/readiness modes and L1/L2 model/evidence hashes; legacy Bundle values and forged metadata are rejected. Hashes bind declared artifacts, not external truth.
- **Numerical replay:** statuses, seeds, counts, hashes, JSON types, and object structure remain exact. Only floating-point leaves use relative/absolute \(10^{-12}\) tolerances, with the maximum difference reported; non-finite or out-of-tolerance values still fail.
- **Common external protocol:** `sim/EXTERNAL_VALIDATION_PROTOCOL.md` design-freezes, but does not execute, comparisons on Ingel's RL environments and Albantakis's automata. It includes RNI/NRI/Shapley, next-state PID (BROJA primary, SxPID sensitivity), Albantakis's candidates, empowerment, reduced models, and intervention-attribution balanced accuracy. External SESOI, power, outcome registration, and results remain pending.
- **Standalone manuscript:** abstract and main text remove revision-history narration while preserving legacy evidence boundaries. Discussion distinguishes UNKNOWN from N/A, and T8 separates present \(A^{\mathrm{state}}\) from resilience \(A^{\mathrm{res}}\). The paper remains 104 pages after compression.

The R15 execution-horizon, compatibility, goal-identification, state/readiness, C2, and statistical repairs remain in force; see the historical R15 section in `RELEASE_NOTES.md`.

## Evidence status, not a headline tally

| Evidence package | Current interpretation |
|---|---|
| R23 editorial-source validation | Two clean environments; numerical source/artifact changes since R22 = 0; 429 tests and stable replays; frozen-grid read-only integrity; 101-page clean build. R22 full-grid validation inherited, not rerun or upgraded; not external validation |
| Mathematical and implementation guards | **429/429 tests pass**, including R22 matched A/B/C construction and propagation contrasts, exact R21-C reproduction, platform-independent resampling/mask audits, and all R21/R20/R19/R18/R17/R16 controls; software correctness is decoupled from empirical outcomes (snapshot regressions only); not external validation |
| R22 native joint-log audit | One SCM, one log schema, one joint operating batch; formal R21 certificate field-for-field unchanged; matched A/B/C on common replicates with C exactly reproducing R21; descriptive rather than causal coverage-pattern interpretation; immutable-input evidence binding, sampled surgery/decoupled controls; exact composites \(0.4608565/0.0003908/0.4011989\) are model anchors; NRI remains INDETERMINATE |
| R22 detection-rule study | Full predeclared 16-seed x {2048,8192} matched grid; original formal-A and C reproduce R21 cell by cell; A/B/C coverage, widths, independent exact-truth bias/RMSE, and complete pairwise 2x2 `descriptive_interval_method_contrast` counts; no formal bias decomposition, power claim, or universal coverage |
| R21 native joint-log audit | Read-only, superseded by R22 (matched A/B/C added; A/C causal attribution withdrawn); artifact byte-identical and replayable |
| R21 detection-rule study | Read-only frozen study; original formal-A and C reproduced by R22; its single-cause interpretation of coverage patterns is superseded by R22's descriptive matched method contrasts |
| R20 native joint-log audit | Read-only, superseded by R21 (share-conditional intervals now honestly named with conditioning_scope; coverage semantics separated; joint bootstrap added); artifact byte-identical, replay still passes |
| R20 detection-rule study | Read-only frozen descriptive study; share-conditional coverage reproduced by R21; its single "coverage" heading superseded by R21's separated containment/coverage columns |
| R19 native joint-log audit | Read-only, superseded by R20 (oracle-triggered detection outside the certificate replaced by the data-driven in-certificate rule); artifact byte-identical, replay still passes |
| R19 multi-seed sampling study | Read-only frozen descriptive study (8 seeds): plug-in bias amplified by \(x^{0.2}\) prevents recovery of the near-zero NRI endpoint (percentile under-coverage NRI 0/8, RNI 1/8); bias correction halves NRI RMSE but does not restore the endpoint |
| R18 native joint-log audit | Read-only, superseded by R19/R20; cross-environment replay failure recorded in `runs/20261122_r19/REPLAY_FAILURE_R18.md` and repaired by R19 (canonicalization + separated evidence binding + per-field tolerances) |
| R17-native benchmark | Read-only, superseded by the R18/R19 joint-log audits; same-instance \(T=3\) compositional fixture with exact truth, sampling errors/intervals, semantic sensitivity, negative controls |
| R17 weight regions | Exact closed-simplex log bounds and halfspaces (a sensitivity characterization); 22 unique finite contrasts, 17 weight-dependent; zero/log-undefined cases separated |
| R16 source-attribution audit | OR, duplicate-register order control, three exact \(T=2\) policies, mediation and direct-bypass witnesses; independent closed-form and atom-wise log-ratio checks |
| Historical 4,620-run ENV-0 archive | Read-only legacy implementation and same-model checks. Its `a_org` is internal-causal and combined `a_via` is a resilience marker; neither is silently re-signed as a current value |
| R14 pooled/stratified X5-c | Current-source read-only replays pass; \(D_{noise}=0.089799622>0.01\), so point readings remain **MODEL_SENSITIVE** |
| R15 X5-c paired cross-check | Shared \((X,Z,J)\) uses paired-difference SE; `POST_HOC_PASS`, not preregistered CONFIRMED. Replay comparison tolerates only floating-point round-off |
| R15 weight/statistical audit | Read-only Kendall \(\tau_b\) with ties and scenario strata; overall range \([0.927595,1]\), but no uniform \(0.93\) scenario-level floor |
| C0-CF-v2 | Same-environment model construction; custom L1 weights and equal-weight sensitivity are both reported |
| T7 / DEL-1 | **INCONCLUSIVE** pending a selector-conditional estimator and nondegenerate bracket |
| External protocol | **DESIGN_FROZEN_UNEXECUTED**; engineering equivalence/non-inferiority margins and TOST rule frozen; no domain SESOI/power, independent-substrate result, expert validation, or Lean certification is claimed |

Failed criteria, post hoc replacements, unrun programs, legacy markers, unavailable historical SPEC bytes, and the invalid first C0 fixture remain visible. Historical verdicts are not rewritten. The 480,000 X5-c evaluations use 120,000 base \((X,U)\) draws with common random numbers across arms within each noise/time cell.

## Repository layout

```text
latex/                     complete paper source, 115-entry bibliography,
                           Unicode map, submission manifest, 5 external PDF
                           figures + 1 TikZ figure, built 101-page PDF
sim/
  src/autonomy_sim/        ENV-0, estimators, SCMs, open-loop/source/certificate guards
                           (r22_interval_contrast matched A/B/C; r21_guards,
                           r21_joint_bootstrap, r21_joint_audit; r20 detection/schema;
                           r19/r18 compatibility layers, canonical capacity input)
  tests/                   429 unit/integration/regression tests (correctness decoupled
                           from empirical expectations; frozen-artifact snapshots labeled)
  analysis_r22_joint_audit.* R22 joint-log audit with matched A/B/C (current)
  analysis_r22_detection_study.* R22 full matched-grid method-contrast study (current)
  analysis_r21_joint_audit.* R21 joint-log audit (read-only, superseded)
  analysis_r21_detection_study.* R21 separated-coverage study (read-only, superseded)
  analysis_r20_joint_audit.* R20 joint-log audit (read-only, superseded)
  analysis_r20_detection_study.* R20 detection study (read-only, superseded)
  analysis_r19_joint_audit.* R19 joint-log audit (read-only, superseded)
  analysis_r19_sampling_study.* R19 frozen 8-seed bias/coverage/width study (read-only)
  analysis_r18_native_joint_audit.* R18 joint-log audit (read-only, superseded)
  analysis_r17_native_benchmark.* R17-native benchmark (read-only, superseded)
  analysis_r17_weight_regions.* exact weight-simplex sensitivity bounds
  analysis_r16_source_attribution.* exact OR and T=2 attribution audit
  analysis_r15_statistics.* Kendall tau-b, ties and scenario reporting audit
  analysis_r15_x5c_paired.* paired cross-check SEs and tolerant replay
  EXTERNAL_VALIDATION_PROTOCOL.md design-frozen, unexecuted external protocol
  SPEC_*.md                current specifications and R14 preservation copy
  CRITERION_VERSION_MAP.md R11–R23 supersession and evidence boundaries
  runs/20261017_full/      read-only historical 4,620-run campaign archive
  runs/20261102_r11/del1/  separate 30-run R11 replay summary
  runs/20261116_r14/       X5-c, C0-CF-v2, superseded/failed records
  runs/20261117_r15/       preserved R15 validation
  runs/20261117_r16/       preserved R16 validation
  runs/20261119_r17/       preserved R17 validation
  runs/20261121_r18/       preserved R18 validation
  runs/20261122_r19/       preserved R19 validation + retained R18 replay-failure record
  runs/20261122_r20/       preserved R20 validation (tag v1.3-r20)
  runs/20261122_r21/       preserved R21 validation (tag v1.4-r21)
  runs/20261123_r22/       preserved R22 full numerical validation (tag v1.5-r22)
  runs/20261124_r23/       current editorial provenance, technical supplement,
                           and validation (tag v1.6-r23)
refs/manifest.md           graded bibliography verification ledger;
                           third-party PDFs are not redistributed
tools/                     source-package and frozen-validation scripts
```

## Requirements

- Python ≥ 3.10 with `numpy` and `matplotlib` (developed on Python 3.12; see `sim/requirements.txt`)
- A TeX distribution with `pdflatex` and `bibtex`

## Reproduction

```bash
# 1. Run all 429 tests
cd sim
python3 -m unittest discover -s tests -q

# 2. Read-only R14 evidence replays
python3 run_x5c_r14.py --out runs/20261116_r14/x5c --check
python3 run_x5c_r14_stratified.py --out runs/20261116_r14/x5c_stratified --check
python3 run_c0cf_r14.py --out runs/20261116_r14/c0cf_v2 --check

# 3. Read-only R15/R16/R17 reporting and analytic audits
python3 analysis_r15_statistics.py --check
python3 analysis_r15_x5c_paired.py --check
python3 analysis_r16_source_attribution.py --check
python3 analysis_r17_native_benchmark.py --check
python3 analysis_r17_weight_regions.py --check

# 4. R22 current matched A/B/C audit and full matched-grid study
#    (the study --check recomputes the full matched grid; slow)
python3 analysis_r22_joint_audit.py --check
python3 analysis_r22_detection_study.py --check

# 5. R21 frozen artifacts (byte-identical; superseded by R22)
python3 analysis_r21_joint_audit.py --check
python3 analysis_r21_detection_study.py --check

# 6. R20 frozen artifacts (byte-identical; superseded by R21)
python3 analysis_r20_joint_audit.py --check
python3 analysis_r20_detection_study.py --check

# 7. R19 frozen artifacts (byte-identical after validator decoupling; superseded)
python3 analysis_r19_joint_audit.py --check
python3 analysis_r19_sampling_study.py --check

# 8. R18 joint-log audit (original-environment numerical replay; superseded)
python3 analysis_r18_native_joint_audit.py --check

# 9. Rebuild the complete paper
cd ../latex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

For R23 editorial validation, create a clean worktree at the R23 content commit in `RELEASE_NOTES.md` and run `tools/make_r23_validation.py`. It verifies zero numerical changes since R22, runs the suite and stable replays in TWO same-platform thread/hash environments, validates frozen grids read-only, and independently rebuilds the 101-page paper. It writes only `sim/runs/20261124_r23/validation.json`; it does not rerun the full grids. For the authoritative full numerical-grid recomputation, use the R22 content commit and `tools/make_r22_validation.py`, which writes the preserved `sim/runs/20261123_r22/validation.json`. Neither procedure modifies historical evidence or supplies independent-investigator replication.

The R14 replays and R15/R16/R17/R19/R20/R21/R22 checks use **current** source and compare against saved outputs or independent analytic anchors; they are not represented as execution of earlier source bytes or recovery of unavailable historical SPEC snapshots. See the R14–R23 `PROVENANCE.md` files, `runs/20261122_r19/REPLAY_FAILURE_R18.md`, and `sim/CRITERION_VERSION_MAP.md`.

The complete LaTeX tree is required; uploading only `main.tex` is not a valid source submission. See [`latex/SUBMISSION_MANIFEST.md`](latex/SUBMISSION_MANIFEST.md).

## Public-snapshot boundary

This repository is a fresh-history public snapshot of the authors' development work. It intentionally excludes third-party bibliographic PDFs and internal review archives. Development-source and public-content commit relationships are recorded in [`RELEASE_NOTES.md`](RELEASE_NOTES.md). Existing tags and the Zenodo concept DOI remain historical and are not rewritten.

## Licenses

- **Code** (`sim/`, `tools/`): MIT — [LICENSE](LICENSE)
- **Paper text, figures, data, and documentation**: CC BY 4.0 — [CONTENT-LICENSE.md](CONTENT-LICENSE.md)

## Citation

```bibtex
@misc{hu_zhang2026autonomy_r23,
  title  = {Autonomy as Determination by One's Own Normative Structure:
            A White-Box-First Five-Channel Audit Framework with Axioms
            and Conditional Theorems},
  author = {Hu, Wen and Zhang, Gong},
  year   = {2026},
  note   = {Author manuscript; R23 editorial finalization,
            24 November 2026, 101 pages; immutable tag v1.6-r23;
            no R23 version DOI yet},
  url    = {https://github.com/hurrywhen/autonomy-five-channel}
}
```

Machine-readable metadata: [`CITATION.cff`](CITATION.cff). For the historical software/data archive only, see Zenodo concept DOI [10.5281/zenodo.23608751](https://doi.org/10.5281/zenodo.23608751).
