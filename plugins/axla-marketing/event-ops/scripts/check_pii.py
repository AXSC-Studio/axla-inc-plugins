#!/usr/bin/env python3
"""使う側の git に実名・連絡先を入れない検査（コミット前）。spec 002。

loop/marketing/event-ops/ の中で git に入るファイル（台帳・決まり）に、
メールアドレス・電話番号・names.local の名前があれば exit 1。

使い方
  python3 check_pii.py --names loop/marketing/event-ops/names.local <ファイル>...
  python3 check_pii.py --names loop/marketing/event-ops/names.local --staged   # git に入れようとしているものだけ
pre-commit に入れる例（使う側のリポの .git/hooks/pre-commit）：
  python3 "<プラグインの場所>/event-ops/scripts/check_pii.py" --names loop/marketing/event-ops/names.local --staged
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
PHONE = re.compile(r"(\+81[\s-]?\d{1,4}[\s-]?\d{1,4}[\s-]?\d{3,4}|\b0\d{1,4}-\d{1,4}-\d{3,4}\b)")
WATCH = "loop/marketing/event-ops/"


def names_from(path):
    out = []
    p = Path(path)
    if not p.exists():
        return out
    for raw in p.read_text(encoding="utf-8").splitlines():
        if raw.strip() and not raw.lstrip().startswith("#"):
            cols = [c.strip() for c in raw.split("\t")]
            if len(cols) > 1 and cols[1]:
                out.append((cols[0], cols[1]))
    return out


def staged_files():
    r = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"], capture_output=True, text=True)
    return [f for f in r.stdout.splitlines() if f.startswith(WATCH) and not f.endswith("names.local")]


def main():
    p = argparse.ArgumentParser(description="git に実名・連絡先を入れない検査")
    p.add_argument("--names", required=True)
    p.add_argument("--staged", action="store_true")
    p.add_argument("files", nargs="*")
    a = p.parse_args()
    files = staged_files() if a.staged else a.files
    names = names_from(a.names)
    findings = []
    for f in files:
        try:
            text = Path(f).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if EMAIL.search(line):
                findings.append(f"{f}:{lineno} メールアドレス")
            if PHONE.search(line):
                findings.append(f"{f}:{lineno} 電話番号")
            for pid, name in names:
                if name in line:
                    findings.append(f"{f}:{lineno} 実名（{pid}）。番号で書いてください")
    if findings:
        print("git に入れられません：")
        for x in findings:
            print("  " + x)
        return 1
    print(f"実名・連絡先 0 件（{len(files)} ファイル）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
