"""spec 006：返事と送信済みの見張りの検証器。

- watch_partner_mail.gs（Apps Script）の判定部分を Node で確かめる（watch_gs_test.js）
- match_partner.py：メールアドレスを相手の番号に手元で引き当てる（名前の表は外に出さない）
- ルーティンの設定の見本に、書き込みの道具が無い
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
ADAPTERS = HERE.parent / "adapters"


@unittest.skipUnless(shutil.which("node"), "Node が無い")
class AppsScriptTest(unittest.TestCase):
    def test_watch_gs(self):
        p = subprocess.run(["node", str(HERE / "watch_gs_test.js")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)


class MatchPartnerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.names = Path(self.tmp.name) / "names.local"
        self.names.write_text("PT-001\tVenue Owner\tvenue@partner.example\nPT-002\tSponsor Lead\tlead@sponsor.example\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_match(self, *args):
        p = subprocess.run([sys.executable, str(SCRIPTS / "match_partner.py"), "--names", str(self.names), *args], capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr

    def test_exact_email(self):
        code, out, err = self.run_match("--email", "Venue Owner <VENUE@partner.example>")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip(), "PT-001")

    def test_same_domain_is_a_candidate_not_a_match(self):
        code, out, err = self.run_match("--email", "someone@sponsor.example")
        self.assertEqual(code, 1, out + err)
        self.assertIn("PT-002", out)
        self.assertNotIn("Sponsor Lead", out)

    def test_unknown(self):
        code, out, err = self.run_match("--email", "x@nowhere.example")
        self.assertEqual(code, 1)


class RoutineConfigTest(unittest.TestCase):
    def test_routine_example_disallows_write_tools(self):
        cfg = json.loads((ADAPTERS / "email" / "routine.example.json").read_text(encoding="utf-8"))
        disallowed = " ".join(cfg["disallowed_tools"])
        for word in ["send", "draft", "reply", "forward", "label", "trash", "delete", "Bash", "Write", "Edit"]:
            self.assertIn(word, disallowed, word)
        for t in cfg.get("allowed_tools", []):
            self.assertRegex(t.split("__")[-1], r"^(get|list|search|read)_", t)


if __name__ == "__main__":
    unittest.main()
