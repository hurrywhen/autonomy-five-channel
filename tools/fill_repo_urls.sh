#!/usr/bin/env bash
# fill_repo_urls.sh — 将公开发布快照中的仓库 URL 占位符（GHUSER / GITEEUSER）
# 替换为真实用户名，并重编译论文 PDF 与 arXiv 源码包。
#
# 用法：tools/fill_repo_urls.sh <github_user> <gitee_user> [snapshot_root]
#   snapshot_root 缺省为本脚本所在目录的上一级（即快照仓库根）。
# 说明：占位符出现在 latex/main.tex（Data and code availability）、
#   README.md、CITATION.cff 中；替换后 PDF 与 arXiv 包自动重建。
set -euo pipefail
GH="${1:?usage: fill_repo_urls.sh <github_user> <gitee_user> [snapshot_root]}"
GITEE="${2:?missing gitee_user}"
ROOT="${3:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

echo "[fill] snapshot root: $ROOT"
grep -rl 'GHUSER\|GITEEUSER' "$ROOT" \
  --include='*.tex' --include='*.md' --include='*.cff' --include='*.bib' 2>/dev/null |
while read -r f; do
  sed -i "s/GHUSER/${GH}/g; s/GITEEUSER/${GITEE}/g" "$f"
  echo "[fill]   $f"
done || true

# 同级 arxiv/ 与 preprint/ 元数据文件（若存在，dev 树 dist/ 布局）
for SIB in "$(dirname "$ROOT")/arxiv" "$(dirname "$ROOT")/preprint"; do
  if [ -d "$SIB" ]; then
    grep -rl 'GHUSER\|GITEEUSER' "$SIB" --include='*.md' 2>/dev/null |
    while read -r f; do
      sed -i "s/GHUSER/${GH}/g; s/GITEEUSER/${GITEE}/g" "$f"
      echo "[fill]   $f"
    done || true
  fi
done

# 重编译论文 PDF（两遍，交叉引用稳定）
( cd "$ROOT/latex" && pdflatex -interaction=nonstopmode main.tex >/dev/null \
  && pdflatex -interaction=nonstopmode main.tex >/dev/null )
echo "[fill] rebuilt $ROOT/latex/main.pdf ($(pdfinfo "$ROOT/latex/main.pdf" | awk '/^Pages/{print $2}') pages)"

# 重建 arXiv 源码包（仅当 arxiv 目录与快照同级存在时）
ARX="$(dirname "$ROOT")/arxiv"
if [ -d "$ARX" ]; then
  ( cd "$ROOT/latex" && tar czf "$ARX/autonomy-five-channel-arxiv-src.tar.gz" \
      main.tex main.bbl appendix.tex related_work.tex refs.bib sections figures )
  echo "[fill] rebuilt $ARX/autonomy-five-channel-arxiv-src.tar.gz"
fi

if grep -rq 'GHUSER\|GITEEUSER' "$ROOT" \
     --include='*.tex' --include='*.md' --include='*.cff' 2>/dev/null; then
  echo "[fill] WARNING: 仍有占位符残留："
  grep -rn 'GHUSER\|GITEEUSER' "$ROOT" --include='*.tex' --include='*.md' --include='*.cff'
  exit 1
else
  echo "[fill] 全部占位符已填充。"
fi
