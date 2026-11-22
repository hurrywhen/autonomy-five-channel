# R21 small revision provenance (batch 2026-11-22)

## Scope

R21 addresses the R20 review, which confirmed that the four R20 fixes
(data-driven in-certificate detection, three-state interval sensitivity, real
interval propagation with kinds, test decoupling) were substantive and that no
new foundational theory/implementation problem remained. The two remaining items
were statistical-naming precision and coverage-interpretation completeness:

1. The above-detection-limit composite sampling interval propagates ONLY the
   source-share basic bootstrap interval; the execution/epistemic/reflection
   channels are fixed at their plug-in points. It is therefore a
   SHARE-CONDITIONAL composite sampling interval, not a full joint-uncertainty
   interval, and this conditioning scope was not fully disclosed.
2. Logical-envelope anchor containment (NRI 16/16) and sampling-interval coverage
   (RNI 0/16 at n=8192) were reported under one "coverage" heading, inviting the
   misreading that NRI is estimated more reliably.

R21 closes both without changing the detection rule, the three-state sensitivity
system, the estimator, or the historical archive.

Historical R11--R20 results, manifests, verdicts, and validation sidecars are
read-only inputs. The R20 joint-audit and detection-study artifacts are
superseded by R21 but preserved unchanged (byte-identical; R21 adds new modules
and artifacts without touching R20 code, and R20 --check replays still pass).

## What changed

1. **Conditioning disclosure (priority 1).** `r21_guards.py`
   (R21_CHANNEL_SCHEMA_V1) renames the above-limit composite sampling kind to
   SHARE_CONDITIONAL_SAMPLING_BASIC_BOOTSTRAP and adds a `conditioning_scope`
   field to every interval-mode composite interval (value
   `other_channels_fixed_at_plugin` when the non-org channels are DEFINED points,
   `other_channels_at_declared_bounds` otherwise). A certificate-level
   `composite_interval_conditioning` policy declares the share-conditional
   design, its two under-coverage causes (directed-information plug-in bias and
   the conditional design), and that the joint bootstrap is an artifact-level
   supplementary diagnostic. The share's own interval keeps
   SAMPLING_BASIC_BOOTSTRAP (unconditional). The propagated bounds are
   numerically identical to R20 (only the kind/scope changed); the sampled
   baseline certificate remains INTERVAL-valued with overall range
   [0, 0.4622412] on the default seed.

2. **Separated coverage semantics (priority 2).** Logical-envelope anchor
   containment is reported as `logical_envelope_anchor_containment` (a
   containment diagnostic, NOT statistical coverage); share-conditional sampling
   coverage as `share_conditional_sampling_coverage` (conditional on other
   channels fixed at points); the two are never combined into a single rate nor
   compared as estimator quality. Enforced in `analysis_r21_detection_study.py`
   and the joint-audit convention table.

3. **Joint trajectory bootstrap (supplementary diagnostic).**
   `r21_joint_bootstrap.py` recomputes ALL operating-side channels from the same
   resampled operating batch (within-batch covariance preserved) and the
   execution channel from the independent precommitted stream (resampled
   stratified by sequence), then the composite per convention; the percentile-95
   interval is a genuine joint composite sampling interval. Per-trajectory
   sufficient statistics make each resample numpy aggregation plus a small (4x2)
   Blahut--Arimoto capacity call (the well-conditioned unique capacity VALUE; no
   canonical-input IPF). Deterministic given the seed; cross-environment float
   diff 0. It is an ARTIFACT-LEVEL diagnostic, NOT the certificate's reported
   semantics, and it does NOT remove plug-in bias.

4. **Two-cause under-coverage attribution (descriptive).** On the predeclared
   16-seed x {2048,8192} grid (200 bootstrap resamples; unchanged from R20), the
   share-conditional results reproduce R20 exactly (NRI INDETERMINATE 16/16,
   zero false-below/above, envelope containment 16/16; RNI share-conditional
   coverage 4/16 -> 0/16; order-average 8/16 -> 2/16). The joint diagnostic
   quantifies the conditional-design cause: at n=8192, 14/16 RNI cells (11/16
   order-average) miss under share-conditional but cover under joint; residual
   both-miss cells (2/16 RNI, 3/16 order-average) reflect plug-in bias. Joint
   coverage: RNI 16/16 (n=2048) -> 14/16 (n=8192); order-average 15/16 -> 13/16;
   NRI 0/16 at both sizes (bias dominates; joint does not remove it).

5. **Paper.** R21 certificate contract (conditioning disclosure, separated
   coverage); native table marks above-limit intervals "SC" (share-conditional);
   detection table separates Env.contain / SC cov. / Joint cov. columns with a
   two-cause reading paragraph; abstract/intro/conclusion note the conditioning
   and joint diagnostic. Page target: the user accepted **105 pages** (R20 was
   103; the reviewer-required additions net ~+2 pages after honest compression of
   ~60 lines of related-work/discussion/appendix prose; no formatting tricks).
   115 references, 6 figures, 0 undefined references, 51 embedded fonts with
   Unicode maps, max overfull 8.94pt. Date remains 22 November 2026.

## Evidence boundaries (unchanged)

- Internal joint-log concept validation on one small registered instance plus
  internal descriptive finite-sample studies; NOT external construct validation,
  NOT a generic MaxEnt-IRL solver, NOT a power analysis, NOT statistical
  consistency, NOT universal coverage.
- The joint bootstrap is a supplementary diagnostic, not the reported certificate
  semantics, and does not remove plug-in bias; the near-zero NRI endpoint is
  still not shown recoverable from finite samples.
- T7 INCONCLUSIVE; X5-c MODEL_SENSITIVE (D_noise=0.089799622); paired audit
  POST_HOC_PASS; failed/post hoc criteria retained.
- Legacy a_org/combined a_via/Bundle remain legacy markers, not upgraded.
- External protocol DESIGN_FROZEN_UNEXECUTED; domain SESOI/power, public outcome
  timestamp, independent-substrate execution, independent-investigator
  replication, expert/downstream criteria, selector-conditional DEL-1, general
  MaxEnt-IRL identified-set solver, more SCMs, Lean, Chinese synchronization
  remain outstanding.
- This batch creates immutable tag `v1.4-r21` and a two-environment frozen replay
  manifest on the final public synchronization commit. A version DOI requires
  Zenodo archiving of the tag and is NOT claimed. No formal Release.
- The three unavailable R14 run-time SPEC byte snapshots remain unrecovered.
- The two validation environments differ in thread/hash settings on the same
  platform; this is not a claim of cross-platform replication by independent
  investigators.

## Acceptance

`tools/make_r21_validation.py` runs from clean worktrees of the public content
commit in TWO environments (differing thread/hash settings): 406/406 tests, all
R14/R15/R16/R17-weight read-only replays, the R19 and R20 replays (byte-identical
artifacts), the R21 joint-audit and detection-study replays (the latter recomputes
the full grid including the joint bootstrap, so it is slow), read-only
integrity/anchor checks of the R17-native and R18 numerical blocks,
original-environment R17-native/R18 numerical confirmations, and an independent
105-page LaTeX build (115 references, 6 figures, fonts embedded with Unicode
maps). The sidecar `validation.json` records the content commit/tree, both
environments, and the scientific-source hashes. See
`docs/R21paper_GitHub_Gitee发布说明_v1.md` (development repository) for the final
public commit and online verification.