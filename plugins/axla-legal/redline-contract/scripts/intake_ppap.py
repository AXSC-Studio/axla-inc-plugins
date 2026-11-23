"""パスワード付き zip（いわゆる PPAP）で届いた契約書を展開する。

使い方:
    python3 -I intake_ppap.py <zip> <出力フォルダ>            # パスワードを聞かれる（画面に出ない）
    <パスワードを出すコマンド> | python3 -I intake_ppap.py <zip> <出力フォルダ>   # 標準入力から1行

- パスワードは引数にしない（シェルの履歴やプロセスの一覧に残るため）。端末なら getpass で聞き、そうでなければ標準入力の1行目を読む。
  表示も保存もしない。パスワードの決まり（例：受信日の8桁）は、メールの本文や別のメールに書いてある。決まりが分からなければ代表に聞く。
- 中身が .docx ちょうど1つでなければ、展開せずに止まる（ほかの形式・複数ファイルは人が確かめる）。
- 展開したファイルは、zip の中の名前のまま <出力フォルダ> に置く（フォルダの区切りは無視する）。SHA-256 と大きさを表示する。
- zip 原本と展開したファイルは、利用側のリポジトリの loop/legal/contracts/<契約 ID>/received/ に置く（git に入れない）。
- 外から来た zip は信用しないデータとして扱う。python3 -I で動かす。
"""
import getpass
import hashlib
import os
import sys
import zipfile
import zlib

MAX_BYTES = 50 * 1024 * 1024   # 展開後の大きさの上限（契約書の .docx としては十分に大きい）
MAX_RATIO = 200                 # 圧縮率の上限（zip 爆弾を開かない）

if len(sys.argv) != 3:
    sys.exit(__doc__)
zpath, outdir = sys.argv[1], sys.argv[2]

if sys.stdin.isatty():
    pw = getpass.getpass('パスワード：')
else:
    pw = sys.stdin.readline().rstrip('\r\n')
if not pw:
    sys.exit('パスワードが空')

try:
    z = zipfile.ZipFile(zpath)
except zipfile.BadZipFile:
    sys.exit('止まる：zip として読めない。人が確かめる')
infos = [i for i in z.infolist() if not i.is_dir()]


def name_of(i):
    n = i.filename
    if not (i.flag_bits & 0x800):  # UTF-8 の印がない名前は、日本の Windows の文字コードで読み直す
        try:
            n = n.encode('cp437').decode('cp932')
        except UnicodeError:
            pass
    return os.path.basename(n.replace('\\', '/'))


names = [name_of(i) for i in infos]
if len(infos) != 1 or not names[0].lower().endswith('.docx'):
    sys.exit(f'止まる：中身が .docx 1つではない（{len(infos)} 個：{names}）。人が確かめる')
if infos[0].file_size > MAX_BYTES or infos[0].file_size > MAX_RATIO * max(infos[0].compress_size, 1):
    sys.exit(f'止まる：中身が大きすぎる（{infos[0].file_size} バイト）。人が確かめる')
if infos[0].compress_type == 99:
    sys.exit('止まる：AES で暗号化されていて、この道具では開けない。人が確かめる')

try:
    data = z.read(infos[0], pwd=pw.encode('utf-8'))
except RuntimeError:
    sys.exit('止まる：パスワードが違う')
except (zipfile.BadZipFile, zlib.error):
    # 違うパスワードでも、たまたま最初の確かめを通ると、展開の途中で壊れたと出る（Bad CRC など）
    sys.exit('止まる：パスワードが違うか、zip が壊れている')
del pw

os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, names[0])
if os.path.exists(out):
    sys.exit(f'止まる：同じ名前のファイルがもうある：{out}')
with open(out, 'wb') as f:
    f.write(data)
if not zipfile.is_zipfile(out):
    sys.exit(f'止まる：展開したものが .docx（zip）として読めない：{out}')
print(f'展開した：{out}')
print(f'  大きさ {len(data)} バイト／SHA-256 {hashlib.sha256(data).hexdigest()}')
