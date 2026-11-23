"""outer_loop.py と count_findings.py のテスト。作り話の契約で、外側のループを1回回して世代が上がるまでを確かめる。"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
GIT = ['git', '-c', 'user.name=t', '-c', 'user.email=t@example.test']

LOG = """# 990101_NDA_1 Loop Log

## 1. いまの状態と次の一手
- 状態：Signed

## 8. 学び
- 作り話の学び：返信の下書きの引用に画像が入る。柵：hooks/guard.py の「下書きの画像」

## 9. 付録
- ここは集めない
"""


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, '-I', os.path.join(SCRIPTS, script), *args], capture_output=True, text=True, cwd=cwd)


class TestOuterLoop(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        legal = os.path.join(self.root, 'loop', 'legal')
        c = os.path.join(legal, 'contracts', '990101_NDA_1')
        os.makedirs(c)
        with open(os.path.join(legal, 'LEGAL.md'), 'w', encoding='utf-8') as f:
            f.write('# LEGAL.md\n\n- 世代：**0**（説明）\n')
        with open(os.path.join(c, 'loop-log.md'), 'w', encoding='utf-8') as f:
            f.write(LOG)
        subprocess.run(['git', 'init', '-q', '-b', 'main', self.root], check=True)
        subprocess.run(GIT + ['-C', self.root, 'commit', '-q', '--allow-empty', '-m', 'x'], check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def legal_md(self):
        with open(os.path.join(self.root, 'loop', 'legal', 'LEGAL.md'), encoding='utf-8') as f:
            return f.read()

    def test_collect_takes_only_learnings(self):
        r = run('outer_loop.py', 'collect', '--root', self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('作り話の学び', r.stdout)
        self.assertNotIn('ここは集めない', r.stdout)
        self.assertNotIn('状態：Signed', r.stdout)

    def test_bump_refused_outside_outer_branch(self):
        r = run('outer_loop.py', 'bump', '--root', self.root)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('世代：**0**', self.legal_md())

    def test_one_outer_loop_raises_generation(self):
        subprocess.run(['git', '-C', self.root, 'checkout', '-q', '-b', 'legal-outer/990101_NDA_1'], check=True)
        r = run('outer_loop.py', 'bump', '--root', self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('世代：**1**', self.legal_md())


class TestCountFindings(unittest.TestCase):
    def write(self, text):
        f = tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8')
        f.write(text)
        f.close()
        self.addCleanup(os.remove, f.name)
        return f.name

    def test_pass(self):
        p = self.write('- 【重要】第3条：あいまい。直し方：…\n- 【軽微】表記\n\n致命的 0件・重要 1件・軽微 1件\n')
        self.assertEqual(run('count_findings.py', p).returncode, 0)

    def test_critical(self):
        p = self.write('1. 【致命的】第1条：空欄\n\n致命的 1件・重要 0件・軽微 0件\n')
        self.assertEqual(run('count_findings.py', p).returncode, 1)

    def test_reviewer_miscounted(self):
        # 検証役が「致命的 0件」と書いても、印が1つあれば数が合わない
        p = self.write('- 【致命的】第1条：空欄\n\n致命的 0件・重要 0件・軽微 0件\n')
        r = run('count_findings.py', p)
        self.assertEqual(r.returncode, 2)
        self.assertIn('合わない', r.stdout)

    def test_no_summary(self):
        p = self.write('- 【軽微】表記\n')
        self.assertEqual(run('count_findings.py', p).returncode, 2)


if __name__ == '__main__':
    unittest.main()
