#!/usr/bin/env python3
"""メールアドレスを相手の番号に引き当てる（手元だけで動く）。spec 006。

見張りのルーティンは名前の表（names.local）を持たない。返事や送信済みの知らせを受けたら、
手元でこの道具を使い、差出人・宛先のアドレスを相手の番号（PT-001）に直す。

exit 0：アドレスが一致した（番号を1行で出す）
exit 1：一致しない（同じドメインの相手がいれば「候補」として番号だけ出す。名前は出さない）

使い方
  python3 match_partner.py --names loop/marketing/event-ops/names.local --email "Name <a@b.example>"
"""
import argparse
import re
import sys
from pathlib import Path

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def main():
    p = argparse.ArgumentParser(description="アドレスを相手の番号に引き当てる")
    p.add_argument("--names", required=True)
    p.add_argument("--email", required=True)
    a = p.parse_args()
    if not Path(a.names).exists():
        sys.stderr.write("names.local がありません\n")
        return 2
    m = EMAIL.search(a.email)
    if not m:
        sys.stderr.write("アドレスが読めません\n")
        return 2
    addr, dom = m.group(0).lower(), m.group(1).lower()
    candidates = []
    for raw in Path(a.names).read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        cols = [c.strip() for c in raw.split("\t")]
        if len(cols) < 3 or not cols[2]:
            continue
        if cols[2].lower() == addr:
            print(cols[0])
            return 0
        if cols[2].lower().endswith("@" + dom):
            candidates.append(cols[0])
    if candidates:
        print("一致なし。同じドメインの候補：" + "、".join(candidates) + "（人に確かめ、names.local に足す）")
    else:
        print("一致なし（新しい相手なら、人が names.local に番号を付けて足す）")
    return 1


if __name__ == "__main__":
    sys.exit(main())
