# autonomy-five-channel

**Autonomy as Determination by One's Own Normative Structure: A White-Box-First Five-Channel Audit Framework with Axioms and Conditional Theorems**

Wen Hu<sup>1,2</sup> and Gong Zhang<sup>1,2</sup> — <sup>1</sup>College of Electronic and Information Engineering, Nanjing University of Aeronautics and Astronautics, Nanjing, China; <sup>2</sup>Jiangsu Yunhefeng Intelligent Technology Co., Ltd., Nanjing, China — `huwen@nuaa.edu.cn`; `gzhang@nuaa.edu.cn`

**R18 public source synchronization, 2026-11-21.** Paper: [`latex/main.pdf`](latex/main.pdf) (**103 pages**, **6 figures**, **115 cited references**) · [Gitee mirror](https://gitee.com/jiangsu-yunhefeng-intelligent/autonomy-five-channel) · [Release and provenance notes](RELEASE_NOTES.md)

[![Historical Zenodo concept DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23608751.svg)](https://doi.org/10.5281/zenodo.23608751) — this DOI archives the historical `v1.0-r10` release. **The present revision is frozen by the immutable tag `v1.1-r18` with a clean-worktree replay manifest (`sim/runs/20261121_r18/validation.json`). A version DOI requires Zenodo archiving of that tag and is not yet minted; the historical concept DOI does not cover R18.**

---

## What R18 changes

R18 is a focused local revision addressing the R17 review, which confirmed that the R16 core defects were already repaired in R17. It does not rewrite the theory or historical evidence.

- **Full-profile certificates:** the R18 schema (`r18_guards.py`) makes the profile-first principle machine-checked. Mandatory fields carry the complete layer-applicable channel vector (value/state/interval/protocol version), the goal structural point and IRL interval, the execution open-loop horizon, the reflection three factors with logged event counts, the registered RNI/NRI/order-average shares with every flow term and alternative semantic partition, the aggregation weights, and the recomputed composite under each convention with its range. When the composite spread across order conventions or semantic partitions exceeds the preregistered internal threshold (0.05, an engineering threshold, not a domain SESOI), the certificate must carry `ORDER_SENSITIVE`/`MODEL_SENSITIVE`, a scalar-export warning, and a sensitivity-qualified grade. A near-one RNI share with a near-zero NRI share cannot be exported as a single unflagged positive scalar.
- **Joint-log end-to-end native audit:** the R17-native compositional fixture is superseded (read-only, not rewritten) by `native_joint_audit.py`, which estimates every operating-side estimand from one joint trajectory-log batch of a single registered \(T=3\) SCM under one log schema. Execution is audited on a separate precommitted open-loop intervention stream from the same environment law, as the estimand requires. The paper now reports the convention composites directly: RNI \(0.4608565\), NRI \(0.0003908\), order-average \(0.4011989\), alternative partition \(\approx0.4608565\); composite range \([0.0003908,0.4608565]\). Internal concept validation only.
- **Open-loop output conventions:** the zero-MI quantifier is support-relative for a fixed precommitted distribution (a point-mass distribution is always zero); capacity mode quantifies over sequences assignable positive probability by some admissible distribution. The terminal-observation estimand (normalized \(0.2655022\) for a two-step BSC at error \(0.1\)) is kept separate from the whole-observation-sequence Kronecker object (\(0.5310044\)).
- **Weight sensitivity terminology:** exact log-domain simplex bounds and halfspaces are an exact sensitivity characterization, not robustness evidence; 17 of 22 unique finite historical contrasts are weight-dependent. The closed simplex (zero vertices) is a sensitivity relaxation; the representation theorem and certificate weights use strictly positive interior weights.
- **External protocol precision:** equivalence is decided by TOST (two one-sided \(\alpha=0.05\) tests, equivalently a 90% two-sided interval inside the frozen margins); non-inferiority directions are explicit (\(\delta_{BA}=BA_{full}-BA_{reduced}\) upper bound \(<\Delta_{BA,NI}\); \(\delta_{Brier}=Brier_{full}-Brier_{reduced}\) lower bound \(>-\Delta_{Brier,NI}\)). Engineering margins are frozen; a domain-justified SESOI, power analysis, and external execution remain pending.

## What R17 changes

R17 is a major revision addressing the R16 review without rewriting historical evidence.

- **Open-loop execution repair:** multi-step \(A_{\mathrm{exec}}\) now optimizes precommitted open-loop action-sequence distributions under intervention kernels. A feedback-copy counterexample shows ordinary reactive MI can score 0.5 while open-loop capacity is zero. EXEC-1/ENV-0 are explicitly \(n=1\) open-loop special cases.
- **Co-primary current/history outputs:** certificates carry `current_structural_profile` and `historical_formation_profile`. A fixed-point goal implant can leave \(A_{\mathrm{goal}}=1\) and current channels unchanged while historical formation records surgery. Lambda time origins distinguish audit-time removal from original-implant prevention.
- **R17-native end-to-end benchmark:** one registered \(T=3\) reactive SCM with action-dependent environment, N/R/I roles, resource/defense split, structural goal point and IRL interval, reflection events, and explicit XOR endorsement SCM. Execution is audited separately by \(n=2\) open-loop interventions. Reports exact truth, seeded sampling errors, bootstrap/Wilson intervals, alternative semantic partition, surgery/decoupling negative controls, and R17 certificates. Internal concept validation only.
- **Weight-simplex bookkeeping bounds:** exact log-domain bounds and pairwise damage halfspaces replace a few alternative weights as the primary robustness check. Among 22 unique finite historical contrasts, 17 are weight-dependent. Log-damage shares are bookkeeping under the selected geometric aggregator, not causal attribution or ratio-scale effects.
- **Claim contraction:** T2 is single-channel insufficiency, not exactly-five minimality; T3/T8 are design propositions and T5 zero-factor bookkeeping. C1 uses a local OU premise, C2 states the [0,1] truncation convention, and T1d's Le Cam bound does not depend on finite verification capacity.
- **External equivalence design:** the unexecuted protocol now freezes equivalence/non-inferiority margins, an independent downstream Brier outcome, nested instance-level validation, and independent-investigator reimplementation requirements. Non-significance is not equivalence.

The R16 ordered-attribution, certificate, interval, non-finite, and replay repairs remain in force; see the historical R16 section in `RELEASE_NOTES.md`.

## Historical R16 changes

R16 closed the R15 re-review without rewriting historical evidence.

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
| Mathematical and implementation guards | **273/273 tests pass**, including R18 full-profile certificates, joint-log audit, open-loop conventions, and all R17/R16 controls; not external validation |
| R18 native joint-log audit | One SCM, one log schema, one joint operating batch for attribution/epistemic/reflection/formation channels; separate precommitted open-loop execution stream; exact convention composites \(0.4608565/0.0003908/0.4011989\), enforced sensitivity flags, sampling agreement |
| R17-native benchmark | Read-only, superseded by the R18 joint-log audit; same-instance \(T=3\) compositional fixture with exact truth, sampling errors/intervals, semantic sensitivity, negative controls |
| R17 weight regions | Exact closed-simplex log bounds and halfspaces (a sensitivity characterization); 22 unique finite contrasts, 17 weight-dependent; zero/log-undefined cases separated |
| R16 source-attribution audit | OR, duplicate-register order control, three exact \(T=2\) policies, mediation and direct-bypass witnesses; independent closed-form and atom-wise log-ratio checks |
| Historical 4,620-run ENV-0 archive | Read-only legacy implementation and same-model checks. Its `a_org` is internal-causal and combined `a_via` is a resilience marker; neither is silently re-signed as a current value |
| R14 pooled/stratified X5-c | Current-source read-only replays pass; \(D_{noise}=0.089799622>0.01\), so point readings remain **MODEL_SENSITIVE** |
| R15 X5-c paired cross-check | Shared \((X,Z,J)\) uses paired-difference SE; `POST_HOC_PASS`, not preregistered CONFIRMED. Replay comparison tolerates only floating-point round-off |
| R15 weight/statistical audit | Read-only Kendall \(\tau_b\) with ties and scenario strata; overall range \([0.927595,1]\), but no uniform \(0.93\) scenario-level floor |
| C0-CF-v2 | Same-environment model construction; custom L1 weights and equal-weight sensitivity are both reported |
| T7 / DEL-1 | **INCONCLUSIVE** pending a selector-conditional estimator and nondegenerate bracket |
| External protocol | **DESIGN_FROZEN_UNEXECUTED**; engineering equivalence/non-inferiority margins and TOST rule frozen; no domain SESOI/power, independent-substrate result, expert validation, or Lean certification is claimed |

Failed criteria, post hoc replacements, unrun programs, legacy markers, unavailable historical SPEC bytes, and the invalid first C0 fixture remain visible. Historical verdicts are not rewritten. The 480,000 X5-c evaluations use 120,000 base \((X,U)\) draws with common random numbers across arms within each noise/time cell.

## Repository layout

```text
latex/                     complete paper source, 115-entry bibliography,
                           Unicode map, submission manifest, 5 external PDF
                           figures + 1 TikZ figure, built 103-page PDF
sim/
  src/autonomy_sim/        ENV-0, estimators, SCMs, open-loop/source/certificate guards
                           (r18_guards full-profile schema, native_joint_audit)
  tests/                   273 unit/integration/regression tests
  analysis_r18_native_joint_audit.* R18 single-batch joint-log end-to-end audit
  analysis_r17_native_benchmark.* R17-native benchmark (read-only, superseded)
  analysis_r17_weight_regions.* exact weight-simplex sensitivity bounds
  analysis_r16_source_attribution.* exact OR and T=2 attribution audit
  analysis_r15_statistics.* Kendall tau-b, ties and scenario reporting audit
  analysis_r15_x5c_paired.* paired cross-check SEs and tolerant replay
  EXTERNAL_VALIDATION_PROTOCOL.md design-frozen, unexecuted external protocol
  SPEC_*.md                current specifications and R14 preservation copy
  CRITERION_VERSION_MAP.md R11–R18 supersession and evidence boundaries
  runs/20261017_full/      read-only historical 4,620-run campaign archive
  runs/20261102_r11/del1/  separate 30-run R11 replay summary
  runs/20261116_r14/       X5-c, C0-CF-v2, superseded/failed records
  runs/20261117_r15/       preserved R15 validation
  runs/20261117_r16/       preserved R16 validation
  runs/20261119_r17/       preserved R17 validation
  runs/20261121_r18/       current clean-worktree validation and provenance (tag v1.1-r18)
refs/manifest.md           graded bibliography verification ledger;
                           third-party PDFs are not redistributed
tools/                     source-package and frozen-validation scripts
```

## Requirements

- Python ≥ 3.10 with `numpy` and `matplotlib` (developed on Python 3.12; see `sim/requirements.txt`)
- A TeX distribution with `pdflatex` and `bibtex`

## Reproduction

```bash
# 1. Run all 273 tests
cd sim
python3 -m unittest discover -s tests -q

# 2. Read-only R14 evidence replays
python3 run_x5c_r14.py --out runs/20261116_r14/x5c --check
python3 run_x5c_r14_stratified.py --out runs/20261116_r14/x5c_stratified --check
python3 run_c0cf_r14.py --out runs/20261116_r14/c0cf_v2 --check

# 3. Read-only R15/R16/R17/R18 reporting and analytic audits
python3 analysis_r15_statistics.py --check
python3 analysis_r15_x5c_paired.py --check
python3 analysis_r16_source_attribution.py --check
python3 analysis_r17_native_benchmark.py --check
python3 analysis_r17_weight_regions.py --check
python3 analysis_r18_native_joint_audit.py --check

# 4. Rebuild the complete paper
cd ../latex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

For clean-source-commit validation, create a clean worktree at the R18 content commit recorded in `RELEASE_NOTES.md` and run `tools/make_r18_validation.py`. It writes only `sim/runs/20261121_r18/validation.json`, uses a separate temporary LaTeX build directory, and does not modify historical evidence.

The R14 replays and R15/R16/R17/R18 checks use **current** source and compare against saved outputs or independent analytic anchors; they are not represented as execution of earlier source bytes or recovery of unavailable historical SPEC snapshots. See the R14/R15/R16/R17/R18 `PROVENANCE.md` files and `sim/CRITERION_VERSION_MAP.md`.

The complete LaTeX tree is required; uploading only `main.tex` is not a valid source submission. See [`latex/SUBMISSION_MANIFEST.md`](latex/SUBMISSION_MANIFEST.md).

## Public-snapshot boundary

This repository is a fresh-history public snapshot of the authors' development work. It intentionally excludes third-party bibliographic PDFs and internal review archives. Development-source and public-content commit relationships are recorded in [`RELEASE_NOTES.md`](RELEASE_NOTES.md). Existing tags and the Zenodo concept DOI remain historical and are not rewritten.

## Licenses

- **Code** (`sim/`, `tools/`): MIT — [LICENSE](LICENSE)
- **Paper text, figures, data, and documentation**: CC BY 4.0 — [CONTENT-LICENSE.md](CONTENT-LICENSE.md)

## Citation

```bibtex
@misc{hu_zhang2026autonomy_r18,
  title  = {Autonomy as Determination by One's Own Normative Structure:
            A White-Box-First Five-Channel Audit Framework with Axioms
            and Conditional Theorems},
  author = {Hu, Wen and Zhang, Gong},
  year   = {2026},
  note   = {Author manuscript; R18 public source synchronization,
            21 November 2026, 103 pages; immutable tag v1.1-r18;
            no R18 version DOI yet},
  url    = {https://github.com/hurrywhen/autonomy-five-channel}
}
```

Machine-readable metadata: [`CITATION.cff`](CITATION.cff). For the historical software/data archive only, see Zenodo concept DOI [10.5281/zenodo.23608751](https://doi.org/10.5281/zenodo.23608751).
