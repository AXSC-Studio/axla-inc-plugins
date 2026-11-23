"""make_clean.py と accept.py のテスト（作り話の契約書で確かめる。実物の契約書は使わない）。

使い方:
    python3 -I -m unittest discover -s "${CLAUDE_PLUGIN_ROOT}/scripts/tests"
"""
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

DOCUMENT = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document {W}><w:body>
<w:p><w:commentRangeStart w:id="0"/><w:r><w:t>第1条 甲と乙は、</w:t></w:r>
<w:del w:id="1" w:author="Tester"><w:r><w:delText>古い言葉</w:delText></w:r></w:del>
<w:ins w:id="2" w:author="Tester"><w:r><w:t>新しい言葉</w:t></w:r></w:ins>
<w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r></w:p>
{{extra}}
</w:body></w:document>'''
COMMENTS = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:comments {W}><w:comment w:id="0" w:author="Tester"><w:p><w:r><w:t>社内向けの理由</w:t></w:r></w:p></w:comment></w:comments>'
RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/></Relationships>')
TYPES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
         '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
         '<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/></Types>')
CORE = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        '<dc:title>作り話の NDA</dc:title><dc:creator>Someone</dc:creator><cp:lastModifiedBy>Someone</cp:lastModifiedBy>'
        '<dcterms:modified xsi:type="dcterms:W3CDTF">2020-01-01T00:00:00Z</dcterms:modified></cp:coreProperties>')
APP = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties><Company>Example Co.</Company></Properties>'


def make_unpacked(root, extra='', settings=False):
    d = os.path.join(root, 'work')
    files = {
        '[Content_Types].xml': TYPES,
        'word/document.xml': DOCUMENT.replace('{extra}', extra),
        'word/comments.xml': COMMENTS,
        'word/_rels/document.xml.rels': RELS,
        'docProps/core.xml': CORE,
        'docProps/app.xml': APP,
    }
    if settings:
        files['word/settings.xml'] = f'<w:settings {W}><w:trackRevisions/></w:settings>'
    for path, text in files.items():
        p = os.path.join(d, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(text)
    return d


def run(script, *args):
    return subprocess.run([sys.executable, '-I', os.path.join(SCRIPTS, script), *args], capture_output=True, text=True)


class TestMakeClean(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.out = os.path.join(self.root, 'clean.docx')

    def tearDown(self):
        self.tmp.cleanup()

    def test_accept_without_settings(self):
        d = make_unpacked(self.root)
        r = run('accept.py', d)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_clean_without_settings(self):
        d = make_unpacked(self.root)
        before = open(os.path.join(d, 'word/document.xml'), encoding='utf-8').read()
        r = run('make_clean.py', d, '--out', self.out, '--date', '2026-01-01T00:00:00Z')
        self.assertEqual(r.returncode, 0, r.stderr)
        with zipfile.ZipFile(self.out) as z:
            names = z.namelist()
            doc = z.read('word/document.xml').decode()
            core = z.read('docProps/core.xml').decode()
            self.assertEqual(names[0], '[Content_Types].xml')
            self.assertNotIn('word/comments.xml', names)
            self.assertNotIn('comments.xml', z.read('word/_rels/document.xml.rels').decode())
            self.assertNotIn('Example Co.', z.read('docProps/app.xml').decode())
        self.assertIn('新しい言葉', doc)
        self.assertNotIn('古い言葉', doc)
        self.assertNotRegex(doc, r'<w:(ins|del|comment)')
        self.assertNotIn('Someone', core)
        self.assertIn('2026-01-01T00:00:00Z', core)
        # 元の展開済みフォルダは書き換えない
        self.assertEqual(before, open(os.path.join(d, 'word/document.xml'), encoding='utf-8').read())

    def test_same_input_same_bytes(self):
        d = make_unpacked(self.root, settings=True)
        out2 = os.path.join(self.root, 'clean2.docx')
        for o in (self.out, out2):
            r = run('make_clean.py', d, '--out', o, '--date', '2026-01-01T00:00:00Z')
            self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(open(self.out, 'rb').read(), open(out2, 'rb').read())

    def test_stops_and_leaves_no_file(self):
        # accept.py が扱わない変更履歴（移動）を入れる → 検査で止まり、前の清書も消える
        extra = '<w:p><w:moveFrom w:id="5" w:author="Tester"><w:r><w:t>動かした文</w:t></w:r></w:moveFrom></w:p>'
        d = make_unpacked(self.root, extra=extra)
        with open(self.out, 'wb') as f:
            f.write(b'old clean')
        r = run('make_clean.py', d, '--out', self.out)
        self.assertEqual(r.returncode, 1)
        self.assertIn('止めた', r.stderr)
        self.assertFalse(os.path.exists(self.out))
        self.assertFalse(os.path.exists(self.out + '.part'))

    def test_hidden_text_stops(self):
        extra = '<w:p><w:r><w:rPr><w:vanish/></w:rPr><w:t>隠し文字</w:t></w:r></w:p>'
        d = make_unpacked(self.root, extra=extra)
        r = run('make_clean.py', d, '--out', self.out)
        self.assertEqual(r.returncode, 1)
        self.assertIn('隠し文字', r.stderr)
        self.assertFalse(os.path.exists(self.out))

    def test_accept_failure_stops(self):
        d = make_unpacked(self.root)
        os.remove(os.path.join(d, 'word/document.xml'))  # accept.py が落ちる形
        r = run('make_clean.py', d, '--out', self.out)
        self.assertEqual(r.returncode, 1)
        self.assertIn('accept.py', r.stderr)
        self.assertFalse(os.path.exists(self.out))


if __name__ == '__main__':
    unittest.main()
