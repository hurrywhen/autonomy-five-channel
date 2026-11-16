# autonomy-five-channel

**Autonomy as Determination by One's Own Normative Structure: A White-Box-First Five-Channel Audit Framework with Axioms and Conditional Theorems**

Wen Hu<sup>1,2</sup> and Gong Zhang<sup>1,2</sup> — <sup>1</sup>College of Electronic and Information Engineering, Nanjing University of Aeronautics and Astronautics, Nanjing, China; <sup>2</sup>Jiangsu Yunhefeng Intelligent Technology Co., Ltd., Nanjing, China — `huwen@nuaa.edu.cn`; `gzhang@nuaa.edu.cn`

**R14 public source synchronization, 2026-11-17.** Paper: [`latex/main.pdf`](latex/main.pdf) (**98 pages**, 5 figures) · [Gitee mirror](https://gitee.com/jiangsu-yunhefeng-intelligent/autonomy-five-channel) · [Release and provenance notes](RELEASE_NOTES.md)

[![Historical Zenodo concept DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23608751.svg)](https://doi.org/10.5281/zenodo.23608751) — this DOI archives the historical `v1.0-r10` release. **No immutable R14 tag or R14 version DOI is claimed by this main-branch synchronization.**

---

## What this is

A conceptual and mathematical, white-box-first audit schema for agent autonomy. Autonomy is operationalized relative to a fixed instantiation through five channels—direct-bypass origination, goal alignment, execution, epistemic accuracy, and reflection—behind a viability gate. The primary output is a **channel profile and evidence grade**, not a context-free scalar score. A conditional representation theorem characterizes the weighted-geometric aggregator only under explicitly stated calibration, invariance, and homogeneity commitments.

The R14 paper contains:

- corrected conditional results T1–T8 and C0–C2, with explicit counterexamples delimiting positivity, strict comparison, attack optimization, full-state script equivalence, and retention claims;
- a finite-discrete definition of the reflection ensemble and an explicit distinction between normalized coordinates and substantive ratio-scale interpretations;
- an endorsement factor \(\Lambda\) defined only by actual/no-surgery **output-law total variation** under abduction–action–prediction, separately from surgery history;
- nondegenerate identity/XOR structural models demonstrating passive non-identifiability, plus direct comparison with recent code-inspection, deployment-measurement, empowerment, evaluation, and auditability literature.

## Evidence status, not a headline tally

| Evidence package | Current interpretation |
|---|---|
| Historical 4,620-run ENV-0 archive | Definition checks, implementation replays, and same-model demonstrations; **not external construct validation** and not a count of confirmed theories |
| R14 analytic and numerical regressions | **180/180 tests pass**, including theorem counterexamples, optimization boundaries, SCM computations, report governance, and archive write protection |
| X5-c pooled and time-stratified SCM studies | Implementation criteria pass; \(D_{noise}=0.089799622>0.01\), so point readings are **MODEL_SENSITIVE** and reported as two-model bands |
| C0-CF-v2 | Nondegenerate same-environment construction with identical full-trajectory \((E^T,O^T,A^T)\) laws; \(A(Z_1)=0.8312378961\), \(A(Z_2)=0.7236346187\) |
| T7 / DEL-1 | Remains **INCONCLUSIVE** pending a selector-conditional estimator and nondegenerate bracket |
| External validation | Not completed: no independent-substrate validation, external SESOI/power analysis, or external expert validation is claimed |

Failed criteria, post hoc replacements, unrun programs, legacy markers, and the invalid first C0 fixture remain visible. Historical `law_level_lambda` values are **legacy markers**, not computations of the R14 counterfactual estimand. The current report generator separates historical verdicts from present mathematical and evidence status.

## Repository layout

```text
latex/                     complete paper source, bibliography, local Unicode map,
                           submission manifest, 5 figures, and built 98-page PDF
sim/
  src/autonomy_sim/        ENV-0, estimators, scenarios, aggregation, DI tools,
                           R14 attack optimization and counterfactual SCMs
  tests/                   180 unit/integration/regression tests
  run_matrix.py            historical campaign runner
  run_x5c_r14.py           pooled X5-c runner and read-only --check replay
  run_x5c_r14_stratified.py time-stratified X5-c runner and replay
  run_c0cf_r14.py          nondegenerate C0-CF-v2 runner and replay
  analysis_r14_math.*      counterexamples and optimization certificates
  SPEC_*.md                current specifications and preservation copy
  CRITERION_VERSION_MAP.md criterion supersession and evidence boundaries
  runs/20261017_full/      read-only historical 4,620-run campaign archive
  runs/20261102_r11/del1/  separate 30-run R11 replay summary (3 files)
  runs/20261116_r14/       X5-c, C0-CF-v2, superseded/failed records, provenance
refs/manifest.md           bibliography verification ledger (119 entries;
                           third-party PDFs are not redistributed)
tools/                     repository and source-package maintenance scripts
```

## Requirements

- Python ≥ 3.9 with `numpy` and `matplotlib` (developed on Python 3.12; see `sim/requirements.txt`)
- A TeX distribution with `pdflatex` and `bibtex`

## Reproduction

```bash
# 1. Run all 180 tests (about two minutes)
cd sim
python3 -m unittest discover -s tests -q

# 2. Read-only R14 evidence replays
python3 run_x5c_r14.py --out runs/20261116_r14/x5c --check
python3 run_x5c_r14_stratified.py --out runs/20261116_r14/x5c_stratified --check
python3 run_c0cf_r14.py --out runs/20261116_r14/c0cf_v2 --check

# 3. Rebuild the complete paper
cd ../latex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

The X5-c replays use the **current** source and compare against saved numerical outputs; they are not represented as execution of the earlier source bytes recorded in historical manifests. The stratified study has 480,000 cell/context evaluations but 120,000 base \(X,U\) draws: arms within each noise/time cell use common random numbers. See [`sim/runs/20261116_r14/PROVENANCE.md`](sim/runs/20261116_r14/PROVENANCE.md) for source evolution, three unavailable run-time SPEC snapshots, and post-run protocol changes.

The complete LaTeX tree is required; uploading only `main.tex` is not a valid source submission. See [`latex/SUBMISSION_MANIFEST.md`](latex/SUBMISSION_MANIFEST.md).

## Public-snapshot boundary

This repository is a fresh-history public snapshot of the authors' development work. It intentionally excludes third-party bibliographic PDFs and internal review archives. The R14 development-source commit and snapshot relationship are recorded in [`RELEASE_NOTES.md`](RELEASE_NOTES.md). Existing tags and the Zenodo concept DOI remain historical and are not rewritten.

## Licenses

- **Code** (`sim/`, `tools/`): MIT — [LICENSE](LICENSE)
- **Paper text, figures, data, and documentation**: CC BY 4.0 — [CONTENT-LICENSE.md](CONTENT-LICENSE.md)

## Citation

```bibtex
@misc{hu_zhang2026autonomy_r14,
  title  = {Autonomy as Determination by One's Own Normative Structure:
            A White-Box-First Five-Channel Audit Framework with Axioms
            and Conditional Theorems},
  author = {Hu, Wen and Zhang, Gong},
  year   = {2026},
  note   = {Author manuscript; R14 public source synchronization,
            17 November 2026, 98 pages; no R14 version DOI},
  url    = {https://github.com/hurrywhen/autonomy-five-channel}
}
```

Machine-readable metadata: [`CITATION.cff`](CITATION.cff). For the historical software/data archive only, see Zenodo concept DOI [10.5281/zenodo.23608751](https://doi.org/10.5281/zenodo.23608751).
