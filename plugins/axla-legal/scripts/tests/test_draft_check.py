"""送る前の検査（check_draft.py と Hook の自動の検査）のテスト。作り話の下書きで確かめる（Issue #20・#34）。"""
import base64
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(os.path.dirname(HERE))
GUARD = os.path.join(PLUGIN, 'hooks', 'guard.py')
SCRIPTS = os.path.join(PLUGIN, 'scripts')
GMAIL = 'mcp__0000-test__'
REPLY = 'お世話になっております。\n・第1条（目的）：目的を書いた\n　（理由）目的が空欄だったため\nよろしくお願いいたします。\n'


def mime(text, html=None):
    if html is None:
        body = f'Content-Type: text/plain; charset=utf-8\r\n\r\n{text}'
    else:
        body = ('Content-Type: multipart/alternative; boundary="b"\r\n\r\n--b\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n'
                f'{text}\r\n--b\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{html}\r\n--b--\r\n')
    return base64.urlsafe_b64encode(body.encode()).decode()


def hook(mode, data):
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_PROJECT_DIR'}
    r = subprocess.run([sys.executable, '-I', GUARD, mode], input=json.dumps(data), capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout) if r.stdout.strip() else None


class TestDraftCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.c = os.path.join(self.root, 'loop', 'legal', 'contracts', '990101_NDA_1')
        os.makedirs(self.c)
        sys.path.insert(0, SCRIPTS)
        import gate
        self.gate = gate
        gate.update(self.c, 'watch', {'to': ['legal@partner.example.test'], 'threads': ['t-1'], 'messages': []})
        gate.update(self.c, 'draft', {'pending': True, 'ids': ['d-1']})

    def tearDown(self):
        self.tmp.cleanup()

    def write_reply(self, text=REPLY):
        with open(os.path.join(self.c, 'reply.txt'), 'w', encoding='utf-8') as f:
            f.write(text)

    def get_draft(self, raw, fmt='RAW'):
        resp = [{'type': 'text', 'text': json.dumps({'id': 'd-1', 'threadId': 't-1', 'raw': raw})}] if raw else {'id': 'd-1'}
        return hook('post', {'tool_name': GMAIL + 'get_draft', 'tool_input': {'draftId': 'd-1', 'messageFormat': fmt},
                             'tool_response': resp, 'cwd': self.root})

    # --- #20 ---
    def test_cli_stops_when_reply_has_no_correction_lines(self):
        raw = os.path.join(self.root, 'd.json')
        with open(raw, 'w') as f:
            json.dump({'raw': mime('本文だけ')}, f)
        empty = os.path.join(self.root, 'empty.txt')
        with open(empty, 'w', encoding='utf-8') as f:
            f.write('お世話になっております。\n')
        r = subprocess.run([sys.executable, '-I', os.path.join(SCRIPTS, 'check_draft.py'), raw, '--reply', empty],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('1行も無い', r.stdout)

    def test_cli_stops_when_a_correction_line_is_missing(self):
        raw = os.path.join(self.root, 'd.json')
        with open(raw, 'w') as f:
            json.dump({'raw': mime('お世話になっております。\nよろしくお願いいたします。\n')}, f)
        rp = os.path.join(self.root, 'reply.txt')
        with open(rp, 'w', encoding='utf-8') as f:
            f.write(REPLY)
        r = subprocess.run([sys.executable, '-I', os.path.join(SCRIPTS, 'check_draft.py'), raw, '--reply', rp],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)

    # --- #34：Hook がその場で検査する ---
    def test_hook_checks_raw_draft_and_lets_turn_end(self):
        self.write_reply()
        out = hook('post', {'tool_name': GMAIL + 'get_draft', 'tool_input': {'draftId': 'd-1', 'messageFormat': 'RAW'},
                            'tool_response': [{'type': 'text', 'text': json.dumps({'id': 'd-1', 'raw': mime(REPLY)})}],
                            'cwd': self.root})
        self.assertIn('OK', out['hookSpecificOutput']['additionalContext'])
        self.assertFalse(self.gate.load(self.c)['draft']['pending'])
        self.assertIsNone(hook('stop', {'cwd': self.root, 'stop_hook_active': False}))

    def test_hook_flags_quoted_image(self):
        self.write_reply()
        out = self.get_draft(mime(REPLY, '<p>本文</p><img src="cid:logo">'))
        self.assertIn('NG', out['hookSpecificOutput']['additionalContext'])
        self.assertTrue(self.gate.load(self.c)['draft']['pending'])
        self.assertEqual(hook('stop', {'cwd': self.root, 'stop_hook_active': False})['decision'], 'block')

    def test_hook_asks_for_raw(self):
        out = self.get_draft(None, fmt='PLAIN_TEXT')
        self.assertIn('RAW', out['hookSpecificOutput']['additionalContext'])

    def test_hook_needs_reply_txt(self):
        out = self.get_draft(mime(REPLY))
        self.assertIn('reply.txt が無い', out['hookSpecificOutput']['additionalContext'])
        self.assertTrue(self.gate.load(self.c)['draft']['pending'])

    def test_other_drafts_are_ignored(self):
        out = hook('post', {'tool_name': GMAIL + 'get_draft', 'tool_input': {'draftId': 'other', 'messageFormat': 'RAW'},
                            'tool_response': {'raw': mime('x')}, 'cwd': self.root})
        self.assertIsNone(out)

    def test_sent_message_check_flags_incident(self):
        self.write_reply()
        out = hook('post', {'tool_name': GMAIL + 'get_message', 'tool_input': {'messageId': 'm-9', 'messageFormat': 'RAW'},
                            'tool_response': {'id': 'm-9', 'threadId': 't-1', 'raw': mime(REPLY)}, 'cwd': self.root})
        ctx = out['hookSpecificOutput']['additionalContext']
        self.assertIn('NG', ctx)  # 添付の清書が無い
        self.assertIn('INCIDENT', ctx)


if __name__ == '__main__':
    unittest.main()
