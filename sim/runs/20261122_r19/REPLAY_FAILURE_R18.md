# R18 cross-environment replay failure record (retained, not replaced)

**Status:** RECORDED_FAILURE_SUPERSEDED_BY_R19
**Recorded:** 2026-11-22 (R19 revision)
**Superseded artifact:** `sim/analysis_r18_native_joint_audit.json` (read-only)
**Superseding artifact:** `sim/analysis_r19_joint_audit.json`

## 1. The failure (as reported by the R18 independent review)

The R18 joint-audit read-only replay (`analysis_r18_native_joint_audit.py
--check`) PASSED in the original development environment (273/273 tests, max
abs float diff 0) but FAILED in the reviewer's independent environment:

- Two components of the open-loop optimal input distribution
  (`sampled.execution_open_loop.score.input_distribution_over_allowed`)
  differed by approximately **7.524e-10**, exceeding the declared 1e-12
  float replay tolerance.
- This changed `baseline_certificate.evidence_hash` (the R18 evidence payload
  included the full `sampled` analysis block, hence the optimizer
  coordinates).
- Single-run and single-thread runs in the reviewer environment reproduced
  the same (different-from-saved) result, so the current code was
  self-consistent there; the saved artifact's source commit matched the
  current code, ruling out version mismatch.

The capacity VALUE itself was essentially unchanged across environments.

## 2. Root cause

The native execution kernel is the parity channel
`K(o | a1,a2) = BSC(p)(o | a1 xor a2)`, whose rows satisfy
`row00 = row11` and `row01 = row10`. Its capacity-achieving input set is the
two-dimensional face `{q : q00 + q11 = q01 + q10 = 1/2}` of the simplex.
The capacity-achieving distribution is therefore **non-unique**, and the
Blahut–Arimoto / active-set solver returns a platform-dependent point on that
face (floating-point/libm/BLAS differences). The capacity value is
well-conditioned (unique), but the auxiliary input coordinates are not.

The R18 design compounded this by putting those non-unique auxiliary
coordinates inside the byte-level `evidence_hash`. A ~1e-9 coordinate drift
thus broke a byte-exact hash comparison even though the estimand (capacity /
A_exec) was stable.

## 3. The R19 repair (three parts)

1. **Separated evidence binding.** `evidence_hash` now binds IMMUTABLE
   registered inputs only: raw operating/execution log SHA-256 digests,
   config, seed, sample counts, log schema. Approximate analysis outputs
   (plug-in estimates, bootstrap intervals, optimizer coordinates) are
   excluded. See `r19_joint_audit.run_joint_audit_r19` `evidence_binding`.

2. **Declared canonicalization rule**
   (`open_loop_execution.canonical_capacity_input_distribution`,
   `canonicalize_input=True`):
   - if the uniform distribution achieves the certified capacity within
     1e-9 nats, return the EXACT uniform vector (bit-identical everywhere);
   - if capacity is near zero (<= 1e-3 nats; ill-conditioned moment matching,
     e.g. a sampled action-decoupled control), return exact uniform as the
     declared representative;
   - otherwise return the UNIQUE maximum-entropy capacity-achieving
     distribution (Shannon entropy is strictly concave on the convex optimal
     face), computed by deterministic iterative scaling against the solver's
     capacity-achieving output, rounded to 12 decimals with exact
     renormalization, and verified fail-closed at 1e-6 nats (KKT).
   On all registered EXACT instances the canonical input is exactly uniform.
   Perturbation-injection tests confirm stability under raw-coordinate drifts
   up to 5e-9 (larger than the observed 7.5e-10). The default
   `canonicalize_input=False` path is byte-identical to R17/R18 (no
   `input_canonicalization` key), so historical replays are unaffected.

3. **Declared per-field replay tolerances**
   (`compare_replay_json(field_tolerances=...)`): canonical input coordinates
   1e-6, capacity-derived values 1e-9. Raw hashes, event counts, seeds, and
   statuses are non-float leaves and remain byte-exact; they are never covered
   by float tolerances. Drift beyond the declared field tolerance still fails.

## 4. Verification

- The full R19 replay suite (R14 X5-c/stratified/C0-CF, R15 statistics/paired,
  R16 source-attribution, R17 native/weight-regions, R18 joint-audit
  [original-environment], R19 joint-audit, R19 sampling-study) is verified in
  TWO independent clean worktrees with differing thread/hash environments
  (see `validation.json` `environments`).
- 319/319 unit/integration/regression tests pass, including the
  canonicalization perturbation-stability tests and the
  `state_autonomy_RNI` consistency regression.

## 5. Honesty boundary

- The R18 artifact is retained READ-ONLY with this failure record; it is NOT
  silently replaced and then claimed to replay cross-platform.
- The R18 `--check` still passes in the original environment (same platform);
  its cross-environment numerical replay is superseded by R19. The R19
  frozen acceptance therefore checks the R18 artifact's integrity and
  internal anchors (read-only) rather than asserting cross-environment
  byte-replay of the superseded R18 numerical block.
- This is numerical governance for INTERNAL audits. It is not a claim of
  external independent-investigator replication, external construct
  validation, or a version DOI.
