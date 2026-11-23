"""spec 003：plan-event（内側のループ）の検証器。

- recalc_budget：収支を道具で計算し直す。変わったら記録に1行、関係する checklist を未達に戻す
- new_event：イベントのフォルダをひな形から作る。checklist は全部未達から始める
- checklist：証拠の無い項目は達成にできない。検証役の項目は「致命的: 0」が要る
- check_kit：全部達成で 0。未達か、G2 のあとの【仮】で 1
- stop_guard（Stop hook）：内側のループの途中は止めさせない。3周で G1 に上げて止まる
"""
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


def run(script, *args, cwd=None, stdin=None, folder=SCRIPTS):
    p = subprocess.run([sys.executable, str(folder / script), *args], capture_output=True, text=True, cwd=cwd, input=stdin)
    return p.returncode, p.stdout, p.stderr


BUDGET = {
    "venue": {"hourly": 13200, "hours": 3},
    "fee": 2000,
    "fee_rate": 0.10,
    "per_person_cost": 0,
    "fixed_costs": [],
    "capacity": 48,
    "headcounts": [20, 30, 40, 48],
}


class RecalcBudgetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def budget(self, **kw):
        b = json.loads(json.dumps(BUDGET))
        for k, v in kw.items():
            b[k] = v
        f = self.d / "budget.json"
        f.write_text(json.dumps(b), encoding="utf-8")
        return f

    def test_breakeven_and_profit_match_the_real_example(self):
        code, out, err = run("recalc_budget.py", str(self.budget()), "--json")
        self.assertEqual(code, 0, err)
        r = json.loads(out)
        self.assertEqual(r["fixed_total"], 39600)
        self.assertEqual(r["breakeven"], 22)
        self.assertEqual(r["profit"]["40"], 32400)

    def test_four_hours_needs_thirty(self):
        code, out, err = run("recalc_budget.py", str(self.budget(venue={"hourly": 13200, "hours": 4})), "--json")
        self.assertEqual(json.loads(out)["breakeven"], 30)

    def test_cannot_break_even_within_capacity(self):
        code, out, err = run("recalc_budget.py", str(self.budget(fee=1000)), "--json")
        r = json.loads(out)
        self.assertEqual(r["breakeven"], 44)
        code, out, err = run("recalc_budget.py", str(self.budget(fee=500)), "--json")
        r = json.loads(out)
        self.assertIsNone(r["breakeven_within_capacity"])

    def test_no_margin_means_never(self):
        code, out, err = run("recalc_budget.py", str(self.budget(per_person_cost=2000)), "--json")
        self.assertIsNone(json.loads(out)["breakeven"])

    def test_markdown_table_has_unverified_assumptions(self):
        code, out, err = run("recalc_budget.py", str(self.budget(unverified=["税込みかどうか"])))
        self.assertEqual(code, 0, err)
        self.assertIn("| 40 |", out)
        self.assertIn("未確認", out)


class EventLoopTest(unittest.TestCase):
    """new_event → checklist → recalc → check_kit → stop_guard を通しで見る。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        self.base = self.project / "loop" / "marketing" / "event-ops"
        self.base.mkdir(parents=True)
        self.eid = "261211_startup-night"
        self.event = self.base / "events" / self.eid

    def tearDown(self):
        self.tmp.cleanup()

    def init(self):
        code, out, err = run("new_event.py", "init", "--id", self.eid, cwd=self.project)
        self.assertEqual(code, 0, err)

    def checklist(self):
        return json.loads((self.event / "checklist.json").read_text(encoding="utf-8"))

    # --- new_event -------------------------------------------------------
    def test_init_creates_event_with_all_items_unmet(self):
        self.init()
        for name in ["plan.md", "event-log.md", "checklist.json", "budget.json", "state.json", "event.json"]:
            self.assertTrue((self.event / name).exists(), name)
        items = self.checklist()["items"]
        self.assertGreaterEqual(len(items), 8)
        self.assertTrue(all(i["passes"] is False and i["evidence"] is None for i in items))
        reg = (self.base / "register.csv").read_text(encoding="utf-8")
        self.assertIn(self.eid, reg)

    def test_init_prefers_user_templates(self):
        (self.base / "templates").mkdir()
        (self.base / "templates" / "plan.md").write_text("# 自社の計画のひな形\n", encoding="utf-8")
        self.init()
        self.assertIn("自社の計画のひな形", (self.event / "plan.md").read_text(encoding="utf-8"))

    def test_init_refuses_existing_event(self):
        self.init()
        code, out, err = run("new_event.py", "init", "--id", self.eid, cwd=self.project)
        self.assertNotEqual(code, 0)

    def test_init_rejects_bad_id(self):
        code, out, err = run("new_event.py", "init", "--id", "../oops", cwd=self.project)
        self.assertEqual(code, 2, err)

    # --- checklist -------------------------------------------------------
    def test_mark_requires_existing_evidence(self):
        self.init()
        code, out, err = run("checklist.py", "mark", "--event", str(self.event), "--item", "plan", "--evidence", "nope.md")
        self.assertEqual(code, 1, err)
        self.assertFalse(next(i for i in self.checklist()["items"] if i["id"] == "plan")["passes"])
        code, out, err = run("checklist.py", "mark", "--event", str(self.event), "--item", "plan", "--evidence", "plan.md")
        self.assertEqual(code, 0, err)
        self.assertTrue(next(i for i in self.checklist()["items"] if i["id"] == "plan")["passes"])

    def pass_script_items(self):
        data = self.checklist()
        (self.event / "evidence").mkdir(exist_ok=True)
        for i in data["items"]:
            if i["kind"] == "script":
                (self.event / "evidence" / f"{i['id']}.md").write_text("exit 0\n", encoding="utf-8")
                i["passes"], i["evidence"] = True, f"evidence/{i['id']}.md"
        (self.event / "checklist.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_review_items_need_zero_criticals(self):
        self.init()
        self.pass_script_items()
        (self.event / "reviews").mkdir(exist_ok=True)
        (self.event / "reviews" / "money.md").write_text("致命的: 2\n重要: 1\n", encoding="utf-8")
        code, out, err = run("checklist.py", "mark", "--event", str(self.event), "--item", "review_money", "--evidence", "reviews/money.md")
        self.assertEqual(code, 1, err)
        (self.event / "reviews" / "money.md").write_text("致命的: 0\n重要: 1\n", encoding="utf-8")
        code, out, err = run("checklist.py", "mark", "--event", str(self.event), "--item", "review_money", "--evidence", "reviews/money.md")
        self.assertEqual(code, 0, err)

    def test_reviews_wait_for_scripts(self):
        self.init()
        (self.event / "reviews").mkdir(exist_ok=True)
        (self.event / "reviews" / "money.md").write_text("致命的: 0\n", encoding="utf-8")
        # 収支（スクリプトの項目）が未達のうちは、検証役の項目は達成にできない
        code, out, err = run("checklist.py", "mark", "--event", str(self.event), "--item", "review_money", "--evidence", "reviews/money.md")
        self.assertEqual(code, 1)
        self.assertIn("スクリプト", out + err)

    # --- recalc_budget を呼び直す ----------------------------------------
    def test_recalc_records_change_and_resets_dependent_items(self):
        self.init()
        (self.event / "budget.json").write_text(json.dumps(BUDGET), encoding="utf-8")
        code, out, err = run("recalc_budget.py", "--event", str(self.event))
        self.assertEqual(code, 0, err)
        self.assertTrue((self.event / "budget.md").exists())
        self.assertTrue(next(i for i in self.checklist()["items"] if i["id"] == "budget")["passes"])
        # 料金を変えて呼び直す
        b = json.loads((self.event / "budget.json").read_text(encoding="utf-8"))
        b["venue"]["hours"] = 4
        (self.event / "budget.json").write_text(json.dumps(b), encoding="utf-8")
        run("checklist.py", "mark", "--event", str(self.event), "--item", "plan", "--evidence", "plan.md")
        (self.event / "kit" / "sponsor.md").write_text("スポンサー資料\n", encoding="utf-8")
        code, out, err = run("checklist.py", "mark", "--event", str(self.event), "--item", "sponsor_deck", "--evidence", "kit/sponsor.md")
        self.assertEqual(code, 0, out + err)
        self.assertTrue({i["id"]: i for i in self.checklist()["items"]}["sponsor_deck"]["passes"])
        code, out, err = run("recalc_budget.py", "--event", str(self.event))
        self.assertEqual(code, 0, err)
        log = (self.event / "event-log.md").read_text(encoding="utf-8")
        self.assertIn("22 → 30", log)
        items = {i["id"]: i for i in self.checklist()["items"]}
        self.assertTrue(items["budget"]["passes"])          # 計算し直したので達成のまま
        self.assertFalse(items["sponsor_deck"]["passes"])   # 収支に関わる資料は未達に戻る
        self.assertTrue(items["plan"]["passes"])            # 収支に関わらない項目は達成のまま

    # --- check_kit -------------------------------------------------------
    def mark_all(self):
        for i in self.checklist()["items"]:
            ev = f"evidence/{i['id']}.md"
            (self.event / "evidence").mkdir(exist_ok=True)
            (self.event / ev).write_text("致命的: 0\n", encoding="utf-8")
            i["passes"] = True
            i["evidence"] = ev
        data = self.checklist()
        data["items"] = [dict(i, passes=True, evidence=f"evidence/{i['id']}.md") for i in data["items"]]
        (self.event / "checklist.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_check_kit_fails_while_items_unmet(self):
        self.init()
        code, out, err = run("check_kit.py", "--event", str(self.event))
        self.assertEqual(code, 1)

    def test_check_kit_passes_when_all_met(self):
        self.init()
        self.mark_all()
        code, out, err = run("check_kit.py", "--event", str(self.event))
        self.assertEqual(code, 0, out + err)

    def test_tentative_mark_blocks_after_g2(self):
        self.init()
        self.mark_all()
        (self.event / "kit").mkdir(exist_ok=True)
        (self.event / "kit" / "layout.md").write_text("会場レイアウト【仮】\n", encoding="utf-8")
        code, out, err = run("check_kit.py", "--event", str(self.event))
        self.assertEqual(code, 0, out + err)  # 会場が決まる前は【仮】でよい
        st = json.loads((self.event / "state.json").read_text(encoding="utf-8"))
        st["g2_confirmed"] = True
        (self.event / "state.json").write_text(json.dumps(st), encoding="utf-8")
        code, out, err = run("check_kit.py", "--event", str(self.event))
        self.assertEqual(code, 1, out + err)
        self.assertIn("【仮】", out)

    def test_missing_evidence_file_fails_even_if_marked(self):
        self.init()
        self.mark_all()
        (self.event / "evidence" / "plan.md").unlink()
        code, out, err = run("check_kit.py", "--event", str(self.event))
        self.assertEqual(code, 1)

    # --- Stop hook（終了条件と予算上限） ----------------------------------
    def stop(self):
        payload = json.dumps({"hook_event_name": "Stop", "cwd": str(self.project), "stop_hook_active": False})
        p = subprocess.run([sys.executable, str(HOOKS / "stop_guard.py")], input=payload, capture_output=True, text=True,
                           env=dict(os.environ, CLAUDE_PROJECT_DIR=str(self.project)))
        return p.returncode, p.stdout, p.stderr

    def test_stop_is_free_when_no_inner_loop_runs(self):
        self.init()
        code, out, err = self.stop()
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip(), "")

    def test_stop_is_blocked_while_items_unmet(self):
        self.init()
        run("checklist.py", "start", "--event", str(self.event))
        code, out, err = self.stop()
        self.assertEqual(code, 0, err)
        decision = json.loads(out)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("1/3", decision["reason"])

    def test_stop_escalates_to_g1_after_max_rounds(self):
        self.init()
        run("checklist.py", "start", "--event", str(self.event))
        for _ in range(3):
            self.stop()
        code, out, err = self.stop()
        self.assertEqual(out.strip(), "", "上限のあとは止まれる")
        log = (self.event / "event-log.md").read_text(encoding="utf-8")
        self.assertIn("G1", log)
        st = json.loads((self.event / "state.json").read_text(encoding="utf-8"))
        self.assertFalse(st["inner_active"])

    def test_stop_is_allowed_when_all_met(self):
        self.init()
        run("checklist.py", "start", "--event", str(self.event))
        self.mark_all()
        code, out, err = self.stop()
        self.assertEqual(out.strip(), "")
        st = json.loads((self.event / "state.json").read_text(encoding="utf-8"))
        self.assertFalse(st["inner_active"])
        runs = (self.base / "runs.jsonl").read_text(encoding="utf-8")
        self.assertIn('"result": "achieved"', runs)


if __name__ == "__main__":
    unittest.main()
