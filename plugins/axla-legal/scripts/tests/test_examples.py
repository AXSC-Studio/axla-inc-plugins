"""お試しセット（examples/）で、README の「5分で試す」が最後まで通ることを確かめる（Issue #17）。"""
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
EX = os.path.join(os.path.dirname(SCRIPTS), 'examples')


def run(script, *args, cwd=None):
    path = script if os.path.isabs(script) else os.path.join(SCRIPTS, script)
    return subprocess.run([sys.executable, '-I', path, *args], capture_output=True, text=True, cwd=cwd)


class TestExamples(unittest.TestCase):
    def test_example_docx_is_reproducible(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, 'nda.docx')
            r = run(os.path.join(EX, 'make_example_nda.py'), out)
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(out, 'rb') as a, open(os.path.join(EX, 'example-nda.docx'), 'rb') as b:
                self.assertEqual(a.read(), b.read())

    def test_five_minute_trial(self):
        rd = os.path.join(EX, 'Redline Data.json')
        with tempfile.TemporaryDirectory() as w:
            work = os.path.join(w, 'work')
            with zipfile.ZipFile(os.path.join(EX, 'example-nda.docx')) as z:
                z.extractall(work)
            self.assertEqual(run('redline.py', work, rd).returncode, 0)
            v = run('view.py', work, 'changed')
            self.assertIn('{+両者の業務提携の検討+}', v.stdout)
            self.assertEqual(run('check_refs.py', work, '--out', os.path.join(w, 'review-refs.md')).returncode, 0)
            with open(os.path.join(EX, 'review-sample.md'), encoding='utf-8') as f, \
                    open(os.path.join(w, 'review-a.md'), 'w', encoding='utf-8') as g:
                g.write(f.read())
            c = run('count_findings.py', os.path.join(w, 'review-a.md'), os.path.join(w, 'review-refs.md'))
            self.assertEqual(c.returncode, 0, c.stdout)
            m = run('make_clean.py', work, '--out', os.path.join(w, 'clean.docx'), '--date', '2099-01-02T00:00:00Z')
            self.assertEqual(m.returncode, 0, m.stderr)
            with zipfile.ZipFile(os.path.join(w, 'clean.docx')) as z:
                core = z.read('docProps/core.xml').decode()
            self.assertNotIn('架空商事 法務部', core)  # 相手の作成者の情報は清書に残らない
            r = run('make_reply.py', rd, '--out-text', os.path.join(w, 'reply.txt'), '--out-html', os.path.join(w, 'reply.html'))
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(os.path.join(w, 'reply.txt'), encoding='utf-8') as f:
                self.assertEqual(f.read().count('（理由）'), 3)
            # 返信の HTML：画像は無く、最後に短い引用の枠がある（update_draft で相手の引用を付け直させないため。#12）
            with open(os.path.join(w, 'reply.html'), encoding='utf-8') as f:
                h = f.read()
            self.assertNotIn('<img', h)
            self.assertIn('<blockquote class="gmail_quote"', h)
            # その HTML と文の下書きは、送る前の検査に通る
            sys.path.insert(0, SCRIPTS)
            import base64
            import check_draft
            with open(os.path.join(w, 'reply.txt'), encoding='utf-8') as f:
                txt = f.read()
            mime = ('Content-Type: multipart/alternative; boundary="b"\r\n\r\n--b\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n'
                    + txt + '\r\n--b\r\nContent-Type: text/html; charset=utf-8\r\n\r\n' + h + '\r\n--b--\r\n')
            ok, lines = check_draft.check(base64.urlsafe_b64encode(mime.encode()).decode(), 0, txt)
            self.assertTrue(ok, lines)


if __name__ == '__main__':
    unittest.main()
