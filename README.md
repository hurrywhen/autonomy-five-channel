# autonomy-five-channel

**Autonomy as Determination by One's Own Normative Structure: A White-Box-First Five-Channel Audit Framework with Axioms, Theorems, and a Simulation Benchmark**

Wen Hu<sup>1,2</sup> — <sup>1</sup>College of Electronic and Information Engineering, Nanjing University of Aeronautics and Astronautics, Nanjing, China; <sup>2</sup>Jiangsu Yunhefeng Intelligent Technology Co., Ltd. — `huwen@nuaa.edu.cn`

Paper (PDF): [`latex/main.pdf`](latex/main.pdf) (87 pages, 5 figures) · arXiv: *number assigned after submission* · Gitee mirror: `https://gitee.com/jiangsu-yunhefeng-intelligent/autonomy-five-channel`

---

## What this is

A white-box-first audit framework for agent autonomy. Autonomy is operationalized as the degree to which behavior is determined by the agent's own normative structure (goals, beliefs, self-model), decomposed into **five channels** — origination, goal, execution, epistemic, reflection — **behind a viability gate**. The repository contains:

1. **The paper** (`latex/`): axioms AX0–AX8; a representation theorem (the aggregation of the five channels is characterized by the weighted geometric mean, via two independent derivations plus a minimal-axiom analysis); a theorem suite (T1–T8, C0–C2) in which *every theorem carries an explicit registered falsification window*; identifiability results (white-box point identification, black-box interval bounds, an impossibility theorem for implanted endorsement).
2. **The simulation benchmark** (`sim/`): a 4,620-run campaign (11,250 registered counting bundles; see paper Appendix N) on a tabular substrate (ENV-0) that exercises every falsification window. Run-level verdicts of the main matrix: **2,520 CONFIRMED + 360 INCONCLUSIVE** (defense-arm cells outside their registered criterion window, by construction) **+ 0 REFUTED**.

> **Evidence discipline.** The benchmark establishes *implementation-level consistency*, not construct validity: every registered window is satisfied, as expected of a correct implementation. Construct validity of the indicator family remains unestablished and is registered as future work (external-substrate ports and human-side studies). This scoping is stated in the abstract, Section 9.4, and the conclusion of the paper.

## Repository layout

```
latex/                 paper LaTeX source (main.tex, sections/, appendix.tex,
                       related_work.tex, refs.bib, main.bbl) + figures/ + main.pdf
sim/
  src/autonomy_sim/    platform: env, estimators, scenarios, aggregation, DI tools
  tests/               122 unit/integration tests (TDD; run in ~2 min)
  run_matrix.py        full-campaign batch runner (reproduces sim/runs/)
  make_figures.py      figure generator (TrueType-embedded PDFs, fonttype=42)
  make_report.py       auto-generates runs/<campaign>/report.md
  estimator_checks.py  two-path estimator error checks
  analysis_*.py/json   sensitivity-arm analyses (EXEC-1 weights, P3, X5 arms)
  SPEC_*.md            four specifications (platform / estimators / experiments / tests)
  runs/20261017_full/  authoritative campaign data (7.1 MB, 146 files):
                       per-arm results.csv + NDJSON bundles + manifests + report.md
refs/manifest.md       verified-bibliography ledger (112 entries; PDFs not redistributed)
tools/                 fill_repo_urls.sh (maintenance)
```

## Requirements

- Python ≥ 3.9 with `numpy` and `matplotlib` (developed on Python 3.12, numpy 2.3, matplotlib 3.10; see `sim/requirements.txt`)
- A TeX distribution (TeX Live) to rebuild the paper

## Quick start

```bash
# 1. Run the test suite (122 tests, ~2 minutes)
cd sim && python3 -m unittest discover -s tests -q

# 2. Regenerate the paper figures from the archived campaign data
cd sim && python3 make_figures.py --root runs/20261017_full --out ../latex/figures

# 3. Rebuild the paper (87 pages)
cd latex && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex

# 4. Reproduce the full campaign from scratch (hours; deterministic seeds)
cd sim && python3 run_matrix.py          # see sim/SPEC_experiments.md for the matrix
```

Every run is bit-reproducible from its (scenario, configuration, replication) coordinates; seeds derive deterministically as `seed = 30000 + 1000·s + 97·c + r` (paper Appendix N).

## Licenses

- **Code** (`sim/`, `tools/`): MIT — see [LICENSE](LICENSE)
- **Paper text, figures, data, documentation** (`latex/`, `sim/runs/`, `refs/manifest.md`, `*.md`): CC BY 4.0 — see [CONTENT-LICENSE.md](CONTENT-LICENSE.md)

## Citation

```bibtex
@misc{hu2026autonomy,
  title   = {Autonomy as Determination by One's Own Normative Structure:
             A White-Box-First Five-Channel Audit Framework with Axioms,
             Theorems, and a Simulation Benchmark},
  author  = {Hu, Wen},
  year    = {2026},
  note    = {Preprint; version v1.0-r10},
  url     = {https://github.com/hurrywhen/autonomy-five-channel}
}
```

Machine-readable: [CITATION.cff](CITATION.cff). Provenance (tag ↔ development commits, checksums): [RELEASE_NOTES.md](RELEASE_NOTES.md).
