# R20 small-to-medium revision provenance (batch 2026-11-22)

## Scope

R20 addresses the R19 review, which confirmed that the R18 cross-environment
replay problem was substantively repaired and that the core theory issues
(execution channel, historical provenance, certificate profile) should no
longer be rejection reasons. The remaining problems were: the near-zero
detection limit was oracle-triggered and outside the formal certificate;
interval midpoints were used to infer "convention agreement"; degenerate
[s,s] intervals were propagated instead of available sampling intervals; and
some tests encoded expected empirical outcomes as universal pass conditions.
R20 closes these four items without rewriting the theory or the historical
archive.

Historical R11--R19 results, manifests, verdicts, and validation sidecars are
read-only inputs. The R19 joint-audit and sampling-study artifacts are
superseded by R20 but preserved unchanged (byte-identical; their --check
replays still pass after the validator decoupling, which removed empirical
raises without changing compute outputs).

## What changed

1. **Data-driven near-zero detection inside the formal certificate
   (priority 1).** `r20_detection.py` declares, BEFORE the R20 study outcomes,
   one executable rule: plug-in share + trajectory-block bootstrap percentile
   95% interval -> basic (pivotal) bias-corrected interval
   [2p - q97.5, 2p - q2.5] clipped to [0,1] -> three-state classification
   against the inherited post hoc frozen limit delta=1e-6 (upper < delta:
   DATA_BELOW_LIMIT; lower > delta: DATA_ABOVE_LIMIT; otherwise
   INDETERMINATE_NEAR_ZERO; boundary equality fail-closed). The deployable
   classifier has no truth parameter. The old truth-triggered rule is retained
   only as `oracle_assisted_fixture_classification`, explicitly labeled
   ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE, for labeling
   classifications in fixture/study evaluation. `r20_guards.py`
   (R20_CHANNEL_SCHEMA_V1) puts a convention_report inside every L1/L2
   convention: convention_status, share_interval{bounds,kind},
   composite_interval{bounds,kind}, detection limit + rule/value provenance,
   and diagnostic plug-in outputs. BELOW/INDETERMINATE conventions export the
   conservative logical envelope [0, composite(upper)] (kind
   LOGICAL_ENVELOPE, explicitly not a confidence interval); ABOVE conventions
   export the monotone propagation of the sampling interval. The sampled
   baseline certificate is INTERVAL-valued (no point export); its
   overall_composite_range is the hull of the reported convention composite
   intervals ([0, 0.4622412] on the default seed), so certificate and external
   summary agree by construction. The plug-in NRI composite 0.1478374 is
   stored only as diagnostic_plugin_composite (it lies outside the reported
   envelope [0, 0.1324217]) and is labeled diagnostic in the paper. On this
   instance the honest data verdict for NRI is INDETERMINATE_NEAR_ZERO:
   n=8192 data cannot confirm the near-zero share.

2. **Three-state interval sensitivity (priority 2).** Minimum possible
   convention separation max(0, max lower - min upper) > threshold ->
   CONFIRMED_SENSITIVE; worst-case spread max upper - min lower <= threshold
   -> NO_CONFIRMED_SENSITIVITY; otherwise INDETERMINATE; zero total flow or
   UNKNOWN inputs -> NOT_EVALUABLE; L0 -> NOT_APPLICABLE. Identical wide
   intervals are NEVER read as agreement; the midpoint spread is retained
   only as midpoint_spread_descriptive. Flags fire only on CONFIRMED; absence
   of a flag means "no confirmed sensitivity detected", not agreement. POINT
   mode reproduces the R19 flag behavior exactly (degenerate intervals).

3. **Real interval propagation with declared kinds (priority 3).** Sampling
   certificates propagate the actual basic bias-corrected share intervals,
   not degenerate [s,s] points. Every interval carries a kind: POINT_EXACT /
   LOGICAL_ENVELOPE / SAMPLING_BASIC_BOOTSTRAP / SAMPLING_PERCENTILE /
   SAMPLING_NORMAL_APPROX / SENSITIVITY / MODEL_SELECTION. Monotone endpoint
   propagation is documented as an envelope guarantee FOR THE GIVEN INPUT
   INTERVALS, not automatically a full statistical uncertainty interval;
   logical envelopes are explicitly non-statistical.

4. **Test decoupling (priority 4).** Software correctness tests check
   formulas, data structures, boundary conditions, independent analytic
   anchors, numerical stability, and governance fail-closed behavior only.
   The empirical expectations in the R19 validators/tests (every NRI plug-in
   error must exceed 0.05; bias correction must improve RMSE; intervals must
   not cover the truth) were removed; the frozen artifact's specific values
   are covered by explicitly labeled SNAPSHOT regressions. R19 compute
   outputs are unchanged, so R19 artifacts remain byte-identical and their
   --check replays pass. A future improved estimator or new legitimate seeds
   must not fail validation for recovering the endpoint better.

5. **Detection-rule misclassification study (priority 5).**
   `analysis_r20_detection_study.py` with a PREDECLARED grid frozen in source
   before outcomes: 16 independent seeds (20261122--20261137) x n in
   {2048, 8192} x 200 trajectory-block bootstrap resamples; per convention x
   n: three-state classification rates, oracle comparison rates (false-below
   / false-above / indeterminate), reported composite-interval coverage of
   the exact anchor, mean width, share-interval coverage, descriptive plug-in
   bias/RMSE. Findings (descriptive): NRI is INDETERMINATE in 16/16 seeds at
   both sample sizes, with zero false-below/false-above classifications and
   16/16 envelope coverage (width 0.1854 -> 0.1435); ABOVE-limit conventions
   are correctly classified but their sampling intervals under-cover the
   exact composites because plug-in bias dominates (RNI coverage 4/16 ->
   0/16; order-average 8/16 -> 2/16). Indeterminate is an honest outcome, not
   a failure; the rule is reporting governance, not a consistency guarantee,
   power claim, or universal coverage claim.

6. **Paper.** R20 certificate contract (detection-complete, three-state
   sensitivity, interval kinds); native table with exact anchors / diagnostic
   plug-ins / reported certificate intervals; new detection-rule paragraph
   and tab:detection; frozen R19 sampling table retained as descriptive;
   cross-environment repair narrative compressed to a pointer plus summary
   (full record retained in runs/20261122_r19/REPLAY_FAILURE_R18.md); DEL-1
   six-criterion ledger moved to the repository ledger (T7 verdict and counts
   retained in text); related work / discussion / identifiability /
   experiments historical prose tightened. Net **103 pages** (R19: 105; R18:
   103): ~1.5 pages of reviewer-required new content offset by compression;
   115 references, 6 figures, 0 undefined references, 51 embedded fonts with
   Unicode maps, max overfull 8.94pt. Date remains 22 November 2026.

## Evidence boundaries (unchanged)

- Internal joint-log concept validation on one small registered instance plus
  internal descriptive finite-sample studies; NOT external construct
  validation, NOT a generic MaxEnt-IRL solver, NOT a power analysis, NOT
  statistical consistency, NOT universal coverage.
- T7 INCONCLUSIVE; X5-c MODEL_SENSITIVE (D_noise=0.089799622); paired audit
  POST_HOC_PASS; failed/post hoc criteria retained.
- Legacy a_org/combined a_via/Bundle remain legacy markers, not upgraded.
- External protocol DESIGN_FROZEN_UNEXECUTED; domain SESOI/power, public
  outcome timestamp, independent-substrate execution, independent-investigator
  replication, expert/downstream criteria, selector-conditional DEL-1, general
  MaxEnt-IRL identified-set solver, more SCMs, Lean, Chinese synchronization
  remain outstanding.
- This batch creates immutable tag `v1.3-r20` and a two-environment frozen
  replay manifest on the final public synchronization commit. A version DOI
  requires Zenodo archiving of the tag and is NOT claimed. No formal Release.
- The three unavailable R14 run-time SPEC byte snapshots remain unrecovered.
- The two validation environments differ in thread/hash settings on the same
  platform; this is not a claim of cross-platform replication by independent
  investigators.

## Acceptance

`tools/make_r20_validation.py` runs from clean worktrees of the public content
commit in TWO environments (differing thread/hash settings): 369/369 tests,
all R14/R15/R16/R17-weight read-only replays, the R19 joint-audit and
sampling-study replays (byte-identical artifacts), the R20 joint-audit and
detection-study replays, read-only integrity/anchor checks of the R17-native
and R18 numerical blocks, original-environment R17-native/R18 numerical
confirmations, and an independent 103-page LaTeX build (115 references, 6
figures, fonts embedded with Unicode maps). The sidecar `validation.json`
records the content commit/tree, both environments, and the scientific-source
hashes. See `docs/R20paper_GitHub_Gitee发布说明_v1.md` (development repository)
for the final public commit and online verification.