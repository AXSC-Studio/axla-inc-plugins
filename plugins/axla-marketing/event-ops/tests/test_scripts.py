"""spec 002：approve.py・check_outbound.py・check_pii.py・check_neutral.py の検証器。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"


def run(script, *args, cwd=None, env=None, stdin=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True, cwd=cwd, env=e, stdin=stdin)
    return p.returncode, p.stdout + p.stderr


NAMES = "PT-001\tVenue Owner\tvenue@example.org\nPT-002\tSponsor Lead\tsponsor@example.net\n"


class CheckOutboundTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        (self.d / "names.local").write_text(NAMES, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, text):
        f = self.d / "reply.md"
        f.write_text(text, encoding="utf-8")
        return str(f)

    def test_clean_text_passes(self):
        code, out = run("check_outbound.py", "--names", str(self.d / "names.local"), "--to", "PT-001", self.write("Venue Owner 様\n資料をお送りします。"))
        self.assertEqual(code, 0, out)

    def test_internal_marker_fails(self):
        code, out = run("check_outbound.py", "--names", str(self.d / "names.local"), "--to", "PT-001", self.write("資料です【要確認】"))
        self.assertEqual(code, 1, out)
        self.assertIn("【要確認】", out)

    def test_stale_draft_marker_fails(self):
        code, out = run("check_outbound.py", "--names", str(self.d / "names.local"), "--to", "PT-001", self.write("【古い】 計画が変わった\n資料です"))
        self.assertEqual(code, 1, out)

    def test_other_partner_name_fails(self):
        code, out = run("check_outbound.py", "--names", str(self.d / "names.local"), "--to", "PT-001", self.write("Sponsor Lead さんにも聞いています"))
        self.assertEqual(code, 1, out)
        self.assertIn("PT-002", out)
        self.assertNotIn("Sponsor Lead", out)  # 見つけた名前は番号で知らせる

    def test_other_partner_email_fails(self):
        code, out = run("check_outbound.py", "--names", str(self.d / "names.local"), "--to", "PT-001", self.write("cc: sponsor@example.net"))
        self.assertEqual(code, 1, out)

    def test_missing_names_file_stops(self):
        code, out = run("check_outbound.py", "--names", str(self.d / "nope.local"), "--to", "PT-001", self.write("hi"))
        self.assertEqual(code, 2, out)


class CheckPiiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        (self.d / "names.local").write_text(NAMES, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_counts_only_csv_passes(self):
        f = self.d / "partners.csv"
        f.write_text("id,kind,status\nPT-001,venue,confirmed\n", encoding="utf-8")
        code, out = run("check_pii.py", "--names", str(self.d / "names.local"), str(f))
        self.assertEqual(code, 0, out)

    def test_email_phone_and_names_fail(self):
        for text in ["contact venue@example.org", "電話 090-" + "1234-5678", "PT-001 は Venue Owner"]:
            f = self.d / "partners.csv"
            f.write_text(text, encoding="utf-8")
            code, out = run("check_pii.py", "--names", str(self.d / "names.local"), str(f))
            self.assertEqual(code, 1, f"{text}: {out}")


class CheckNeutralTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_neutral_folder_passes(self):
        (self.d / "spec.md").write_text("会場・登壇者・スポンサー。例：venue@example.com", encoding="utf-8")
        code, out = run("check_neutral.py", str(self.d))
        self.assertEqual(code, 0, out)

    def test_reserved_example_domains_pass(self):
        (self.d / "spec.md").write_text("見本：venue@partner.example と a@b.test", encoding="utf-8")
        code, out = run("check_neutral.py", str(self.d))
        self.assertEqual(code, 0, out)

    def test_company_and_person_fail(self):
        for text in ["株式" + "会社サンプル商事", "連絡先 someone@" + "realcorp.co.jp", "電話 03-" + "1234-5678"]:
            (self.d / "spec.md").write_text(text, encoding="utf-8")
            code, out = run("check_neutral.py", str(self.d))
            self.assertEqual(code, 1, f"{text}: {out}")

    def test_denylist_from_env_fails(self):
        (self.d / "spec.md").write_text("会場は Hidden Venue です", encoding="utf-8")
        code, out = run("check_neutral.py", str(self.d), env={"NEUTRAL_DENYLIST": "Hidden Venue\nOther"})
        self.assertEqual(code, 1, out)
        self.assertNotIn("Hidden Venue", out)  # 秘密の語は出力に出さない

    def test_real_event_ops_folder_is_neutral(self):
        code, out = run("check_neutral.py", str(HERE.parent))
        self.assertEqual(code, 0, out)


class ApproveTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        self.event = self.project / "loop" / "marketing" / "event-ops" / "events" / "261211_startup-night"
        self.event.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_refuses_without_a_human_terminal(self):
        code, out = run(
            "approve.py", "new", "--event", str(self.event), "--kit", "https://claude.ai/artifact/KIT", "--sha256", "a" * 64,
            "--to", "PT-001", "--tools", "send_message", stdin=subprocess.DEVNULL, env={"EVENT_OPS_NO_TTY": "1"},
        )
        self.assertEqual(code, 2, out)
        self.assertFalse((self.event / "approvals").exists() and any((self.event / "approvals").iterdir()))

    def test_refuses_yes_flag(self):
        code, out = run(
            "approve.py", "new", "--event", str(self.event), "--kit", "https://claude.ai/artifact/KIT", "--sha256", "a" * 64,
            "--to", "PT-001", "--tools", "send_message", "--yes", stdin=subprocess.DEVNULL, env={"EVENT_OPS_NO_TTY": "1"},
        )
        self.assertNotEqual(code, 0, out)

    def test_show_lists_approvals_without_writing(self):
        (self.event / "approvals").mkdir()
        (self.event / "approvals" / "A-001.json").write_text(json.dumps({"id": "A-001", "to": ["PT-001"], "tools": ["send_message"], "kit": {"url": "u", "sha256": "a" * 64}, "expires_at": "2999-01-01T00:00:00+00:00"}), encoding="utf-8")
        code, out = run("approve.py", "show", "--event", str(self.event))
        self.assertEqual(code, 0, out)
        self.assertIn("A-001", out)


if __name__ == "__main__":
    unittest.main()
