"""spec 004：告知の下書きとアイキャッチの検証器。

- event_page.py：event.json から、貼る文面（Markdown）と告知サービスに渡す中身（JSON）を作る
  - 公開の設定はいつも private（公開は人のまとめ承認のあと）
  - 定員・参加費が budget.json と食い違えば exit 1
- make_eyecatch.py：文字だけのアイキャッチ（外の API を呼ばない）
"""
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


EVENT = {
    "title": "Startup Night",
    "date": "2026-12-11",
    "start": "19:00",
    "end": "22:00",
    "timezone": "Asia/Tokyo",
    "place_area": "札幌駅の近く",
    "capacity": 48,
    "fee": 2000,
    "visibility": "public",
    "points": ["来年なにかを始めたい人が集まる夜", "一部はピッチ、二部は交流"],
    "audience": "起業家・会社員・学生",
}


class EventPageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.event = Path(self.tmp.name) / "loop" / "marketing" / "event-ops" / "events" / "261211_startup-night"
        (self.event / "kit").mkdir(parents=True)
        (self.event / "event.json").write_text(json.dumps(EVENT, ensure_ascii=False), encoding="utf-8")
        (self.event / "budget.json").write_text(json.dumps({"fee": 2000, "capacity": 48}), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_builds_markdown_and_payload(self):
        code, out, err = run("event_page.py", "--event", str(self.event))
        self.assertEqual(code, 0, out + err)
        md = (self.event / "kit" / "event_page.md").read_text(encoding="utf-8")
        self.assertIn("Startup Night", md)
        self.assertIn("2026-12-11", md)
        self.assertIn("2,000", md)
        payload = json.loads((self.event / "kit" / "event_page.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "Startup Night")
        self.assertEqual(payload["start_at"], "2026-12-11T19:00:00+09:00")
        self.assertEqual(payload["end_at"], "2026-12-11T22:00:00+09:00")
        self.assertEqual(payload["timezone"], "Asia/Tokyo")
        self.assertEqual(payload["max_capacity"], 48)

    def test_visibility_is_always_private(self):
        code, out, err = run("event_page.py", "--event", str(self.event))
        payload = json.loads((self.event / "kit" / "event_page.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["visibility"], "private")
        self.assertIn("private", out + err)

    def test_capacity_mismatch_with_budget_fails(self):
        (self.event / "budget.json").write_text(json.dumps({"fee": 2000, "capacity": 40}), encoding="utf-8")
        code, out, err = run("event_page.py", "--event", str(self.event))
        self.assertEqual(code, 1, out + err)
        self.assertIn("定員", out + err)

    def test_fee_mismatch_with_budget_fails(self):
        (self.event / "budget.json").write_text(json.dumps({"fee": 3000, "capacity": 48}), encoding="utf-8")
        code, out, err = run("event_page.py", "--event", str(self.event))
        self.assertEqual(code, 1, out + err)
        self.assertIn("参加費", out + err)

    def test_missing_facts_fail(self):
        e = dict(EVENT)
        del e["date"]
        (self.event / "event.json").write_text(json.dumps(e), encoding="utf-8")
        code, out, err = run("event_page.py", "--event", str(self.event))
        self.assertEqual(code, 1, out + err)

    def test_falls_back_to_budget_for_capacity_and_fee(self):
        e = dict(EVENT)
        e.pop("capacity")
        e.pop("fee")
        (self.event / "event.json").write_text(json.dumps(e), encoding="utf-8")
        code, out, err = run("event_page.py", "--event", str(self.event))
        self.assertEqual(code, 0, out + err)
        payload = json.loads((self.event / "kit" / "event_page.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["max_capacity"], 48)


try:
    import PIL  # noqa: F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


@unittest.skipUnless(HAS_PIL, "Pillow が無い")
class EyecatchTest(unittest.TestCase):
    def test_makes_png_of_the_configured_size(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "eyecatch.png"
            code, o, err = run("make_eyecatch.py", "--title", "Startup Night", "--date", "2026-12-11", "--sub", "札幌駅の近く", "--size", "1080x1080", "--out", str(out))
            self.assertEqual(code, 0, o + err)
            img = Image.open(out)
            self.assertEqual(img.size, (1080, 1080))
            colors = img.convert("RGB").getcolors(maxcolors=1_000_000)
            self.assertGreater(len(colors), 2, "文字が描かれている（色が2つより多い）")


if __name__ == "__main__":
    unittest.main()
