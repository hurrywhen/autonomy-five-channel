# autonomy-five-channel

**Autonomy as Determination by One's Own Normative Structure: A White-Box-First Five-Channel Audit Framework with Axioms and Conditional Theorems**

Wen Hu<sup>1,2</sup> and Gong Zhang<sup>1,2</sup> — <sup>1</sup>College of Electronic and Information Engineering, Nanjing University of Aeronautics and Astronautics, Nanjing, China; <sup>2</sup>Jiangsu Yunhefeng Intelligent Technology Co., Ltd., Nanjing, China — `huwen@nuaa.edu.cn`; `gzhang@nuaa.edu.cn`

**R15 public source synchronization, 2026-11-17.** Paper: [`latex/main.pdf`](latex/main.pdf) (**104 pages**, **6 figures**, **113 cited references**) · [Gitee mirror](https://gitee.com/jiangsu-yunhefeng-intelligent/autonomy-five-channel) · [Release and provenance notes](RELEASE_NOTES.md)

[![Historical Zenodo concept DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23608751.svg)](https://doi.org/10.5281/zenodo.23608751) — this DOI archives the historical `v1.0-r10` release. **No immutable R15 tag or R15 version DOI is claimed by this main-branch synchronization.**

---

## What R15 changes

R15 is a substantive reviewer-counterexample revision, not a cosmetic refresh.

- **Execution normalization:** empowerment now uses exactly \(n\) actions, \(I(A_{t:t+n-1};O_{t+n}\mid S_t)\), divided by \(n\log|\mathcal A|\). The R14 two-bit indexing counterexample is an automatic regression. Max attainment requires an explicitly compact certified input set; Blahut–Arimoto is restricted to an explicit finite discrete memoryless channel. Zero execution can mean repertoire collapse **or action–environment decoupling**.
- **T2 compatibility:** the no-surgery/full-mediation/honesty iff and four-track criterion are withdrawn. Compatibility is componentwise non-decrease, with explicit sufficient structural conditions and a before/after \(F_{\mathrm{src}}+F_{\mathrm{oth}}>0\) premise. An unchanged baseline \(\Lambda=0.5\) can be compatible; honest information can still reduce goal alignment by moving \(\operatorname{Fix}\); zero denominators are undefined. Blindness claims are existence witnesses, not universal consequences of an unchanged observation kernel.
- **Random-source construct:** L0 is explicitly **internal-causal autonomy only**. At L1+, the registered chain \(R\to N\to I\), with \(N=(G,B,M)\), separates innovation, normative, and external directed flows. A pure independent-register policy has zero, not maximal, normative source attribution.
- **Goal identification:** structural white-box \(U_{\mathrm{eff}}\) reads can yield point values under fixed-point and metric premises. Behavior-based MaxEnt-IRL generally yields an admissible set and an induced \(A_{\mathrm{goal}}\) interval, not a point. Fixed-point theorem and measurable-selection assumptions are stated separately. General additive-shift invariance is withdrawn; only a joint domain translation with equivariant dynamics/metric is admitted.
- **State versus readiness:** current resource viability \(V_{\mathrm{state}}\), present autonomy \(A^{\mathrm{state}}\), defense readiness \(R_{\mathrm{def}}\), and optional resilience \(A^{\mathrm{res}}\) are separate. Zero repair capacity does not automatically zero present autonomy.
- **Proof repairs:** C2 distinguishes \(s>s_c\) after attack removal from \(s>\delta+s_c\) under persistent attack. Route B uses quotient-cone pointedness and explicit covector normalization.
- **Mandatory output:** actual `produce_r15_certificate` and fail-closed `write_r15_certificate` paths carry layer/construct scope, \(A^{\mathrm{state}}\), \(V_{\mathrm{state}}\), \(R_{\mathrm{def}}\), surgery history, \(\Lambda\) plus `DEFINED`/`NOT_APPLICABLE`/`UNKNOWN` status, source registration, and an evidence ceiling. Unknown provenance caps the grade at `LIMITED`; N/A and unknown are distinct; no score is an integrity certificate.
- **Literature and reporting:** substantive comparisons with Ingel et al. (2022), Albantakis (2021), and Jung–Polani–Stone (2011); explicit classical-precursor/novelty table; corrected bibliography/figure counts and reporting details.

## Evidence status, not a headline tally

| Evidence package | Current interpretation |
|---|---|
| R15 mathematical guards | **194/194 tests pass**, including 14 new deterministic reviewer counterexamples; mathematical/implementation checks, not external validation |
| Historical 4,620-run ENV-0 archive | Read-only legacy implementation and same-model checks. Its `a_org` is internal-causal and combined `a_via` is a resilience marker; these are not silently re-signed as R15 values |
| R14 pooled/stratified X5-c | Current-source read-only replays pass; \(D_{noise}=0.089799622>0.01\), so point readings remain **MODEL_SENSITIVE** |
| R15 X5-c paired cross-check | Shared \((X,Z,J)\) uses per-context paired-difference SE; both pass the post hoc inherited tolerance. Status `POST_HOC_PASS`, not a preregistered CONFIRMED criterion; R14's unpaired `combined_se` is retained but not used for R15 inference |
| R15 weight/statistical audit | Read-only Kendall \(\tau_b\) with explicit ties and scenario strata; overall range \([0.927595,1]\), but no uniform \(0.93\) scenario-level floor |
| C0-CF-v2 | Same-environment model construction; custom L1 weights \((4/15,4/15,4/15,1/5)\) and equal-weight sensitivity are both reported |
| T7 / DEL-1 | Remains **INCONCLUSIVE** pending a selector-conditional estimator and nondegenerate bracket |
| External validation | Not completed: no independent-substrate validation, external SESOI/power analysis, external expert validation, or Lean certification is claimed |

Failed criteria, post hoc replacements, unrun programs, legacy markers, unavailable historical SPEC bytes, and the invalid first C0 fixture remain visible. Historical verdicts are not rewritten. The 480,000 X5-c evaluations use 120,000 base \((X,U)\) draws with common random numbers across arms within each noise/time cell.

## Repository layout

```text
latex/                     complete paper source, 113-entry bibliography,
                           local Unicode map, submission manifest, 5 external
                           PDF figures + 1 TikZ figure, built 104-page PDF
sim/
  src/autonomy_sim/        ENV-0, estimators, SCMs, R15 source/goal/state/output guards
  tests/                   194 unit/integration/regression tests
  run_matrix.py            historical campaign runner
  run_x5c_r14.py           pooled X5-c runner and read-only --check replay
  run_x5c_r14_stratified.py time-stratified X5-c runner and replay
  run_c0cf_r14.py          nondegenerate C0-CF-v2 runner and replay
  analysis_r14_math.*      R14 counterexamples and optimization certificates
  analysis_r15_statistics.* Kendall tau-b, ties and scenario reporting audit
  analysis_r15_x5c_paired.* paired per-context cross-check standard errors
  SPEC_*.md                current specifications and R14 preservation copy
  CRITERION_VERSION_MAP.md R11–R15 supersession and evidence boundaries
  runs/20261017_full/      read-only historical 4,620-run campaign archive
  runs/20261102_r11/del1/  separate 30-run R11 replay summary (3 files)
  runs/20261116_r14/       X5-c, C0-CF-v2, superseded/failed records, provenance
  runs/20261117_r15/       clean-worktree source-commit validation manifest
refs/manifest.md           graded bibliography verification ledger;
                           third-party PDFs are not redistributed
tools/                     source-package and frozen-validation scripts
```

## Requirements

- Python ≥ 3.10 with `numpy` and `matplotlib` (developed on Python 3.12; see `sim/requirements.txt`)
- A TeX distribution with `pdflatex` and `bibtex`

## Reproduction

```bash
# 1. Run all 194 tests
cd sim
python3 -m unittest discover -s tests -q

# 2. Read-only R14 evidence replays
python3 run_x5c_r14.py --out runs/20261116_r14/x5c --check
python3 run_x5c_r14_stratified.py --out runs/20261116_r14/x5c_stratified --check
python3 run_c0cf_r14.py --out runs/20261116_r14/c0cf_v2 --check

# 3. Read-only R15 reporting audits
python3 analysis_r15_statistics.py --check
python3 analysis_r15_x5c_paired.py --check

# 4. Rebuild the complete paper
cd ../latex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

For a clean-source-commit validation, create a clean worktree at the R15 content commit recorded in `RELEASE_NOTES.md` and run `tools/make_r15_validation.py`. It writes only `sim/runs/20261117_r15/validation.json`, uses a separate temporary LaTeX build directory, and does not modify historical evidence.

The R14 replays and R15 checks use **current** source and compare against saved outputs; they are not represented as execution of earlier source bytes or recovery of unavailable historical SPEC snapshots. See [`sim/runs/20261116_r14/PROVENANCE.md`](sim/runs/20261116_r14/PROVENANCE.md) and [`sim/runs/20261117_r15/PROVENANCE.md`](sim/runs/20261117_r15/PROVENANCE.md).

The complete LaTeX tree is required; uploading only `main.tex` is not a valid source submission. See [`latex/SUBMISSION_MANIFEST.md`](latex/SUBMISSION_MANIFEST.md).

## Public-snapshot boundary

This repository is a fresh-history public snapshot of the authors' development work. It intentionally excludes third-party bibliographic PDFs and internal review archives. The R15 development-source commit and snapshot relationship are recorded in [`RELEASE_NOTES.md`](RELEASE_NOTES.md). Existing tags and the Zenodo concept DOI remain historical and are not rewritten.

## Licenses

- **Code** (`sim/`, `tools/`): MIT — [LICENSE](LICENSE)
- **Paper text, figures, data, and documentation**: CC BY 4.0 — [CONTENT-LICENSE.md](CONTENT-LICENSE.md)

## Citation

```bibtex
@misc{hu_zhang2026autonomy_r15,
  title  = {Autonomy as Determination by One's Own Normative Structure:
            A White-Box-First Five-Channel Audit Framework with Axioms
            and Conditional Theorems},
  author = {Hu, Wen and Zhang, Gong},
  year   = {2026},
  note   = {Author manuscript; R15 public source synchronization,
            17 November 2026, 104 pages; no R15 version DOI},
  url    = {https://github.com/hurrywhen/autonomy-five-channel}
}
```

Machine-readable metadata: [`CITATION.cff`](CITATION.cff). For the historical software/data archive only, see Zenodo concept DOI [10.5281/zenodo.23608751](https://doi.org/10.5281/zenodo.23608751).
