"""hooks/guard.py（柵）のテスト。作り話の契約と宛先（example.test）で、止まる例と通る例を確かめる。

使い方:
    python3 -I -m unittest discover -s "${CLAUDE_PLUGIN_ROOT}/scripts/tests"
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(os.path.dirname(HERE))
GUARD = os.path.join(PLUGIN, 'hooks', 'guard.py')
GATE = os.path.join(PLUGIN, 'scripts', 'gate.py')
GMAIL = 'mcp__0000-test__'
PARTNER = 'legal@partner.example.test'


def hook(mode, data):
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_PROJECT_DIR'}
    r = subprocess.run([sys.executable, '-I', GUARD, mode], input=json.dumps(data), capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout) if r.stdout.strip() else None


def denied(out):
    return bool(out) and out.get('hookSpecificOutput', {}).get('permissionDecision') == 'deny'


class TestGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        subprocess.run(['git', 'init', '-q', '-b', 'main', self.root], check=True)
        self.legal = os.path.join(self.root, 'loop', 'legal')
        self.c = os.path.join(self.legal, 'contracts', '990101_NDA_1')
        os.makedirs(self.c)
        with open(os.path.join(self.legal, 'LEGAL.md'), 'w', encoding='utf-8') as f:
            f.write('# 作り話の LEGAL.md\n')
        subprocess.run([sys.executable, '-I', GATE, 'watch', self.c, '--to', PARTNER, '--message', 'm-1'],
                       check=True, capture_output=True)

    def tearDown(self):
        self.tmp.cleanup()

    def pre(self, tool, inp):
        return hook('pre', {'tool_name': tool, 'tool_input': inp, 'cwd': self.root})

    def set_clean_ok(self):
        sys.path.insert(0, os.path.join(PLUGIN, 'scripts'))
        import gate
        gate.update(self.c, 'clean', {'ok': True, 'sha256': '0' * 64, 'at': gate.now()})

    # --- 送信 ---
    def test_send_to_partner_is_denied(self):
        self.assertTrue(denied(self.pre(GMAIL + 'send_message', {'to': [PARTNER], 'body': 'x'})))

    def test_send_to_partner_domain_is_denied(self):
        self.assertTrue(denied(self.pre(GMAIL + 'send_message', {'to': ['boss@partner.example.test'], 'body': 'x'})))

    def test_reply_to_partner_message_is_denied(self):
        self.assertTrue(denied(self.pre(GMAIL + 'reply', {'messageId': 'm-1', 'body': 'x'})))

    def test_reply_without_to_is_denied_when_unknown(self):
        self.assertTrue(denied(self.pre(GMAIL + 'reply', {'messageId': 'm-unknown', 'body': 'x'})))

    def test_send_to_others_is_allowed(self):
        self.assertIsNone(self.pre(GMAIL + 'send_message', {'to': ['someone@other.example.test'], 'body': 'x'}))

    def test_slack_is_not_mail(self):
        self.assertIsNone(self.pre('mcp__0000-test__slack_send_message', {'to': [PARTNER]}))

    def test_outside_legal_repo_is_allowed(self):
        with tempfile.TemporaryDirectory() as other:
            out = hook('pre', {'tool_name': GMAIL + 'send_message', 'tool_input': {'to': [PARTNER]}, 'cwd': other})
        self.assertIsNone(out)

    # --- 下書き（送る前のゲート） ---
    def test_draft_without_clean_gate_is_denied(self):
        self.assertTrue(denied(self.pre(GMAIL + 'create_draft', {'to': [PARTNER], 'body': 'x'})))

    def test_draft_with_image_is_denied(self):
        # INCIDENT の再現：引用の署名ロゴなど、画像の入った下書き
        self.set_clean_ok()
        out = self.pre(GMAIL + 'create_draft', {'to': [PARTNER], 'htmlBody': '<p>x</p><img src="https://example.test/logo.png">'})
        self.assertTrue(denied(out))
        self.assertIn('画像', out['hookSpecificOutput']['permissionDecisionReason'])

    def test_draft_with_attachment_is_denied(self):
        self.set_clean_ok()
        self.assertTrue(denied(self.pre(GMAIL + 'create_draft', {'to': [PARTNER], 'body': 'x',
                                                                  'attachments': [{'content': 'AA==', 'filename': 'a.docx'}]})))

    def test_draft_after_redline_changed_is_denied(self):
        self.set_clean_ok()
        time.sleep(1.1)
        p = os.path.join(self.c, 'Redline Data.json')
        with open(p, 'w') as f:
            f.write('{}')
        os.utime(p, (time.time() + 5, time.time() + 5))
        self.assertTrue(denied(self.pre(GMAIL + 'create_draft', {'to': [PARTNER], 'body': 'x'})))

    def test_clean_draft_is_allowed_and_then_stop_blocks_until_checked(self):
        self.set_clean_ok()
        self.assertIsNone(self.pre(GMAIL + 'create_draft', {'to': [PARTNER], 'body': 'x'}))
        hook('post', {'tool_name': GMAIL + 'create_draft', 'tool_input': {'to': [PARTNER]}, 'cwd': self.root,
                      'tool_response': {'id': 'd-1', 'threadId': 't-1'}})
        out = hook('stop', {'cwd': self.root, 'stop_hook_active': False})
        self.assertEqual(out['decision'], 'block')
        # 2回目は無限に止めない
        self.assertNotIn('decision', hook('stop', {'cwd': self.root, 'stop_hook_active': True}))
        # 作った下書きの送信も止まる
        self.assertTrue(denied(self.pre(GMAIL + 'send_message', {'draftId': 'd-1'})))
        # check_draft.py --record で OK になれば、終われる
        raw = os.path.join(self.root, 'draft.json')
        import base64
        mime = b'Content-Type: text/plain; charset=utf-8\r\n\r\nhello\r\n'
        with open(raw, 'w') as f:
            json.dump({'raw': base64.urlsafe_b64encode(mime).decode(), 'threadId': 't-1'}, f)
        r = subprocess.run([sys.executable, '-I', os.path.join(PLUGIN, 'scripts', 'check_draft.py'), raw,
                            '--expect-attachments', '0', '--record', self.c], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIsNone(hook('stop', {'cwd': self.root, 'stop_hook_active': False}))

    # --- 閉じた世界 ---
    def test_edit_legal_md_is_denied(self):
        self.assertTrue(denied(self.pre('Edit', {'file_path': os.path.join(self.legal, 'LEGAL.md')})))

    def test_bash_write_legal_md_is_denied(self):
        self.assertTrue(denied(self.pre('Bash', {'command': 'echo x >> loop/legal/LEGAL.md'})))
        self.assertTrue(denied(self.pre('Bash', {'command': "sed -i '' 's/a/b/' loop/legal/LEGAL.md"})))

    def test_read_legal_md_is_allowed(self):
        self.assertIsNone(self.pre('Bash', {'command': 'cat loop/legal/LEGAL.md'}))

    def test_edit_legal_md_on_outer_branch_is_allowed(self):
        subprocess.run(['git', '-C', self.root, '-c', 'user.name=t', '-c', 'user.email=t@example.test',
                        'commit', '-q', '--allow-empty', '-m', 'x'], check=True)
        subprocess.run(['git', '-C', self.root, 'checkout', '-q', '-b', 'legal-outer/990101_NDA_1'], check=True)
        self.assertIsNone(self.pre('Edit', {'file_path': os.path.join(self.legal, 'LEGAL.md')}))

    def test_hand_written_gate_is_denied(self):
        self.assertTrue(denied(self.pre('Write', {'file_path': os.path.join(self.c, 'gate.json')})))
        self.assertTrue(denied(self.pre('Bash', {'command': f'echo {{}} > {self.c}/gate.json'})))

    def test_git_add_contracts_is_denied(self):
        self.assertTrue(denied(self.pre('Bash', {'command': 'git add loop/legal/contracts/990101_NDA_1/loop-log.md'})))
        self.assertTrue(denied(self.pre('Bash', {'command': 'git add -f loop/legal'})))
        self.assertIsNone(self.pre('Bash', {'command': 'git add loop/legal/register.csv && git commit -m x'}))


if __name__ == '__main__':
    unittest.main()
