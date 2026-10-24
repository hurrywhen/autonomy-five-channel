#!/usr/bin/env python3
"""R3c 全矩阵批处理（SPEC_experiments §2 实验矩阵／§6 产出物；M9.5 schema）。

用法：python3 run_matrix.py [--out ROOT] [--quick]
分组（每组一个子目录，M9.5 四件产出物）：
  main          ATK-1~6 × 防御 2³ × σ∈{0.5,1} × 30 种子 = 2880 run
  stress_sigma2 同网格 σ=2（AX5 松弛压力测试，1440 run，单列"哪些结论翻转"）
  del1/c0_demo/c0corr/res1/force1/bb1/lh1/bb2/erosion/exec1  独立实验组（σ=1、defense=(0,0,0)、30 种子）
  ——独立组 10 组 × 30 = 300 run；全矩阵总计 4620 run（v0.5）
--quick：冒烟参数（2 种子、2 防御、SMOKE_GRIDS），用于脚本链路自检。
"""
import argparse
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from autonomy_sim.matrix import SMOKE_GRIDS, run_matrix  # noqa: E402

DEFENSES_8 = tuple((m1, m2, m4) for m1 in (0, 1) for m2 in (0, 1) for m4 in (0, 1))
INDEPENDENT = ((7, "del1"), (8, "c0_demo"), (13, "c0corr"), (10, "res1"),
               (11, "force1"), (12, "bb1"), (9, "lh1"), (14, "bb2"),
               (15, "erosion"), (16, "exec1"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    root = args.out or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "runs", f"{time.strftime('%Y%m%d')}_full")

    if args.quick:
        groups = [("quick_main", dict(scenarios=(1, 2, 3, 4, 5, 6),
                                      defenses=((0, 0, 0), (1, 1, 1)),
                                      sigmas=(0.5, 1.0), reps=2, grids=SMOKE_GRIDS))]
    else:
        groups = [
            # 独立组先行（快，早出产出物）
            *[(mid, dict(scenarios=(code,), defenses=((0, 0, 0),), sigmas=(1.0,), reps=30))
              for code, mid in INDEPENDENT],
            ("main", dict(scenarios=(1, 2, 3, 4, 5, 6), defenses=DEFENSES_8,
                          sigmas=(0.5, 1.0), reps=30)),
            ("stress_sigma2", dict(scenarios=(1, 2, 3, 4, 5, 6), defenses=DEFENSES_8,
                                   sigmas=(2.0,), reps=30)),
        ]

    failures = []
    for mid, kw in groups:
        out_dir = os.path.join(root, mid)
        t0 = time.perf_counter()
        print(f"[group {mid}] start -> {out_dir}", flush=True)
        try:
            rows = run_matrix(out_dir=out_dir, matrix_id=mid, **kw)
        except Exception:
            failures.append(mid)
            traceback.print_exc()
            continue
        from autonomy_sim.scenarios import Verdict
        from collections import Counter
        dist = Counter(r["overall"].value for r in rows)
        print(f"[group {mid}] done {len(rows)} runs in {time.perf_counter()-t0:.1f}s "
              f"verdicts={dict(dist)}", flush=True)
    print(f"[batch] root={root} failures={failures}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
