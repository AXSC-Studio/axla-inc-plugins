"""spec 007：当日・撤収・お礼（中間ループの終わり）の検証器。

- count_roster：名簿から件数だけを台帳に入れる。名前は残さない。--delete で元の名簿を消す
- close_event：撤収の確認・精算・お礼の送信の3つがそろったら「終了」（外側の起動トリガー）
"""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"


def run(script, *args, cwd=None):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


ROSTER = [
    {"name": "Guest A", "email": "a@guest.example", "approval_status": "approved", "checked_in_at": "2026-12-11T19:05:00+09:00", "consent": "yes"},
    {"name": "Guest B", "email": "b@guest.example", "approval_status": "approved", "checked_in_at": "", "consent": "no"},
    {"name": "Guest C", "email": "c@guest.example", "approval_status": "approved", "checked_in_at": "2026-12-11T19:20:00+09:00", "consent": ""},
    {"name": "Guest D", "email": "d@guest.example", "approval_status": "declined", "checked_in_at": "", "consent": ""},
]


class MeasureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        code, out, err = run("new_event.py", "init", "--id", "261211_startup-night", cwd=self.project)
        self.assertEqual(code, 0, err)
        self.base = self.project / "loop" / "marketing" / "event-ops"
        self.event = self.base / "events" / "261211_startup-night"
        self.roster = self.project / "roster.csv"
        with open(self.roster, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(ROSTER[0].keys()))
            w.writeheader()
            w.writerows(ROSTER)

    def tearDown(self):
        self.tmp.cleanup()

    def register_row(self):
        with open(self.base / "register.csv", encoding="utf-8") as f:
            return next(r for r in csv.DictReader(f) if r["id"] == "261211_startup-night")

    # --- count_roster ----------------------------------------------------
    def test_counts_only(self):
        code, out, err = run("count_roster.py", "--event", str(self.event), "--roster", str(self.roster))
        self.assertEqual(code, 0, err)
        row = self.register_row()
        self.assertEqual(row["applied"], "3")
        self.assertEqual(row["attended"], "2")
        self.assertEqual(row["consented"], "1")
        everything = (self.base / "register.csv").read_text(encoding="utf-8") + (self.event / "event-log.md").read_text(encoding="utf-8") + out
        for secret in ["Guest A", "a@guest.example"]:
            self.assertNotIn(secret, everything)

    def test_delete_removes_the_roster(self):
        code, out, err = run("count_roster.py", "--event", str(self.event), "--roster", str(self.roster), "--delete")
        self.assertEqual(code, 0, err)
        self.assertFalse(self.roster.exists())

    def test_unknown_columns_stop(self):
        self.roster.write_text("who,when\nx,y\n", encoding="utf-8")
        code, out, err = run("count_roster.py", "--event", str(self.event), "--roster", str(self.roster))
        self.assertEqual(code, 2, out + err)

    # --- close_event -----------------------------------------------------
    def check_teardown(self):
        rs = self.event / "run-sheet.md"
        text = rs.read_text(encoding="utf-8").replace("- [ ]", "- [x]")
        rs.write_text(text, encoding="utf-8")

    def test_not_closed_until_three_conditions(self):
        code, out, err = run("close_event.py", "status", "--event", str(self.event))
        self.assertEqual(code, 1)
        for label in ["撤収", "精算", "お礼"]:
            self.assertIn(label, out)

    def test_teardown_needs_every_box_checked(self):
        code, out, err = run("close_event.py", "teardown", "--event", str(self.event))
        self.assertEqual(code, 1, out + err)
        self.check_teardown()
        code, out, err = run("close_event.py", "teardown", "--event", str(self.event))
        self.assertEqual(code, 0, out + err)

    def test_closes_and_marks_outer_trigger(self):
        self.check_teardown()
        run("close_event.py", "teardown", "--event", str(self.event))
        run("close_event.py", "settle", "--profit", "32400", "--event", str(self.event))
        code, out, err = run("close_event.py", "thanks-sent", "--event", str(self.event))
        self.assertEqual(code, 0, out + err)
        st = json.loads((self.event / "state.json").read_text(encoding="utf-8"))
        self.assertTrue(st["closed"])
        self.assertEqual(self.register_row()["profit"], "32400")
        self.assertEqual(self.register_row()["state"], "closed")
        runs = (self.base / "runs.jsonl").read_text(encoding="utf-8")
        self.assertIn('"result": "closed"', runs)

    def test_thanks_draft_goes_to_checked_in_only(self):
        code, out, err = run("close_event.py", "thanks-draft", "--event", str(self.event))
        self.assertEqual(code, 0, out + err)
        d = json.loads((self.event / "kit" / "thanks.json").read_text(encoding="utf-8"))
        self.assertEqual(d["recipient_groups"], ["checked_in"])
        self.assertIn("来場", out)


if __name__ == "__main__":
    unittest.main()
