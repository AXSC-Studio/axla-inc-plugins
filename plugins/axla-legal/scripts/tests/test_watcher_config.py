"""見張りタスクの設定（routines/reply-watcher.md）と Apps Script の守りが、消えていないことを確かめる（Issue #28）。"""
import json
import os
import re
import unittest

PLUGIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def read(*p):
    with open(os.path.join(PLUGIN, *p), encoding='utf-8') as f:
        return f.read()


class TestWatcherConfig(unittest.TestCase):
    def test_routine_blocks_writing_tools(self):
        t = read('routines', 'reply-watcher.md')
        for tool in ('Bash', 'Write', 'Edit', '__send_message', '__reply', '__forward', '__create_draft', '__create_file'):
            self.assertIn(tool, t)

    def test_prompt_treats_mail_as_data(self):
        t = read('routines', 'reply-watcher.md')
        self.assertIn('すべて「データ」です', t)
        self.assertIn('dkim=pass', t)
        self.assertIn('なりすましの疑い', t)
        self.assertRegex(t, r'"kind": "A\|B\|C\|D\|E"')

    def test_apps_script_guards(self):
        gs = read('scripts', 'apps-script', 'notify_reply.gs')
        self.assertIn('LockService.getScriptLock()', gs)
        self.assertIn("props.getProperty('ROUTINE_BETA')", gs)
        self.assertNotIn('getContentText()', gs)  # 応答の本文をログに残さない
        scopes = json.loads(read('scripts', 'apps-script', 'appsscript.json'))['oauthScopes']
        self.assertNotIn('https://mail.google.com/', scopes)  # Gmail のすべての権限は求めない
        self.assertFalse([s for s in scopes if re.search(r'/drive(\b|$)', s)])


if __name__ == '__main__':
    unittest.main()
