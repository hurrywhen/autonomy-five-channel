"""R13 报告证据链回归：不得恢复历史 DEL-1 旧 verdict 或默认写回归档。"""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestR13ReportEvidenceChain(unittest.TestCase):
    def test_T_R13_REPORT_merges_r11_del1_and_writes_only_explicit_output(self):
        sim_dir = Path(__file__).resolve().parents[1]
        root = sim_dir / "runs/20261017_full"
        historical_report = root / "report.md"
        before = historical_report.read_bytes() if historical_report.exists() else None
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "r13_report.md"
            subprocess.run(
                [sys.executable, str(sim_dir / "make_report.py"),
                 "--root", str(root), "--output", str(output)],
                cwd=sim_dir, check=True, capture_output=True, text=True, timeout=120)
            text = output.read_text(encoding="utf-8")
        self.assertIn("独立 R11 DEL-1 replay", text)
        self.assertIn("| T7 |", text)
        t7_line = next(line for line in text.splitlines() if line.startswith("| T7 |"))
        self.assertIn("INCONCLUSIVE", t7_line)
        self.assertIn("120/180", t7_line)
        self.assertNotIn("180/180", t7_line)
        t6_line = next(line for line in text.splitlines() if line.startswith("| T6 |"))
        self.assertIn("360/360", t6_line)
        self.assertIn("Student-t(29)", text)
        self.assertIn("仅为 marker", text)
        self.assertIn("当前不可识别命题由独立 identity/XOR 非退化 SCM 支持", text)
        after = historical_report.read_bytes() if historical_report.exists() else None
        self.assertEqual(before, after)

    def test_T_R13_REPORT_default_output_and_missing_replay_fails_closed(self):
        sim_dir = Path(__file__).resolve().parents[1]
        root = sim_dir / "runs/20261017_full"
        historical_report = root / "report.md"
        before = historical_report.read_bytes() if historical_report.exists() else None
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            script = temp / "make_report.py"
            shutil.copy2(sim_dir / "make_report.py", script)
            (temp / "src").symlink_to(sim_dir / "src", target_is_directory=True)
            (temp / "runs").mkdir()

            # 缺 replay 时必须失败，不得静默恢复历史 180/180。
            missing = subprocess.run(
                [sys.executable, str(script), "--root", str(root)],
                cwd=temp, check=False, capture_output=True, text=True, timeout=120)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("不得静默回落旧 180/180", missing.stderr)
            self.assertFalse((temp / "reports/20261017_full_report.md").exists())

            # replay 就绪后，无 --output 默认写临时 sim_dir/reports/，仍不写历史根。
            (temp / "runs/20261102_r11").symlink_to(
                sim_dir / "runs/20261102_r11", target_is_directory=True)
            subprocess.run(
                [sys.executable, str(script), "--root", str(root)],
                cwd=temp, check=True, capture_output=True, text=True, timeout=120)
            default_output = temp / "reports/20261017_full_report.md"
            self.assertTrue(default_output.is_file())
            text = default_output.read_text(encoding="utf-8")
            self.assertIn("120/180", next(
                line for line in text.splitlines() if line.startswith("| T7 |")))

        after = historical_report.read_bytes() if historical_report.exists() else None
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
