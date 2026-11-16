# R14 complete LaTeX submission manifest

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
- `refs.bib` — complete bibliography, including all R14 direct-comparison entries.
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

- `sim/analysis_r14_math.json` — counterexamples and optimization certificates.
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

These evidence packages do not constitute external validation. The R14 source
synchronization is public on the repository `main` branches; the exact
development-source commit and fresh-history snapshot relationship are recorded
in `RELEASE_NOTES.md`. An immutable R14 release tag/version DOI and the
external-substrate power/validation program remain incomplete; the historical
concept DOI does not cover them.
