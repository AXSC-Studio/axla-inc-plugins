"""プラグインの中に、特定の会社の決め打ちが無いことを確かめる（Issue #5〜#7・#25）。
製品名の「Axla Legal」「axla-legal」と、例だと分かる書き方（「例：」のある行）は除く。"""
import os
import re
import unittest

PLUGIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATTERN = re.compile(r'Axla合同会社|Analy┊|Axla Comments|axla-inc の|乙（Axla|Axla の直し|Axla が')
SKIP_DIRS = {'tests'}
SKIP_FILES = {'LICENSE', 'PRIVACY.md', 'README.md'}


class TestNoCompany(unittest.TestCase):
    def test_no_hard_coded_company(self):
        found = []
        for root, dirs, files in os.walk(PLUGIN):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            for name in files:
                if name in SKIP_FILES or not name.endswith(('.py', '.md', '.json', '.gs', '.csv')):
                    continue
                path = os.path.join(root, name)
                with open(path, encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        if PATTERN.search(line) and '例：' not in line:
                            found.append(f'{os.path.relpath(path, PLUGIN)}:{i}')
        self.assertEqual(found, [], '特定の会社の決め打ちがある')


if __name__ == '__main__':
    unittest.main()
