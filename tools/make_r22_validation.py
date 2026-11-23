#!/usr/bin/env python3
"""Validate the R22 content commit from clean worktrees in TWO environments.

Historical R11--R21 results are read-only inputs.  R21 artifacts are byte-
identical (R22 adds matched-contrast modules/artifacts without touching R21
code); their replays are included.  R22 adds full matched A/B/C joint-audit and
16-seed detection-study replays in both environments.  The R17-native and R18
saved numerical blocks contain non-canonical optimizer coordinates whose
cross-environment byte replay is not guaranteed (the R18 failure is retained);
they receive read-only integrity/anchor checks in both environments and
original-environment numerical --check confirmation in env A.

The two environments differ in thread/hash settings on the same platform, not
cross-platform independent replication.  LaTeX builds occur only in a fresh
/tmp/opencode directory.  There is no page-count cap for R22 (the authors chose
completeness over a page limit); all other paper quality gates remain fail-
closed.  This sidecar is a frozen replay manifest, not external validation or a
version DOI.  The full R21 and R22 detection-study checks recompute their grids,
so allow a long runtime.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

EXPECTED_TESTS = 429
EXPECTED_REFERENCES = 115
EXPECTED_FIGURES = 6

ENVIRONMENTS = [
    {"label": "env_A_default_threads", "overrides": {}},
    {"label": "env_B_single_thread_fixed_hash",
     "overrides": {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
                   "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1",
                   "PYTHONHASHSEED": "0"}},
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], cwd: Path, *, env_overrides: dict | None = None,
        full_output: bool = False) -> dict:
    started = time.monotonic()
    env = dict(os.environ)
    env.update(env_overrides or {})
    proc = subprocess.run(command, cwd=cwd, text=True, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = proc.stdout
    if proc.returncode:
        print(output)
        raise SystemExit(f"validation command failed ({proc.returncode}): {' '.join(command)}")
    record = {"command": command, "returncode": proc.returncode,
              "seconds": round(time.monotonic() - started, 3),
              "summary": output.strip().splitlines()[-10:]}
    if full_output:
        record["output"] = output
    return record


def read_only_integrity(module: str, artifact: str, cwd: Path,
                        env_overrides: dict) -> dict:
    snippet = (
        "import json; "
        f"from {module} import validate_result; "
        f"validate_result(json.load(open('{artifact}'))); "
        f"print('{module} read-only integrity + anchors OK')"
    )
    return run([sys.executable, "-c", snippet], cwd, env_overrides=env_overrides)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                            text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=root,
                                   text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root,
                               text=True).strip():
        raise SystemExit("frozen validation requires a clean worktree")

    sim = root / "sim"
    required = [
        sim / "runs/20261017_full/estimator_checks.json",
        sim / "runs/20261017_full/main/results.csv",
        sim / "runs/20261102_r11/del1/results.csv",
        sim / "runs/20261117_r15/validation.json",
        sim / "runs/20261117_r16/validation.json",
        sim / "runs/20261119_r17/validation.json",
        sim / "runs/20261121_r18/validation.json",
        sim / "runs/20261122_r19/validation.json",
        sim / "runs/20261122_r20/validation.json",
        sim / "runs/20261122_r21/validation.json",
        sim / "analysis_r16_source_attribution.json",
        sim / "analysis_r17_native_benchmark.json",
        sim / "analysis_r17_weight_regions.json",
        sim / "analysis_r18_native_joint_audit.json",
        sim / "analysis_r19_joint_audit.json",
        sim / "analysis_r19_sampling_study.json",
        sim / "analysis_r20_joint_audit.json",
        sim / "analysis_r20_detection_study.json",
        sim / "analysis_r21_joint_audit.json",
        sim / "analysis_r21_detection_study.json",
        sim / "analysis_r22_joint_audit.json",
        sim / "analysis_r22_detection_study.json",
        sim / "runs/20261122_r19/REPLAY_FAILURE_R18.md",
        sim / "EXTERNAL_VALIDATION_PROTOCOL.md",
        root / "latex/main.bbl",
    ]
    missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("clean checkout lacks required frozen evidence: " + ", ".join(missing))

    stable_replays = [
        ["run_x5c_r14.py", "--out", "runs/20261116_r14/x5c", "--check"],
        ["run_x5c_r14_stratified.py", "--out", "runs/20261116_r14/x5c_stratified", "--check"],
        ["run_c0cf_r14.py", "--out", "runs/20261116_r14/c0cf_v2", "--check"],
        ["analysis_r15_statistics.py", "--check"],
        ["analysis_r15_x5c_paired.py", "--check"],
        ["analysis_r16_source_attribution.py", "--check"],
        ["analysis_r17_weight_regions.py", "--check"],
        ["analysis_r19_joint_audit.py", "--check"],
        ["analysis_r19_sampling_study.py", "--check"],
        ["analysis_r20_joint_audit.py", "--check"],
        ["analysis_r20_detection_study.py", "--check"],
        ["analysis_r21_joint_audit.py", "--check"],
        ["analysis_r21_detection_study.py", "--check"],
        ["analysis_r22_joint_audit.py", "--check"],
        ["analysis_r22_detection_study.py", "--check"],
    ]
    environment_records = []
    test_count = None
    for environment in ENVIRONMENTS:
        overrides = environment["overrides"]
        records = [run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                       sim, env_overrides=overrides)]
        test_text = "\n".join(records[0]["summary"])
        match = re.search(r"Ran (\d+) tests", test_text)
        if not match or int(match.group(1)) != EXPECTED_TESTS:
            raise SystemExit(f"expected {EXPECTED_TESTS} tests, got {test_text!r}")
        test_count = int(match.group(1))
        for command in stable_replays:
            records.append(run([sys.executable, *command], sim, env_overrides=overrides))
        records.append(read_only_integrity("analysis_r17_native_benchmark",
                                           "analysis_r17_native_benchmark.json", sim, overrides))
        records.append(read_only_integrity("analysis_r18_native_joint_audit",
                                           "analysis_r18_native_joint_audit.json", sim, overrides))
        if not overrides:
            records.append(run([sys.executable, "analysis_r17_native_benchmark.py", "--check"],
                               sim, env_overrides=overrides))
            records.append(run([sys.executable, "analysis_r18_native_joint_audit.py", "--check"],
                               sim, env_overrides=overrides))
        environment_records.append({"label": environment["label"],
                                    "env_overrides": overrides,
                                    "commands": records})

    latex = root / "latex"
    build = Path(tempfile.mkdtemp(prefix="r22-frozen-build-", dir="/tmp/opencode"))
    try:
        for name in ["main.tex", "appendix.tex", "related_work.tex", "refs.bib",
                     "glyphtounicode.tex", "main.bbl"]:
            shutil.copy2(latex / name, build / name)
        for name in ["sections", "figures"]:
            shutil.copytree(latex / name, build / name)
        for command in [["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                        ["bibtex", "main"],
                        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]]:
            run(command, build)
        log = (build / "main.log").read_text(encoding="utf-8", errors="replace")
        forbidden = ["There were undefined references", "There were undefined citations",
                     "Float too large for page"]
        found = [item for item in forbidden if item in log]
        if found:
            raise SystemExit("LaTeX validation warnings fail closed: " + "; ".join(found))
        overfull = [float(value) for value in
                    re.findall(r"Overfull \\hbox \((\d+\.\d+)pt too wide\)", log)]
        run(["pdftotext", "main.pdf", "clean.txt"], build)
        run(["pdftotext", str(latex / "main.pdf"), "reference.txt"], build)
        run(["cmp", "clean.txt", "reference.txt"], build)
        run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=nullpage", "main.pdf"], build)
        info = run(["pdfinfo", "main.pdf"], build, full_output=True)
        info_text = info["output"]
        pages_match = re.search(r"Pages:\s+(\d+)", info_text)
        if not pages_match:
            raise SystemExit("pdfinfo lacks page count")
        pages = int(pages_match.group(1))
        if pages <= 0:
            raise SystemExit("paper page count must be positive")
        title = next((line.split(":", 1)[1].strip() for line in info_text.splitlines()
                      if line.startswith("Title:")), "")
        author = next((line.split(":", 1)[1].strip() for line in info_text.splitlines()
                       if line.startswith("Author:")), "")
        if not title or not author:
            raise SystemExit("PDF title/author metadata is incomplete")
        fonts = run(["pdffonts", "main.pdf"], build, full_output=True)
        font_rows = [line for line in fonts["output"].splitlines() if line.strip()
                     and not line.startswith(("name", "---"))]
        malformed_fonts = []
        for row in font_rows:
            fields = row.split()
            if len(fields) < 8 or fields[-5] != "yes" or fields[-3] != "yes":
                malformed_fonts.append(row)
        if not font_rows or malformed_fonts:
            raise SystemExit("font embedding/Unicode validation failed: "
                             + "; ".join(malformed_fonts))
        bibliography_entries = len(re.findall(r"^\\bibitem", (build / "main.bbl").read_text(
            encoding="utf-8"), flags=re.MULTILINE))
        if bibliography_entries != EXPECTED_REFERENCES:
            raise SystemExit(f"expected {EXPECTED_REFERENCES} references, got {bibliography_entries}")
    finally:
        shutil.rmtree(build)

    tex_files = [latex / "main.tex", latex / "appendix.tex", latex / "related_work.tex",
                 *sorted((latex / "sections").glob("*.tex"))]
    figures = sum(path.read_text(encoding="utf-8").count(r"\begin{figure}")
                  for path in tex_files)
    if figures != EXPECTED_FIGURES:
        raise SystemExit(f"expected {EXPECTED_FIGURES} figures, got {figures}")
    abstract = (latex / "main.tex").read_text(encoding="utf-8").split(
        r"\begin{abstract}", 1)[1].split(r"\end{abstract}", 1)[0]
    if "R15" in abstract or "reviewer" in abstract.lower():
        raise SystemExit("abstract contains revision-narration markers")

    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root,
                               text=True).strip():
        raise SystemExit("validation commands dirtied the frozen worktree")

    tracked = {
        "latex/main.tex", "latex/main.pdf", "latex/main.bbl", "latex/refs.bib",
        "latex/appendix.tex", "latex/related_work.tex", "latex/SUBMISSION_MANIFEST.md",
        "refs/manifest.md", "sim/README.md",
        "sim/SPEC_estimators.md", "sim/SPEC_experiments.md", "sim/SPEC_tests.md",
        "sim/CRITERION_VERSION_MAP.md", "sim/EXTERNAL_VALIDATION_PROTOCOL.md",
        "sim/analysis_r15_statistics.py", "sim/analysis_r15_statistics.json",
        "sim/analysis_r15_x5c_paired.py", "sim/analysis_r15_x5c_paired.json",
        "sim/analysis_r16_source_attribution.py", "sim/analysis_r16_source_attribution.json",
        "sim/analysis_r17_native_benchmark.py", "sim/analysis_r17_native_benchmark.json",
        "sim/analysis_r17_weight_regions.py", "sim/analysis_r17_weight_regions.json",
        "sim/analysis_r18_native_joint_audit.py", "sim/analysis_r18_native_joint_audit.json",
        "sim/analysis_r19_joint_audit.py", "sim/analysis_r19_joint_audit.json",
        "sim/analysis_r19_sampling_study.py", "sim/analysis_r19_sampling_study.json",
        "sim/analysis_r20_joint_audit.py", "sim/analysis_r20_joint_audit.json",
        "sim/analysis_r20_detection_study.py", "sim/analysis_r20_detection_study.json",
        "sim/analysis_r21_joint_audit.py", "sim/analysis_r21_joint_audit.json",
        "sim/analysis_r21_detection_study.py", "sim/analysis_r21_detection_study.json",
        "sim/analysis_r22_joint_audit.py", "sim/analysis_r22_joint_audit.json",
        "sim/analysis_r22_detection_study.py", "sim/analysis_r22_detection_study.json",
        "sim/runs/20261117_r15/validation.json", "sim/runs/20261117_r16/validation.json",
        "sim/runs/20261119_r17/validation.json", "sim/runs/20261121_r18/validation.json",
        "sim/runs/20261122_r19/validation.json", "sim/runs/20261122_r20/validation.json",
        "sim/runs/20261122_r21/validation.json",
        "sim/runs/20261119_r17/PROVENANCE.md", "sim/runs/20261121_r18/PROVENANCE.md",
        "sim/runs/20261122_r19/PROVENANCE.md", "sim/runs/20261122_r19/REPLAY_FAILURE_R18.md",
        "sim/runs/20261122_r20/PROVENANCE.md", "sim/runs/20261122_r21/PROVENANCE.md",
        "sim/runs/20261123_r22/PROVENANCE.md",
        "tools/make_r17_validation.py", "tools/make_r18_validation.py",
        "tools/make_r19_validation.py", "tools/make_r20_validation.py",
        "tools/make_r21_validation.py", "tools/make_r22_validation.py",
    }
    for base, pattern in [(latex / "sections", "*.tex"),
                          (sim / "src/autonomy_sim", "*.py"),
                          (sim / "tests", "*.py")]:
        for path in base.glob(pattern):
            tracked.add(str(path.relative_to(root)))
    result = {
        "artifact_version": "R22-frozen-source-validation-v1",
        "source_commit": source_commit,
        "source_tree": tree,
        "worktree_clean_before_and_after_commands": True,
        "environments": environment_records,
        "tests": {"ran": test_count, "passed": test_count},
        "paper": {
            "pages": pages, "page_cap": None,
            "clean_build_text_match": True,
            "ghostscript_all_pages": True, "bibliography_entries": bibliography_entries,
            "figures": figures, "title": title, "author": author,
            "float_too_large": False, "undefined_references_or_citations": False,
            "max_overfull_pt": max(overfull, default=0.0),
            "fonts_embedded": True, "font_unicode_maps": True,
            "font_count": len(font_rows), "abstract_deversioned": True,
        },
        "sha256": {name: sha(root / name) for name in sorted(tracked)},
        "scope": {
            "current_source_commit_replay": True,
            "two_independent_clean_environments": True,
            "environments_differ_in_thread_hash_not_platform": True,
            "historical_r11_r21_files_modified": False,
            "r21_artifacts_byte_identical": True,
            "r18_cross_environment_replay_failure_recorded": True,
            "r18_r17_native_numerical_blocks_read_only_integrity": True,
            "detection_rule_data_driven_declared_before_outcomes": True,
            "detection_inside_formal_certificate": True,
            "oracle_rule_labeled_fixture_only": True,
            "interval_sensitivity_three_state_not_midpoint_agreement": True,
            "real_interval_propagation_with_kinds": True,
            "composite_intervals_share_conditional_with_conditioning_scope": True,
            "logical_envelope_containment_separated_from_sampling_coverage": True,
            "joint_bootstrap_supplementary_diagnostic_not_reported_semantics": True,
            "matched_A_B_C_common_replicates": True,
            "resampling_input_and_mask_audits_platform_independent": True,
            "no_native_float_output_byte_hash_dependency": True,
            "matched_output_alias_consistency_checked": True,
            "empirical_error_thresholds_as_pass_conditions": False,
            "B_vs_C_matched_percentile_channel_propagation_contrast": True,
            "A_vs_B_interval_construction_contrast": True,
            "descriptive_interval_method_contrast_not_causal_attribution": True,
            "r21_conditional_design_attribution_withdrawn": True,
            "formal_bias_decomposition": False,
            "plugin_bias_assessed_by_separate_exact_truth_simulation": True,
            "tests_decoupled_from_empirical_expectations": True,
            "external_protocol_design_frozen": True,
            "external_protocol_executed": False,
            "external_construct_validation": False,
            "external_sesoi_or_power": False,
            "engineering_equivalence_margins_frozen": True,
            "sensitivity_thresholds_post_hoc_frozen": True,
            "detection_limit_value_post_hoc_frozen_inherited": True,
            "selector_conditional_del1_estimator": False,
            "immutable_tag": "v1.5-r22 (created on the final synchronization commit)",
            "formal_release": False,
            "version_doi": False,
            "old_spec_snapshots_recovered": False,
            "legacy_org_via_or_bundle_upgraded": False,
            "lean_certification": False,
        },
    }
    out = root / "sim/runs/20261123_r22/validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"R22 frozen-source validation PASS: commit={source_commit}, "
          f"tests={test_count}, pages={pages}, references={bibliography_entries}, "
          f"environments={len(environment_records)}")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
