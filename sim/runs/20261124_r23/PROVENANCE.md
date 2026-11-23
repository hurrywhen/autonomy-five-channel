# R23 editorial-finalization provenance (2026-11-24)

## Scope and baseline

R22 was assessed as ready for acceptance with editorial finishing only. Its
public baseline is commit `c8e691be98a9516128b08d9e601055207c72a4b2`, immutable
tag `v1.5-r22`, 105 pages, with 429/429 tests and a completed two-environment
full numerical validation.

R23 makes **no scientific or numerical change**. It does not alter a theorem,
proof, definition, estimand, certificate schema, detection rule, A/B/C interval
construction, estimator, test, simulation input, numerical output, negative
control, or R11--R22 artifact. No new theory or simulation is necessary for the
reviewer's editorial recommendations.

## Editorial changes

1. **Explicit article positioning and external-validity boundary.** The
   abstract, introduction, and conclusion now call the contribution a
   conditional conceptual and mathematical audit framework with executable
   model checks, not a deployment-ready tool or cross-substrate measurement
   standard. They explicitly disclaim cross-substrate construct validity,
   universal interval coverage, statistical consistency, and external
   validation of real-LLM or human autonomy. Independent substrates,
   domain-justified SESOI/power, external execution, and
   independent-investigator replication remain outstanding.

2. **Noncausal A/B/C interpretation retained.** B/C remains a matched-
   replicate, matched-percentile channel-propagation contrast; A/B an interval-
   construction contrast; A/C a mixed comparison. B-miss/C-cover is not a
   conditional-design effect and both-miss is not a plug-in-bias effect.
   Source-share bias, other-channel estimation error/covariance, and interval
   construction remain possible sources. Matched A does not replace original
   certificate A; envelope containment is not statistical coverage/recovery.
   The current A/B/C formulas, table, and bias/RMSE results remain in the
   article unchanged in substance.

3. **Revision history moved out of scientific exposition.** The article now
   states current rules and findings directly instead of recounting R17--R22
   repair sequences. The complete R11--R22 history remains in
   `sim/CRITERION_VERSION_MAP.md`, public `RELEASE_NOTES.md`, and all read-only
   historical provenance/failure records.

4. **Numerical details moved to public technical supplement.** The old
   estimator two-path table, historical quantitative anchors, log-domain
   bookkeeping shares, older weight-battery details, X5-c protocol detail, and
   R18 numerical-failure explanation are preserved in
   `sim/runs/20261124_r23/TECHNICAL_SUPPLEMENT.md`. The article retains the
   current native audit, detection and matched-method tables, multi-seed
   recoverability table, core counterexamples, negative controls, and evidence
   limitations.

5. **No formatting contraction.** Geometry, font size, bibliography size, and
   figure scaling were not used to reduce pages. Reduction comes from rewriting
   and relocating content. The clean build is 101 pages rather than 105, with 6
   figures and 115 cited references.

## Validation design

`tools/make_r23_validation.py` checks the R23 public content commit from clean
worktrees in two same-platform thread/hash environments. It runs all 429 tests
and stable R14--R22 joint/statistical replays, and performs read-only structural
and anchor validation of the frozen R17-native, R18, R19 sampling, and
R20--R22 detection artifacts. It also compares the content commit against the
R22 public baseline and fails if any file under `sim/src/`, `sim/tests/`, any
`sim/analysis_*.py` or `sim/analysis_*.json`, or any historical run directory
through R22 changed.

The expensive R21/R22 full-grid recomputations are **not represented as newly
rerun in R23**. Their completed R22 two-environment records are inherited and
checked for presence; R23 instead validates their frozen artifacts read-only
because neither code nor data changed. This is not cross-platform or
independent-investigator replication.

The paper is rebuilt independently in `/tmp/opencode`: extracted text must match
the submitted PDF; pages must be fewer than 105; all 115 bibliography entries
must be cited; 6 figures, embedded Unicode-mapped fonts, Ghostscript page
parsing, metadata, no undefined references/citations, no oversized floats, and
maximum overfull at most 10 pt are required. The source scan also rejects the
withdrawn causal-attribution phrases.

## Publication boundary

The present revision is to be frozen by immutable tag `v1.6-r23`; no formal
Release or version DOI is claimed by the source edit. A version DOI requires
actual Zenodo archiving of that tag and remains pending. Historical concept DOI
`10.5281/zenodo.23608751` does not cover R23. T7 remains INCONCLUSIVE and X5-c
MODEL_SENSITIVE. Selector-conditional DEL-1, independent substrates, external
SESOI/power, independent-investigator replication, general MaxEnt-IRL,
deployment middleware, Lean, Chinese synchronization, and the three unavailable
R14 run-time SPEC byte snapshots remain outstanding. Internal node-b hot backup
is not asserted to be refreshed.
