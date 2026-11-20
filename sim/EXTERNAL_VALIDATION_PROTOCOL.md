# AFC-EXT-001: Prospective Independent-Substrate Validation Protocol

**Design status:** `DESIGN_FROZEN_UNEXECUTED`
**Design freeze date:** 2026-11-17
**Decision-rule precision (R18):** 2026-11-21 (TOST wording and non-inferiority direction clarified; frozen margins unchanged)
**Evidence status:** no external outcomes, no external construct validation, no domain-justified SESOI or power analysis.

This file freezes the comparison design requested during review. It is not an outcome preregistration: before any outcome unblinding, the executor must fill the pending numerical fields, timestamp the completed protocol in a public registry, and bind the data/code manifests. Those steps have not been performed.

## 1. Estimands and hypotheses

The unit of evaluation is an independently instantiated agent--environment--intervention SCM, not a historical ENV-0 record. The audit must register, before scoring, the semantic roles `N` (normative goal/belief/memory state), `R` (exogenous innovation/randomization registers), and `I` (external intervention), including update ownership and all mediated/direct paths.

Co-primary endpoints are:

1. **Intervention-attribution balanced accuracy** across the registered surgery classes, with macro-averaged recall and per-class confusion matrices. Random/chance levels and the handling of `INCONCLUSIVE` are fixed before unblinding. This endpoint audits taxonomy recovery against the newly logged operators; by itself it is still model-linked evidence, not construct validity.
2. **Held-out downstream-outcome Brier score** for a binary, independently timestamped outcome `Y_{t+H}` that is not an input to any channel estimator. The preregistered examples are action--environment decoupling or failure to complete a registered recovery task at horizon `H`; exactly one is selected per substrate before unblinding. A fixed mapping from the full or reduced profile to `P(Y_{t+H}=1)` is fit only on calibration instances. The baseline mapping is multinomial/regularized logistic regression with the same feature-standardization and regularization grid for every comparator; hyperparameters are selected by inner instance-level cross-validation, and all tuning is repeated inside each outer training fold. The held-out Brier score, log loss, calibration intercept/slope, and discrimination are reported separately rather than selecting the most favorable after seeing outcomes.

Secondary endpoints are source-order sensitivity, intervention-attribution coverage, downstream robustness prediction, and blinded expert convergent/discriminant ratings. Expert ratings, the independently timed downstream outcome, and SCM-ground-truth attribution are never pooled into one accuracy number.

**Equivalence and non-inferiority, not non-significance.** The added-value comparisons are full profile minus each preregistered reduced comparator. For balanced accuracy, the equivalence margin is `Delta_BA=0.05` and the non-inferiority margin is `Delta_BA_NI=0.03`; for Brier score, lower is better, with `Delta_Brier=0.02` and `Delta_Brier_NI=0.01`. These are frozen engineering design margins, not empirically justified domain SESOI and not a power calculation.

**Decision rule (TOST, R18 precision).** Equivalence is declared only by two one-sided tests (TOST) at level `alpha=0.05` each: both inferiority nulls are rejected, which is equivalent to the **90% two-sided** confidence interval for the difference lying wholly inside `(-Delta, +Delta)`. A one-sided 95% interval is unbounded on one side and cannot "lie wholly within" a finite margin; if a 95% two-sided interval is preferred instead, the two one-sided tests must each be run at `alpha=0.025`. Any other result is `INCONCLUSIVE`, never "no significant difference, therefore equivalent."

**Non-inferiority direction (reduced model not worse than full).** Let `delta_BA = BA_full - BA_reduced` (higher BA is better). The reduced model is non-inferior iff the one-sided 95% **upper** confidence bound for `delta_BA` is strictly below `Delta_BA_NI` (test of `H0: delta_BA >= Delta_BA_NI`). Let `delta_Brier = Brier_full - Brier_reduced` (lower Brier is better). The reduced model is non-inferior iff the one-sided 95% **lower** confidence bound for `delta_Brier` is strictly above `-Delta_Brier_NI` (test of `H0: delta_Brier <= -Delta_Brier_NI`). The same decision rule is applied per substrate and in a preregistered random-effects pooled analysis; a pooled interval cannot rescue a failed required substrate.

The substantive added-value falsifier is therefore an explicitly declared equivalence or non-inferiority result for a behavior-only, utility-only, scalar, or reduced-channel comparator on both co-primary endpoints across the required substrates. Source attribution is additionally falsified as an order-free interpretation whenever RNI, NRI, and Shapley-style values materially disagree. Independent-investigator reimplementation of at least one substrate and its outcome pipeline is required before upgrading any model-linked success to external construct validation; the present authors' SCMs and newly logged surgery labels remain model constructions.

## 2. Independent substrates

At minimum, implement both:

- **Ingel et al. (2022):** Gridworld and repeating-pattern reinforcement-learning settings, including observation perturbations and the registered memory architecture. Their next-internal-state PID estimand is reproduced as a comparator, not relabeled as action-directed `N/R/I` flow.
- **Albantakis (2021):** structurally diverse discrete Markov Brains on PathFollow tasks, reproducing the structural, information-theoretic, causal, and dynamical candidate measures selected before unblinding.

MiniGrid with a learned tabular agent and a simplified LLM tool-use harness may be added as separate transfer arms. They cannot replace either minimum substrate. Human/LLM self-report is not SCM ground truth. “Independent substrate” means independent of ENV-0, not independent-investigator replication; the present authors' reimplementations and added SCMs remain new model constructions.

## 3. Candidate measures and reduced comparators

The candidate battery contains:

- the present RNI ordered residual share, reverse NRI share, and two-player Shapley-style sensitivity descriptor;
- Ingel's next-internal-state PID quantities, with **BROJA as the primary redundancy implementation and SxPID as the sensitivity implementation**, plus explicit finite-histogram, discretized-memory, and estimator-version conventions; changing the PID definition requires a new protocol version;
- Albantakis's preregistered candidate measures and empowerment estimated under the Jung--Polani--Stone normalization protocol;
- the present goal, execution, epistemic, reflection, viability, readiness, and endorsement fields where the substrate identifies them;
- behavior-only, utility-only, scalar-only, and preregistered reduced-channel models.

PID, directed information, and causal intervention measures remain separate estimands. No post hoc choice among PID redundancy functions or source orders is allowed after outcomes are seen.

## 4. Intervention and negative-control matrix

Each substrate includes honest mediated information, direct external bypass, goal/endorsement surgery, policy-script bypass, observation-kernel change, action-leverage contraction, resource reduction, pure exogenous randomness, pure normative control, and mixed redundant/synergistic `N/R` policies.

Every arm records whether influence is mediated by `N` or bypasses it. Negative controls include unchanged behavior with hidden surgery, behavior change without autonomy loss, action--environment decoupling, zero defense readiness with intact present state, and an OR-style redundant-source law. Alternative reasonable `N/R` semantic partitions are registered before scoring and reported as sensitivity arms rather than selected by their results.

Ground-truth intervention labels come from the newly ported and logged surgery operators, not from the published papers' outcome tables. Published observation/pattern perturbations and maximum-entropy internal-state perturbations are not automatically instances of this framework's surgery taxonomy: each mapping, including any environment-reinstantiation boundary, is registered before scoring. Any auxiliary endorsement SCM added by the executors is explicitly labeled a new construction. Without an applicable endorsement SCM, Lambda is `NOT_APPLICABLE`, no value is imputed, and no L2/five-channel score is fabricated.

## 5. Sampling, blinding, and analysis

- **Independent sampling unit:** independently generated SCM/instance seed; repeated trajectories and time points are nested, not independent replicates.
- **Partitioning:** instance-level calibration, inner-validation, outer-validation, and final held-out test splits. No trajectory from one instance may cross partitions. Profile-to-outcome mapping, feature selection, regularization, imputation, and calibration are refit inside every outer training fold; the final test set is touched once.
- **Blinding:** scoring code receives role-bound logs without intervention labels; downstream outcomes are generated and timestamped independently of channel computation, and analysts remain blinded to held-out outcomes until the completed protocol and analysis code are timestamped.
- **Estimation:** report exact enumeration where feasible and otherwise the registered estimator, bias correction, interval method, and independent reference implementation. Multi-step feedback must be included; one-step guards alone are insufficient.
- **Reporting:** per-substrate and pooled random-effects analyses, per-class failures, all source orders, semantic-partition ranges, ties, missingness, and every exclusion. Legacy CONFIRMED labels play no role.

Pending before outcome unblinding: numerical SESOI for each co-primary endpoint, minimum detectable effect, target power, significance/family-wise error rule, external error model, number of independent instances, trajectory lengths, and stopping rule. The historical `n=30` replay count and the internal `0.01` numerical threshold are not external power or domain SESOI justifications.

## 6. Reproducibility and evidence grades

Before execution, freeze substrate commit, dependency environment, estimator SPEC, seeds, intervention registry, candidate-measure versions, analysis code, and expected output schema. After execution, publish immutable data/result manifests and a clean-worktree replay. Certificate metadata must bind `channel_schema_version`, `org_mode`, `goal_mode`, `state_readiness_version`, and model/evidence hashes; a hash binds bytes but does not prove their external validity.

The result remains `INCONCLUSIVE` if a required substrate, `N/R/I` role registry, nondegenerate estimator bracket, or pending numerical field is absent. `SCM_AUDITED` requires an actual SCM audit; complete registration alone is `REGISTERED_COMPLETE`. `NOT_APPLICABLE` and `UNKNOWN` remain distinct, and neither a high score nor an SCM audit constitutes external construct validation.

## 7. Current completion ledger

| Item | Status |
|---|---|
| Comparison design and minimum substrates | Design frozen here |
| Engineering equivalence/non-inferiority margins and TOST rule | Frozen here (R18 precision); not domain SESOI |
| Ingel/Albantakis execution | Not run |
| PID/candidate numerical comparison | Not run |
| Intervention-attribution accuracy outcomes | Not run |
| External expert study | Not run |
| Domain-justified SESOI and power calculation | Pending before unblinding |
| Public outcome preregistration timestamp | Not created |
| Immutable external-data/result release and version DOI | Not created |
