#!/usr/bin/env python3
"""Validate the editorial-only R23 content commit from clean worktrees.

R23 changes presentation, not science. Numerical source/tests/artifacts and all
historical run directories through R22 must be byte-identical to the R22 public
baseline. Two same-platform thread/hash environments run the complete test
suite and stable replays. Frozen full-grid artifacts receive read-only
structural/anchor validation; their R22 two-environment numerical recomputation
is inherited, not falsely claimed as a new R23 full-grid run.

The paper must be independently rebuilt, fewer than R22's 105 pages, with 115
cited references, 6 figures, clean text equality, embedded Unicode fonts, and
maximum overfull <=10 pt. No font/geometry/figure scaling change is allowed as
a page-reduction device. This sidecar is not external validation or a DOI.
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

R22_PUBLIC_BASELINE = "c8e691be98a9516128b08d9e601055207c72a4b2"
EXPECTED_TESTS = 429
EXPECTED_REFERENCES = 115
EXPECTED_FIGURES = 6
PREVIOUS_PAGES = 105
MAX_OVERFULL_PT = 10.0
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
        f"print('{module} frozen artifact integrity + anchors OK')"
    )
    return run([sys.executable, "-c", snippet], cwd, env_overrides=env_overrides)


def editorial_only_changes(root: Path) -> tuple[list[str], list[str]]:
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", R22_PUBLIC_BASELINE, "HEAD"],
        cwd=root, text=True).splitlines()
    numerical = []
    for name in changed:
        historical_run = name.startswith("sim/runs/") and not name.startswith(
            "sim/runs/20261124_r23/")
        analysis_file = re.fullmatch(r"sim/analysis_.*\.(?:py|json)", name) is not None
        if (name.startswith(("sim/src/", "sim/tests/")) or historical_run
                or analysis_file):
            numerical.append(name)
    if numerical:
        raise SystemExit("R23 must not alter numerical source/artifacts: "
                         + ", ".join(numerical))
    return changed, numerical


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                            text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=root,
                                   text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root,
                               text=True).strip():
        raise SystemExit("frozen validation requires a clean worktree")
    changed_files, numerical_changes = editorial_only_changes(root)

    sim = root / "sim"
    required = [
        sim / "analysis_r17_native_benchmark.json",
        sim / "analysis_r18_native_joint_audit.json",
        sim / "analysis_r19_sampling_study.json",
        sim / "analysis_r20_detection_study.json",
        sim / "analysis_r21_joint_audit.json",
        sim / "analysis_r21_detection_study.json",
        sim / "analysis_r22_joint_audit.json",
        sim / "analysis_r22_detection_study.json",
        sim / "runs/20261122_r19/REPLAY_FAILURE_R18.md",
        sim / "runs/20261123_r22/validation.json",
        sim / "runs/20261124_r23/PROVENANCE.md",
        sim / "runs/20261124_r23/TECHNICAL_SUPPLEMENT.md",
        root / "latex/main.bbl",
    ]
    missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("clean checkout lacks required evidence: " + ", ".join(missing))
    r22_validation = json.loads((sim / "runs/20261123_r22/validation.json").read_text(
        encoding="utf-8"))
    if (r22_validation["tests"] != {"ran": 429, "passed": 429}
            or len(r22_validation["environments"]) != 2):
        raise SystemExit("R22 two-environment numerical validation is not intact")

    stable_replays = [
        ["run_x5c_r14.py", "--out", "runs/20261116_r14/x5c", "--check"],
        ["run_x5c_r14_stratified.py", "--out", "runs/20261116_r14/x5c_stratified", "--check"],
        ["run_c0cf_r14.py", "--out", "runs/20261116_r14/c0cf_v2", "--check"],
        ["analysis_r15_statistics.py", "--check"],
        ["analysis_r15_x5c_paired.py", "--check"],
        ["analysis_r16_source_attribution.py", "--check"],
        ["analysis_r17_weight_regions.py", "--check"],
        ["analysis_r19_joint_audit.py", "--check"],
        ["analysis_r20_joint_audit.py", "--check"],
        ["analysis_r21_joint_audit.py", "--check"],
        ["analysis_r22_joint_audit.py", "--check"],
    ]
    frozen_integrity = [
        ("analysis_r17_native_benchmark", "analysis_r17_native_benchmark.json"),
        ("analysis_r18_native_joint_audit", "analysis_r18_native_joint_audit.json"),
        ("analysis_r19_sampling_study", "analysis_r19_sampling_study.json"),
        ("analysis_r20_detection_study", "analysis_r20_detection_study.json"),
        ("analysis_r21_detection_study", "analysis_r21_detection_study.json"),
        ("analysis_r22_detection_study", "analysis_r22_detection_study.json"),
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
        for module, artifact in frozen_integrity:
            records.append(read_only_integrity(module, artifact, sim, overrides))
        environment_records.append({"label": environment["label"],
                                    "env_overrides": overrides,
                                    "commands": records})

    latex = root / "latex"
    build = Path(tempfile.mkdtemp(prefix="r23-frozen-build-", dir="/tmp/opencode"))
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
        max_overfull = max(overfull, default=0.0)
        if max_overfull > MAX_OVERFULL_PT:
            raise SystemExit(f"overfull limit exceeded: {max_overfull} > {MAX_OVERFULL_PT}")
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
        if not 0 < pages < PREVIOUS_PAGES:
            raise SystemExit(f"R23 must reduce pages below {PREVIOUS_PAGES}, got {pages}")
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
        bibliography_entries = len(re.findall(
            r"^\\bibitem", (build / "main.bbl").read_text(encoding="utf-8"),
            flags=re.MULTILINE))
        bibliography_database = len(re.findall(
            r"^@[A-Za-z]+\s*\{", (latex / "refs.bib").read_text(encoding="utf-8"),
            flags=re.MULTILINE))
        if bibliography_entries != EXPECTED_REFERENCES or bibliography_database != EXPECTED_REFERENCES:
            raise SystemExit("reference database/cited-entry count drift: "
                             f"database={bibliography_database}, cited={bibliography_entries}")
    finally:
        shutil.rmtree(build)

    tex_files = [latex / "main.tex", latex / "appendix.tex", latex / "related_work.tex",
                 *sorted((latex / "sections").glob("*.tex"))]
    figures = sum(path.read_text(encoding="utf-8").count(r"\begin{figure}")
                  for path in tex_files)
    if figures != EXPECTED_FIGURES:
        raise SystemExit(f"expected {EXPECTED_FIGURES} figures, got {figures}")
    main_text = (latex / "main.tex").read_text(encoding="utf-8")
    abstract = main_text.split(r"\begin{abstract}", 1)[1].split(r"\end{abstract}", 1)[0]
    if re.search(r"\bR(?:1[1-9]|2[0-3])\b", abstract) or "reviewer" in abstract.lower():
        raise SystemExit("abstract contains revision-narration markers")
    all_tex = "\n".join(path.read_text(encoding="utf-8") for path in tex_files)
    for phrase in ["conditional-design attributable", "quantifies the second cause",
                   "both-miss cells reflect residual plug-in bias"]:
        if phrase in all_tex:
            raise SystemExit("withdrawn causal-attribution phrase found: " + phrase)
    abstract_flat = re.sub(r"\s+", " ", abstract)
    for phrase in ["universal interval coverage", "statistical consistency",
                   "real-LLM or human autonomy", "cross-substrate measurement standard"]:
        if phrase not in abstract_flat:
            raise SystemExit("abstract lacks explicit external-validity boundary: " + phrase)
    experiments = (latex / "sections/sec_experiments.tex").read_text(encoding="utf-8")
    for required_text in [r"\label{eq:interval-a}", r"\label{eq:interval-b}",
                          r"\label{eq:interval-c}", "descriptive\\_interval\\_method\\_contrast",
                          "source-share bias, other-channel estimation error"]:
        if required_text not in experiments:
            raise SystemExit("current matched-method evidence/boundary missing: " + required_text)
    if "tab:anchors" in experiments or "tab:logshares" in experiments:
        raise SystemExit("historical numerical tables were not relocated")
    supplement = (sim / "runs/20261124_r23/TECHNICAL_SUPPLEMENT.md").read_text(
        encoding="utf-8")
    for required_text in ["0.6496 ± 0.0486", "1.951 ± 0.034", "**0.590**",
                          "7.5e-10", "480/480"]:
        if required_text not in supplement:
            raise SystemExit("relocated technical content missing: " + required_text)

    # Presentation-only settings must not be used as a page-reduction shortcut.
    for file_name, setting in [("geometry", "\\usepackage[margin=1in]{geometry}"),
                               ("font", "\\documentclass[11pt]{article}"),
                               ("bibliography", "\\footnotesize")]:
        if setting not in main_text:
            raise SystemExit(f"unexpected {file_name} presentation change")

    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root,
                               text=True).strip():
        raise SystemExit("validation commands dirtied the frozen worktree")

    tracked = {
        "latex/main.tex", "latex/main.pdf", "latex/main.bbl", "latex/refs.bib",
        "latex/appendix.tex", "latex/related_work.tex", "latex/SUBMISSION_MANIFEST.md",
        "refs/manifest.md", "sim/README.md", "sim/SPEC_estimators.md",
        "sim/SPEC_experiments.md", "sim/SPEC_tests.md", "sim/CRITERION_VERSION_MAP.md",
        "sim/EXTERNAL_VALIDATION_PROTOCOL.md",
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
        "sim/runs/20261122_r21/validation.json", "sim/runs/20261123_r22/validation.json",
        "sim/runs/20261119_r17/PROVENANCE.md", "sim/runs/20261121_r18/PROVENANCE.md",
        "sim/runs/20261122_r19/PROVENANCE.md",
        "sim/runs/20261122_r19/REPLAY_FAILURE_R18.md",
        "sim/runs/20261122_r20/PROVENANCE.md", "sim/runs/20261122_r21/PROVENANCE.md",
        "sim/runs/20261123_r22/PROVENANCE.md", "sim/runs/20261124_r23/PROVENANCE.md",
        "sim/runs/20261124_r23/TECHNICAL_SUPPLEMENT.md",
        "tools/make_r17_validation.py", "tools/make_r18_validation.py",
        "tools/make_r19_validation.py", "tools/make_r20_validation.py",
        "tools/make_r21_validation.py", "tools/make_r22_validation.py",
        "tools/make_r23_validation.py",
    }
    for base, pattern in [(latex / "sections", "*.tex"),
                          (sim / "src/autonomy_sim", "*.py"),
                          (sim / "tests", "*.py")]:
        for path in base.glob(pattern):
            tracked.add(str(path.relative_to(root)))

    result = {
        "artifact_version": "R23-editorial-frozen-source-validation-v1",
        "source_commit": source_commit,
        "source_tree": tree,
        "r22_public_baseline": R22_PUBLIC_BASELINE,
        "editorially_changed_files": changed_files,
        "numerical_source_or_artifact_changes_since_r22": numerical_changes,
        "worktree_clean_before_and_after_commands": True,
        "environments": environment_records,
        "tests": {"ran": test_count, "passed": test_count},
        "paper": {
            "pages": pages, "previous_pages": PREVIOUS_PAGES,
            "page_reduction": PREVIOUS_PAGES - pages,
            "clean_build_text_match": True, "ghostscript_all_pages": True,
            "bibliography_database_entries": bibliography_database,
            "bibliography_entries": bibliography_entries, "all_references_cited": True,
            "figures": figures, "title": title, "author": author,
            "float_too_large": False, "undefined_references_or_citations": False,
            "max_overfull_pt": max_overfull, "max_overfull_limit_pt": MAX_OVERFULL_PT,
            "fonts_embedded": True, "font_unicode_maps": True,
            "font_count": len(font_rows), "abstract_deversioned": True,
            "geometry_font_figure_scaling_unmodified": True,
        },
        "sha256": {name: sha(root / name) for name in sorted(tracked)},
        "scope": {
            "editorial_only": True,
            "theory_or_certificate_changed": False,
            "numerical_source_or_artifacts_changed": False,
            "historical_r11_r22_files_modified": False,
            "r22_two_environment_full_grid_validation_inherited": True,
            "r23_full_detection_grids_recomputed": False,
            "frozen_detection_artifacts_read_only_validated": True,
            "stable_joint_and_statistical_replays_in_two_environments": True,
            "environments_differ_in_thread_hash_not_platform": True,
            "r18_cross_environment_replay_failure_recorded": True,
            "matched_A_B_C_content_retained": True,
            "descriptive_interval_method_contrast_not_causal_attribution": True,
            "withdrawn_causal_phrases_absent": True,
            "external_validity_boundary_explicit": True,
            "cross_substrate_construct_validation": False,
            "universal_interval_coverage_claim": False,
            "statistical_consistency_claim": False,
            "real_llm_or_human_external_validation": False,
            "deployment_ready_tool_claim": False,
            "cross_substrate_measurement_standard_claim": False,
            "external_protocol_executed": False,
            "external_sesoi_or_power": False,
            "independent_investigator_replication": False,
            "version_doi": False,
            "immutable_tag": "v1.6-r23 (created on final synchronization commit)",
            "formal_release": False,
            "technical_supplement_public": True,
            "historical_numerical_tables_relocated_not_deleted": True,
        },
    }
    out = root / "sim/runs/20261124_r23/validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"R23 editorial validation PASS: commit={source_commit}, tests={test_count}, "
          f"pages={pages} (R22={PREVIOUS_PAGES}), references={bibliography_entries}, "
          f"environments={len(environment_records)}, numerical_changes=0")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
