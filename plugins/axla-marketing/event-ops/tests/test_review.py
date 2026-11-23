"""spec 008：review-event（外側のループ）の検証器。

- judge_lines seal：線のハッシュを register.csv（git に入る）に刻む
- judge_lines judge：封じた線と件数を照らす。線が書き換えられていたら止める。前回との判断の数を比べる。
  同じ fail_code が2回なら、決まりに上げる案を PR の下書きに入れる
- guard hook：線を封じていないと、告知の公開を止める
"""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
HOOKS = HERE.parent / "hooks"


def run(script, *args, cwd=None):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


LINES = {"lines": [
    {"id": "attended", "metric": "attended", "target": 40, "definition": "チェックインした人"},
    {"id": "consented", "metric": "consented", "target": 10, "definition": "後日の連絡に同意した人"},
    {"id": "profit", "metric": "profit", "target": 0, "definition": "赤字にしない"},
]}


class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        self.base = self.project / "loop" / "marketing" / "event-ops"

    def tearDown(self):
        self.tmp.cleanup()

    def make_event(self, eid, attended, consented, profit, judgments=None):
        code, out, err = run("new_event.py", "init", "--id", eid, cwd=self.project)
        self.assertEqual(code, 0, err)
        ev = self.base / "events" / eid
        (ev / "lines.json").write_text(json.dumps(LINES, ensure_ascii=False), encoding="utf-8")
        rows = self.rows()
        for r in rows:
            if r["id"] == eid:
                r.update(attended=str(attended), consented=str(consented), profit=str(profit), state="closed")
                if judgments is not None:
                    r["judgments"] = str(judgments)
        self.write_rows(rows)
        return ev

    def rows(self):
        with open(self.base / "register.csv", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def write_rows(self, rows):
        fields = list(rows[0].keys())
        with open(self.base / "register.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    def test_seal_writes_hash_into_register(self):
        ev = self.make_event("261211_night", 42, 8, 30000)
        code, out, err = run("judge_lines.py", "seal", "--event", str(ev))
        self.assertEqual(code, 0, err)
        row = next(r for r in self.rows() if r["id"] == "261211_night")
        self.assertEqual(len(row["lines_sha256"]), 64)
        items = {i["id"]: i for i in json.loads((ev / "checklist.json").read_text(encoding="utf-8"))["items"]}
        self.assertTrue(items["lines"]["passes"])  # 内側の checklist の項目も達成になる

    def test_judge_gives_hit_weak_and_miss(self):
        ev = self.make_event("261211_night", 42, 8, -5000)
        run("judge_lines.py", "seal", "--event", str(ev))
        code, out, err = run("judge_lines.py", "judge", "--event", str(ev))
        self.assertEqual(code, 0, out + err)
        rep = (ev / "review.md").read_text(encoding="utf-8")
        self.assertRegex(rep, r"attended.*当たり")
        self.assertRegex(rep, r"consented.*弱い当たり")
        self.assertRegex(rep, r"profit.*外れ")

    def test_judge_refuses_rewritten_lines(self):
        ev = self.make_event("261211_night", 42, 8, 30000)
        run("judge_lines.py", "seal", "--event", str(ev))
        lines = json.loads((ev / "lines.json").read_text(encoding="utf-8"))
        lines["lines"][0]["target"] = 30
        (ev / "lines.json").write_text(json.dumps(lines), encoding="utf-8")
        code, out, err = run("judge_lines.py", "judge", "--event", str(ev))
        self.assertEqual(code, 2, out + err)
        self.assertIn("書き換え", out + err)

    def test_judge_refuses_unsealed_lines(self):
        ev = self.make_event("261211_night", 42, 8, 30000)
        code, out, err = run("judge_lines.py", "judge", "--event", str(ev))
        self.assertEqual(code, 2, out + err)

    def test_compares_judgments_with_previous_event(self):
        prev = self.make_event("261101_first", 15, 3, 1000, judgments=24)
        ev = self.make_event("261211_night", 42, 10, 30000)
        (ev / "approvals" / "A-001.json").write_text("{}", encoding="utf-8")
        log = ev / "event-log.md"
        log.write_text(log.read_text(encoding="utf-8").replace("## 2. 開いている人の判断（G1）\n（まだない）", "## 2. 開いている人の判断（G1）\n- G1：開催日\n- G1：参加費"), encoding="utf-8")
        run("judge_lines.py", "seal", "--event", str(ev))
        code, out, err = run("judge_lines.py", "judge", "--event", str(ev))
        self.assertEqual(code, 0, out + err)
        rep = (ev / "review.md").read_text(encoding="utf-8")
        self.assertIn("24 → 3", rep)
        row = next(r for r in self.rows() if r["id"] == "261211_night")
        self.assertEqual(row["judgments"], "3")

    def test_repeated_fail_code_becomes_a_rule_proposal(self):
        ev = self.make_event("261211_night", 42, 10, 30000)
        with open(self.base / "runs.jsonl", "a", encoding="utf-8") as f:
            for _ in range(2):
                f.write(json.dumps({"ts": "2026-12-01T00:00:00+00:00", "layer": "middle", "primitive": "sandbox", "result": "blocked", "fail_code": "unapproved_recipient", "event": "261211_night"}) + "\n")
        run("judge_lines.py", "seal", "--event", str(ev))
        run("judge_lines.py", "judge", "--event", str(ev))
        pr = (ev / "learning-pr.md").read_text(encoding="utf-8")
        self.assertIn("unapproved_recipient", pr)
        self.assertIn("EVENTS.md", pr)

    # --- 公開の前に線を封じる（spec 002 の hook に足した） ------------------
    def guard(self, tool, tool_input):
        payload = json.dumps({"tool_name": tool, "tool_input": tool_input, "cwd": str(self.project)})
        p = subprocess.run([sys.executable, str(HOOKS / "guard_send.py")], input=payload, capture_output=True, text=True,
                           env=dict(os.environ, CLAUDE_PROJECT_DIR=str(self.project)))
        return p.returncode, p.stderr

    def test_publishing_is_blocked_until_lines_are_sealed(self):
        ev = self.make_event("261211_night", 0, 0, 0)
        code, err = self.guard("mcp__luma__update_event", {"event_id": "e", "visibility": "public"})
        self.assertEqual(code, 2, err)
        self.assertIn("線", err)


if __name__ == "__main__":
    unittest.main()
