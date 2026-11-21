# Release Notes

## R19 public source synchronization — 2026-11-22 (`main`, immutable tag `v1.2-r19`)

**Paper:** `latex/main.pdf`, 105 pages, 6 figures, 115 cited references.
**Authors:** Wen Hu and Gong Zhang.

R19 is a medium revision addressing the R18 review, which confirmed that no new foundational math error (of the feedback-counterexample class) was found and that the remaining issues were certificate generality, cross-environment numerical reproducibility, and near-zero sampling-error propagation. It repairs the R18 cross-environment replay failure, makes the certificate architecture layer-aware and degradation-complete, corrects the `state_autonomy_RNI` field, discloses sampled convention composites and a multi-seed recoverability study, decomposes order/semantic sensitivity, and renames the 0.05 thresholds as post hoc frozen. This revision **is frozen by an immutable annotated tag `v1.2-r19`** on the final synchronization commit, with a **two-environment** clean-worktree replay manifest. The earlier tag `v1.1-r18` is retained; its recorded cross-environment replay failure is preserved (not replaced). A version DOI requires Zenodo archiving of the current tag and is **not** yet minted; no formal Release page is created.

### Development-source and frozen-content provenance

| Item | Value |
|---|---|
| R19 development-source commit | `43d65db823027e5aa1d2a5790a0289c2fbdedc3e` |
| R19 public content commit used for clean validation | `R19_PUBLIC_CONTENT_COMMIT` |
| Validated public source tree | `R19_VALIDATED_TREE` |
| Final public synchronization commit (tag `v1.2-r19` target) | `R19_FINAL_COMMIT` |
| R18 reviewed public baseline | `fd568690b796aa6beef9c1a3af650550dec7a016` (tag `v1.1-r18`) |
| `latex/main.tex` SHA-256 | `316bdcf8f4daf9e034df7900e6a9e0ba562c3741197ca2d5c8478342d795b405` |
| `latex/main.pdf` SHA-256 | `739bbfb1b444cc046c72d25c339d068d7cd4efa27c72798351ea16965c3c78a0` |
| Public tag | `v1.2-r19` (annotated; created on the final synchronization commit) |
| R19 version DOI | **Not minted** (requires Zenodo archiving of `v1.2-r19`) |
| Historical archive | `v1.0-r10.1`; concept DOI `10.5281/zenodo.23608751`, which does not archive R19 |

`sim/runs/20261122_r19/validation.json` records the exact clean content commit, its tree, both environments, and current scientific-source hashes: **319/319 tests** in two independent clean environments (differing thread/hash settings), three R14 read-only replays, R15 tau-b and paired-X5-c audits, R16 source-attribution audit, R17 weight-region audit, the R19 joint-log and multi-seed sampling-study replays, read-only integrity/anchor checks of the R17-native and R18 numerical blocks (whose cross-environment byte-replay is not guaranteed), original-environment R17-native/R18 numerical `--check` confirmations, and an independent clean build. It also checks extracted-text equality, all-page Ghostscript parsing, 115 cited references, 6 figures, unresolved-reference/float warnings, metadata, embedded fonts, and Unicode maps. Its scope remains internal mathematical/implementation consistency, small-scale concept validation, and an internal finite-sample study.

### Substantive R19 changes

- **Cross-environment numerical reproducibility (`open_loop_execution.py`, `r19_joint_audit.py`):** the R18 joint-audit artifact failed independent-environment replay because the parity execution kernel has a two-dimensional capacity-achieving face, so the optimizer's auxiliary input coordinates are non-unique and platform-sensitive (~7.524e-10 drift) yet sat inside the byte-level evidence hash. Repair: (i) evidence hashes bind immutable raw inputs only (log SHA-256 + config); (ii) a declared canonicalization rule (`canonical_capacity_input_distribution`) returns exact uniform when capacity-achieving or near-zero (<=1e-3 nats), otherwise the unique maximum-entropy capacity-achieving input via deterministic iterative scaling, fail-closed verified at 1e-6 nats; (iii) declared per-field replay tolerances (1e-6 coordinates, 1e-9 capacity values), raw hashes/counts/statuses byte-exact. The default `canonicalize_input=False` path is byte-identical to R17/R18. Verified in two clean environments; the failure record `runs/20261122_r19/REPLAY_FAILURE_R18.md` is retained.
- **Layer-aware, degradation-complete certificates (`r19_guards.py`):** L0 uses an independent `L0_INTERNAL_CAUSAL` report (F_int/F_ext share only; RNI/NRI not imposed); L1/L2 use RNI/NRI/order-average + semantic partitions. Channel states DEFINED/INTERVAL/UNKNOWN/NOT_APPLICABLE; point vs interval certificates separate; composite intervals propagate exactly by coordinatewise monotonicity. IRL-interval goal mode (structural point optional), thin-log/zero-entropy reflection degradation to [0, product of defined factors], zero-total-flow share unidentifiability ([0,1] org interval + composite interval), UNKNOWN worst-case propagation with LIMITED ceiling.
- **Corrected `state_autonomy_RNI`:** computed from the actual five channels (R18 returned only the resource gate 0.8); regression asserts equality with the registered RNI certificate composite.
- **Sampled NRI disclosure + multi-seed study (`analysis_r19_joint_audit.py`, `analysis_r19_sampling_study.py`):** the paper tabulates exact AND sampled per-convention composites with errors (sampled NRI 0.1478374 vs exact 0.0003908, error 0.1474 > 0.05). Near-zero detection limit (NRI share < 1e-6) -> interval semantics [0, 0.1866]. 8 independent seeds (20261122--20261129), 8192 trajectories, 200 bootstrap resamples: NRI mean bias +0.151, percentile under-coverage (NRI 0/8, RNI 1/8, order-average 0/8); bias correction halves NRI RMSE (0.151 -> 0.081) but does not restore the endpoint. Exact endpoints are model anchors, not finite-sample recoverability claims.
- **Decomposed sensitivity + threshold provenance:** `order_spread` (registered partition, across orders), `semantic_partition_spread` (max over orders of across-partition spread), `overall_composite_range` (overview only); ORDER_SENSITIVE and MODEL_SENSITIVE trigger independently. Native instance: order 0.4604657; per-convention partition differences RNI 0 / NRI 0.4604657 / order-average 0.0596576. The 0.05 thresholds are post hoc frozen internal engineering thresholds (frozen after the R17-native results were observed; not preregistered before outcomes; not a domain SESOI).
- **Sampled negative controls:** surgery (Lambda=0 -> all convention composites zero, REGISTERED_SURGERY) and action-decoupled (execution zero within sampling precision <=1e-3; exact arm exactly zero) arms run through the same joint-log pipeline.

### Evidence boundaries

Historical 4,620-run records, R11 replay, R13 CUSUM, old X5, R14 manifest/results/verdicts, R15/R16/R17/R18 analysis artifacts and validations are preserved read-only. R19 adds new source, test, analysis, and validation files only; the R18 joint-audit numerical block is superseded with its failure recorded. Historical `a_org` remains an internal-causal marker, combined `a_via` a resilience marker, X5-c `MODEL_SENSITIVE`, paired X5-c `POST_HOC_PASS`, and T7 `INCONCLUSIVE`. No legacy record is promoted to current N/R/I attribution, present-state autonomy, SCM audit, or external validation.

Still outstanding: a version DOI (Zenodo archiving of `v1.2-r19`); selector-conditional DEL-1 and a nondegenerate bracket; actual Ingel/Albantakis/PID comparisons and intervention-attribution accuracy; domain-justified SESOI/power, held-out external error analysis, experts and downstream criteria; independent-investigator reimplementation; general MaxEnt-IRL identified-set solving; more SCMs and Lean; Chinese synchronization; and recovery of the three unavailable R14 run-time SPEC byte snapshots. The cross-environment numerical governance is for internal audits, not a claim of external independent replication. No third-party bibliographic PDFs or internal review archives are redistributed.

---

## R18 public source synchronization — 2026-11-21 (`main`, immutable tag `v1.1-r18`)

**Paper:** `latex/main.pdf`, 103 pages, 6 figures, 115 cited references.
**Authors:** Wen Hu and Gong Zhang.

R18 is a focused local revision addressing the R17 review (which confirmed the R16 core defects were already repaired in R17): full-profile certificates with enforced order/semantic sensitivity flags; a single-SCM/single-log-schema joint-batch end-to-end native audit superseding the R17-native compositional fixture; support-relative open-loop zero-MI quantifiers and terminal-observation vs observation-sequence conventions; weight results unified as exact sensitivity characterization; and TOST/non-inferiority precision in the external protocol. Unlike R17, this revision **is frozen by an immutable annotated tag `v1.1-r18`** on the final synchronization commit, with a clean-worktree replay manifest. A version DOI requires Zenodo archiving of the tag and is **not** yet minted; no formal Release page is created.

### Development-source and frozen-content provenance

| Item | Value |
|---|---|
| R18 development-source commit | `bc1c5380f440f6de9ccfb629ca9050d65a4ded48` |
| R18 public content commit used for clean validation | `618704d612632297601a646b98392b31703b7b08` |
| Validated public source tree | `05973c0711db3d2dc35a94fdc63b66b1e1218d7d` |
| Final public synchronization commit (tag `v1.1-r18` target) | The commit adding this validation sidecar; its SHA is recorded by the annotated tag object itself and in the development repository's R18 release record |
| R17 reviewed public baseline | `21c6016f1aa946d41ebe43355e899c1efda69d33` |
| `latex/main.tex` SHA-256 | `d56a1893ef2a7545fe6521d86085a0bfdaac250153c203931a0f97921a57a39d` |
| `latex/main.pdf` SHA-256 | `97caea96f32cb7d3be13be9f53db0a17857bf632aa7d02cc17322f8a1c2408a0` |
| Public tag | `v1.1-r18` (annotated; created on the final synchronization commit) |
| R18 version DOI | **Not minted** (requires Zenodo archiving of `v1.1-r18`) |
| Historical archive | `v1.0-r10.1`; concept DOI `10.5281/zenodo.23608751`, which does not archive R18 |

`sim/runs/20261121_r18/validation.json` records the exact clean content commit, its tree and current scientific-source hashes, **273/273 tests**, three R14 read-only replays, R15 tau-b and paired-X5-c audits, R16 source-attribution audit, R17 native-benchmark and weight-region audits, the R18 joint-log audit, and an independent clean build. It also checks extracted-text equality, all-page Ghostscript parsing, 115 cited references, 6 figures, unresolved-reference/float warnings, metadata, embedded fonts, and Unicode maps. Its scope remains internal mathematical/implementation consistency and small-scale concept validation.

### Substantive R18 changes

- **Full-profile certificates (`r18_guards.py`):** mandatory complete channel vector (value/state/interval/protocol version), goal structural point + IRL interval, execution open-loop horizon, reflection three factors + logged event counts, registered RNI/NRI/order-average shares + flow terms + alternative semantic partitions, weights, and recomputed per-convention composites with range. Composite spread > 0.05 (preregistered internal engineering threshold, not domain SESOI) forces `ORDER_SENSITIVE`/`MODEL_SENSITIVE`, a scalar-export warning, and a sensitivity-qualified grade. The exported scalar must equal the registered RNI-convention composite; a near-one RNI / near-zero NRI reading cannot be exported unflagged.
- **Joint-log native audit (`native_joint_audit.py`):** one registered \(T=3\) SCM, one log schema, one joint operating batch (8192 trajectories) estimates attribution (both partitions), epistemic accuracy, reflection fidelity/consistency/Lambda, and viability/defense; execution uses a separate precommitted open-loop stream from the same environment law. Exact convention composites: RNI 0.4608565248, NRI 0.0003907989, order-average 0.4011989073; alternative partition ~0.4608565; range [0.0003908, 0.4608565]. The paper reports these directly (Table tab:native). R17-native artifact preserved read-only.
- **Open-loop conventions:** fixed-Q zero MI is support-relative (point-mass Q always zero); capacity-mode iff quantifies over sequences assignable positive probability by some admissible Q. Terminal-observation BSC p=0.1 n=2 normalized 0.2655022 vs observation-sequence 0.5310044, guarded separately.
- **Weight terminology:** exact sensitivity characterization, not robustness; closed simplex (zero vertices) is a relaxation, certificate/representation weights strictly positive interior.
- **External protocol:** TOST (two one-sided alpha=0.05 ⇔ 90% two-sided CI inside margins; 95% two-sided requires alpha=0.025); NI directions delta_BA upper bound < Delta_BA_NI and delta_Brier lower bound > -Delta_Brier_NI. Engineering margins frozen; domain SESOI/power/execution pending. Paper abstract/conclusion corrected accordingly.

### Evidence boundaries

Historical 4,620-run records, R11 replay, R13 CUSUM, old X5, R14 manifest/results/verdicts, R15/R16/R17 analysis artifacts and validations are preserved read-only. R18 adds new source, test, analysis, protocol, and validation files only. Historical `a_org` remains an internal-causal marker, combined `a_via` a resilience marker, X5-c `MODEL_SENSITIVE`, paired X5-c `POST_HOC_PASS`, and T7 `INCONCLUSIVE`. No legacy record is promoted to current N/R/I attribution, present-state autonomy, SCM audit, or external validation.

Still outstanding: a version DOI (Zenodo archiving of `v1.1-r18`); selector-conditional DEL-1 and a nondegenerate bracket; actual Ingel/Albantakis/PID comparisons and intervention-attribution accuracy; domain-justified SESOI/power, held-out external error analysis, experts and downstream criteria; independent-investigator reimplementation; general MaxEnt-IRL identified-set solving; more SCMs and Lean; Chinese synchronization; and recovery of the three unavailable R14 run-time SPEC byte snapshots. No third-party bibliographic PDFs or internal review archives are redistributed.

---

## R17 public source synchronization — 2026-11-20 (`main`, untagged)

**Paper:** `latex/main.pdf`, 103 pages, 6 figures, 115 cited references.
**Authors:** Wen Hu and Gong Zhang.

R17 is a major revision: precommitted open-loop multi-step execution with a feedback-copy counterexample; co-primary current structural and historical formation profiles; explicit Lambda time origins; an R17-native multi-step end-to-end internal benchmark; exact weight-simplex bookkeeping bounds; contracted aggregation/necessity claims; C1/C2/T1d corrections; and an external protocol with equivalence/non-inferiority design. It updates GitHub and Gitee `main` only; it is not an immutable tag, formal Release, version DOI, external validation, or independent-investigator replication.

### Development-source and frozen-content provenance

| Item | Value |
|---|---|
| R17 development-source commit | `140e631bb03307ac2bc98af20bfd7736fe28ddf2` |
| R17 public content commit used for clean validation | `b0edb7694d9f769b31f800f9ff5ebeb929247e2c` |
| Validated public source tree | `6413a515fd47566e2ac43d2d1f5151656aa192b2` |
| R16 reviewed public baseline | `cb000d8748a7aa4d0f048c52485e70b2e7128f4c` |
| R16 validated content commit | `397b52e4f858c690ed7692b3563adfb274021ea5` |
| `latex/main.tex` SHA-256 | `b111710845eda034fe9f2d32227a6ad48adb4a830e00d51ad095d882e27c2fd1` |
| `latex/main.pdf` SHA-256 | `d0de7a76cdad1a398008ec4ae42022c8e85fca5339d3388e83111ae8c7d781ff` |
| Public tag / R17 version DOI | **Not created** |
| Historical archive | `v1.0-r10.1`; concept DOI `10.5281/zenodo.23608751`, which does not archive R17 |

`sim/runs/20261119_r17/validation.json` records the exact clean content commit, its tree and current scientific-source hashes, **251/251 tests**, three R14 read-only replays, R15 tau-b and paired-X5-c audits, R16 source-attribution audit, R17 native-benchmark audit, R17 weight-region audit, and an independent clean build. It also checks extracted-text equality, all-page Ghostscript parsing, 115 cited references, 6 figures, unresolved-reference/float warnings, metadata, embedded fonts, and Unicode maps. Its scope remains internal mathematical/implementation consistency and small-scale concept validation.

### Substantive R17 changes

- **Open-loop execution:** multi-step execution optimizes precommitted sequence distributions under intervention kernels; reactive ordinary MI is excluded. The feedback-copy witness has old score 0.5 and open-loop score 0. EXEC-1/ENV-0 are \(n=1\) special cases.
- **Current/history co-primary outputs:** R17 certificates carry separate current structural and historical formation profiles. Fixed-point goal implant can leave current channels unchanged while formation status records surgery. Lambda audit-time removal and original-implant prevention are distinct estimands.
- **R17-native benchmark:** same-instance \(T=3\) reactive SCM plus separate open-loop execution audit, exact truth, seeded sampling errors/intervals, alternative semantic partition, surgery/decoupling negative controls, and certificates. Internal concept validation only.
- **Weight regions:** exact closed-simplex log bounds and pairwise damage halfspaces; 22 unique finite contrasts, 17 weight-dependent. Log-damage shares are bookkeeping, not causal/ratio-scale attribution.
- **Claim contraction:** single-channel insufficiency rather than exactly-five minimality; design propositions/bookkeeping corollaries; C1 OU premise, C2 truncation, T1d Le Cam scope.
- **External protocol:** equivalence/non-inferiority margins, independent downstream Brier outcome, nested validation, and independent-investigator reimplementation requirements; still unexecuted.

### Evidence boundaries

Historical 4,620-run records, R11 replay, R13 CUSUM, old X5, R14 manifest/results/verdicts, R15/R16 analysis artifacts and validations are preserved. R17 adds new source, test, analysis, protocol, and validation files only. Historical `a_org` remains an internal-causal marker, combined `a_via` a resilience marker, X5-c `MODEL_SENSITIVE`, paired X5-c `POST_HOC_PASS`, and T7 `INCONCLUSIVE`. No legacy record is promoted to current N/R/I attribution, present-state autonomy, SCM audit, or external validation.

Still outstanding: immutable tag/formal Release/version DOI and their frozen release replay; selector-conditional DEL-1 and a nondegenerate bracket; actual Ingel/Albantakis/PID comparisons and intervention-attribution accuracy; external SESOI/power, held-out external error analysis, experts and downstream criteria; independent-investigator reimplementation; general MaxEnt-IRL identified-set solving; more SCMs and Lean; Chinese synchronization; and recovery of the three unavailable R14 run-time SPEC byte snapshots. No third-party bibliographic PDFs or internal review archives are redistributed.

---

## R16 public source synchronization — 2026-11-17 (`main`, untagged)

**Paper:** `latex/main.pdf`, 104 pages, 6 figures, 115 cited references.
**Authors:** Wen Hu and Gong Zhang.

R16 closes the R15 re-review: ordered source-attribution semantics, exact multi-step internal guards, Route B scaling, T2 interval/non-finite rules, certificate schema/evidence separation, tolerant numerical replay, and a design-frozen external protocol. It updates GitHub and Gitee `main` only; it is not an immutable tag, formal Release, version DOI, external validation, or independent-investigator replication.

### Development-source and frozen-content provenance

| Item | Value |
|---|---|
| R16 development-source commit | `ae7ab1f7ce5a90547a8fba3f3c2720b46dc95ac4` |
| R16 public content commit used for clean validation | `397b52e4f858c690ed7692b3563adfb274021ea5` |
| Validated public source tree | `a2887f9bbf9f6774ea5d6a35f0b787c35fee4b0f` |
| Superseded first R16 candidate | `7b74ec43265e606694b9494ef81433b8c6ea8633` (content `3f1f8e6c1921a65301da94f1f41c8c57021976c5`) |
| R15 reviewed public baseline | `ec53f987a8348dbe374987178acad80c39b3e726` |
| R15 validated content commit | `0f789d7c419b6c57f32a431a96484d8367daf965` |
| `latex/main.tex` SHA-256 | `824e75ed058135d84fa4b72ca06adabd19837b4bd5e696b1155742ce65d95a99` |
| `latex/main.pdf` SHA-256 | `93f2684cb2939328d60ba10e33ec1789ac5fb073d888fd52f551222e95a1479a` |
| Public tag / R16 version DOI | **Not created** |
| Historical archive | `v1.0-r10.1`; concept DOI `10.5281/zenodo.23608751`, which does not archive R16 |

`sim/runs/20261117_r16/validation.json` records the exact clean content commit, its tree and current scientific-source hashes, **230/230 tests**, three R14 read-only replays, R15 tau-b and paired-X5-c audits, the R16 source-attribution audit, and an independent 104-page build. It also checks extracted-text equality, all-page Ghostscript parsing, 115 cited references, 6 figures, unresolved-reference/float warnings, metadata, embedded fonts, and Unicode maps. Its scope remains internal mathematical/implementation consistency.

### Substantive R16 changes

- **Ordered residual attribution:** RNI is a registered normative choice, not an order-free causal fraction. R first separates exogenous innovation, N receives normative-state mediation, and I last isolates direct bypass. Nondegenerate R/N reports include NRI and an I-last two-order Shapley-style descriptor. Alternative N/R/I semantic partitions are preregistered sensitivities. Conditioning can increase MI, so R-first is not universally conservative; the order average is not PID or interventional identification. Pure-random zero claims are RNI-specific: with \(N=R,A=R\), RNI gives 0 but NRI gives 1.
- **OR counterexample:** independent fair \(R,N\), \(A=R\lor N\), no I. In bits, marginal DI is `0.311278124459`, conditional DI `0.5`, joint DI `0.811278124459`; normative shares are `0.6163114534` (RNI), `0.3836885466` (NRI), and `0.5` (order average). The value 0.5 is specific to this symmetric example.
- **Exact closed-loop audit:** 16 exogenous trajectories of a \(T=2\) binary SCM test pure-random, pure-normative, and mixed XOR policies, action feedback into N, joint-DI chain identities, N-mediated external flow, and direct bypass. Mixed XOR changes normative share from 1 under RNI to 0 under NRI, with I-last average 0.5. An independent atom-wise conditional-MI oracle and `analysis_r16_source_attribution.json` reproduce the results.
- **Route B:** the proof and regression now derive \(g(u+t'\mathbf1)=g(u)+t'\Rightarrow\varphi(z+st')=\varphi(z)+t'\), then \(q=st'\Rightarrow\varphi(z+q)=\varphi(z)+q/s\). The final normalized geometric representation is unchanged.
- **T2 intervals and non-finite values:** default interval compatibility is endpoint order \(l_1\ge l_0\) and \(u_1\ge u_0\); crossing intervals fail. Stronger independent cross-world guarantees need \(\ell_1\ge u_0\) or a registered coupling. NaN and ±Inf raise before any compatibility verdict, including NaN→NaN.
- **R16 certificate contract:** registration completeness and mechanism evidence are separate. Complete registration without SCM is `REGISTERED_COMPLETE`; explicit audited-SCM evidence with model/evidence hash bindings is required for `SCM_AUDITED`. UNKNOWN/incomplete registration remains LIMITED, while L0/L1 N/A is not UNKNOWN. `channel_schema_version`, `org_mode`, `goal_mode`, `state_readiness_version`, and L1/L2 hashes are machine checked. Legacy Bundle values and forged schema/mode/hash fields are rejected by producer and writer. Hashes bind declared bytes, not external truth.
- **Final numerical/state guards:** source shares check the ratio itself, so `flow_share(1e-13,1e-15)` is rejected rather than returning 100. Certificates additionally enforce \(A^{\mathrm{state}}\le V_{\mathrm{state}}\): `state=1,viability=0` fails in both producer and writer, while `0/0` remains registrable. These controls supersede the first R16 candidate and raise the suite to 230 tests.
- **Replay infrastructure:** only JSON float leaves use relative/absolute \(10^{-12}\) tolerance and maximum-difference reporting. Verdicts, seeds, counts, hashes, types, keys, and list lengths remain exact; non-finite and out-of-tolerance values fail. R16 source-attribution replay additionally checks independent closed-form anchors.
- **External protocol:** `sim/EXTERNAL_VALIDATION_PROTOCOL.md` fixes the common design for Ingel's Gridworld/repeating-pattern RL systems and Albantakis's PathFollow automata. Candidates include RNI/NRI/Shapley, next-state PID (BROJA primary, SxPID sensitivity), Albantakis's battery, empowerment, behavior-only/utility-only and reduced models. Intervention-attribution balanced accuracy and held-out calibration are co-primary; expert/downstream endpoints are separate. Published perturbations and auxiliary endorsement SCMs require preregistered mappings and are new constructions, not automatic surgery labels. Status is `DESIGN_FROZEN_UNEXECUTED`; numerical SESOI, power, sample sizes, public outcome registration, and all external outcomes remain pending.
- **Standalone paper:** revision narration is removed from the abstract and main text; historical supersession remains in `sim/CRITERION_VERSION_MAP.md`. UNKNOWN is distinguished from N/A, T8 explicitly concerns present \(A^{\mathrm{state}}\), and an \(A^{\mathrm{res}}\) decrease requires fixed positive \(R_{\mathrm{def}}\). Repeated version-governance prose is compressed; the paper remains 104 pages and now cites Shapley and Williams–Beer in addition to the R15 bibliography.

### Evidence boundaries

Historical 4,620-run records, R11 replay, R13 CUSUM, old X5, R14 manifest/results/verdicts, R15 analysis artifacts, and `sim/runs/20261117_r15/validation.json` are preserved. R16 adds new source, test, analysis, protocol, and validation files only. Historical `a_org` remains an internal-causal marker, combined `a_via` a resilience marker, X5-c `MODEL_SENSITIVE`, paired X5-c `POST_HOC_PASS`, and T7 `INCONCLUSIVE`. No legacy record is promoted to current N/R/I attribution, present-state autonomy, SCM audit, or external validation.

Still outstanding: immutable tag/formal Release/version DOI and their frozen release replay; selector-conditional DEL-1 and a nondegenerate bracket; actual Ingel/Albantakis/PID comparisons and intervention-attribution accuracy; external SESOI/power, held-out external error analysis, experts and downstream criteria; general MaxEnt-IRL identified-set solving; more SCMs and Lean; Chinese synchronization; and recovery of the three unavailable R14 run-time SPEC byte snapshots. No third-party bibliographic PDFs or internal review archives are redistributed.

---

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
| R15 public content commit used for clean validation | `0f789d7c419b6c57f32a431a96484d8367daf965` |
| Validated public source tree | `bbe01f84d5cd9195fdc00f323e804db363b7bc80` |
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

Those tags and DOI records remain historical. They do not include R11–R16 mathematics, code, evidence packages, or the present two-author manuscript.

## Licensing

Code: MIT (`LICENSE`). Paper text, figures, data, and documentation: CC BY 4.0 (`CONTENT-LICENSE.md`).
