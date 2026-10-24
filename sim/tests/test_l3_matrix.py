"""L3 矩阵回归冒烟（SPEC_tests §4：X-MATRIX-SMOKE、X-META；SPEC_experiments §9 M9.1–M9.7）。

冒烟网格：6 场景（ATK-1~6）× 2 防御配置 {(0,0,0),(1,1,1)} × σ∈{0.5,1} × 2 种子 = 48 run；
完整 30 种子矩阵为批处理（7d），不进 CI。
"""
import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import logschema, matrix  # noqa: E402
from autonomy_sim.env0 import Env0Config, build_env0  # noqa: E402
from autonomy_sim.scenarios import Verdict  # noqa: E402

N_SMOKE = 6 * 2 * 2 * 2  # 场景 × 防御 × σ × 种子


class TestL3Matrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="l3_matrix_")
        cls.rows = matrix.run_matrix(
            scenarios=(1, 2, 3, 4, 5, 6), defenses=((0, 0, 0), (1, 1, 1)),
            sigmas=(0.5, 1.0), reps=2, out_dir=cls.tmp, grids=matrix.SMOKE_GRIDS)
        cls.meta = matrix.xmeta_check(cls.rows)

    # ------------------------------------------------------------ X-MATRIX-SMOKE
    def test_XMATRIX_SMOKE(self):
        rows = self.rows
        # 48 行齐、坐标全覆盖
        self.assertEqual(len(rows), N_SMOKE)
        coords = {(r["scenario_code"], r["config_code"], r["sigma"], r["rep"]) for r in rows}
        self.assertEqual(len(coords), N_SMOKE)
        for r in rows:
            self.assertIsInstance(r["overall"], Verdict)
            self.assertEqual(r["config_code"], 4 * r["m1"] + 2 * r["m2"] + r["m4"])
        # REFUTED 零容忍（2026-10-16 恢复全零）：ATK-4 C1 在 A_epi 精度化首跑曾翻转，
        # 根因=α 臂探针坐标错位（场景操作化缺陷），修复探针对齐 i=κ(e) 后结案
        # （见 test_l2_scenarios.test_XATK4 注记）——登记例外已退役，任何 REFUTED 均失败。
        refuted = sorted({(r["scenario_code"], r["config_code"], r["sigma"], r["rep"])
                          for r in rows if r["overall"] == Verdict.REFUTED})
        self.assertEqual(refuted, [], msg=f"REFUTED 行: {refuted}")
        # 无防御 cell：攻击物理 verdict 权威落定，全部 CONFIRMED
        for r in rows:
            if r["config_code"] == 0:
                self.assertEqual(r["overall"], Verdict.CONFIRMED,
                                 msg=f"无防御 cell 应 CONFIRMED: s{r['scenario_code']} σ={r['sigma']} rep={r['rep']}")
        # 防御方向断言（M9.7）：ATK-1/2 防御臂末端档 a_obj 不差于无防御臂
        direction = matrix.defense_direction(rows)
        for code in (1, 2):
            self.assertTrue(all(v for k, v in direction.items() if k[0] == code),
                            msg=f"场景 {code} 防御方向断言失败: {direction}")
        # 产出物四件齐备且格式正确（M9.5）
        f_csv = os.path.join(self.tmp, "results.csv")
        f_tab = os.path.join(self.tmp, "verdict_table.csv")
        f_man = os.path.join(self.tmp, "manifest.json")
        for f in (f_csv, f_tab, f_man):
            self.assertTrue(os.path.isfile(f), msg=f"缺产出物 {f}")
        with open(f_csv, newline="", encoding="utf-8") as fh:
            csv_rows = list(csv.DictReader(fh))
        self.assertEqual(len(csv_rows), N_SMOKE)
        for col in ("scenario_code", "config_code", "sigma", "rep", "seed", "overall", "metrics_json"):
            self.assertIn(col, csv_rows[0])
        self.assertTrue(any(c.startswith("V:") for c in csv_rows[0]))
        json.loads(csv_rows[0]["metrics_json"])  # metrics_json 可解析
        with open(f_tab, newline="", encoding="utf-8") as fh:
            tab = list(csv.DictReader(fh))
        self.assertEqual(len(tab), 6 * 2 * 2)  # cell=(场景, 防御, σ)
        with open(f_man, encoding="utf-8") as fh:
            man = json.load(fh)
        for key in ("type", "spec_version", "matrix_id", "created", "git_commit", "grid", "n_runs"):
            self.assertIn(key, man)
        self.assertEqual(man["n_runs"], N_SMOKE)
        # 抽样 NDJSON 日志：每 (场景, 防御) 一条，过 P8.3 完整性校验
        log_dir = os.path.join(self.tmp, "logs")
        logs = sorted(f for f in os.listdir(log_dir) if f.endswith(".ndjson"))
        self.assertEqual(len(logs), 6 * 2)
        al = build_env0(Env0Config()).alphabet
        for name in logs:
            meta, trajs = logschema.read_run(os.path.join(log_dir, name))
            errors = logschema.validate_log(meta, [rec for tr in trajs for rec in tr], al)
            self.assertEqual(errors, [], msg=f"{name} 日志校验失败: {errors}")

    # ------------------------------------------------------------ X-META（P3.5 操作化，M9.6）
    def test_XMETA(self):
        # M9.6 v0.5：盲见证表五类全集（β_G/γ/β_π/τ/δ）——δ 类由 EXEC-1 臂束登记，
        # 冒烟矩阵外补一条 EXEC-1 run（对应 make_report 的 main+exec1 合并口径）
        from autonomy_sim.scenarios import scenario_exec1
        rows = list(self.rows)
        res = scenario_exec1()
        rows.append({"scenario_code": 16, "config_code": 0, "sigma": 1.0, "rep": 0,
                     "seed": 0, "overall": res.overall.value, "metrics": res.metrics})
        meta = matrix.xmeta_check(rows)
        for key in ("C1_range", "C2_zero_attribution", "C3_no_single_channel", "C4_sigma_robust"):
            self.assertTrue(meta[key], msg=f"元判据 {key} 失败: {json.dumps(meta['details'], ensure_ascii=False, default=str)[:800]}")
        # 盲见证表实质性：五类攻击登记
        det = meta["details"]["detect_table"]
        self.assertGreaterEqual(len(meta["details"]["attack_classes"]), 5)
        # 签名内容锚：β_π 经 Λ 因子响应 a_ref；δ 仅 a_exec；τ 仅 a_ref；交集为空
        self.assertEqual(set(det["beta_pi"]), {"a_org", "a_ref"})
        self.assertEqual(set(det["delta"]), {"a_exec"})
        self.assertEqual(set(det["tau"]), {"a_ref"})
        inter = set.intersection(*(set(v) for v in det.values()))
        self.assertEqual(inter, set())


if __name__ == "__main__":
    unittest.main()
