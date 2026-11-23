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

    def with_para(self):
        d = base.make_unpacked(self.root)
        with open(os.path.join(d, 'word/document.xml'), encoding='utf-8') as f:
            x = f.read()
        with open(os.path.join(d, 'word/document.xml'), 'w', encoding='utf-8') as f:
            f.write(x.replace('<w:p>', '<w:p w14:paraId="0000000A" xmlns:w14="w14">', 1))
        os.remove(os.path.join(d, 'word/comments.xml'))  # コメントの無い原本にする
        with open(os.path.join(d, 'word/_rels/document.xml.rels'), 'w', encoding='utf-8') as f:
            f.write('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>')
        with open(os.path.join(d, 'word/document.xml'), encoding='utf-8') as f:
            x = f.read()
        x = x.replace('<w:commentRangeStart w:id="0"/>', '').replace('<w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r>', '')
        with open(os.path.join(d, 'word/document.xml'), 'w', encoding='utf-8') as f:
            f.write(x)
        with open(os.path.join(d, '[Content_Types].xml'), encoding='utf-8') as f:
            ct = f.read()
        with open(os.path.join(d, '[Content_Types].xml'), 'w', encoding='utf-8') as f:
            f.write(ct.replace('<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>', ''))
        return d

    def changes(self, comments, author='T'):
        ch = os.path.join(self.root, 'c.json')
        with open(ch, 'w', encoding='utf-8') as f:
            json.dump({'author': author, 'initials': 'TT', 'date': '2099-01-01T00:00:00Z', 'comments': comments}, f, ensure_ascii=False)
        return ch

    def test_add_comments_missing_paragraph_writes_nothing(self):
        d = self.with_para()
        with open(os.path.join(d, 'word/document.xml'), encoding='utf-8') as f:
            before = f.read()
        r = run('add_comments.py', d, self.changes([{'start': 'NOPE0001', 'text': 'x'}]))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('NOPE0001', r.stderr)
        with open(os.path.join(d, 'word/document.xml'), encoding='utf-8') as f:
            self.assertEqual(before, f.read())
        self.assertFalse(os.path.exists(os.path.join(d, 'word/comments.xml')))

    def test_add_comments_without_outside_tools(self):
        # 外のスキルの部品も venv も使わずに、コメントの本体・関係づけ・登録・本文の印を書く（#8・#9）
        d = self.with_para()
        r = run('add_comments.py', d, self.changes([{'start': '0000000A', 'text': '理由の1行目\n2行目 & <記号>'}]))
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(d, 'word/comments.xml'), encoding='utf-8') as f:
            com = f.read()
        self.assertIn('w:author="T"', com)
        self.assertIn('&amp; &lt;記号&gt;', com)
        with open(os.path.join(d, 'word/_rels/document.xml.rels'), encoding='utf-8') as f:
            self.assertIn('Target="comments.xml"', f.read())
        v = run('validate_docx.py', d)
        self.assertEqual(v.returncode, 0, v.stdout)
        # 2回目はその後ろに足し、ID は続きから
        r = run('add_comments.py', d, self.changes([{'start': '0000000A', 'text': '2件目'}]))
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(d, 'word/comments.xml'), encoding='utf-8') as f:
            self.assertIn('w:id="1"', f.read())
        self.assertEqual(run('validate_docx.py', d).returncode, 0)

    def test_add_comments_id_collision_stops(self):
        d = self.with_para()
        self.assertEqual(run('add_comments.py', d, self.changes([{'start': '0000000A', 'text': 'a'}])).returncode, 0)
        r = run('add_comments.py', d, self.changes([{'start': '0000000A', 'text': 'b'}]), '--comment-id-start', '0')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('ぶつかる', r.stderr)

    def test_validate_finds_broken_comment_pairs(self):
        d = self.with_para()
        self.assertEqual(run('add_comments.py', d, self.changes([{'start': '0000000A', 'text': 'a'}])).returncode, 0)
        os.remove(os.path.join(d, 'word/comments.xml'))
        v = run('validate_docx.py', d)
        self.assertEqual(v.returncode, 1)
        self.assertIn('無い部品', v.stdout)

    def test_validate_refuses_doctype(self):
        d = self.with_para()
        with open(os.path.join(d, 'word/styles.xml'), 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><x>&a;</x>')
        v = run('validate_docx.py', d)
        self.assertEqual(v.returncode, 1)
        self.assertIn('DOCTYPE', v.stdout)

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
