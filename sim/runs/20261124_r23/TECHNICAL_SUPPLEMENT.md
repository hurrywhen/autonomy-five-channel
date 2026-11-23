# R23 public technical supplement: editorial relocations

**Date:** 2026-11-24
**Status:** Technical supplement, not a new experiment or a new evidence grade.

R23 is an editorial-only revision of the accepted R22 scientific content. It
moves row-wise historical numerical tables, old estimator-validation details,
and software replay narrative out of the article. No theorem, estimand,
detection rule, certificate schema, A/B/C interval construction, simulation
input, numerical result, negative control, or historical artifact is changed.
The complete R11--R22 revision and supersession history remains in
`sim/CRITERION_VERSION_MAP.md`, `RELEASE_NOTES.md`, and the read-only R11--R22
provenance records; it is not reproduced as article-length narrative.

This supplement does not establish external construct validity, universal
interval coverage, statistical consistency, deployment readiness, or
cross-substrate measurement standards. Real-LLM/human validation, independent
substrates, domain SESOI/power, and independent-investigator replication remain
outstanding.

## 1. Estimator two-path validation table removed from the article

Each quantity has a truth path (tensor enumeration) and a finite-sample log
estimation path. The historical five fixed synthetic configurations give:

| Quantity | Configuration | Estimate vs truth | Absolute error |
|---|---|---:|---:|
| `A_org^R14` probe flow (legacy internal-causal) | toy + policy-script uniform probe arm | 0.6496 ± 0.0486 vs 0.6592 | 0.0096 |
| `A_via^R14` (Z-log read; combined gate) | ENV-0 baseline | 0.5248 ± 0.0107 vs 0.5344 | 0.0095 |
| Goal input `U_eff` (white-box read) | ENV-0 baseline | 1.0000 ± 0.0000 vs 1.0000 | < 1e-6 |
| Epistemic input mean accuracy against logged truth | ENV-0 observation-noise 0.5 arm, paired seeds | 0.6573 ± 0.0087 vs 0.6587 | 0.0014 |
| Passive execution `I(A_t;O_{t+1})` | ENV-0 sharp-temperature arm | 0.0103 ± 0.0029 vs 0.0104 | 0.00009 |

Each row is one fixed out-of-matrix run (seeds 910097--910099) with
2,000--8,000 sampled trajectories. The ± values are trajectory-block standard
errors with Miller--Madow bias registered, not cross-seed confidence intervals.
The maximum 0.0096 is therefore a sampling-error statement for these
configurations, not a seed-distribution bound, statistical-consistency claim,
or independent-instrument validation.

BB-1 exercises the black-box rules end to end: zero violations of the certified
upper end in 3/3 bypass-semantics arms. The reference lower end happens to
contain truth there, with widths 0.01/0.005/0.003 across probe probabilities,
but this is not an interval-containment theorem. The lower end is uncertified
and mediation is outside the certificate. Passive ENV-0 execution direction and
the independent open-loop direction are instance contrasts; only the latter is
a general conditional rule.

MaxEnt-IRL black-box recovery of `U_eff` and deployable event-level Lambda
instrumentation outside the registered fixture SCMs remain unimplemented. The
current native joint-log audit implements fixture-level endorsement-event and
surgery-context carriers from one batch; this does not close the deployment
gap.

## 2. Cross-environment numerical protocol and retained failure

The retained R18 replay failure arose because the parity kernel's
capacity-achieving input set is a two-dimensional face. Non-unique auxiliary
optimizer coordinates drifted by approximately 7.5e-10 across platforms and
were incorrectly included in a byte-level evidence hash. The original failure
record remains unchanged at
`sim/runs/20261122_r19/REPLAY_FAILURE_R18.md`.

The repaired governance rule binds evidence hashes to immutable raw inputs
only. It canonicalizes capacity input under a declared rule: exact uniform when
capacity-achieving or near-zero; otherwise the unique maximum-entropy optimum
by deterministic iterative scaling, verified fail-closed. Auxiliary coordinates
use per-field replay tolerances, while hashes, counts, and statuses remain
byte-exact. R22 additionally audits exact integer resampling indices and
platform-independent common finite masks rather than hashing native
floating-point analysis outputs.

R22's two-environment frozen validation is retained in
`sim/runs/20261123_r22/validation.json`. The environments are same-platform
thread/hash variants, not cross-platform or independent-investigator
replication. R23 performs editorial-source validation without rewriting that
numerical record.

## 3. Historical quantitative-anchor table removed from the article

“Deterministic” denotes exact computation with no statistical content;
“seeded” denotes random units under the stated interval convention.
Deterministic 30/30 replays receive no binomial bound.

| Anchor | Value | Reference point | Class |
|---|---|---|---|
| Mediation witness `I(I;A)=1-H_b(0.1)` | 0.531 bit | External flow 0 under the same law (direction reversal) | deterministic |
| Gaussian CUSUM halving ratio, fixed alpha | 1.951 ± 0.034; Student-t29: 1.951 ± 0.035 | ENV-0 observation; normal and Student-t 95% sensitivity intervals, not a test of the fixed-delta asymptotic | seeded (30 seeds) |
| C1 recovery scaling slope | -0.504 ± 0.000, R²=1.0000 | theory -0.5 | deterministic |
| EXEC-1 dynamic-range restoration | 0.234/0.017 = 13.7× | exact chain 0.234 > 0.218 > 0 | deterministic |
| T7 legacy unconditioned-fit deviation | 2.0e-5 | ENV-0 fit, not selector-conditional exact-law verification | deterministic |
| X5-a endorsement-quantization continuum limit | `A_goal^infinity(eta)=1-2eta/(1+eta)` | stationary gap `eta(1-eta)^2/(2(1+eta))`, maximum 0.0567 ≤ 0.057 | deterministic |
| X5-b kappa-layer attenuation | `1/|kappa|` | 0.500 → 0.250 as `|kappa|: 2 → 4` (deep-capture floor) | deterministic |
| Exact-simulator capture / design-rule boundedness | 30/30 both directions | ATK-6 implementation of the registered certificate-failure band | deterministic replay (30 repeats) |

The Gaussian CUSUM arm uses 30 seeds × 200 post-change paths at drift
0.25/0.125. Its within-seed scaled-EDD ratio is 1.951 ± 0.034 (normal) and
± 0.035 (Student-t29), recorded in `sim/analysis_cusum_sensitivity.json`.
These are not intervals over individual paths or power claims.

## 4. Historical log-domain bookkeeping shares removed from the article

Under selected weights and the geometric aggregator,
`ln(A0/A) = sum_j w_j ln(x_j^0/x_j)`. The shares below are bookkeeping under
that aggregator, not canonical causal attribution or ratio-scale effects.
Negative entries can occur when components improve; zero-annihilation arms
produce infinite log-damage and are counted separately.

| Campaign | A_org | A_goal | A_exec | A_epi | A_ref | Zero arms |
|---|---:|---:|---:|---:|---:|---:|
| ATK-1 (goal planting) | 0.000 | **0.590** | -0.003 | -0.000 | 0.414 | 180 |
| ATK-2 (observation poisoning) | 0.000 | 0.000 | **0.756** | 0.068 | 0.175 | 360 |
| ATK-4 (policy-script injection) | **0.800** | 0.000 | -0.008 | -0.001 | 0.209 | 0 |
| ATK-5 (urgency) | 0 | 0 | 0 | 0 | **1.000** | 0 |
| EXEC-1 (action contraction) | 0.000 | -0.000 | **0.910** | 0.090 | 0.000 | 30 |

The epistemic magnitude share is small in ATK-2 (0.068, rounded to 0.07 in the
former article), while its necessity is attributional rather than volumetric.
The freeze ablation remains the substantive necessity check: freezing any one
channel breaks unique attack-class identification in at least one campaign.

## 5. Older weight-sensitivity batteries

The exact log-domain simplex bounds and halfspaces in
`sim/analysis_r17_weight_regions.json` remain primary. The older five-vector
battery is descriptive: zero range violations, zero annihilation in 120/120
complete-capture arms, and no T3a monotonicity violation in checked cells.
The read-only Kendall tau-b audit reports exact ties and scenario strata;
across 5,760 main arms its overall range is [0.9276,1], with scenario minima
including 0.8667. These nested deterministic recomputations are not independent
samples or power, and a generic tau ≥ 0.93 statement is not a uniform
scenario-level claim.

The T4 attack point moves by construction because
`argmax_i w_i s_i/c_i` depends on `w`: equal weights make the epistemic channel
optimal in 480/480 cells; an origination-heavy vector splits the optimum
240/480. This is a comparative static, not a defect.

Default ENV-0 has passive execution approximately 0.010, producing an effective
four-channel-plus-suppression composite. The rich-coupling EXEC-1 battery
(`sim/analysis_exec1_weights.json`) preserves the verdict chain
0.647 > 0.637 > 0 under all five weight vectors (rich-arm levels 0.570--0.742;
zero-empowerment arm exactly zero) and under elasticity values
0.25/0.5/0.75/1. The elasticity-2 stress arm shows the expected annihilation
failure (A=0.545). The direct chain check is primary.

## 6. X5-c protocol details condensed in the article

The canonical stratified supplement registers T=3 and 20,000 base `(X,U)`
draws per noise-by-time cell, four arms sharing those draws: 480,000
cell/context evaluations from 120,000 base draws, plus 8,000 cross-check
contexts. The three time cells are independent cross-sectional audit-time
strata, not a longitudinal trajectory; this protocol clarification is post hoc
and thresholds are unchanged. Gaussian and logistic arms implement abduction
`U=Z-aX-bJ`, action `J=0`, and prediction with shared `V`. No-surgery and
history-without-output-effect both give Lambda=1, while surgery history is 1 in
the latter. Pooled C1--C5 and stratified C1/C2/C5/C6 criteria pass.

The paired audit is POST_HOC_PASS, not unqualified CONFIRMED. The saved
unpaired `combined_se` bytes remain unchanged but are superseded for current
reporting. The strong/weak ordering is a CDF identity, not noise-robustness
evidence. Identity and XOR SCMs share fair factual endorsement and fixed
passive actions but give Lambda=1 versus 0. These checks do not upgrade ENV-0
marker-based ATK-1, policy-script, T2/T3, or C0 values.

## 7. Historical registry arithmetic condensed in the article

The 4,620 execution records comprise 2,880 main-matrix runs, 1,440 stress-arm
runs, and ten independent 30-run supplements. Arm-bundle pool (i) contains
8,640 ATK-1/2/4 strength records (5,760 main plus 2,880 stress). The recursive
six-component registry contains 7,290 main/EXEC-1 bundles and 11,250
full-campaign bundles; the 1,530 main difference is 1,440 non-row records plus
90 EXEC-1 chain arms. Defense-direction checks cover 840 matched ATK-1/2
comparisons. Main run-level verdicts are 2,520 CONFIRMED and 360 INCONCLUSIVE.
These are nested/deterministic evaluation counts, not independent observations
or an aggregate confirmed-theory tally.

The separate DEL-1 replay has 30 runs and six criteria each: 120 CONFIRMED and
60 INCONCLUSIVE criterion evaluations, with all 30 run-level totals
INCONCLUSIVE because corrected brackets are non-diagnostic. CUSUM sensitivity
uses 30 seed-level scaled-EDD ratios with mean 1.95118556 and sample SD
0.09365234; normal and Student-t half-widths are 0.034 and 0.035. Full ratios,
seeds, and hashes are in `sim/analysis_cusum_sensitivity.json`.

## 8. Current evidence that remains in the article

For completeness, the native audit's 11 registered step fields are
`E,O,B,N,R,I,A,G,M,Z,D`, together with normative-update and surgery-context
events. The execution channel uses the separate precommitted open-loop stream
required by the estimand.

The article retains the current native joint-log audit table, exact anchors and
reported certificate intervals, executable near-zero rule, matched A/B/C
formulas and complete headline coverage table, independent truth-based
bias/RMSE, multi-seed recoverability results, T7 INCONCLUSIVE status, X5-c
MODEL_SENSITIVE status, negative controls, and all external-validity
limitations. In particular:

- B-miss/C-cover is not called a conditional-design effect;
- both-miss is not called a plug-in-bias effect;
- source-share bias, other-channel estimation error/covariance, and interval
  construction remain possible sources;
- matched A does not replace the formal certificate's original A;
- logical-envelope containment is not statistical coverage or recovery.
