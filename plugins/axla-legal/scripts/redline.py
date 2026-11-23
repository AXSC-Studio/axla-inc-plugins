"""展開した .docx の word/document.xml に、changes JSON の修正を変更履歴（w:ins / w:del）で入れる。

使い方:
    python -I redline.py <unpacked_dir> <changes.json> [--author "<作成者名>"] [--date 2026-11-16T00:00:00Z]

--date を省くと、changes JSON の "date"、それもなければ実行時刻（UTC）を使う。送った版で使った日時を
JSON の "date" に残しておくと、同じ JSON から同じ document.xml を作り直せる（再現テスト）。

changes JSON の形は README.md を参照。段落は w14:paraId で指す。
新しく足す段落には、--new-para-id-start（16進8桁）から順に ID を振る（コメントで参照できるように）。
--author を省くと、changes JSON の "author"、それもなければ利用側の loop/legal/config.json の "author" を使う。
どれにも無ければ止まる（作成者名をコードに決め打ちしない。Issue #5）。

Google ドキュメントから書き出した文書の空の包み（タグ goog_rdk_N の w:sdt）は、先に外す（文字は変えない）。
新しく振る変更履歴の ID と段落の ID が、文書にもとからある ID とぶつかるときは、書く前に止める。

制約：rebuild・substitute・delete は、段落を「ランの文字」だけで組み直す。段落の中にハイパーリンク・ブックマーク・
タブ・改行・フィールド・コメントの印・図・既存の変更履歴などがあると、それが消えてしまうので、その段落では止める。
そういう段落は、Word などで手で直すか、insert_after／insert_before で別の段落として足す。
"""
import argparse
import datetime
import os
import difflib
import html
import json
import re
import sys

ap = argparse.ArgumentParser()
ap.add_argument('unpacked')
ap.add_argument('changes')
ap.add_argument('--author', help='変更履歴の作成者。省くと changes JSON の "author"')
ap.add_argument('--date', help='変更履歴の日時（UTC）。省くと JSON の "date"、それもなければ実行時刻')
ap.add_argument('--rev-id-start', type=int, default=9000, help='w:id の起点（既存の ID とぶつからない値）')
ap.add_argument('--new-para-id-start', default='1A000000', help='足す段落の w14:paraId の起点（16進）')
args = ap.parse_args()

D = args.unpacked + '/word/document.xml'
spec = json.load(open(args.changes, encoding='utf-8'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate  # noqa: E402
args.author = args.author or spec.get('author') or gate.load_config(os.path.abspath(args.changes)).get('author')
args.date = args.date or spec.get('date') or datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
if not args.author:
    sys.exit('作成者名がない：--author か、changes JSON の "author" か、利用側の loop/legal/config.json の "author" に書く')
x = open(D, encoding='utf-8').read()


def all_text(s):
    return ''.join(re.findall(r'<w:(?:t|delText)(?: [^>]*)?>([^<]*)</w:(?:t|delText)>', s))


# Google ドキュメントから書き出した文書は、段落の中のランが空の印（タグ goog_rdk_N の w:sdt）で包まれている。
# 入力欄ではない（id と tag だけ）ので、包みだけを外す。中の文字と書式は残し、前後で文字が同じことを確かめる。
GOOG_SDT = re.compile(r'<w:sdt>\s*<w:sdtPr>\s*(?:<w:id w:val="-?\d+"/>\s*)?<w:tag w:val="goog_rdk_\d+"/>\s*'
                      r'(?:<w:id w:val="-?\d+"/>\s*)?</w:sdtPr>\s*(?:<w:sdtEndPr/>\s*)?<w:sdtContent>'
                      r'((?:(?!<w:sdt[ >]).)*?)</w:sdtContent>\s*</w:sdt>', re.S)
before = all_text(x)
x, n_goog = GOOG_SDT.subn(lambda m: m.group(1), x)
if all_text(x) != before:
    sys.exit('Google の包みを外したら文字が変わった。止める（文書は書き換えていない）')
if n_goog:
    print(f'Google ドキュメントの空の包み（goog_rdk）を {n_goog} 個外した')

# 新しく振る ID が、文書にもとからある ID とぶつからないことを確かめる（ぶつかると Word が壊れたと言う）
_used_rev = {int(v) for v in re.findall(
    r'<w:(?:ins|del|moveFrom|moveTo|\w+Change|comment(?:RangeStart|RangeEnd|Reference)?)\b[^>]*\bw:id="(\d+)"', x)}
_used_pid = {v.upper() for v in re.findall(r'w14:paraId="([0-9A-Fa-f]{8})"', x)}
if any(v > args.rev_id_start for v in _used_rev):
    sys.exit(f'--rev-id-start {args.rev_id_start} より大きい変更履歴・コメントの ID がもうある'
             f'（最大 {max(_used_rev)}）。それより大きい値を渡す')
if any(int(v, 16) > int(args.new_para_id_start, 16) for v in _used_pid if int(v, 16) < 0x80000000):
    sys.exit(f'--new-para-id-start {args.new_para_id_start} より大きい段落の ID がもうある。それより大きい値を渡す')
_id = [args.rev_id_start]
_pid = [int(args.new_para_id_start, 16)]


def nid():
    _id[0] += 1
    return str(_id[0])


def npid():
    _pid[0] += 1
    return '%08X' % _pid[0]


def attrs():
    return f'w:id="{nid()}" w:author="{html.escape(args.author)}" w:date="{args.date}"'


def esc(s):
    return html.escape(s, quote=False)


def get_para(pid):
    """段落を探す。`<w:p …/>` の1つのタグで閉じた空の段落は、`<w:p …></w:p>` に開いてから返す。"""
    global x
    pat = r'<w:p\b[^>]*?w14:paraId="%s"[^>]*?(?:/>|>.*?</w:p>)' % re.escape(pid)
    m = re.search(pat, x, flags=re.S)
    if not m:
        sys.exit(f'段落が見つからない: {pid}')
    if m.group(0).endswith('/>'):
        x = x[:m.start()] + m.group(0)[:-2] + '></w:p>' + x[m.end():]
        m = re.search(pat, x, flags=re.S)
    return m


def split_para(p):
    head = re.match(r'<w:p\b[^>]*>', p).group(0)
    m = re.search(r'<w:pPr>.*?</w:pPr>', p, flags=re.S)
    ppr = m.group(0) if m else ''
    runs = []
    for r in re.finditer(r'<w:r(?: [^>]*)?>(.*?)</w:r>', p, flags=re.S):
        inner = r.group(1)
        rm = re.search(r'<w:rPr>.*?</w:rPr>', inner, flags=re.S)
        rpr = rm.group(0) if rm else ''
        t = ''.join(html.unescape(s) for s in re.findall(r'<w:t(?: [^>]*)?>([^<]*)</w:t>', inner))
        runs.append((rpr, t))
    return head, ppr, runs


# 組み直すと消えてしまう要素（これがある段落では rebuild／delete をしない）
UNSAFE = ('w:hyperlink', 'w:bookmarkStart', 'w:bookmarkEnd', 'w:tab', 'w:br', 'w:cr', 'w:fldChar', 'w:fldSimple',
          'w:instrText', 'w:commentRangeStart', 'w:commentRangeEnd', 'w:commentReference', 'w:drawing', 'w:pict',
          'w:object', 'w:sym', 'w:footnoteReference', 'w:endnoteReference', 'w:sdt', 'w:smartTag', 'w:ins', 'w:del',
          'w:moveFrom', 'w:moveTo', 'w:noBreakHyphen', 'w:softHyphen', 'w:ptab')


def check_safe(pid, p):
    inner = re.sub(r'<w:pPr>.*?</w:pPr>', '', p, flags=re.S)
    found = sorted({t for t in UNSAFE if re.search(r'<%s[\s/>]' % t, inner)})
    if found:
        sys.exit(f'段落 {pid} に、組み直すと消える要素がある：{", ".join(found)}。手で直すか、別の段落として足す')


def para_text(pid):
    return ''.join(t for _, t in split_para(get_para(pid).group(0))[2])


def run(rpr, t, deleted=False):
    tag = 'w:delText' if deleted else 'w:t'
    return f'<w:r>{rpr}<{tag} xml:space="preserve">{esc(t)}</{tag}></w:r>'


def coalesce(ops):
    """短い一致（2文字以下）を前後の置換に吸収して、読みやすい差分にする。"""
    out = [list(op) for op in ops]
    changed = True
    while changed:
        changed = False
        for k in range(1, len(out) - 1):
            t, i1, i2, j1, j2 = out[k]
            if t == 'equal' and i2 - i1 <= 2 and out[k - 1][0] != 'equal' and out[k + 1][0] != 'equal':
                a, b = out[k - 1], out[k + 1]
                out[k - 1:k + 2] = [['replace', a[1], b[2], a[3], b[4]]]
                changed = True
                break
    return out


def no_underline(rpr):
    return re.sub(r'<w:u [^>]*/>', '', rpr).replace('<w:rPr></w:rPr>', '')


def rebuild(pid, new, clear_underline=False):
    """段落の本文を new に変える。文字単位の差分を取り、元のランの書式を保つ。
    clear_underline=True なら、残す文字と足す文字から下線を外す（雛形で空欄を示す下線を消すため）。
    外した下線は、書式の変更履歴（w:rPrChange）として残す。"""
    global x
    m = get_para(pid)
    check_safe(pid, m.group(0))
    head, ppr, runs = split_para(m.group(0))
    chars = [(c, rpr) for rpr, t in runs for c in t]
    old = ''.join(c for c, _ in chars)
    ops = coalesce(difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes())
    body = []

    def emit_old(i1, i2, deleted):
        seg = []
        for c, rpr in chars[i1:i2]:
            if seg and seg[-1][0] == rpr:
                seg[-1][1] += c
            else:
                seg.append([rpr, c])
        out = ''
        for r, t in seg:
            if clear_underline and not deleted and '<w:u ' in r:
                inner = re.search(r'<w:rPr>(.*?)</w:rPr>', r, flags=re.S).group(1)
                kept = re.sub(r'<w:u [^>]*/>', '', inner)
                r = f'<w:rPr>{kept}<w:rPrChange {attrs()}><w:rPr>{inner}</w:rPr></w:rPrChange></w:rPr>'
            out += run(r, t, deleted)
        return out

    for t, i1, i2, j1, j2 in ops:
        if t == 'equal':
            body.append(emit_old(i1, i2, False))
            continue
        if i2 > i1:
            body.append(f'<w:del {attrs()}>' + emit_old(i1, i2, True) + '</w:del>')
        if j2 > j1:
            rpr = chars[i1 - 1][1] if i1 > 0 else (chars[0][1] if chars else (runs[0][0] if runs else ''))
            if clear_underline:
                rpr = no_underline(rpr)
            body.append(f'<w:ins {attrs()}>' + run(rpr, new[j1:j2]) + '</w:ins>')
    x = x[:m.start()] + head + ppr + ''.join(body) + '</w:p>' + x[m.end():]


def mark_ppr(ppr, kind):
    mark = f'<w:{kind} {attrs()}/>'
    if not ppr:
        return f'<w:pPr><w:rPr>{mark}</w:rPr></w:pPr>'
    if '<w:rPr>' in ppr:
        return ppr.replace('<w:rPr>', '<w:rPr>' + mark, 1)
    return ppr.replace('</w:pPr>', f'<w:rPr>{mark}</w:rPr></w:pPr>')


def new_para(template_pid, text):
    _, tppr, truns = split_para(get_para(template_pid).group(0))
    trpr = next((r for r, t in truns if t), truns[0][0] if truns else '')
    return (f'<w:p w14:paraId="{npid()}" w14:textId="77777777">' + mark_ppr(tppr, 'ins')
            + f'<w:ins {attrs()}>' + run(trpr, text) + '</w:ins></w:p>')


def insert_after(anchor, template, texts):
    global x
    new = ''.join(new_para(template, t) for t in texts)
    m = get_para(anchor)
    x = x[:m.end()] + new + x[m.end():]


def insert_before(anchor, items):
    global x
    new = ''.join(new_para(it['template'], it['text']) for it in items)
    m = get_para(anchor)
    x = x[:m.start()] + new + x[m.start():]


def delete_para(pid):
    global x
    m = get_para(pid)
    check_safe(pid, m.group(0))
    head, ppr, runs = split_para(m.group(0))
    body = f'<w:del {attrs()}>' + ''.join(run(r, t, True) for r, t in runs if t) + '</w:del>'
    x = x[:m.start()] + head + mark_ppr(ppr, 'del') + body + '</w:p>' + x[m.end():]


for c in spec['changes']:
    op = c['op']
    if op == 'rebuild':
        rebuild(c['para'], c['text'], c.get('clear_underline', False))
    elif op == 'substitute':
        old = para_text(c['para'])
        if old.count(c['old']) != 1:
            sys.exit(f"substitute: {c['para']} に「{c['old']}」がちょうど1回ない")
        rebuild(c['para'], old.replace(c['old'], c['new']), c.get('clear_underline', False))
    elif op == 'insert_after':
        insert_after(c['anchor'], c['template'], c['texts'])
    elif op == 'insert_before':
        insert_before(c['anchor'], c['items'])
    elif op == 'delete':
        delete_para(c['para'])
    else:
        sys.exit(f'知らない op: {op}')

open(D, 'w', encoding='utf-8').write(x)
print(f'ok: changes={len(spec["changes"])} revisions={_id[0] - args.rev_id_start} '
      f'new_paras={_pid[0] - int(args.new_para_id_start, 16)}')
