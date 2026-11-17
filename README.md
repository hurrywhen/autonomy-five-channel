# autonomy-five-channel

**Autonomy as Determination by One's Own Normative Structure: A White-Box-First Five-Channel Audit Framework with Axioms and Conditional Theorems**

Wen Hu<sup>1,2</sup> and Gong Zhang<sup>1,2</sup> — <sup>1</sup>College of Electronic and Information Engineering, Nanjing University of Aeronautics and Astronautics, Nanjing, China; <sup>2</sup>Jiangsu Yunhefeng Intelligent Technology Co., Ltd., Nanjing, China — `huwen@nuaa.edu.cn`; `gzhang@nuaa.edu.cn`

**R16 public source synchronization, 2026-11-17.** Paper: [`latex/main.pdf`](latex/main.pdf) (**104 pages**, **6 figures**, **115 cited references**) · [Gitee mirror](https://gitee.com/jiangsu-yunhefeng-intelligent/autonomy-five-channel) · [Release and provenance notes](RELEASE_NOTES.md)

[![Historical Zenodo concept DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23608751.svg)](https://doi.org/10.5281/zenodo.23608751) — this DOI archives the historical `v1.0-r10` release. **No immutable R16 tag or R16 version DOI is claimed by this main-branch synchronization.**

---

## What R16 changes

R16 closes the R15 re-review without rewriting historical evidence.

- **Ordered source attribution:** the L1+ \(R\to N\to I\) decomposition is explicitly an **ordered residual-attribution axiom**, not a unique causal decomposition. Reports require reverse NRI and an I-last two-order Shapley-style sensitivity descriptor when \(R,N\) are nondegenerate. The \(N/R/I\) semantic partition is registered before scoring; alternative partitions are sensitivity arms. PID remains a comparator, not a silent replacement estimand. Pure-random zero claims are RNI-specific: with \(N=R\) and \(A=R\), the RNI normative share is 0 but NRI is 1.
- **Executable order and closed-loop guards:** the one-step OR law gives normative shares `0.6163114534` (RNI), `0.3836885466` (NRI), and `0.5` (order average). Exact \(T=2\) enumeration covers pure-random, pure-normative, and mixed feedback policies, joint-DI chain identities, mediated external influence, and direct bypass. The mixed XOR model changes its ordered normative share from 1 to 0; the I-last average is 0.5.
- **Route B scaling:** homogeneity now explicitly gives \(\varphi(z+st')=\varphi(z)+t'\) before \(q=st'\) yields \(\varphi(z+q)=\varphi(z)+q/s\). The regression derives this from the actual homogeneous function rather than restating the incorrect unscaled intermediate equation.
- **T2 interval and finite-value discipline:** identified-goal intervals use endpoint order, \(l_1\ge l_0\) **and** \(u_1\ge u_0\). Stronger cross-world guarantees require \(\ell_1\ge u_0\) or a registered coupling. NaN and either infinity fail closed, including NaN→NaN.
- **Certificate schema and evidence axes:** `registration_completeness` is distinct from `mechanism_evidence`. Complete registration without an SCM audit is `REGISTERED_COMPLETE`, not `SCM_AUDITED`. R16 certificates require schema/origin/goal/readiness modes and L1/L2 model/evidence hashes; legacy Bundle values and forged metadata are rejected. Hashes bind declared artifacts, not external truth.
- **Numerical replay:** statuses, seeds, counts, hashes, JSON types, and object structure remain exact. Only floating-point leaves use relative/absolute \(10^{-12}\) tolerances, with the maximum difference reported; non-finite or out-of-tolerance values still fail.
- **Common external protocol:** `sim/EXTERNAL_VALIDATION_PROTOCOL.md` design-freezes, but does not execute, comparisons on Ingel's RL environments and Albantakis's automata. It includes RNI/NRI/Shapley, next-state PID (BROJA primary, SxPID sensitivity), Albantakis's candidates, empowerment, reduced models, and intervention-attribution balanced accuracy. External SESOI, power, outcome registration, and results remain pending.
- **Standalone manuscript:** abstract and main text remove revision-history narration while preserving legacy evidence boundaries. Discussion distinguishes UNKNOWN from N/A, and T8 separates present \(A^{\mathrm{state}}\) from resilience \(A^{\mathrm{res}}\). The paper remains 104 pages after compression.

The R15 execution-horizon, compatibility, goal-identification, state/readiness, C2, and statistical repairs remain in force; see the historical R15 section in `RELEASE_NOTES.md`.

## Evidence status, not a headline tally

| Evidence package | Current interpretation |
|---|---|
| Mathematical and implementation guards | **230/230 tests pass**, including exact source-attribution, certificate, interval, non-finite, and replay controls; not external validation |
| R16 source-attribution audit | OR, duplicate-register order control, three exact \(T=2\) policies, mediation and direct-bypass witnesses; independent closed-form and atom-wise log-ratio checks |
| Historical 4,620-run ENV-0 archive | Read-only legacy implementation and same-model checks. Its `a_org` is internal-causal and combined `a_via` is a resilience marker; neither is silently re-signed as a current value |
| R14 pooled/stratified X5-c | Current-source read-only replays pass; \(D_{noise}=0.089799622>0.01\), so point readings remain **MODEL_SENSITIVE** |
| R15 X5-c paired cross-check | Shared \((X,Z,J)\) uses paired-difference SE; `POST_HOC_PASS`, not preregistered CONFIRMED. Replay comparison tolerates only floating-point round-off |
| R15 weight/statistical audit | Read-only Kendall \(\tau_b\) with ties and scenario strata; overall range \([0.927595,1]\), but no uniform \(0.93\) scenario-level floor |
| C0-CF-v2 | Same-environment model construction; custom L1 weights and equal-weight sensitivity are both reported |
| T7 / DEL-1 | **INCONCLUSIVE** pending a selector-conditional estimator and nondegenerate bracket |
| External protocol | **DESIGN_FROZEN_UNEXECUTED**; no external SESOI/power, independent-substrate result, expert validation, or Lean certification is claimed |

Failed criteria, post hoc replacements, unrun programs, legacy markers, unavailable historical SPEC bytes, and the invalid first C0 fixture remain visible. Historical verdicts are not rewritten. The 480,000 X5-c evaluations use 120,000 base \((X,U)\) draws with common random numbers across arms within each noise/time cell.

## Repository layout

```text
latex/                     complete paper source, 115-entry bibliography,
                           Unicode map, submission manifest, 5 external PDF
                           figures + 1 TikZ figure, built 104-page PDF
sim/
  src/autonomy_sim/        ENV-0, estimators, SCMs, source/certificate guards
  tests/                   230 unit/integration/regression tests
  analysis_r16_source_attribution.* exact OR and T=2 attribution audit
  analysis_r15_statistics.* Kendall tau-b, ties and scenario reporting audit
  analysis_r15_x5c_paired.* paired cross-check SEs and tolerant replay
  EXTERNAL_VALIDATION_PROTOCOL.md design-frozen, unexecuted external protocol
  SPEC_*.md                current specifications and R14 preservation copy
  CRITERION_VERSION_MAP.md R11–R16 supersession and evidence boundaries
  runs/20261017_full/      read-only historical 4,620-run campaign archive
  runs/20261102_r11/del1/  separate 30-run R11 replay summary
  runs/20261116_r14/       X5-c, C0-CF-v2, superseded/failed records
  runs/20261117_r15/       preserved R15 validation
  runs/20261117_r16/       current clean-worktree validation and provenance
refs/manifest.md           graded bibliography verification ledger;
                           third-party PDFs are not redistributed
tools/                     source-package and frozen-validation scripts
```

## Requirements

- Python ≥ 3.10 with `numpy` and `matplotlib` (developed on Python 3.12; see `sim/requirements.txt`)
- A TeX distribution with `pdflatex` and `bibtex`

## Reproduction

```bash
# 1. Run all 230 tests
cd sim
python3 -m unittest discover -s tests -q

# 2. Read-only R14 evidence replays
python3 run_x5c_r14.py --out runs/20261116_r14/x5c --check
python3 run_x5c_r14_stratified.py --out runs/20261116_r14/x5c_stratified --check
python3 run_c0cf_r14.py --out runs/20261116_r14/c0cf_v2 --check

# 3. Read-only R15/R16 reporting and analytic audits
python3 analysis_r15_statistics.py --check
python3 analysis_r15_x5c_paired.py --check
python3 analysis_r16_source_attribution.py --check

# 4. Rebuild the complete paper
cd ../latex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

For clean-source-commit validation, create a clean worktree at the R16 content commit recorded in `RELEASE_NOTES.md` and run `tools/make_r16_validation.py`. It writes only `sim/runs/20261117_r16/validation.json`, uses a separate temporary LaTeX build directory, and does not modify historical evidence.

The R14 replays and R15/R16 checks use **current** source and compare against saved outputs or independent analytic anchors; they are not represented as execution of earlier source bytes or recovery of unavailable historical SPEC snapshots. See the R14/R15/R16 `PROVENANCE.md` files and `sim/CRITERION_VERSION_MAP.md`.

The complete LaTeX tree is required; uploading only `main.tex` is not a valid source submission. See [`latex/SUBMISSION_MANIFEST.md`](latex/SUBMISSION_MANIFEST.md).

## Public-snapshot boundary

This repository is a fresh-history public snapshot of the authors' development work. It intentionally excludes third-party bibliographic PDFs and internal review archives. Development-source and public-content commit relationships are recorded in [`RELEASE_NOTES.md`](RELEASE_NOTES.md). Existing tags and the Zenodo concept DOI remain historical and are not rewritten.

## Licenses

- **Code** (`sim/`, `tools/`): MIT — [LICENSE](LICENSE)
- **Paper text, figures, data, and documentation**: CC BY 4.0 — [CONTENT-LICENSE.md](CONTENT-LICENSE.md)

## Citation

```bibtex
@misc{hu_zhang2026autonomy_r16,
  title  = {Autonomy as Determination by One's Own Normative Structure:
            A White-Box-First Five-Channel Audit Framework with Axioms
            and Conditional Theorems},
  author = {Hu, Wen and Zhang, Gong},
  year   = {2026},
  note   = {Author manuscript; R16 public source synchronization,
            17 November 2026, 104 pages; no R16 version DOI},
  url    = {https://github.com/hurrywhen/autonomy-five-channel}
}
```

Machine-readable metadata: [`CITATION.cff`](CITATION.cff). For the historical software/data archive only, see Zenodo concept DOI [10.5281/zenodo.23608751](https://doi.org/10.5281/zenodo.23608751).
