# Release Notes

## R15 public source synchronization — 2026-11-17 (`main`, untagged)

**Title:** *Autonomy as Determination by One's Own Normative Structure: A White-Box-First Five-Channel Audit Framework with Axioms and Conditional Theorems*

**Authors:** Wen Hu and Gong Zhang

**Paper:** `latex/main.pdf`, 104 pages, 6 figures (5 external PDF figures plus 1 TikZ dependency graph), 113 cited references.

This synchronization publishes the R15 reviewer-counterexample revision, complete LaTeX source, simulation source, tests, specifications, and evidence packages on GitHub and Gitee `main`. It is a **public source refresh, not a new immutable release tag or Zenodo version release**. Existing tags and DOI records are not rewritten.

### Development-source provenance

| Item | Value |
|---|---|
| R15 final development-source commit | `0ebbae17dc8bceeb3dda4a9852fc7f0f355869ee` |
| Preceding R15 content commit | `7095de389d9271fc1226d5a1701b91853afbef96` |
| R15 public content commit used for clean validation | `f11491937a0dcf6d86069959ba078ffd206770ab` |
| Validated public source tree | `a7351ec32aa236a3f162037e8ec897141799ef34` |
| R14 development-source commit | `6a6130869157a885a9bc44aba24ae60196927179` |
| R14 public snapshot commit | `dbdf2f6f05c2f4d38b43bcc1d435a10ac0721b7f` |
| Public repository relationship | Fresh-history public snapshot; public commit hashes differ from development hashes by design |
| `latex/main.tex` SHA-256 | `17a22ced91d401321519ccc1dbe78c58834e4fb0b3fd28067232a9490ad3ef06` |
| `latex/main.pdf` SHA-256 | `64c2c856c9b530298b709a15f3fff79f057722d1e0cac4da08be86033222b417` |
| Public tag / R15 version DOI | **Not created in this synchronization** |
| Historical archive | `v1.0-r10.1`; Zenodo concept DOI `10.5281/zenodo.23608751`, which does not archive R14 or R15 |

The R15 validation manifest records a clean temporary worktree at the exact content commit, its tree hash, source/SPEC hashes, 194 tests, three R14 read-only replays, two R15 read-only statistical checks, and a clean 104-page paper build. It does not assert an immutable tag, formal Release, version DOI, recovery of unavailable historical SPEC bytes, or external construct validation.

### Substantive R15 changes

- Repairs the execution horizon to \(A_{t:t+n-1}\) and \(O_{t+n}\), exactly \(n\) actions. Adds the R14 two-bit ratio-2 regression, compactness/channel conditions for attained maxima and Blahut–Arimoto, and environment-decoupling zero semantics.
- Withdraws T2's no-surgery/full-mediation/honesty iff and four-track shortcut. Replaces them with componentwise compatibility and sufficient structural conditions, including baseline-relative \(\Lambda\) and goal/reflection/resource controls. The sufficient certificate explicitly requires point-valued before/after states with \(F_{\mathrm{src}}+F_{\mathrm{oth}}>0\); a zero denominator is undefined, not compatible. Adds unchanged-\(\Lambda=0.5\), honest-information-moving-\(\operatorname{Fix}\), and zero-denominator controls.
- Restricts epistemic and goal blindness to explicit action-independent or fixed-structural-object witnesses. Zero external flow alone no longer serves as an R15 blindness proof.
- Labels L0 as internal-causal autonomy only. At L1+, separates \(F_{\mathrm{rand}}\), \(F_{\mathrm{norm}}\), and \(F_{\mathrm{ext}}\) using the registered \(R\to N\to I\) chain, so pure independent-register randomness receives zero normative-source attribution.
- Distinguishes structural goal reads from behavior-based IRL identified sets/intervals. States Brouwer, Banach, Tarski, Kakutani–Fan–Glicksberg, and Kuratowski–Ryll-Nardzewski premises separately. Degenerate goal intervals are no longer collapsed to their upper endpoint in new point-composite requests. Withdraws general additive-shift invariance: only a joint translation of \(U_{\mathrm{eff}}\), \(\operatorname{Fix}\), and \(\Theta\) with equivariant dynamics/metric preserves the goal reading.
- Splits current \(V_{\mathrm{state}}\) and \(A^{\mathrm{state}}\) from defense \(R_{\mathrm{def}}\) and optional \(A^{\mathrm{res}}\). Zero repair/readiness does not automatically zero present autonomy. Historical EROSION is a legacy resilience demonstration only.
- Corrects C2 to \(s>\delta+s_c\) under persistent attack and \(s>s_c\) after attack removal. Route B now uses quotient-cone pointedness, closedness, and the explicit \(1/\sum_iw_i\) normalization step.
- Adds actual `produce_r15_certificate` and fail-closed `write_r15_certificate` production/validation paths. Mandatory fields include surgery history, \(\Lambda\) plus `DEFINED`/`NOT_APPLICABLE`/`UNKNOWN` status, source registration, state/readiness, and evidence ceiling. Unknown provenance caps evidence at `LIMITED`; N/A is not conflated with unknown, legacy `Bundle` is not auto-upgraded, and no output is an integrity certificate or external validation.
- Adds substantive comparisons with Ingel et al. (2022, PID-based RL autonomy), Albantakis (2021, candidate autonomy measures on structurally diverse automata), and Jung–Polani–Stone (2011, continuous-state/discrete-action empowerment), plus a classical-precursor/R15-increment table.

### Evidence and reporting

- **194/194 tests pass**, including 14 new deterministic R15 counterexamples.
- Read-only current-source replays pass for pooled X5-c, stratified X5-c, and C0-CF-v2.
- New R15 read-only Kendall \(\tau_b\) and paired-X5-c checks pass. Historical analysis JSON files are not overwritten.
- X5-c is reported as **480,000 cell/context evaluations from 120,000 base \((X,U)\) draws**, not 480,000 independent samples. The three time cells are cross-sectional strata.
- R15 paired cross-checks use per-context differences because integrated and sampled estimates share \((X,Z,J)\). Gaussian absolute difference `0.0077274650`, paired SE `0.0064778640`; logistic `0.0003983553`, SE `0.0056650019`. Both pass the **post hoc** inherited \(\max(4\mathrm{SE},0.02)\) rule. The analysis is explicitly `POST_HOC_PASS`, not a preregistered CONFIRMED criterion.
- C0's custom L1 vector is \((4/15,4/15,4/15,1/5)\), yielding `0.8312378961427878` and `0.723634618720189`; equal-weight sensitivity values are \(2^{-1/4}\) and \(2^{-1/2}\).
- The weight audit uses \(\tau_b\) with exact ties and scenario strata. Overall values span `[0.927595,1]`; the origination-heavy scenario-4 minimum is `0.866667`, so no uniform `0.93` scenario-level claim is made.
- The `0.01` numeric SESOI is only `1.0417` times the largest reported sample-mode absolute error `0.0096`. It is not an externally calibrated domain-important effect or power analysis.
- PDF: 104 pages; clean-source rebuild produces identical extracted text; no unresolved references or LaTeX errors; Ghostscript parses all pages; fonts have Unicode mappings; maximum overfull box is approximately 8.94 pt.

These are local mathematical, implementation, and same-model checks. They are **not** independent-substrate construct validation, external SESOI/power analysis, Lean certification, or an immutable R15 release/version DOI.

### Bibliography and repository-metadata correction

R14's source library contained 119 entries, but its PDF/`main.bbl` actually cited **110**, and its paper had **6 figures**, not 5. R15 removes the 9 uncited entries and adds 3 verified direct precursors. The R15 library and PDF both contain **113** entries; all are cited. Figure counting now includes both 5 external PDF figures and the TikZ theorem-dependency graph. Related Work now says eight literatures, fixes `My increment`/`an separate`, and distinguishes full-text from bibliographic-only verification in `refs/manifest.md`.

### Evidence-package provenance and legacy boundaries

Historical 4,620-run files, the separate R11 replay, R13 CUSUM analysis, old X5 records, R14 manifests/results/verdicts, and failed constructions are preserved. R15 analyses are new files and do not alter them.

- `sim/runs/20261116_r14/PROVENANCE.md` still records three unavailable run-time SPEC snapshots, source evolution, common random numbers, and post hoc protocol changes.
- Historical `a_org` lacks the R15 \(N/R\) split and remains an internal-causal marker.
- Historical combined `a_via` remains a resource-plus-defense resilience marker, not present R15 state autonomy.
- R15 paired-SE and \(\tau_b\) artifacts supersede only current reporting interpretations; they do not rewrite R14 bytes or verdicts.
- `sim/runs/20261117_r15/validation.json` records the clean exact-content-commit replay and its limited scope.

No third-party bibliographic PDFs or internal review archives are redistributed.

### Still outstanding

- Immutable R15 tag, formal Release, and R15 version DOI, with their own frozen-release replay manifest;
- selector-conditional DEL-1 estimation and a nondegenerate bracket;
- preregistered independent-substrate comparisons on Ingel's RL environments, Albantakis's automata, and other substrates, including full/ablated/behavior-only/utility-only/PID comparators;
- external SESOI/power analysis, held-out calibration, external error distributions, and expert evaluation;
- generalized event-level \(A_{ref}\), additional nontrivial-action SCMs, and Lean certification;
- R15 synchronization of the Chinese translation and further editorial compression.

---

## R14 public source synchronization — 2026-11-17 (`main`, untagged)

R14 published the 98-page conditional-theorem and counterfactual-estimand revision at public commit `dbdf2f6f05c2f4d38b43bcc1d435a10ac0721b7f`, from development source `6a6130869157a885a9bc44aba24ae60196927179`. It included 180 tests, SPEC v1.0, R11 DEL-1 summary, X5-c studies, nondegenerate C0-CF-v2, and failure/provenance records. X5-c remains `MODEL_SENSITIVE`, T7 remains `INCONCLUSIVE`, and historical marker values are not counterfactual computations.

R15 supersedes R14's execution indexing, T2 compatibility shortcut, universal blindness wording, random-source interpretation, all-channel point-identification statement, C2 threshold quantifier, combined current/defense gate, and several reporting statistics. R14 files and its public commit remain historical and are not rewritten.

## Historical release record — v1.0-r10 / v1.0-r10.1

The first public release archived the R10 paper source, simulation platform, and authoritative 4,620-run campaign. It was a fresh-history snapshot and excluded third-party PDFs and internal review materials.

| Item | Historical value |
|---|---|
| Initial public tag | `v1.0-r10`, 2026-10-23 |
| Corrected tag | `v1.0-r10.1`, fixing a Table 1 float overflow without removing content |
| Initial Zenodo version DOI | `10.5281/zenodo.23608752` |
| Zenodo concept DOI | `10.5281/zenodo.23608751` |
| Historical paper | 87 pages, 5 data figures; earlier author list and manuscript claims |
| Later metadata synchronization | Wen Hu and Gong Zhang are the current paper authors; top-level software/data creator metadata was not inferred from paper authorship alone |

Those tags and DOI records remain historical. They do not include R11–R15 mathematics, code, evidence packages, or the present two-author manuscript.

## Licensing

Code: MIT (`LICENSE`). Paper text, figures, data, and documentation: CC BY 4.0 (`CONTENT-LICENSE.md`).
