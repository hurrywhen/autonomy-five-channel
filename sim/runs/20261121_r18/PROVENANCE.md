# R18 major-revision provenance (batch 2026-11-21)

## Scope

R18 is a focused local revision addressing the R17 review. It does not rewrite
the theory or the historical archive. The R17 review confirmed that the R16
core defects (multi-step reactive-MI execution, history/current conflation)
were already repaired in R17; R18 closes the remaining certificate, benchmark,
output-convention, terminology, and protocol-precision gaps.

Historical R11--R17 results, manifests, verdicts, and validation sidecars are
read-only inputs. The R17-native benchmark artifact
(`analysis_r17_native_benchmark.json`) is superseded by the R18 joint-log audit
but is preserved unchanged and still replay-checked.

## What changed

1. **Full-profile certificate (R18 schema).** `r18_guards.py` adds
   `R18_CHANNEL_SCHEMA_V1` on top of the R17 co-primary profiles. Mandatory
   top-level fields: `channel_profile` (full layer-applicable channel vector
   with value/state/interval/protocol_version; goal structural point + IRL
   interval; execution open-loop horizon + no-intermediate-observation mark;
   reflection three factors + logged event counts), `attribution_sensitivity`
   (registered RNI/NRI/order-average shares + every flow term + alternative
   semantic partitions + weights + recomputed per-convention composites +
   composite range), `sensitivity_flags`, `composite_scalar_grade`,
   `scalar_export_warning`. The producer recomputes composites and flags from
   declared inputs; required flags cannot be suppressed. Preregistered internal
   thresholds: order/model composite spread > 0.05 forces ORDER_SENSITIVE /
   MODEL_SENSITIVE (engineering thresholds, not domain SESOI). The exported
   scalar must equal the registered RNI-convention composite.

2. **Joint-log end-to-end native audit.** `native_joint_audit.py` +
   `analysis_r18_native_joint_audit.py` generate ONE joint operating-log batch
   from ONE registered T=3 reactive SCM under ONE log schema
   (`R18_JOINT_LOG_SCHEMA_V1`), estimating source attribution (both partitions),
   epistemic accuracy, reflection fidelity/consistency/Lambda, and
   viability/defense from the SAME batch. Execution is audited on a separate
   precommitted open-loop intervention stream from the same environment law
   (required by the estimand; the operating policy is reactive). Default
   n=8192/stream, seed=20261121, 100 trajectory-level bootstrap resamples; log
   SHA-256 binds the batch. Exact registered-convention composites:
   RNI 0.4608565248, NRI 0.0003907989, order-average 0.4011989073; alternative
   partition ~0.4608565; composite range [0.0003908, 0.4608565]. Both
   sensitivity flags fire on the baseline; the surgery arm (Lambda=0)
   annihilates every convention composite to zero.

3. **Open-loop output conventions.** `open_loop_execution.py`:
   `memoryless_sequence_kernels` renamed
   `memoryless_observation_sequence_kernels` (whole-observation-sequence
   Kronecker object; alias retained), new
   `memoryless_terminal_observation_kernels` (paper's terminal-observation
   estimand). Two-step BSC p=0.1: terminal 0.2655022 vs observation-sequence
   0.5310044. Zero-MI quantifier made support-relative for fixed precommitted
   Q (`open_loop_zero_iff_positive_support_rows_identical`); capacity-mode iff
   quantifies over sequences assignable positive probability by some
   admissible Q. Point-mass-Q zero regression added.

4. **Weight terminology.** Exact log-domain simplex bounds/halfspaces are an
   exact sensitivity characterization, not robustness evidence. Closed simplex
   (zero vertices) is a sensitivity relaxation; representation theorem and
   certificate weights use strictly positive interior weights. Paper
   abstract/intro/experiments/conclusion/related-work wording unified.

5. **External protocol TOST precision.** `EXTERNAL_VALIDATION_PROTOCOL.md`:
   equivalence by two one-sided alpha=0.05 tests (TOST), equivalently a 90%
   two-sided interval inside the frozen margins (95% two-sided requires
   alpha=0.025 one-sided). Non-inferiority directions:
   delta_BA=BA_full-BA_reduced upper bound < Delta_BA_NI;
   delta_Brier=Brier_full-Brier_reduced lower bound > -Delta_Brier_NI.
   Engineering margins frozen; domain SESOI/power/execution pending. Paper
   abstract/conclusion corrected (margins no longer listed as outstanding).

6. **Paper.** Full-profile certificate contract (sec_framework), native
   results table (sec_experiments, Table tab:native) reporting RNI/NRI/
   order-average composites and alternative-partition consequences directly,
   D-exec/appendix zero-quantifier and terminal-observation precision,
   event-level A_ref/Lambda carriers now implemented (limitations updated),
   TOST wording, weight-sensitivity terminology, de-versioned abstract, and
   historical-prose compression with version history centralized in
   `sim/CRITERION_VERSION_MAP.md`. Date fixed to 21 November 2026.

## Evidence boundaries (unchanged)

- Internal joint-log concept validation on one small registered instance; NOT
  external construct validation, NOT a generic MaxEnt-IRL solver.
- T7 INCONCLUSIVE; X5-c MODEL_SENSITIVE (D_noise=0.089799622); paired audit
  POST_HOC_PASS; failed/post hoc criteria retained.
- Legacy `a_org`/combined `a_via`/Bundle remain legacy markers, not upgraded.
- External protocol DESIGN_FROZEN_UNEXECUTED; domain SESOI/power, public
  outcome timestamp, independent-substrate execution, independent-investigator
  replication, expert/downstream criteria, selector-conditional DEL-1, general
  MaxEnt-IRL identified-set solver, more SCMs, Lean, and Chinese synchronization
  remain outstanding.
- This batch creates the immutable tag `v1.1-r18` and this frozen replay
  manifest on the final public synchronization commit. A version DOI requires
  Zenodo archiving of the tag and is NOT claimed. No formal Release page.

## Acceptance

`tools/make_r18_validation.py` runs from a clean worktree of the public content
commit: 273/273 tests, all R14/R15/R16/R17 read-only replays plus the R18
joint-audit replay, and an independent 103-page LaTeX build (115 references,
6 figures, fonts embedded with Unicode maps). The sidecar
`validation.json` records the content commit/tree and 97+ scientific-source
hashes. See `docs/R18paper_GitHub_Gitee发布说明_v1.md` (development repository)
for the final public commit and online verification.