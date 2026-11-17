# R14 evidence provenance and post-run SPEC changes (2026-11-17)

## 1. Frozen evidence versus unfrozen working tree

The R14 evidence directories and their manifests are **not public releases**.
They record a dirty working tree and an R13 baseline commit, not a frozen R14
commit/tag/version DOI. No old preregistration or manifest is backfilled with a
later SPEC or source hash.

The current editable protocol is `sim/SPEC_experiments.md`. Its content at the
time of this sidecar is also copied to `sim/SPEC_experiments_v1.0_snapshot.md`.
That snapshot is a new preservation copy, not an earlier preregistration file.

## 2. Recorded SPEC hashes and recovery status

| Evidence package | Hash recorded in its preregistration | Byte-identical SPEC snapshot currently available? |
|---|---|---|
| `x5c/` (pooled first run) | `dcc28b7bffbe2abadf9b0aef367002e879102f71b3c518d0ea2b942827300bfd` | **No — provenance gap** |
| `x5c_stratified/` | `97ca5b773141b78c35ede03feee81f1926eabe40c421e16989d03ba38c4c8fc4` | **No — provenance gap** |
| `c0cf/` (invalid first fixture) | `97ca5b773141b78c35ede03feee81f1926eabe40c421e16989d03ba38c4c8fc4` | **No — provenance gap** |
| `c0cf_v2/` (canonical replacement) | `17add289787eda383806620239e2c26eb0095650ebc23cd6cc1aa4fece8b638b` | **No — provenance gap** |
| Current SPEC and new preservation copy | `29365e6fa5ed5b0a28a455c283da68ca2139985e601410e6eadc32b80176809a` | `sim/SPEC_experiments_v1.0_snapshot.md` |

No earlier byte-identical SPEC snapshot was present in the repository or in the
run directories. Three distinct run-time SPEC hashes are recorded across four
evidence packages, and none has a corresponding byte-identical snapshot in the
current tree. They therefore cannot be reconstructed honestly from the current
working tree alone. The hashes are retained as recorded, while the absence of
all three source snapshots is explicitly disclosed. The current SPEC hash must
not be used to claim that any of those earlier protocol texts has been recovered.

## 3. Changes after the runs

Subsequent edits separated mathematical status, legacy markers, and current
counterfactual evidence; corrected the Gaussian differential-entropy numbers;
clarified Feng/KG-Dung scope; narrowed T3b and T4 evidence; added numerical
boundary fail-closed behavior; and documented the C0 fixture defects. These
changes did not alter recorded results, seeds, verdict tables, or manifests.
The post hoc time-stratified sensitivity rule was already labeled as such and
was not backdated to the pooled preregistration.

The initial C0-CF fixture is invalid for nondegenerate composite separation
(AX0, zero empowerment, degenerate goal space, illustrative factors, and only
per-time law checks). `c0cf_v2/` is a new run with an explicit post hoc
correction record. It does not overwrite or repair the initial files.

## 4. Source hashes and replay meaning

For `c0cf_v2/`, the current runner and relevant module hashes match its newly
created manifest. Artifact hashes for preregistration, results, cross-checks,
verdicts, and analysis match the saved files in all three canonical X5-c/C0
packages.

Both the pooled `x5c/` and `x5c_stratified/` packages record earlier runner
and/or `counterfactual.py` hashes. The source later gained input guards,
explicit identity-endorsement computation, and random-stream documentation.
Their `--check` commands therefore mean deterministic recomputation with the
**current** source and agreement with saved numeric outputs, not bit-identical
execution of the original source. In particular, the current stratified runner
hash is `19c72b07af02921badd3c41cf7fa47ea5a0bf89af6bd9babf4767c3b6d5c191c`
and the current counterfactual-module hash is
`793c5da4984c94bc8c313ab9c28084ca3fe5cce007e1085308bfb40fe522f85d`;
the older manifest values remain unchanged. The saved results, verdicts, and
analysis still satisfy their own recorded artifact hashes.

`c0cf_v2/` is generated after the mathematical correction. Its supersession and
source hashes are recorded anew rather than modifying the invalid first package.

## 5. Context counts and random units

For pooled X5-c, 160,000 is the number of arm/context evaluations, while the
base `X,U` draws are 40,000 (2 noises × 20,000). For stratified X5-c, 480,000 is
the number of cell/context evaluations, while base draws are 120,000
(2 noises × 3 times × 20,000). The four arms at a fixed noise and time use
common random numbers. Thus:

- base `X,U` draws are independent **within each noise/time cell**;
- arms within a cell deliberately share those base draws (common random
  numbers), so arm evaluations are not independent random units;
- downstream `V` cross-checks use separate registered streams.

These are numerical integration/sensitivity checks, not external power samples
or independent-substrate experiments.

## 6. Remaining release blocker

A future release must include this sidecar, the preservation copy, all evidence
packages, and an immutable commit/tag/version DOI. All three missing run-time
SPEC snapshots (spanning four evidence packages) and the invalid first C0
fixture must remain disclosed. A clean release tag alone does not erase those
provenance limitations.

## 7. R15 supersession note (2026-11-17)

The word “current” in §4 refers to the R14 sidecar's 2026-11-16 writing time,
not to later R15 source. R15 adds a per-context disagreement accessor for the
new paired-difference analysis, so the displayed R14-era runner/module hashes
must not be reused as R15 source hashes. The historical hashes and all R14
result/verdict bytes remain unchanged. Exact R15 source hashes are recorded in
`sim/runs/20261117_r15/validation.json` once that clean public-snapshot
validation is created. The R15 paired analysis is explicitly post hoc and does
not repair the unavailable historical SPEC snapshots.
