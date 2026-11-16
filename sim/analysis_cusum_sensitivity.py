#!/usr/bin/env python3
"""R13 CUSUM 小样本敏感性重算；只读历史归档，不生成新仿真 run。

读取 runs/20261017_full/main/results.csv 中 ATK-6、config=0、sigma=1 的
30 个种子级比值，输出原始比值、正态近似区间和 Student-t(29) 区间。
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

T_29_975 = 2.045229642132703


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path,
                        default=Path(__file__).parent / "runs/20261017_full/main/results.csv")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "analysis_cusum_sensitivity.json")
    args = parser.parse_args()

    records = []
    with args.source.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if (int(row["scenario_code"]) == 6 and int(row["config_code"]) == 0
                    and float(row["sigma"]) == 1.0):
                damages = json.loads(row["metrics_json"])["damages_detect"]
                records.append({
                    "rep": int(row["rep"]),
                    "seed": int(row["seed"]),
                    "damage_delta_0.25": damages[0],
                    "damage_delta_0.125": damages[1],
                    "ratio": damages[1] / damages[0],
                })
    records.sort(key=lambda item: item["rep"])
    if [item["rep"] for item in records] != list(range(30)):
        raise RuntimeError("expected exactly ATK-6 replications 0..29 at config=0, sigma=1")

    ratios = [item["ratio"] for item in records]
    mean = statistics.mean(ratios)
    sd = statistics.stdev(ratios)
    standard_error = sd / math.sqrt(len(ratios))
    result = {
        "analysis": "R13 CUSUM seed-ratio sensitivity; derived read-only recomputation, not a new run",
        "source": str(args.source),
        "source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
        "selection": {"scenario_code": 6, "config_code": 0, "sigma": 1.0},
        "paths_per_drift_per_seed": 200,
        "path_pairing": "sequential streams within each seed; not common-random-number pairs",
        "n_seed_ratios": len(records),
        "records": records,
        "mean": mean,
        "sample_sd": sd,
        "standard_error": standard_error,
        "normal_95": {
            "critical": 1.96,
            "half_width": 1.96 * standard_error,
            "interval": [mean - 1.96 * standard_error, mean + 1.96 * standard_error],
        },
        "student_t_95_sensitivity": {
            "df": 29,
            "critical": T_29_975,
            "half_width": T_29_975 * standard_error,
            "interval": [mean - T_29_975 * standard_error,
                         mean + T_29_975 * standard_error],
        },
        "scope": "fixed-alpha ENV-0 description; not a test of the fixed-delta Lorden-Lai asymptotic",
    }
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(f"wrote {args.output}: mean={mean:.9f}, normal half={1.96 * standard_error:.9f}, "
          f"t29 half={T_29_975 * standard_error:.9f}")


if __name__ == "__main__":
    main()
