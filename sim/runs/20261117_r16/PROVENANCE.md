# R16 review-closure provenance (2026-11-17)

## Scope

R16 closes the R15 re-review findings without rewriting historical R11--R15 evidence. The reviewed R15 public commit is `ec53f987a8348dbe374987178acad80c39b3e726`; its content-validation commit is `0f789d7c419b6c57f32a431a96484d8367daf965`. Those records and `sim/runs/20261117_r15/validation.json` remain historical inputs, not the validation of this revision.

Current changes cover ordered residual source attribution and sensitivity, an exact T=2 closed-loop guard, the Route B scaled homogeneity step, endpoint-ordered IRL intervals, non-finite compatibility failures, R16 certificate metadata and separate evidence axes, tolerant floating-point replay, a design-frozen but unexecuted external protocol, and manuscript de-versioning/compression.

## New analytic artifacts

- `sim/src/autonomy_sim/source_attribution.py`: exact finite-binary sequence-DI routines.
- `sim/analysis_r16_source_attribution.py` and `.json`: OR, three T=2 closed-loop policies, mediation and direct-bypass witnesses, with independent closed-form anchors.
- `sim/tests/test_r16_source_attribution.py`: independent atom-wise conditional-MI log-ratio oracle.
- `sim/tests/test_r16_certificate_guards.py`: interval, non-finite, schema, evidence-ceiling, legacy-rejection and writer controls.
- `sim/tests/test_r16_analysis_replay.py`: exact non-float versus tolerant float replay controls.
- `sim/EXTERNAL_VALIDATION_PROTOCOL.md`: `DESIGN_FROZEN_UNEXECUTED`; no external outcome, SESOI, power, public outcome-preregistration timestamp or independent-investigator replication is claimed.

## Validation protocol

`tools/make_r16_validation.py` must be run from a clean public-content commit containing the complete read-only historical archive. It executes 228 tests, three R14 read-only replays, the R15 tau-b and paired-X5-c audits, and the R16 source-attribution audit. It also builds the paper in a fresh directory, compares extracted text, parses every PDF page, checks references/figures, metadata, float/citation warnings, and embedded fonts with Unicode maps, and hashes the current scientific source files. `validation.json` is generated only after these checks pass.

A passing result establishes current-source/internal-model consistency only. T7 remains INCONCLUSIVE, X5-c remains MODEL_SENSITIVE, and the paired audit remains POST_HOC_PASS. No immutable tag, formal Release, version DOI, external construct validation, selector-conditional DEL-1 estimator, external SESOI/power analysis, Lean certification, or Chinese synchronization is asserted.
