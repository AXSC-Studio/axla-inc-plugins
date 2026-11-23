"""check_refs.py と、count_findings.py の重さの決め直しのテスト（Issue #35）。作り話の契約書で確かめる。"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def p(text, ilvl=None):
    num = '' if ilvl is None else f'<w:pPr><w:numPr><w:ilvl w:val="{ilvl}"/><w:numId w:val="1"/></w:numPr></w:pPr>'
    return f'<w:p>{num}<w:r><w:t>{text}</w:t></w:r></w:p>'


GOOD = [p('第1条（定義）'), p('「秘密情報」とは、開示された情報をいう。', 0), p('前項の規定にかかわらず、公知の情報は除く。', 0),
        p('公知の情報', 1), p('第2条（秘密保持）'), p('受領者は、第1条第2項の情報も秘密に保つ。', 0), p('前条の定義に従う。', 0),
        p('第3条（存続）'), p('第1条から第2条の規定は、終了後も存続する。')]


def make(root, paras):
    d = os.path.join(root, 'work')
    os.makedirs(os.path.join(d, 'word'))
    with open(os.path.join(d, 'word', 'document.xml'), 'w', encoding='utf-8') as f:
        f.write(f'<w:document {NS}><w:body>{"".join(paras)}</w:body></w:document>')
    return d


def run(script, *args):
    return subprocess.run([sys.executable, '-I', os.path.join(SCRIPTS, script), *args], capture_output=True, text=True)


class TestCheckRefs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, paras):
        return run('check_refs.py', make(self.root, paras))

    def test_good_contract_passes(self):
        r = self.check(GOOD)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn('条 3', r.stdout)  # 「第1条から…」で始まる本文を見出しにしない

    def test_missing_article(self):
        bad = GOOD[:-1] + [p('第1条から第12条の規定は、終了後も存続する。')]
        r = self.check(bad)
        self.assertEqual(r.returncode, 1)
        self.assertIn('【致命的】', r.stdout)
        self.assertIn('第12条', r.stdout)

    def test_too_few_items(self):
        bad = list(GOOD)
        bad[5] = p('受領者は、第1条第6項の情報も秘密に保つ。', 0)
        r = self.check(bad)
        self.assertEqual(r.returncode, 1)
        self.assertIn('2項までしか無い', r.stdout)

    def test_previous_article_in_first_article(self):
        bad = list(GOOD)
        bad[1] = p('前条の情報を「秘密情報」という。', 0)
        self.assertEqual(self.check(bad).returncode, 1)

    def test_previous_item_in_first_item(self):
        bad = list(GOOD)
        bad[5] = p('前項の情報も秘密に保つ。', 0)
        r = self.check(bad)
        self.assertEqual(r.returncode, 1)
        self.assertIn('前項', r.stdout)

    def test_no_headings_stops(self):
        r = self.check([p('本文だけの文書')])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('見つからない', r.stderr)


class TestSeverityRaised(unittest.TestCase):
    def write(self, text):
        f = tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8')
        f.write(text)
        f.close()
        self.addCleanup(os.remove, f.name)
        return f.name

    def test_reference_error_marked_important_counts_as_critical(self):
        # 2026-11-23 の受け入れテストで起きた形：参照の誤りを4体とも「重要」にした
        p_ = self.write('- 【重要】第2条第1項：「前条」の参照が誤っている（第2条第6項を指すべき）。直し方：…\n\n致命的 0件・重要 1件・軽微 0件\n')
        r = run('count_findings.py', p_)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('致命的として数える', r.stdout)

    def test_ordinary_important_stays_important(self):
        p_ = self.write('- 【重要】第3条：期間があいまい。直し方：…\n\n致命的 0件・重要 1件・軽微 0件\n')
        self.assertEqual(run('count_findings.py', p_).returncode, 0)


if __name__ == '__main__':
    unittest.main()
