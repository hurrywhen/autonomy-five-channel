#!/usr/bin/env bash
# make_arxiv_package.sh — 构建 arXiv 源码包。
# 用法：tools/make_arxiv_package.sh [snapshot_root]
#   snapshot_root 缺省为本脚本所在目录的上一级（快照仓库根，含 latex/）。
# 输出：与 snapshot_root 同级的 arxiv/autonomy-five-channel-arxiv-src.tar.gz
#
# 与仓库权威源的唯一差异（仅 arXiv 包内 main.tex）：
#   1) 条件文档类 \IfFileExists{sn-jnl.cls}{...}{article} 固定为 article——
#      arXiv 依赖扫描把条件分支误报为 "missing file: sn-jnl"；
#   2) 删除提及 sn-jnl / \documentclass 的注释行，避免扫描器把注释当依赖。
# 论文正文、公式、图表、参考文献与权威源逐字一致。
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
ROOT="$(cd "$ROOT" && pwd)"   # 绝对化：后续在临时目录中工作，输出路径不能相对
OUT="$(dirname "$ROOT")/arxiv"
mkdir -p "$OUT"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

cp -r "$ROOT/latex/sections" "$ROOT/latex/figures" "$STAGE/"
cp "$ROOT/latex/appendix.tex" "$ROOT/latex/related_work.tex" \
   "$ROOT/latex/refs.bib" "$ROOT/latex/main.bbl" "$STAGE/"

python3 - "$ROOT/latex/main.tex" "$STAGE/main.tex" <<'PYEOF'
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()

old = """\\IfFileExists{sn-jnl.cls}
  {\\documentclass[sn-mathphys-num,numbered]{sn-jnl}}
  {\\documentclass[11pt]{article}}"""
new = """% arXiv build: article class fixed. The journal submission uses the Springer
% Nature class in the development repository; the conditional class loader is
% removed here so that arXiv's dependency scan does not request that file.
\\documentclass[11pt]{article}"""
assert old in s, "conditional class block not found"
s = s.replace(old, new, 1)

# 删除提及 sn-jnl 或 \documentclass 的注释行（含头部切换说明与作者块切换注释）
lines = []
skip_prefixes = ("% --- Author block.",)
in_author_comment = False
for ln in s.split("\n"):
    st = ln.strip()
    if st.startswith(skip_prefixes):
        in_author_comment = True
        continue
    if in_author_comment:
        if st.startswith("%"):
            continue
        in_author_comment = False
    if st.startswith("%") and ("sn-jnl" in ln or "\\documentclass" in ln):
        continue
    lines.append(ln)
s = "\n".join(lines)
assert "sn-jnl" not in s, "sn-jnl still present"
open(dst, "w", encoding="utf-8").write(s)
print("[arxiv] main.tex patched: article fixed, sn-jnl references removed")
PYEOF

( cd "$STAGE" && tar czf "$OUT/autonomy-five-channel-arxiv-src.tar.gz" \
    main.tex main.bbl appendix.tex related_work.tex refs.bib sections figures )
echo "[arxiv] wrote $OUT/autonomy-five-channel-arxiv-src.tar.gz"

# 干净目录试编译验证（pdflatex 两遍；无需 bibtex，使用 main.bbl）
if command -v pdflatex >/dev/null 2>&1; then
  ( cd "$STAGE" \
    && pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1 \
    && pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1 )
  echo "[arxiv] test compile: $(grep -c '^!' "$STAGE/main.log") errors; \
$(grep 'Output written' "$STAGE/main.log")"
  if grep -qi "float too large" "$STAGE/main.log"; then
    echo "[arxiv] WARNING: float overflow present"; exit 1
  fi
fi
