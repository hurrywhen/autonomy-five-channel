# R19 medium-revision provenance (batch 2026-11-22)

## Scope

R19 is a medium revision addressing the R18 review, which confirmed that the
R17 core defects were repaired in R18 and that no new foundational math error
(of the feedback-counterexample class) was found. The remaining issues were
certificate generality, cross-environment numerical reproducibility, and
near-zero sampling-error propagation. R19 closes these without rewriting the
theory or the historical archive.

Historical R11--R18 results, manifests, verdicts, and validation sidecars are
read-only inputs. The R18 joint-audit artifact is superseded by R19 but
preserved unchanged together with its recorded cross-environment replay
failure (`REPLAY_FAILURE_R18.md`).

## What changed

1. **Cross-environment numerical reproducibility (priority 1).** Root cause:
   the parity execution kernel has a two-dimensional capacity-achieving face,
   so the optimizer's auxiliary input coordinates are non-unique and
   platform-sensitive (~7.5e-10 drift), yet sat inside the R18 byte-level
   evidence hash. Repair: (a) evidence hashes bind immutable raw inputs only;
   (b) a declared canonicalization rule (exact uniform when capacity-achieving
   or near-zero; otherwise the unique maximum-entropy capacity-achieving
   input via deterministic iterative scaling, fail-closed verified); (c)
   declared per-field replay tolerances (1e-6 coordinates, 1e-9 capacity
   values), raw hashes/counts/statuses byte-exact. Verified in two independent
   clean worktrees with differing thread/hash environments. Failure record
   retained, not replaced.

2. **Layer-aware, degradation-complete certificates (priority 2).**
   `r19_guards.py` (`R19_CHANNEL_SCHEMA_V1`): L0 uses an independent
   `L0_INTERNAL_CAUSAL` report (F_int/F_ext share only; RNI/NRI not imposed);
   L1/L2 use RNI/NRI/order-average + semantic partitions. Channel states
   DEFINED/INTERVAL/UNKNOWN/NOT_APPLICABLE; point vs interval certificates are
   separate modes; composite intervals propagate exactly by coordinatewise
   monotonicity. IRL-interval goal mode (structural point optional), thin-log
   and zero-entropy reflection degradation to [0, product of defined factors],
   zero-total-flow share unidentifiability ([0,1] org interval + composite
   interval), UNKNOWN worst-case propagation with LIMITED ceiling. New
   L0/L1/interval/thin-log/zero-entropy/zero-flow/unknown regression tests.

3. **Corrected state_autonomy_RNI (priority 3).** The R18 estimator passed a
   unit composite to state_defense_split and returned only the resource gate
   (0.8). R19 computes it from the actual five channels; regression asserts
   equality with the registered RNI certificate composite (and inequality with
   the gate). The R18 module is frozen for read-only replay of its superseded
   artifact (known defective field documented).

4. **Sampled NRI disclosure + multi-seed recoverability (priority 4).** The
   paper now tabulates exact AND sampled per-convention composites with errors
   (sampled NRI 0.1478374 vs exact 0.0003908, error 0.1474 > 0.05 threshold).
   Near-zero detection limit (NRI share < 1e-6) -> interval semantics
   [0, 0.1866], not a high-confidence point. `analysis_r19_sampling_study.py`:
   8 independent seeds (20261122--20261129), 8192 trajectories, 200 bootstrap
   resamples; per-convention bias/RMSE/coverage/width. Finding: plug-in bias
   amplified by x^0.2 prevents recovery of the near-zero NRI endpoint
   (percentile under-coverage: NRI 0/8, RNI 1/8, order-average 0/8); bias
   correction halves NRI RMSE (0.151 -> 0.081) but does not restore the
   endpoint. Exact endpoints are model anchors, not recoverability claims.

5. **Decomposed sensitivity + threshold provenance (priority 5).**
   order_spread (registered partition, across orders), semantic_partition_spread
   (max over orders of across-partition spread), overall_composite_range
   (overview only). ORDER_SENSITIVE and MODEL_SENSITIVE trigger independently.
   Native instance: order 0.4604657; per-convention partition differences
   RNI 0 / NRI 0.4604657 / order-average 0.0596576. The 0.05 thresholds are
   renamed POST HOC FROZEN internal engineering thresholds (frozen after the
   R17-native results were observed; not preregistered before outcomes; not a
   domain SESOI). Preregistration language reserved for future audits.

6. **Sampled negative controls.** Surgery arm (Lambda=0 exactly -> all
   convention composites zero, REGISTERED_SURGERY) and action-decoupled arm
   (execution zero within sampling precision <= 1e-3; exact arm exactly zero)
   now run through the same joint-log pipeline.

7. **Paper.** Layer-aware degradation-complete certificate contract; native
   table with exact+sampled composites; multi-seed study table; cross-
   environment reproducibility paragraph; decomposed-sensitivity paragraph;
   abstract/intro/conclusion updated; historical/redundant prose compressed
   throughout. Net 105 pages (R18: 103): ~2 pages of reviewer-required new
   evidence/governance added, historical prose compressed; float placement
   absorbs the remainder. 115 references, 6 figures, 0 undefined references,
   51 embedded fonts with Unicode maps, max overfull 8.94pt. Date fixed to
   22 November 2026.

## Evidence boundaries (unchanged)

- Internal joint-log concept validation on one small registered instance; NOT
  external construct validation, NOT a generic MaxEnt-IRL solver, NOT a power
  analysis, NOT statistical consistency.
- T7 INCONCLUSIVE; X5-c MODEL_SENSITIVE (D_noise=0.089799622); paired audit
  POST_HOC_PASS; failed/post hoc criteria retained.
- Legacy a_org/combined a_via/Bundle remain legacy markers, not upgraded.
- External protocol DESIGN_FROZEN_UNEXECUTED; domain SESOI/power, public
  outcome timestamp, independent-substrate execution, independent-investigator
  replication, expert/downstream criteria, selector-conditional DEL-1, general
  MaxEnt-IRL identified-set solver, more SCMs, Lean, Chinese synchronization
  remain outstanding.
- This batch creates immutable tag `v1.2-r19` and a two-environment frozen
  replay manifest on the final public synchronization commit. A version DOI
  requires Zenodo archiving of the tag and is NOT claimed. No formal Release.
- The three unavailable R14 run-time SPEC byte snapshots remain unrecovered.

## Acceptance

`tools/make_r19_validation.py` runs from clean worktrees of the public content
commit in TWO environments (differing thread/hash settings): 319/319 tests,
all R14/R15/R16/R17 read-only replays, the R18 artifact integrity/anchor check
(read-only; cross-environment numerical replay superseded), the R19 joint-audit
and sampling-study replays, and an independent 105-page LaTeX build (115
references, 6 figures, fonts embedded with Unicode maps). The sidecar
`validation.json` records the content commit/tree, both environments, and the
scientific-source hashes. See `docs/R19paper_GitHub_Gitee发布说明_v1.md`
(development repository) for the final public commit and online verification.
