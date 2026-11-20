# R17 major-revision provenance (batch 2026-11-19; final synchronization 2026-11-20)

## Scope

R17 addresses the R16 major review without rewriting historical R11--R16 evidence. The reviewed R16 public commit is `cb000d8748a7aa4d0f048c52485e70b2e7128f4c`; its content-validation commit is `397b52e4f858c690ed7692b3563adfb274021ea5`. Those records and `sim/runs/20261117_r16/validation.json` remain historical inputs, not the validation of this revision.

Current changes cover: precommitted open-loop multi-step execution and the feedback-copy counterexample; co-primary current structural and historical formation profiles; fixed-point goal-implant witness and explicit Lambda time origins; an R17-native multi-step end-to-end internal benchmark; exact closed-simplex weight bounds and halfspaces; downgraded log-damage/aggregation claims; C1 OU, C2 truncation, and T1d Le Cam corrections; theorem-strength relabeling; and an external protocol with equivalence/non-inferiority design.

## New analytic artifacts

- `sim/src/autonomy_sim/open_loop_execution.py`: exact finite open-loop sequence-channel guards.
- `sim/src/autonomy_sim/formation_audit.py` and `r17_guards.py`: historical formation profile, fixed-point implant witness, and R17 certificate schema.
- `sim/src/autonomy_sim/native_benchmark.py` and `analysis_r17_native_benchmark.{py,json}`: same-instance T=3 reactive operating SCM plus separate open-loop execution audit, exact truth, seeded sampling errors/intervals, semantic sensitivity, negative controls, and certificates.
- `sim/analysis_r17_weight_regions.{py,json}`: read-only historical geometric bookkeeping bounds over the closed weight simplex.
- R17 test modules for open-loop execution, formation certificates, native benchmark, and weight regions.
- `sim/EXTERNAL_VALIDATION_PROTOCOL.md`: still `DESIGN_FROZEN_UNEXECUTED`; no external outcome, SESOI, power, public outcome-preregistration timestamp, or independent-investigator replication is claimed.

## Validation protocol

`tools/make_r17_validation.py` must be run from a clean public-content commit containing the complete read-only historical archive. It executes 251 tests, three R14 read-only replays, R15 tau-b and paired-X5-c audits, R16 source-attribution audit, R17 native-benchmark audit, and R17 weight-region audit. It also builds the paper in a fresh directory, compares extracted text, parses every PDF page, checks references/figures, metadata, float/citation warnings, embedded fonts with Unicode maps, and hashes the current scientific source files. `validation.json` is generated only after these checks pass.

A passing result establishes current-source/internal-model consistency only. T7 remains INCONCLUSIVE, X5-c remains MODEL_SENSITIVE, and the paired audit remains POST_HOC_PASS. No formal Release, version DOI, external construct validation, selector-conditional DEL-1 estimator, external SESOI/power analysis, Lean certification, or Chinese synchronization is asserted.
