# Release Notes

## R14 public source synchronization — 2026-11-17 (`main`, untagged)

**Title:** *Autonomy as Determination by One's Own Normative Structure: A White-Box-First Five-Channel Audit Framework with Axioms and Conditional Theorems*

**Authors:** Wen Hu and Gong Zhang

**Paper:** `latex/main.pdf`, 98 pages, 5 figures, 119 bibliography entries.

This synchronization publishes the R14 paper, simulation source, tests, specifications, and evidence packages on the GitHub and Gitee `main` branches. It is a **public source refresh, not a new immutable release tag or Zenodo version release**. Existing tags and DOI records are not rewritten.

### Development-source provenance

| Item | Value |
|---|---|
| R14 development-source commit | `6a6130869157a885a9bc44aba24ae60196927179` |
| Preceding R14 content commit | `23f2b17f1c00c11d2c7bd6d271289e6abe09ea69` |
| R13 baseline used by historical R14 manifests | `f816848370d676e08e67559c2544d6dc937322c3` |
| Public repository relationship | Fresh-history public snapshot; public commit hashes differ from development hashes by design |
| `latex/main.tex` SHA-256 | `9e60935778fe8ff89aa362647ab16da14febeb9eb9da788891f8edbc9afbb048` |
| `latex/main.pdf` SHA-256 | `6f0b306e8644de099b38fa8a3f8040264e8a17e77e6488a3a4be4b3e66ddf627` |
| Public tag / R14 version DOI | **Not created in this synchronization** |
| Historical archive | `v1.0-r10.1`; Zenodo concept DOI `10.5281/zenodo.23608751`, which does not archive R14 |

The evidence manifests retain their original `git_dirty: true` and `frozen_release: false` fields: they describe the runs at generation time and are not retroactively altered merely because the resulting files are now public.

### Substantive R14 changes

- Repairs T1b positivity, relative-baseline T2/T3 strictness, T3 layer quantifiers, T4 attack direction/ties/responsiveness and linear-fraction boundary analysis, and T5 full-state script conditions.
- Restricts the reflection fidelity ratio to finite discrete Shannon ensembles; normalized coordinates are no longer presented as proved measurement-theoretic ratio scales.
- Defines \(\Lambda\) solely through actual/no-surgery endorsement output-law total variation under abduction–action–prediction. Surgery history is a separate record; legacy ENV-0 `law_level_lambda` values remain markers.
- Replaces the degenerate black-box certification example with nondegenerate identity/XOR SCMs and explicitly states their abduction contexts and conditional output laws.
- Replaces the invalid first C0 fixture with C0-CF-v2: positive internal flow and empowerment, a nondegenerate goal channel, exact full-trajectory joint-law enumeration, and computed rather than illustrative channel values.
- Adds direct comparison with Cihon et al., Anthropic's deployment study, Plasticity/Empowerment, EELMA, the Agent Compendium, and Auditable Agents. The contribution is scoped as a conditional conceptual audit framework, not a validated universal metric.
- Moves simulation evidence to an appendix and removes “Simulation Benchmark” from the title.

### Evidence and validation

- **180/180 tests pass** in the development tree and public snapshot.
- Read-only current-source replays pass for pooled X5-c, stratified X5-c, and C0-CF-v2.
- Stratified X5-c: 24 rows, 480,000 cell/context evaluations and 120,000 base \(X,U\) draws; \(D_{noise}=0.089799622>0.01\), hence **MODEL_SENSITIVE** point readings and two-model bands.
- C0-CF-v2: identical full-trajectory \((E^T,O^T,A^T)\) laws; \(A_{org}=1\), \(A_{goal}=0.5\), \(A_{exec}\approx1\), \(A_{via}=1\); composites `0.8312378961427878` and `0.723634618720189`.
- T7 remains **INCONCLUSIVE**. T3b legacy curves remain descriptive rather than tests of the expectation/firing bounds. No “14/15 confirmed theories” or zero-refutation headline is used.
- PDF: 98 pages; clean-source rebuild produces identical extracted text; no unresolved references or LaTeX errors; Ghostscript parses all pages; fonts are embedded with Unicode mappings; maximum overfull box is approximately 8.94 pt.

These are local mathematical, implementation, and same-model checks. They are **not** independent-substrate construct validation, external SESOI/power analysis, Lean certification, or a frozen public R14 release/version DOI.

### Evidence-package provenance

`sim/runs/20261116_r14/PROVENANCE.md` records:

1. Three distinct run-time SPEC hashes across four evidence packages whose byte-identical SPEC snapshots cannot be recovered; the current preservation copy is not backdated as an old preregistration.
2. Pooled and stratified X5-c `--check` commands mean deterministic recomputation with the **current** source and agreement with saved numerical outputs, not execution of the original source bytes.
3. Common random numbers across arms within each noise/time cell; arm evaluations are not counted as independent random units.
4. The retained pooled run, post hoc time-stratified supplement, invalid first C0 fixture, failed initial serialization, and the separate C0-CF-v2 replacement.

Historical 4,620-run files, the separate R11 replay, R13 CUSUM analysis, and old X5 records are preserved. New evidence is not pooled into the historical campaign count.

### Public contents added or updated

- Complete compilable LaTeX source, including `glyphtounicode.tex`, `main.bbl`, bibliography, figures, and `SUBMISSION_MANIFEST.md`.
- Current `sim/src`, all 180 tests, R14 analysis and replay runners, report generator, SPEC v1.0 and preservation copy, and `CRITERION_VERSION_MAP.md`.
- Separate R11 DEL-1 summary (`manifest.json`, `results.csv`, `verdict_table.csv`) and 26 R14 evidence/provenance files.
- R14 public README, citation metadata, licensing attribution, and source-package scripts with the Unicode dependency included.

No third-party bibliographic PDFs or internal review archives are redistributed.

### Still outstanding

- Immutable R14 tag and R14 version DOI, with their own frozen-release replay manifest;
- selector-conditional DEL-1 estimation and a nondegenerate bracket;
- independent-substrate validation, external SESOI/power analysis, holdout calibration, and external expert evaluation;
- generalized event-level \(A_{ref}\) estimation and additional SCM instantiations;
- R14 synchronization of the Chinese translation.

---

## Historical release record — v1.0-r10 / v1.0-r10.1

The first public release archived the R10 paper source, simulation platform, and authoritative 4,620-run campaign. It was a fresh-history snapshot and excluded third-party PDFs and internal review materials.

| Item | Historical value |
|---|---|
| Initial public tag | `v1.0-r10`, 2026-10-23 |
| Corrected tag | `v1.0-r10.1`, fixing a Table 1 float overflow without removing content |
| Initial Zenodo version DOI | `10.5281/zenodo.23608752` |
| Zenodo concept DOI | `10.5281/zenodo.23608751` |
| Historical paper | 87 pages, 5 figures; earlier author list and manuscript claims |
| Later metadata synchronization | Wen Hu and Gong Zhang are the current paper authors; top-level software/data creator metadata was not inferred from paper authorship alone |

Those tags and DOI records remain historical. They do not include R11–R14 mathematics, code, evidence packages, or the present two-author 98-page manuscript.

## Licensing

Code: MIT (`LICENSE`). Paper text, figures, data, and documentation: CC BY 4.0 (`CONTENT-LICENSE.md`).
