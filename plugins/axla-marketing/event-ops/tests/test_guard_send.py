"""spec 002：実行境界（Sandbox）と承認ゲート（Human Gate）の検証器。

受け入れ条件をそのまま検査にする。
- 承認の無い送信・公開の道具は止まる（exit 2）
- 承認にない宛先、ハッシュの違う版への送信は止まる
- 送った版の URL への上書きの公開は止まる
- 支払い・契約の道具は、承認があっても止まる
- 承認ファイルを AI が直接書くことは止まる
- event-ops のデータが無いリポでは、何もしない（ほかの仕事を邪魔しない）
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUARD = HERE.parent / "hooks" / "guard_send.py"

KIT_URL = "https://claude.ai/artifact/KITv12"
KIT_HASH = "a" * 64


def run_guard(project: Path, tool_name: str, tool_input: dict):
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool_name, "tool_input": tool_input, "cwd": str(project)}
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project))
    p = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(payload), capture_output=True, text=True, env=env)
    return p.returncode, p.stderr


class GuardSendTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        self.base = self.project / "loop" / "marketing" / "event-ops"
        self.event = self.base / "events" / "261211_startup-night"
        (self.event / "approvals").mkdir(parents=True)
        (self.event / "sent").mkdir(parents=True)
        (self.base / "names.local").write_text(
            "# 番号<TAB>名前<TAB>メール（git に入れない）\n"
            "PT-001\tVenue Owner\tvenue@example.org\n"
            "PT-002\tSponsor Lead\tsponsor@example.net\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def approve(self, to=("PT-001",), tools=("send_message",), kit_hash=KIT_HASH, expires_in_days=7, approval_id="A-001", extra=None):
        now = datetime.now(timezone.utc)
        data = {
            "id": approval_id,
            "kit": {"url": KIT_URL, "sha256": kit_hash},
            "to": list(to),
            "tools": list(tools),
            "approved_by": "human",
            "approved_at": now.isoformat(),
            "expires_at": (now + timedelta(days=expires_in_days)).isoformat(),
        }
        if extra:
            data.update(extra)
        (self.event / "approvals" / f"{approval_id}.json").write_text(json.dumps(data), encoding="utf-8")

    def freeze(self, partner="PT-001", sha=KIT_HASH):
        (self.event / "sent" / f"{partner}_v1.2.json").write_text(json.dumps({"url": KIT_URL, "sha256": sha, "partner": partner}), encoding="utf-8")

    # --- 承認の有無 -------------------------------------------------------
    def test_send_without_approval_is_blocked(self):
        code, err = run_guard(self.project, "mcp__gmail__send_message", {"to": ["venue@example.org"], "body": "hello"})
        self.assertEqual(code, 2, err)
        self.assertIn("承認", err)

    def test_send_with_matching_approval_is_allowed(self):
        self.approve()
        self.freeze()
        code, err = run_guard(self.project, "mcp__gmail__send_message", {"to": ["venue@example.org"], "body": f"資料です {KIT_URL}"})
        self.assertEqual(code, 0, err)

    def test_send_to_unapproved_recipient_is_blocked(self):
        self.approve(to=("PT-001",))
        code, err = run_guard(self.project, "mcp__gmail__send_message", {"to": ["venue@example.org", "sponsor@example.net"], "body": "hi"})
        self.assertEqual(code, 2, err)
        self.assertIn("宛先", err)

    def test_send_with_wrong_kit_hash_is_blocked(self):
        self.approve(kit_hash="b" * 64)
        self.freeze(sha=KIT_HASH)
        code, err = run_guard(self.project, "mcp__gmail__send_message", {"to": ["venue@example.org"], "body": f"資料です {KIT_URL}"})
        self.assertEqual(code, 2, err)
        self.assertIn("版", err)

    def test_expired_approval_is_blocked(self):
        self.approve(expires_in_days=-1)
        code, err = run_guard(self.project, "mcp__gmail__send_message", {"to": ["venue@example.org"], "body": "hi"})
        self.assertEqual(code, 2, err)

    def test_tool_not_listed_in_approval_is_blocked(self):
        self.approve(tools=("send_message",))
        code, err = run_guard(self.project, "mcp__gmail__forward", {"to": ["venue@example.org"]})
        self.assertEqual(code, 2, err)

    # --- 宣言していない送信の道具 ------------------------------------------
    def test_undeclared_send_like_tools_are_blocked(self):
        for name in ["mcp__luma__create_blast", "mcp__unknown__publish_page", "mcp__x__send_invites", "mcp__drive__share_file"]:
            code, err = run_guard(self.project, name, {"id": "evt"})
            self.assertEqual(code, 2, f"{name}: {err}")

    def test_publishing_an_event_by_visibility_is_blocked(self):
        code, err = run_guard(self.project, "mcp__luma__update_event", {"event_id": "evt", "visibility": "public"})
        self.assertEqual(code, 2, err)

    def test_drafts_and_reads_are_allowed(self):
        for name, inp in [
            ("mcp__gmail__create_draft", {"to": ["anyone@example.com"], "body": "draft"}),
            ("mcp__gmail__search_threads", {"q": "from:venue"}),
            ("mcp__luma__update_event", {"event_id": "evt", "visibility": "private"}),
            ("Read", {"file_path": "/tmp/x"}),
            ("mcp__drive__get_shared_drive_metadata", {"id": "d"}),
            ("mcp__drive__list_shared_drives", {}),
            ("mcp__luma__list_blasts", {}),
            ("mcp__slack__search_public", {"query": "publish"}),
        ]:
            code, err = run_guard(self.project, name, inp)
            self.assertEqual(code, 0, f"{name}: {err}")

    # --- 禁止の道具 --------------------------------------------------------
    def test_payment_tools_are_blocked_even_with_approval(self):
        self.approve(tools=("create_payment",))
        code, err = run_guard(self.project, "mcp__stripe__create_payment", {"amount": 100})
        self.assertEqual(code, 2, err)
        self.assertIn("禁止", err)

    # --- 送った版の上書き --------------------------------------------------
    def test_republishing_a_sent_kit_url_is_blocked(self):
        self.freeze()
        code, err = run_guard(self.project, "Artifact", {"url": KIT_URL, "file_path": "/tmp/deck.json"})
        self.assertEqual(code, 2, err)
        self.assertIn("凍結", err)

    def test_publishing_a_new_artifact_is_allowed(self):
        self.freeze()
        code, err = run_guard(self.project, "Artifact", {"file_path": "/tmp/deck.json"})
        self.assertEqual(code, 0, err)

    def test_reading_a_sent_kit_is_allowed(self):
        self.freeze()
        code, err = run_guard(self.project, "Artifact", {"action": "read", "url": KIT_URL})
        self.assertEqual(code, 0, err)

    # --- 承認ファイルは人だけが書く ----------------------------------------
    def test_writing_approval_files_directly_is_blocked(self):
        target = str(self.event / "approvals" / "A-002.json")
        for name, inp in [
            ("Write", {"file_path": target, "content": "{}"}),
            ("Edit", {"file_path": target, "old_string": "a", "new_string": "b"}),
            ("Bash", {"command": f"echo '{{}}' > {target}"}),
            ("Bash", {"command": f"python3 -c \"open('{target}','w')\""}),
            ("Bash", {"command": f"python3 approve.py show --event x; rm {target}"}),
        ]:
            code, err = run_guard(self.project, name, inp)
            self.assertEqual(code, 2, f"{name}: {err}")

    def test_reading_approval_files_is_allowed(self):
        self.approve()
        code, err = run_guard(self.project, "Bash", {"command": f"cat {self.event}/approvals/A-001.json"})
        self.assertEqual(code, 0, err)

    # --- 記録（Observability） ---------------------------------------------
    def test_block_is_recorded_in_runs_jsonl(self):
        run_guard(self.project, "mcp__gmail__send_message", {"to": ["venue@example.org"]})
        lines = (self.base / "runs.jsonl").read_text(encoding="utf-8").strip().splitlines()
        rec = json.loads(lines[-1])
        self.assertEqual(rec["result"], "blocked")
        self.assertEqual(rec["primitive"], "sandbox")
        self.assertNotIn("venue@example.org", lines[-1])  # 実名・連絡先は書かない

    # --- event-ops を使っていないリポ --------------------------------------
    def test_noop_when_project_has_no_event_ops(self):
        with tempfile.TemporaryDirectory() as other:
            code, err = run_guard(Path(other), "mcp__gmail__send_message", {"to": ["a@example.com"]})
            self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
