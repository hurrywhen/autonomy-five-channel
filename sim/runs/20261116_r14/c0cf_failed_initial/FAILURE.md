# Failed initial C0-CF execution (2026-11-16)

The initial `run_c0cf_r14.py` execution wrote `preregistration.json` and then
failed while serializing `analysis.json`: a NumPy boolean reached the stdlib
JSON encoder (`TypeError: Object of type bool is not JSON serializable`).
No results, verdict table, or manifest was produced. The directory was renamed
from `c0cf` to `c0cf_failed_initial` to preserve this failed execution rather
than overwrite it. The corrected runner casts every criterion to a Python
`bool` and writes the canonical evidence package to a new `c0cf` directory.
