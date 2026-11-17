# R15 frozen-source validation provenance

This directory contains only new R15 validation text. It does not alter any
R11–R14 manifest, result, verdict, preservation copy, or historical analysis.

Validation is executed from a clean temporary Git worktree at an exact public
snapshot content commit containing the complete read-only archive.
`validation.json` records the commit, clean-worktree check, source/SPEC hashes,
194-test result, three R14 read-only replays, two R15 read-only statistical
checks, paper build metadata, and their interpretation.

A first attempt from development commit
`7095de389d9271fc1226d5a1701b91853afbef96` was **not** accepted: 191 tests
passed and 3 report tests errored because the development Git history
intentionally excludes the full ignored 4,620-run archive, including
`estimator_checks.json`. This was a data-availability failure in that clean
checkout, not a hidden successful validation or an R15 numerical regression.
The validator now fails preflight explicitly when those files are absent. The
accepted validation therefore uses the complete public snapshot commit rather
than claiming the development checkout is self-contained.

This is a **current-source deterministic replay at a recorded Git commit**. It
is not an immutable tag, a GitHub/Gitee Release, a version DOI, an external
construct-validation study, or a recovery of the three unavailable historical
R14 run-time SPEC byte snapshots. Those gaps remain disclosed in
`sim/runs/20261116_r14/PROVENANCE.md`.

The old `a_org` and combined `a_via` values remain legacy internal-causal and
resilience markers. Replaying them does not identify the R15 normative-source
split or present-state/defense split.
