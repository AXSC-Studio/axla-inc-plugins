"""redline.py のテスト。Google ドキュメントから書き出した形（goog_rdk の包み）の作り話の契約書で確かめる。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REDLINE = os.path.join(os.path.dirname(HERE), 'redline.py')
NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"')


def goog_para(pid, n, text):
    return (f'<w:p w14:paraId="{pid}"><w:pPr><w:spacing w:after="0"/></w:pPr>'
            f'<w:sdt><w:sdtPr><w:id w:val="{1000 + n}"/><w:tag w:val="goog_rdk_{n}"/></w:sdtPr><w:sdtContent>'
            f'<w:r><w:rPr><w:color w:val="130032"/></w:rPr><w:t xml:space="preserve">{text}</w:t></w:r>'
            f'</w:sdtContent></w:sdt></w:p>')


def make(root, body):
    d = os.path.join(root, 'work')
    os.makedirs(os.path.join(d, 'word'))
    with open(os.path.join(d, 'word', 'document.xml'), 'w', encoding='utf-8') as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>{body}</w:body></w:document>')
    return d


def run(d, changes, *extra):
    p = os.path.join(os.path.dirname(d), 'changes.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump({'author': 'Tester', 'date': '2026-01-01T00:00:00Z', 'changes': changes}, f, ensure_ascii=False)
    return subprocess.run([sys.executable, '-I', REDLINE, d, p, *extra], capture_output=True, text=True)


def doc(d):
    with open(os.path.join(d, 'word', 'document.xml'), encoding='utf-8') as f:
        return f.read()


class TestRedline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_google_docs_template_can_be_redlined(self):
        d = make(self.root, goog_para('00000001', 0, '第1条 甲は乙に開示する。') + goog_para('00000002', 1, '第2条 前条の情報は秘密とする。'))
        r = run(d, [{'op': 'substitute', 'para': '00000002', 'old': '前条', 'new': '第1条'}])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('goog_rdk', r.stdout)
        x = doc(d)
        self.assertNotIn('goog_rdk', x)
        self.assertIn('<w:del ', x)
        self.assertIn('第1条 甲は乙に開示する。', x)  # 触らない段落の文字はそのまま
        self.assertIn('<w:color w:val="130032"/>', x)  # 書式も残る

    def test_real_content_control_still_stops(self):
        body = ('<w:p w14:paraId="00000001"><w:sdt><w:sdtPr><w:tag w:val="name"/><w:text/></w:sdtPr><w:sdtContent>'
                '<w:r><w:t>甲の名前</w:t></w:r></w:sdtContent></w:sdt></w:p>')
        d = make(self.root, body)
        before = doc(d)
        r = run(d, [{'op': 'rebuild', 'para': '00000001', 'text': '乙の名前'}])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('w:sdt', r.stdout + r.stderr)
        self.assertEqual(before, doc(d))  # 止まったら何も書かない

    def test_id_collision_stops_before_writing(self):
        body = ('<w:p w14:paraId="00000001"><w:ins w:id="9500" w:author="Other" w:date="2020-01-01T00:00:00Z">'
                '<w:r><w:t>相手の直し</w:t></w:r></w:ins></w:p>'
                '<w:p w14:paraId="00000002"><w:r><w:t>第2条</w:t></w:r></w:p>')
        d = make(self.root, body)
        before = doc(d)
        r = run(d, [{'op': 'rebuild', 'para': '00000002', 'text': '第2条の2'}])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('9500', r.stdout + r.stderr)
        self.assertEqual(before, doc(d))
        r = run(d, [{'op': 'rebuild', 'para': '00000002', 'text': '第2条の2'}], '--rev-id-start', '10000')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == '__main__':
    unittest.main()
