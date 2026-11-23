# R22 small revision provenance (batch 2026-11-23)

## Scope

R22 addresses the R21 review, which confirmed that the R21 conditioning
disclosure, separated coverage semantics, and joint bootstrap were substantive,
with no new foundational mathematical error or cross-environment replay failure.
The remaining issue was **attribution identifiability**, not interval engineering:

- A was the certificate's BASIC share-conditional interval;
- C was a PERCENTILE fully joint interval on another bootstrap stream.

Thus A and C differed in construction, channel propagation, and resampling
stream. R21's interpretations "A misses / C covers -> conditional-design effect"
and "both miss -> plug-in-bias effect" were not identified. R22 withdraws both
interpretations. It does not rewrite the theory, detection rule, certificate
schema, estimator, or historical archive.

User decisions (2026-11-23): (1) implement matched A/B/C diagnostics AND demote
all attribution language; (2) use the full predeclared 16-seed x {2048,8192} x
200 grid; (3) impose no paper-page cap. Historical R11--R21 evidence remains
read-only; R21 artifacts are byte-identical and R21 --check replays still pass.

## What changed

1. **Matched A/B/C on common replicates.** `r22_interval_contrast.py` computes:
   - A (`basic-share-conditional`): basic pivotal share interval
     [2s-q97.5, 2s-q2.5] clipped to [0,1], propagated with the other channels
     fixed at the original plug-in/structural points;
   - B (`percentile-share-conditional`): percentile 95 of composite replicates
     with only the share resampled and the other channels fixed at those same
     original points;
   - C (`percentile-joint`): percentile 95 of composite replicates with every
     channel recomputed, preserving within-batch covariance and independently
     resampling execution stratified by precommitted sequence.
   All three use a common finite-replicate mask. The artifact stores replicate
   counts, a platform-independent packbits mask hash, and SHA-256 of the exact
   integer resampling-input draws (not native floating-point analysis outputs).
   Exact truth never enters interval construction.

2. **Descriptive method contrasts, not attribution.** B/C is a matched-replicate,
   matched-percentile channel-propagation contrast; A/B is an interval-
   construction contrast; A/C remains a mixed construction+conditioning
   contrast. `undercoverage_attribution` is replaced by
   `descriptive_interval_method_contrast`, containing full 2x2
   miss/miss, miss/cover, cover/miss, cover/cover counts for A/B, B/C, and A/C.
   No count is a single-cause estimate or formal bias decomposition. The joint
   bootstrap remains supplementary and does not remove plug-in bias.

3. **R21 reproduction and unchanged certificate.** C uses R21's operation/RNG
   order (default_rng([seed,n,21])) and reproduces its bounds/mean/SE exactly in
   both partitions and all conventions. The tabulated A is a matched-stream
   recomputation of the certificate construction; the formal R21 certificate
   and its original A interval are unchanged and separately reproduced. The
   R22 joint audit's baseline certificate equals the R21 certificate field for
   field, and C equals the retained R21 joint diagnostic.

4. **Separate truth-based bias assessment.** The full detection study retains
   exact-truth multi-seed descriptive plug-in mean bias and RMSE instead of
   inferring bias from both-miss cells. At n=8192, bias/RMSE are
   0.0007154821/0.0020106486 (RNI), 0.1521969107/0.1523790231 (NRI), and
   0.0009470006/0.0018961992 (order average). NRI remains INDETERMINATE with a
   logical envelope; any matched-basic downward shift that contains the anchor
   is not statistical recovery.

5. **Full matched grid.** `analysis_r22_detection_study.py` uses the unchanged
   predeclared 16 seeds 20261122--20261137 x n in {2048,8192} x 200 resamples.
   It reports formal-A and matched-A/B/C coverage, widths, independent bias/RMSE,
   and all pairwise coverage-pattern counts. On each 16-seed grid, A/B/C coverage at n=2048 is RNI 4/5/16, NRI 16/0/0, and order-average 8/8/15; at n=8192 it is RNI 0/2/14, NRI 16/0/0, and order-average 1/1/13. At n=8192 the B/C patterns are 12 B-miss/C-cover, 2 both-miss, 2 both-cover (RNI), and 12/3/1 (order-average). At n=2048 the B-miss/C-cover and both-miss counts are 11/0 (RNI) and 7/1 (order-average). NRI has 16 A-cover/B-miss cells at each n, demonstrating the construction contrast. The original certificate-A results are separately reproduced (RNI 4/16 -> 0/16; order-average 8/16 -> 2/16); matched order-average A at n=8192 is 1/16, not the original 2/16, because the streams differ. Complete pairwise counts and widths are descriptive, not causal attributions.

6. **Paper and governance.** Abstract/introduction/framework/experiments/
   conclusion remove causal attribution and name the three constructions in the
   detection table. SPEC v1.8, criterion-map section 15, 23 new tests (429 total),
   and this frozen provenance record document the supersession. R22 has no page
   cap by explicit user decision; final paper: 105 pages, 6 figures,
   115 cited references. Date: 23 November 2026.

7. **Independent-review hardening.** A read-only implementation review confirmed
   the A/B/C formulas and RNG order. Its governance findings were then closed:
   the inherited 0.05 empirical-error gate was removed (finite/nonnegative checks
   only); native float-output hashes were replaced by exact integer-draw and
   platform-independent mask hashes; top-level/table and C-alias consistency is
   validated; joint/matched bootstrap counts must agree; synthetic-array tests
   independently verify B and non-full masks; and "all channels" is qualified as
   all data-estimated channels with the registered structural goal fixed. A final
   audit pass additionally records the actual execution RNG-index vectors (not
   merely their terminal 0/1 draws) and binds detection A to the independently
   stored R19 cell plug-in share. These changes do not alter A/B/C bounds, the
   formal certificate, or R21 artifacts.

## Evidence boundaries (unchanged)

- Internal joint-log concept validation and internal descriptive finite-sample
  studies on one registered instance; not external construct validation, power,
  statistical consistency, universal coverage, or general MaxEnt-IRL solving.
- Matched method contrasts are not formal bias decomposition or causal
  attribution. Exact-truth anchors are evaluation-only; no truth enters a
  deployable decision.
- T7 INCONCLUSIVE; X5-c MODEL_SENSITIVE; paired audit POST_HOC_PASS; failed and
  post hoc criteria retained. Legacy a_org/combined a_via/Bundle remain legacy.
- External protocol DESIGN_FROZEN_UNEXECUTED; domain SESOI/power, independent
  substrate execution, independent-investigator replication, expert/downstream
  criteria, selector-conditional DEL-1, more SCMs, Lean, Chinese synchronization,
  and version DOI remain outstanding.
- The three unavailable R14 run-time SPEC byte snapshots remain unrecovered.
- The two validation environments differ in thread/hash settings on the same
  platform, not cross-platform independent replication.
- This batch creates immutable tag `v1.5-r22`; no formal Release or version DOI
  is claimed. Historical concept DOI 10.5281/zenodo.23608751 does not cover R22.

## Acceptance

`tools/make_r22_validation.py` validates the public content commit from clean
worktrees in two environments: 429/429 tests, R14--R21 read-only/stable replays,
R22 joint-audit and full matched-grid detection-study replays, read-only
R17-native/R18 integrity/anchors, original-environment R17-native/R18 numerical
checks, and an independent clean LaTeX build with text equality, 115 references,
6 figures, and embedded Unicode-mapped fonts. There is no page cap; all other
quality gates remain fail-closed. `validation.json` records the exact content
commit/tree, both environments, and scientific-source hashes. Final public
commit/tag and online verification are in
`docs/R22paper_GitHub_Gitee发布说明_v1.md` (development repository).
