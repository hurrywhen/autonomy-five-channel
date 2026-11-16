"""R14 report-generator evidence-status regression."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "runs" / "20261017_full" / "report.md"


class R14Report(unittest.TestCase):
    def test_R14_report_separates_history_math_and_external_status(self):
        before = HISTORICAL.read_bytes() if HISTORICAL.exists() else None
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "r14_report.md"
            subprocess.run([
                os.fspath(Path(sys.executable)),
                os.fspath(ROOT / "make_report.py"),
                "--root", os.fspath(ROOT / "runs" / "20261017_full"),
                "--output", os.fspath(out),
            ], cwd=ROOT, check=True, capture_output=True, text=True)
            text = out.read_text(encoding="utf-8")
        self.assertIn("R14 当前状态", text)
        self.assertIn("ANALYTIC PASS（T-R14-T1B", text)
        self.assertIn("DESCRIPTIVE（HI 期望/触发概率界未执行）", text)
        self.assertIn("D_noise=0.089799622", text)
        self.assertIn("MODEL_SENSITIVE", text)
        self.assertIn("C0-CF-v2：同环境全轨迹 (E^T,O^T,A^T)=True", text)
        self.assertIn("A_exec=1.000/1.000", text)
        self.assertIn("c0cf", text)
        self.assertIn("旧 law_level_lambda 一律是 legacy marker", text)
        self.assertIn("其他重复不是 CES 内点 KKT 验证", text)
        self.assertIn("不得声称一般 rank consistency", text)
        self.assertNotIn("运行正性：A_via=0", text)
        self.assertNotIn("支持 R13 的非退化 TV=1 解析证人", text)
        self.assertNotIn("fourteen CONFIRMED", text)
        if before is not None:
            self.assertEqual(HISTORICAL.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
