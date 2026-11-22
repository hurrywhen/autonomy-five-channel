# R20 complete LaTeX submission manifest

The submission unit is the complete `latex/` source tree, **not** only
`main.tex`. The top-level file deliberately uses `\input` and `\bibliography`;
uploading it alone cannot reproduce the paper.

## Required source files

- `main.tex` — document class, macros, title/abstract/front matter and build order.
- `sections/sec_intro.tex`
- `related_work.tex`
- `sections/sec_framework.tex`
- `sections/sec_axioms.tex`
- `sections/sec_representation.tex`
- `sections/sec_theorems.tex`
- `sections/sec_identifiability.tex`
- `sections/sec_experiments.tex`
- `sections/sec_discussion.tex`
- `sections/sec_conclusion.tex`
- `appendix.tex`
- `refs.bib` — 115 cited entries, including the direct autonomy-measurement,
  Shapley-attribution, and PID precursors used in the current text.
- `glyphtounicode.tex` — Unicode mapping used by `\pdfgentounicode`.
- `figures/fig_ews_c1.pdf`
- `figures/fig_t6_blindzone.pdf`
- `figures/fig_t7_delegation.pdf`
- `figures/fig_ahi.pdf`
- `figures/fig_p3_gate_exec.pdf`
- `main.bbl` after the BibTeX build (regenerate from `refs.bib`; do not edit it
  manually). Keep it in arXiv packages that run pdfLaTeX without BibTeX.

The local draft uses `article` when `sn-jnl.cls` is absent. A journal build
that selects `sn-jnl.cls` must also supply that class and its publisher-owned
dependencies; those are not relicensed as part of this source tree.

## Reproducible build

From `latex/`:

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

For a clean-source check, copy the required files to a new empty directory,
run the same sequence there, and compare the resulting PDF with `main.pdf`.
Also check for undefined references, overfull boxes, floats too large for a
page, missing fonts, and text-extraction errors. A top-level-only upload is a
known incomplete submission configuration and must fail review.

## Evidence files referenced by the paper (outside `latex/`)

- `sim/analysis_r14_math.json` — R14 counterexamples and optimization certificates.
- `sim/tests/test_r15_reviewer_counterexamples.py` — 14 R15 definition, construct,
  compatibility, identification, proof, output and statistical negative controls.
- `sim/src/autonomy_sim/r15_guards.py` — normative-source, goal-interval,
  state/defense and mandatory-output implementations.
- `sim/analysis_r15_statistics.json` — new read-only Kendall tau-b and tie/scenario
  reporting audit; historical analysis JSON files are not overwritten.
- `sim/analysis_r15_x5c_paired.json` — paired per-context X5-c cross-check SEs;
  R14's saved unpaired `combined_se` is retained but superseded for R15 reporting.
- `sim/src/autonomy_sim/source_attribution.py` and
  `sim/analysis_r16_source_attribution.{py,json}` — exact ordered-DI, OR and T=2
  closed-loop attribution guards with independent analytic anchors.
- `sim/tests/test_r16_source_attribution.py`,
  `sim/tests/test_r16_certificate_guards.py`, and
  `sim/tests/test_r16_analysis_replay.py` — R16 mathematical and fail-closed controls.
- `sim/src/autonomy_sim/open_loop_execution.py` and
  `sim/tests/test_r17_open_loop_execution.py` — precommitted open-loop execution
  repair and feedback-copy counterexample.
- `sim/src/autonomy_sim/formation_audit.py`, `sim/src/autonomy_sim/r17_guards.py`,
  and `sim/tests/test_r17_formation_certificate.py` — co-primary current/history
  profiles, fixed-point implant witness, and Lambda time-origin certificate guards.
- `sim/src/autonomy_sim/native_benchmark.py`,
  `sim/analysis_r17_native_benchmark.{py,json}`, and
  `sim/tests/test_r17_native_benchmark.py` — R17-native multi-step
  internal concept-validation benchmark (read-only; superseded by the R18
  joint-log audit, not rewritten).
- `sim/src/autonomy_sim/r18_guards.py` and
  `sim/tests/test_r18_certificate_profile.py` — R18 full-profile certificate
  schema with enforced order/semantic sensitivity flags and composite range.
- `sim/src/autonomy_sim/native_joint_audit.py`,
  `sim/analysis_r18_native_joint_audit.{py,json}`, and
  `sim/tests/test_r18_native_joint_audit.py` — R18 single-SCM/single-log-schema
  joint-batch end-to-end internal audit (separate precommitted open-loop
  execution stream); exact convention composites and sampling agreement.
- `sim/tests/test_r18_open_loop_conventions.py` — terminal-observation vs
  observation-sequence capacity and support-relative zero-MI quantifier guards.
- `sim/src/autonomy_sim/r19_guards.py` and
  `sim/tests/test_r19_certificate_schema.py` — R19 layer-aware certificate
  schema: L0 internal-causal attribution, four channel states
  (DEFINED/INTERVAL/UNKNOWN/NOT_APPLICABLE), point/interval modes with composite
  interval propagation, IRL/thin-log/zero-entropy/zero-flow degradation, and
  decomposed order/semantic sensitivity with post hoc frozen thresholds.
- `sim/src/autonomy_sim/r19_joint_audit.py`,
  `sim/analysis_r19_joint_audit.{py,json}`, and
  `sim/tests/test_r19_joint_audit.py` — R19 joint-log audit: corrected
  state_autonomy_RNI, immutable-input evidence binding, canonicalized execution
  input, sampled surgery/decoupled negative controls, near-zero detection-limit
  semantics, and degradation-aware reflection estimation.
- `sim/analysis_r19_sampling_study.{py,json}` and
  `sim/tests/test_r19_sampling_study.py` — multi-seed (8 independent seeds)
  bias/coverage/width study; exact convention endpoints are model anchors, not
  finite-sample recoverability claims.
- `sim/tests/test_r19_numerical_reproducibility.py` — canonical capacity-input
  rule, perturbation stability, and declared per-field replay tolerances.
- `sim/runs/20261122_r19/REPLAY_FAILURE_R18.md` — retained record of the R18
  cross-environment replay failure and its R19 repair (not replaced).
- `sim/src/autonomy_sim/r20_detection.py` and
  `sim/tests/test_r20_detection_rule.py` — R20 declared data-driven near-zero
  detection rule: basic bias-corrected bootstrap interval, three-state
  classification (below/above/indeterminate), no truth parameter in the
  deployable decision, oracle-assisted fixture rule explicitly labeled.
- `sim/src/autonomy_sim/r20_guards.py` and
  `sim/tests/test_r20_certificate_schema.py` — R20 detection-complete
  certificate schema: per-convention detection reports inside the certificate,
  three-state interval sensitivity (confirmed/indeterminate/not-evaluable,
  never midpoint agreement), interval kinds, real interval propagation,
  diagnostic plug-in separation, fail-closed governance.
- `sim/src/autonomy_sim/r20_joint_audit.py`,
  `sim/analysis_r20_joint_audit.{py,json}`, and
  `sim/tests/test_r20_joint_audit.py` — R20 joint-log audit: INTERVAL-valued
  sampled baseline certificate (no point export), data-driven detection
  reports with oracle evaluation at artifact level only, diagnostic
  five-channel plug-in field, sampled surgery/decoupled controls.
- `sim/analysis_r20_detection_study.{py,json}` and
  `sim/tests/test_r20_detection_study.py` — predeclared 16-seed x {2048,8192}
  detection-rule misclassification/coverage study (descriptive; oracle truth
  used for evaluation labeling only).
- `sim/analysis_r17_weight_regions.{py,json}` and
  `sim/tests/test_r17_weight_regions.py` — exact closed-simplex log bounds and
  pairwise damage halfspaces (an exact weight-sensitivity characterization, not
  robustness evidence) for the geometric bookkeeping aggregate.
- `sim/EXTERNAL_VALIDATION_PROTOCOL.md` — design-frozen but unexecuted external
  comparison protocol; engineering equivalence/non-inferiority margins and the
  TOST decision rule are frozen, domain SESOI/power and outcome registration
  remain pending.
- `sim/runs/20261117_r15/`, `sim/runs/20261117_r16/`,
  `sim/runs/20261119_r17/`, `sim/runs/20261121_r18/`, and
  `sim/runs/20261122_r19/` — preserved historical clean-worktree validations;
  not R20 validation.
- `sim/runs/20261122_r20/` — current two-environment clean-worktree provenance
  and exact source-commit replay manifest for the immutable tag `v1.3-r20`;
  not a version DOI or external validation.
- `tools/make_r20_validation.py` — current two-environment clean-worktree
  validator; historical R15/R16/R17/R18/R19 validators and validations are
  retained unchanged.
- `sim/runs/20261116_r14/x5c_stratified/` — canonical time-stratified X5-c
  preregistration, manifest, results, verdicts and analysis.
- `sim/runs/20261116_r14/c0cf_v2/` — same-environment C0-CF evidence package.
- `sim/runs/20261116_r14/x5c/` — retained pooled first X5-c record.
- `sim/runs/20261116_r14/c0cf_failed_initial/` — retained failed first C0-CF
  serialization attempt.
- `sim/CRITERION_VERSION_MAP.md` — criterion supersession and evidence boundaries.
- `sim/SPEC_experiments_v1.0_snapshot.md` — current preservation copy (not an
  earlier preregistration file).
- `sim/runs/20261116_r14/PROVENANCE.md` — run-time SPEC hashes, unavailable
  earlier snapshots, post-run changes, common-random-number accounting and
  remaining release blockers.
- `sim/runs/20261116_r14/c0cf/SUPERSEDED.md` — why the first C0-CF fixture is
  invalid for nondegenerate composite separation.

These evidence packages do not constitute external validation.
`RELEASE_NOTES.md` identifies the development-source commit and the
corresponding fresh-history public commit on the repository `main` branches.
Historical `a_org` and combined-gate values are not silently re-signed as
current normative-source or present-state values. This revision is frozen by
the immutable tag `v1.3-r20` with a two-environment clean-worktree replay
manifest (`sim/runs/20261122_r20/validation.json`); the earlier tags
`v1.1-r18` and `v1.2-r19` are retained and the recorded R18 cross-environment
replay failure is preserved. A version DOI requires Zenodo archiving of the
current tag and is not yet minted, and the external-substrate power/validation
program remains incomplete. The historical concept DOI does not cover them.
