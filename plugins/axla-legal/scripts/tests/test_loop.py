"""入口の道具 loop.py のテスト（Issue #13）。作り話の契約で、段階が順に進むことと、飛ばした確認が見つかることを確かめる。"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
sys.path.insert(0, SCRIPTS)
import gate  # noqa: E402


def nxt(c):
    r = subprocess.run([sys.executable, '-I', os.path.join(SCRIPTS, 'loop.py'), 'next', c, '--json'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)['skill']


def run(script, *args):
    return subprocess.run([sys.executable, '-I', os.path.join(SCRIPTS, script), *args], capture_output=True, text=True)


class TestLoop(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.c = os.path.join(self.tmp.name, 'loop', 'legal', 'contracts', '990101_NDA_1')

    def tearDown(self):
        self.tmp.cleanup()

    def touch_redline(self):
        with open(os.path.join(self.c, 'Redline Data.json'), 'w') as f:
            f.write('{}')
        self.n = getattr(self, 'n', 0) + 1
        t = time.time() + 2 + 10 * self.n  # 直すたびに、前の記録より後の時刻になるようにする
        os.utime(os.path.join(self.c, 'Redline Data.json'), (t, t))

    def review(self, text):
        p = os.path.join(self.tmp.name, 'review.md')
        with open(p, 'w', encoding='utf-8') as f:
            f.write(text)
        return run('count_findings.py', p, '--record', self.c)

    def test_full_path(self):
        self.assertEqual(nxt(self.c), 'intake')
        os.makedirs(self.c)
        self.assertEqual(nxt(self.c), 'intake')
        run('gate.py', 'watch', self.c, '--to', 'legal@partner.example.test')
        self.assertEqual(nxt(self.c), 'redline-contract')
        self.touch_redline()
        self.assertEqual(nxt(self.c), 'review')
        self.review('- 【致命的】第1条：空欄\n\n致命的 1件・重要 0件・軽微 0件\n')
        self.assertEqual(nxt(self.c), 'redline-contract')  # NG なら直しに戻る
        self.touch_redline()
        self.assertEqual(nxt(self.c), 'review')
        self.review('- 【軽微】表記\n\n致命的 0件・重要 0件・軽微 1件\n')
        self.assertEqual(nxt(self.c), 'gdoc')
        run('gate.py', 'mark', self.c, 'gdoc', '--id', 'g-1')
        self.assertEqual(nxt(self.c), '人（最終 OK）')
        run('gate.py', 'mark', self.c, 'approval')
        self.assertEqual(nxt(self.c), 'send')
        gate.update(self.c, 'clean', {'ok': True, 'at': gate.now()})
        time.sleep(0.01)
        # 清書の時刻は Redline Data.json より後でないといけない（Redline は2秒先にしてある）
        self.assertEqual(nxt(self.c), 'send')
        os.utime(os.path.join(self.c, 'Redline Data.json'), (time.time() - 10, time.time() - 10))
        # 直しの時刻を前にずらしたので、検証・gdoc・最終 OK もやり直しにならないよう記録をそろえる
        for k in ('review', 'gdoc', 'approval'):
            g = gate.load(self.c)
            g[k]['redline_mtime'] = time.time() - 10
            gate.save(self.c, g)
        self.assertEqual(nxt(self.c), 'send')  # 返信文がまだ
        gate.update(self.c, 'reply', {'file': 'reply.txt', 'at': gate.now()})
        self.assertEqual(nxt(self.c), 'send')  # 下書きがまだ
        gate.update(self.c, 'draft', {'ids': ['d-1'], 'pending': True})
        self.assertEqual(nxt(self.c), 'send')  # 下書きの検査がまだ
        gate.update(self.c, 'draft', {'ids': ['d-1'], 'pending': False, 'checked_ok': True})
        self.assertEqual(nxt(self.c), '人（送信）')
        gate.update(self.c, 'sent', {'checked_ok': True})
        self.assertEqual(nxt(self.c), '相手の返事待ち')
        run('gate.py', 'mark', self.c, 'signed')
        self.assertEqual(nxt(self.c), 'learn')
        run('gate.py', 'mark', self.c, 'learned')
        self.assertEqual(nxt(self.c), 'done')

    def test_changed_redline_redoes_review_and_approval(self):
        os.makedirs(self.c)
        run('gate.py', 'watch', self.c, '--to', 'legal@partner.example.test')
        self.touch_redline()
        self.review('\n致命的 0件・重要 0件・軽微 0件\n')
        run('gate.py', 'mark', self.c, 'gdoc', '--id', 'g-1')
        run('gate.py', 'mark', self.c, 'approval')
        self.assertEqual(nxt(self.c), 'send')
        # 最終 OK のあとで直しを変えたら、検証からやり直し
        p = os.path.join(self.c, 'Redline Data.json')
        os.utime(p, (time.time() + 60, time.time() + 60))
        self.assertEqual(nxt(self.c), 'review')

    def test_sent_ng_is_incident(self):
        os.makedirs(self.c)
        gate.update(self.c, 'sent', {'checked_ok': False})
        self.assertEqual(nxt(self.c), 'INCIDENT')

    def test_budget_exhausted_goes_to_g1(self):
        os.makedirs(self.c)
        run('gate.py', 'watch', self.c, '--to', 'legal@partner.example.test')
        for _ in range(5):
            run('budget.py', 'cycle', self.c, '--version', 'v0.2.1')
        self.assertEqual(nxt(self.c), 'G1')


if __name__ == '__main__':
    unittest.main()
