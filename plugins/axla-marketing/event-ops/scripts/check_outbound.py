#!/usr/bin/env python3
"""相手に出すものの検査（検証器）。spec 002。

相手に送る返事・資料の中身に、次のものが混ざっていたら exit 1。
- 社内の印（【要確認】【社内】TODO など）
- 送り先ではない相手の名前・メールアドレス（照合の元は git に入れない names.local）
names.local が無ければ照合できないので exit 2（先へ進ませない）。
見つけた名前は、出力では番号（PT-002 など）で知らせ、名前そのものは出さない。

使い方
  python3 check_outbound.py --names loop/marketing/event-ops/names.local --to PT-001 <ファイル>...
  [--markers <社内の印を1行1つ書いたファイル>]
"""
import argparse
import sys
from pathlib import Path

DEFAULT_MARKERS = ["【要確認】", "【社内】", "【TODO】", "【メモ】", "【仮】確認中", "TODO", "FIXME", "社内向け", "（社内）", "fail_code"]


def read_names(path):
    table = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        cols = [c.strip() for c in raw.split("\t")]
        pid = cols[0]
        name = cols[1] if len(cols) > 1 else ""
        email = cols[2] if len(cols) > 2 else ""
        table.append((pid, name, email))
    return table


def main():
    p = argparse.ArgumentParser(description="相手に出すものの検査")
    p.add_argument("--names", required=True)
    p.add_argument("--to", required=True, help="送り先の番号（カンマ区切り）")
    p.add_argument("--markers")
    p.add_argument("files", nargs="+")
    a = p.parse_args()

    if not Path(a.names).exists():
        sys.stderr.write("names.local が見つからないので照合できません。先へ進みません\n")
        return 2
    names = read_names(a.names)
    to = {x.strip() for x in a.to.split(",") if x.strip()}
    markers = list(DEFAULT_MARKERS)
    if a.markers and Path(a.markers).exists():
        markers += [m.strip() for m in Path(a.markers).read_text(encoding="utf-8").splitlines() if m.strip()]

    findings = []
    for f in a.files:
        for lineno, line in enumerate(Path(f).read_text(encoding="utf-8").splitlines(), 1):
            for m in markers:
                if m in line:
                    findings.append(f"{f}:{lineno} 社内の印 {m}")
            for pid, name, email in names:
                if pid in to:
                    continue
                if name and name in line:
                    findings.append(f"{f}:{lineno} 送り先ではない相手の名前（{pid}）")
                if email and email.lower() in line.lower():
                    findings.append(f"{f}:{lineno} 送り先ではない相手のメール（{pid}）")
    if findings:
        print("相手に出せません：")
        for x in findings:
            print("  " + x)
        return 1
    print("相手に出してよい中身です（社内の印 0・ほかの相手 0）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
