#!/usr/bin/env python3
"""Validate R15 from a clean worktree and write a new textual replay manifest.

Run from the exact clean R15 content worktree.  The script never writes to
historical R11--R14 directories and builds LaTeX only in /tmp/opencode.
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


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], cwd: Path) -> dict:
    started = time.monotonic()
    proc = subprocess.run(command, cwd=cwd, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = proc.stdout
    if proc.returncode:
        print(output)
        raise SystemExit(f"validation command failed ({proc.returncode}): {' '.join(command)}")
    return {"command": command, "returncode": proc.returncode,
            "seconds": round(time.monotonic() - started, 3),
            "summary": output.strip().splitlines()[-8:]}


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                            text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=root,
                                   text=True).strip()
    dirty_before = bool(subprocess.check_output(["git", "status", "--porcelain"],
                                                cwd=root, text=True).strip())
    if dirty_before:
        raise SystemExit("frozen validation requires a clean worktree")
    sim = root / "sim"
    required_archive = [sim / "runs/20261017_full/estimator_checks.json",
                        sim / "runs/20261017_full/main/results.csv",
                        sim / "runs/20261102_r11/del1/results.csv"]
    missing = [str(path.relative_to(root)) for path in required_archive if not path.is_file()]
    if missing:
        raise SystemExit(
            "clean checkout lacks the read-only historical evidence required for full validation: "
            + ", ".join(missing)
            + ". Use the complete public snapshot rather than claiming a self-contained replay.")
    results = []
    results.append(run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], sim))
    for command in [
        ["run_x5c_r14.py", "--out", "runs/20261116_r14/x5c", "--check"],
        ["run_x5c_r14_stratified.py", "--out", "runs/20261116_r14/x5c_stratified", "--check"],
        ["run_c0cf_r14.py", "--out", "runs/20261116_r14/c0cf_v2", "--check"],
        ["analysis_r15_statistics.py", "--check"],
        ["analysis_r15_x5c_paired.py", "--check"],
    ]:
        results.append(run([sys.executable, *command], sim))
    test_text = "\n".join(results[0]["summary"])
    match = re.search(r"Ran (\d+) tests", test_text)
    if not match or int(match.group(1)) != 194:
        raise SystemExit(f"expected 194 tests, got {test_text!r}")

    latex = root / "latex"
    build = Path(tempfile.mkdtemp(prefix="r15-frozen-build-", dir="/tmp/opencode"))
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
        run(["pdftotext", "main.pdf", "clean.txt"], build)
        run(["pdftotext", str(latex / "main.pdf"), "reference.txt"], build)
        run(["cmp", "clean.txt", "reference.txt"], build)
        run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=nullpage", "main.pdf"], build)
        info = run(["pdfinfo", "main.pdf"], build)
        pages_line = next(line for line in info["summary"] if line.startswith("Pages:"))
        pages = int(pages_line.split()[1])
    finally:
        shutil.rmtree(build)

    dirty_after = bool(subprocess.check_output(["git", "status", "--porcelain"],
                                               cwd=root, text=True).strip())
    if dirty_after:
        raise SystemExit("validation dirtied the frozen worktree")
    tracked = [
        "latex/main.tex", "latex/main.pdf", "latex/main.bbl", "latex/refs.bib",
        "sim/SPEC_estimators.md", "sim/SPEC_experiments.md", "sim/SPEC_tests.md",
        "sim/analysis_r15_statistics.py", "sim/analysis_r15_statistics.json",
        "sim/analysis_r15_x5c_paired.py", "sim/analysis_r15_x5c_paired.json",
        "sim/src/autonomy_sim/r15_guards.py", "sim/src/autonomy_sim/stats.py",
        "sim/tests/test_r15_reviewer_counterexamples.py",
    ]
    result = {
        "artifact_version": "R15-frozen-source-validation-v1",
        "source_commit": source_commit,
        "source_tree": tree,
        "worktree_clean_before_and_after": True,
        "commands": results,
        "tests": {"ran": 194, "passed": 194},
        "paper": {"pages": pages, "clean_build_text_match": True,
                  "ghostscript_all_pages": True, "bibliography_entries": 113,
                  "figures": 6},
        "sha256": {name: sha(root / name) for name in tracked},
        "scope": {
            "current_source_commit_replay": True,
            "historical_r14_files_modified": False,
            "immutable_tag": False,
            "formal_release": False,
            "version_doi": False,
            "external_construct_validation": False,
            "old_spec_snapshots_recovered": False,
            "legacy_org_via_upgraded": False,
        },
    }
    out = root / "sim/runs/20261117_r15/validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"R15 frozen-source validation PASS: commit={source_commit}, tests=194, pages={pages}")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
