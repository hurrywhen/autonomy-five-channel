# AFC-EXT-001: Prospective Independent-Substrate Validation Protocol

**Design status:** `DESIGN_FROZEN_UNEXECUTED`
**Design freeze date:** 2026-11-17
**Evidence status:** no external outcomes, no external construct validation, no external SESOI or power analysis.

This file freezes the comparison design requested during review. It is not an outcome preregistration: before any outcome unblinding, the executor must fill the pending numerical fields, timestamp the completed protocol in a public registry, and bind the data/code manifests. Those steps have not been performed.

## 1. Estimands and hypotheses

The unit of evaluation is an independently instantiated agent--environment--intervention SCM, not a historical ENV-0 record. The audit must register, before scoring, the semantic roles `N` (normative goal/belief/memory state), `R` (exogenous innovation/randomization registers), and `I` (external intervention), including update ownership and all mediated/direct paths.

Co-primary endpoints are:

1. **Intervention-attribution balanced accuracy** across the registered surgery classes, with macro-averaged recall and per-class confusion matrices. Random/chance levels and the handling of `INCONCLUSIVE` are fixed before unblinding.
2. **Held-out calibration error** of channel profiles and the reduced comparators, using a numerical proper scoring rule selected before unblinding.

Secondary endpoints are source-order sensitivity, intervention-attribution coverage, downstream robustness prediction, and blinded expert convergent/discriminant ratings. Expert ratings and SCM-ground-truth attribution are never pooled into one accuracy number.

The substantive falsifier is that a behavior-only, utility-only, scalar, or reduced-channel comparator matches or exceeds the full profile on the co-primary endpoints across the independent substrates. Source attribution is additionally falsified as an order-free interpretation whenever RNI, NRI, and Shapley-style values materially disagree.

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
- **Partitioning:** instance-level calibration, validation, and held-out test splits. No trajectory from one instance may cross partitions.
- **Blinding:** scoring code receives role-bound logs without intervention labels; analysts remain blinded to held-out outcomes until the completed protocol and analysis code are timestamped.
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
| Ingel/Albantakis execution | Not run |
| PID/candidate numerical comparison | Not run |
| Intervention-attribution accuracy outcomes | Not run |
| External expert study | Not run |
| External SESOI and power calculation | Pending before unblinding |
| Public outcome preregistration timestamp | Not created |
| Immutable external-data/result release and version DOI | Not created |
