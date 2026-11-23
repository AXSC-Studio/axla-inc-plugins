"""spec 005：相手とのやりとり（中間ループ）の検証器。

- freeze_kit：送る版を凍結する。同じ URL で中身が違えば止める（送った版は変えない）
- update_partners：相手の状態を台帳で進める。実名は書かない。返事待ちの超過を数える
- drafts：計画が変わったら、まだ送っていない下書きを「古い」にして止める
- 凍結の記録は、spec 002 の hook が照合する形と同じ
"""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
HOOKS = HERE.parent / "hooks"
URL = "https://claude.ai/artifact/SPONSORv10"


def run(script, *args, cwd=None):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


class PartnersTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        code, out, err = run("new_event.py", "init", "--id", "261211_startup-night", cwd=self.project)
        self.assertEqual(code, 0, err)
        self.base = self.project / "loop" / "marketing" / "event-ops"
        self.event = self.base / "events" / "261211_startup-night"
        self.kit = self.event / "kit" / "sponsor.md"
        self.kit.write_text("スポンサー資料 v1.0\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def rows(self):
        with open(self.base / "partners.csv", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    # --- freeze_kit ------------------------------------------------------
    def test_freeze_records_url_and_hash(self):
        code, out, err = run("freeze_kit.py", "--event", str(self.event), "--partner", "PT-002", "--url", URL, "--file", str(self.kit), "--version", "v1.0")
        self.assertEqual(code, 0, err)
        rec = json.loads((self.event / "sent" / "PT-002_v1.0.json").read_text(encoding="utf-8"))
        self.assertEqual(rec["url"], URL)
        self.assertEqual(len(rec["sha256"]), 64)
        self.assertIn(rec["sha256"], out)  # approve.py に渡すハッシュを出す

    def test_refreezing_same_url_with_different_content_fails(self):
        run("freeze_kit.py", "--event", str(self.event), "--partner", "PT-002", "--url", URL, "--file", str(self.kit), "--version", "v1.0")
        self.kit.write_text("スポンサー資料 v1.0（こっそり直した）\n", encoding="utf-8")
        code, out, err = run("freeze_kit.py", "--event", str(self.event), "--partner", "PT-003", "--url", URL, "--file", str(self.kit), "--version", "v1.0")
        self.assertEqual(code, 1, out + err)
        self.assertIn("新しい版", out + err)

    def test_frozen_record_is_honored_by_the_guard_hook(self):
        run("freeze_kit.py", "--event", str(self.event), "--partner", "PT-002", "--url", URL, "--file", str(self.kit), "--version", "v1.0")
        payload = json.dumps({"tool_name": "Artifact", "tool_input": {"url": URL, "file_path": "/tmp/x"}, "cwd": str(self.project)})
        p = subprocess.run([sys.executable, str(HOOKS / "guard_send.py")], input=payload, capture_output=True, text=True,
                           env=dict(os.environ, CLAUDE_PROJECT_DIR=str(self.project)))
        self.assertEqual(p.returncode, 2, p.stderr)

    # --- update_partners -------------------------------------------------
    def test_status_moves_forward_and_keeps_names_out(self):
        for step in (["add", "--partner", "PT-002", "--kind", "sponsor"], ["sent", "--partner", "PT-002"], ["replied", "--partner", "PT-002"]):
            code, out, err = run("update_partners.py", *step, "--event", str(self.event))
            self.assertEqual(code, 0, out + err)
        row = next(r for r in self.rows() if r["id"] == "PT-002")
        self.assertEqual(row["status"], "replied")
        self.assertEqual(row["kind"], "sponsor")
        log = (self.event / "event-log.md").read_text(encoding="utf-8")
        self.assertIn("PT-002", log)

    def test_rejects_names_instead_of_numbers(self):
        code, out, err = run("update_partners.py", "add", "--partner", "Venue Owner", "--kind", "venue", "--event", str(self.event))
        self.assertEqual(code, 2, out + err)

    def test_confirming_the_venue_records_g2(self):
        run("update_partners.py", "add", "--partner", "PT-001", "--kind", "venue", "--event", str(self.event))
        code, out, err = run("update_partners.py", "confirmed", "--partner", "PT-001", "--event", str(self.event))
        self.assertEqual(code, 0, out + err)
        st = json.loads((self.event / "state.json").read_text(encoding="utf-8"))
        self.assertTrue(st["g2_confirmed"])

    def test_overdue_replies_are_counted(self):
        run("update_partners.py", "add", "--partner", "PT-002", "--kind", "sponsor", "--event", str(self.event))
        run("update_partners.py", "sent", "--partner", "PT-002", "--event", str(self.event))
        rows = self.rows()
        for r in rows:
            if r["id"] == "PT-002":
                r["last_contact"] = (date.today() - timedelta(days=5)).isoformat()
        with open(self.base / "partners.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        code, out, err = run("update_partners.py", "overdue", "--days", "3", "--event", str(self.event))
        self.assertEqual(code, 1, out + err)
        self.assertIn("PT-002", out)

    # --- 古い下書き ------------------------------------------------------
    def test_drafts_become_stale_when_the_plan_changes(self):
        draft = self.event / "kit" / "reply_PT-002.md"
        draft.write_text("返事の下書き\n", encoding="utf-8")
        code, out, err = run("update_partners.py", "draft", "--partner", "PT-002", "--file", str(draft), "--event", str(self.event))
        self.assertEqual(code, 0, out + err)
        code, out, err = run("update_partners.py", "stale", "--event", str(self.event))
        self.assertEqual(code, 0, out + err)
        b = json.loads((self.event / "budget.json").read_text(encoding="utf-8"))
        b["fee"] = 3000
        (self.event / "budget.json").write_text(json.dumps(b), encoding="utf-8")
        code, out, err = run("update_partners.py", "stale", "--event", str(self.event))
        self.assertEqual(code, 1, out + err)
        self.assertIn("reply_PT-002.md", out)
        self.assertTrue(draft.read_text(encoding="utf-8").startswith("【古い】"))


if __name__ == "__main__":
    unittest.main()
