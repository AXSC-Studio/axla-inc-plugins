"""清書の検査を本文の外まで広げたことのテスト（#21）と、小さな道具のエラーの扱いのテスト（#27）。作り話の契約書で確かめる。"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import test_make_clean as base  # noqa: E402

W = base.W


def run(script, *args, stdin=None):
    return subprocess.run([sys.executable, '-I', os.path.join(SCRIPTS, script), *args], capture_output=True, text=True, input=stdin)


def write(d, path, text):
    p = os.path.join(d, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)


class TestCleanExtras(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.out = os.path.join(self.root, 'clean.docx')

    def tearDown(self):
        self.tmp.cleanup()

    def test_header_footnote_move_and_format_changes_are_accepted(self):
        extra = ('<w:p><w:moveFrom w:id="20" w:author="Other"><w:r><w:t>動かす前</w:t></w:r></w:moveFrom>'
                 '<w:moveTo w:id="21" w:author="Other"><w:r><w:t>動かした後</w:t></w:r></w:moveTo></w:p>'
                 '<w:p><w:pPr><w:jc w:val="left"/><w:pPrChange w:id="22" w:author="Other"><w:pPr/></w:pPrChange></w:pPr>'
                 '<w:r><w:t>書式を変えた段落</w:t></w:r></w:p>')
        d = base.make_unpacked(self.root, extra=extra, settings=True)
        write(d, 'word/header1.xml', f'<w:hdr {W}><w:p><w:ins w:id="30" w:author="Other"><w:r><w:t>相手のヘッダー</w:t></w:r></w:ins>'
                                     f'<w:del w:id="31" w:author="Other"><w:r><w:delText>古いヘッダー</w:delText></w:r></w:del></w:p></w:hdr>')
        write(d, 'word/footnotes.xml', f'<w:footnotes {W}><w:footnote w:id="1"><w:p><w:ins w:id="32" w:author="Other">'
                                       f'<w:r><w:t>脚注</w:t></w:r></w:ins></w:p></w:footnote></w:footnotes>')
        r = run('make_clean.py', d, '--out', self.out)
        self.assertEqual(r.returncode, 0, r.stderr)
        with zipfile.ZipFile(self.out) as z:
            doc = z.read('word/document.xml').decode()
            hdr = z.read('word/header1.xml').decode()
            fn = z.read('word/footnotes.xml').decode()
        self.assertIn('動かした後', doc)
        self.assertNotIn('動かす前', doc)
        self.assertNotIn('pPrChange', doc)
        self.assertIn('相手のヘッダー', hdr)
        self.assertNotIn('古いヘッダー', hdr)
        for x in (doc, hdr, fn):
            self.assertNotIn('w:author', x)

    def test_side_information_is_removed(self):
        d = base.make_unpacked(self.root, settings=True)
        write(d, 'word/settings.xml', f'<w:settings {W}><w:attachedTemplate r:id="rId1" xmlns:r="r"/><w:docVars><w:docVar w:name="x" w:val="社内"/></w:docVars>'
                                      '<w:rsids><w:rsidRoot w:val="00A1B2C3"/></w:rsids><w:trackRevisions/></w:settings>')
        write(d, 'customXML/item1.xml', '<root>相手の社内システムの情報</root>')
        write(d, 'docProps/thumbnail.jpeg', 'jpeg')
        write(d, '_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                                '<Relationship Id="rId1" Type="t" Target="docProps/thumbnail.jpeg"/>'
                                '<Relationship Id="rId2" Type="t" Target="docProps/core.xml"/>'
                                '<Relationship Id="rId3" Type="t" Target="word/document.xml"/></Relationships>')
        with open(os.path.join(d, 'word/_rels/document.xml.rels'), encoding='utf-8') as f:
            rels = f.read()
        write(d, 'word/_rels/document.xml.rels', rels.replace('</Relationships>', '<Relationship Id="rId8" Type="t" Target="../customXML/item1.xml"/></Relationships>'))
        r = run('make_clean.py', d, '--out', self.out, '--date', '2026-01-01T00:00:00Z')
        self.assertEqual(r.returncode, 0, r.stderr)
        with zipfile.ZipFile(self.out) as z:
            names = z.namelist()
            s = z.read('word/settings.xml').decode()
            core = z.read('docProps/core.xml').decode()
        self.assertFalse([n for n in names if n.lower().startswith('customxml') or 'thumbnail' in n])
        for word in ('attachedTemplate', 'docVars', 'rsid'):
            self.assertNotIn(word, s)

    def test_dangling_relationship_stops(self):
        d = base.make_unpacked(self.root)
        with open(os.path.join(d, 'word/_rels/document.xml.rels'), encoding='utf-8') as f:
            rels = f.read()
        write(d, 'word/_rels/document.xml.rels', rels.replace('</Relationships>', '<Relationship Id="rId8" Type="t" Target="media/none.png"/></Relationships>'))
        r = run('make_clean.py', d, '--out', self.out)
        self.assertEqual(r.returncode, 1)
        self.assertIn('無い部品', r.stderr)
        self.assertFalse(os.path.exists(self.out))

    # --- #27 ---
    def test_view_without_args_shows_usage(self):
        r = run('view.py')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('usage', r.stderr)
        self.assertNotIn('IndexError', r.stderr)

    def test_add_comments_missing_paragraph_writes_nothing(self):
        d = base.make_unpacked(self.root)
        fake = os.path.join(self.root, 'comment.py')
        with open(fake, 'w') as f:
            f.write('import sys; sys.exit(0)\n')
        ch = os.path.join(self.root, 'c.json')
        with open(ch, 'w', encoding='utf-8') as f:
            json.dump({'author': 'T', 'comments': [{'start': 'NOPE0001', 'text': 'x'}]}, f)
        with open(os.path.join(d, 'word/document.xml'), encoding='utf-8') as f:
            before = f.read()
        r = run('add_comments.py', d, ch, '--comment-py', fake)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('NOPE0001', r.stderr)
        with open(os.path.join(d, 'word/document.xml'), encoding='utf-8') as f:
            self.assertEqual(before, f.read())

    def test_add_comments_failure_in_comment_py_writes_nothing(self):
        d = base.make_unpacked(self.root)
        with open(os.path.join(d, 'word/document.xml'), encoding='utf-8') as f:
            x = f.read()
        with open(os.path.join(d, 'word/document.xml'), 'w', encoding='utf-8') as f:
            f.write(x.replace('<w:p>', '<w:p w14:paraId="0000000A" xmlns:w14="w14">', 1))
        with open(os.path.join(d, 'word/document.xml'), encoding='utf-8') as f:
            before = f.read()
        fake = os.path.join(self.root, 'comment.py')
        with open(fake, 'w') as f:
            f.write('import sys; print("boom", file=sys.stderr); sys.exit(2)\n')
        ch = os.path.join(self.root, 'c.json')
        with open(ch, 'w', encoding='utf-8') as f:
            json.dump({'author': 'T', 'comments': [{'start': '0000000A', 'text': 'x'}]}, f)
        r = run('add_comments.py', d, ch, '--comment-py', fake)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('boom', r.stderr)
        with open(os.path.join(d, 'word/document.xml'), encoding='utf-8') as f:
            self.assertEqual(before, f.read())

    def test_intake_wrong_password_and_bad_zip(self):
        bad = os.path.join(self.root, 'bad.zip')
        with open(bad, 'wb') as f:
            f.write(b'not a zip')
        r = run('intake_ppap.py', bad, os.path.join(self.root, 'out'), stdin='pw\n')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('zip として読めない', r.stderr)
        self.assertNotIn('Traceback', r.stderr)


if __name__ == '__main__':
    unittest.main()
