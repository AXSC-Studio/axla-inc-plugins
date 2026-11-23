"""budget.py（予算）のテスト。作り話の台帳で、「上限なし」の表示と「予算切れ」で止まるのを確かめる。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BUDGET = os.path.join(os.path.dirname(HERE), 'budget.py')
HEADER = 'id,種類,入口,受領日,状態,現在の版,検証の周回,相手との往復,人が触った回数,署名日,署名までの日数,LEGAL.md 世代\n'


def run(*args):
    return subprocess.run([sys.executable, '-I', BUDGET, *args], capture_output=True, text=True)


class TestBudget(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.legal = os.path.join(self.root, 'loop', 'legal')
        self.c = os.path.join(self.legal, 'contracts', '990101_NDA_1')
        os.makedirs(self.c)
        with open(os.path.join(self.legal, 'register.csv'), 'w', encoding='utf-8') as f:
            f.write(HEADER + '990101_NDA_1,NDA,A,2099-01-01,相手の返事待ち,v0.2.3,3,2,4,,,0\n')

    def tearDown(self):
        self.tmp.cleanup()

    def limits(self, **kw):
        with open(os.path.join(self.legal, 'budget.json'), 'w', encoding='utf-8') as f:
            json.dump({'limits': kw}, f)

    def test_show_without_file_says_no_limit(self):
        r = run('show', '--root', self.root)
        self.assertEqual(r.returncode, 0)
        self.assertIn('相手との往復：上限なし', r.stdout)
        self.assertIn('検証の周回（その送付の中）：5 周', r.stdout)  # spec で決まっている値だけ既定

    def test_check_without_limits_passes(self):
        r = run('check', self.c, '--today', '2099-03-01')
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn('2 往復 ／ 上限なし', r.stdout)
        self.assertIn('59 日 ／ 上限なし', r.stdout)

    def test_round_trips_exhausted(self):
        self.limits(round_trips=2)
        r = run('check', self.c, '--today', '2099-01-02')
        self.assertEqual(r.returncode, 3)
        self.assertIn('予算切れ（相手との往復）', r.stdout)

    def test_days_exhausted(self):
        self.limits(days_from_receipt=30)
        r = run('check', self.c, '--today', '2099-02-15')
        self.assertEqual(r.returncode, 3)
        self.assertIn('受け取ってからの日数', r.stdout)

    def test_cycles_count_per_send_and_reset(self):
        for _ in range(4):
            self.assertEqual(run('cycle', self.c, '--version', 'v0.2.4').returncode, 0)
        self.assertEqual(run('check', self.c).returncode, 0)
        run('cycle', self.c, '--version', 'v0.2.5')  # 同じ Y=2 で5周目
        r = run('check', self.c)
        self.assertEqual(r.returncode, 3)
        self.assertIn('予算切れ（検証の周回（その送付の中））', r.stdout)
        # 相手の返事が来て Y が上がったら、数え直す（Z は通算のまま）
        r = run('cycle', self.c, '--version', 'v0.3.6')
        self.assertIn('1 周目', r.stdout)
        self.assertEqual(run('check', self.c).returncode, 0)

    def test_null_removes_default(self):
        self.limits(inner_cycles_per_send=None)
        for _ in range(7):
            run('cycle', self.c, '--version', 'v0.2.9')
        self.assertEqual(run('check', self.c).returncode, 0)

    def test_review_tokens(self):
        self.limits(review_tokens=100000)
        self.assertEqual(run('check', self.c, '--review-tokens', '99999').returncode, 0)
        self.assertEqual(run('check', self.c, '--review-tokens', '100000').returncode, 3)


if __name__ == '__main__':
    unittest.main()
