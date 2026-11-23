#!/usr/bin/env python3
"""公開リポの event-ops/ に、特定の会社・人の情報が入っていないかの検査（CI）。spec 002。

見つけたら exit 1。
- メールアドレス（example.com / example.org / example.net と noreply を除く）
- 電話番号
- 会社の形（日本の会社の種類・社団や財団の法人・英語圏の会社の略称。並びは COMPANY を見る）
- 秘密の語の一覧：環境変数 NEUTRAL_DENYLIST（1行1語。GitHub の Secrets に置く。語そのものは出力しない）

使い方
  python3 check_neutral.py plugins/axla-marketing/event-ops
"""
import os
import re
import sys
from pathlib import Path

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
PHONE = re.compile(r"(\+81[\s-]?\d{1,4}[\s-]?\d{1,4}[\s-]?\d{3,4}|\b0\d{1,4}-\d{1,4}-\d{3,4}\b)")
# 語をつなげて作る（この定義そのものが検査に引っかからないように）
_KAISHA = "会" + "社"
COMPANY = re.compile("(" + "|".join([
    "株式" + _KAISHA, "合同" + _KAISHA, "有限" + _KAISHA, "一般社団" + "法人", "一般財団" + "法人",
    r"Co\.,?\s*" + "Ltd", r"\b" + "Inc" + r"\.", r"\b" + "LL" + "C" + r"\b", r"\b" + "Gm" + "bH" + r"\b",
]) + ")")
ALLOWED_DOMAINS = {"example.com", "example.org", "example.net"}
TEXT_SUFFIXES = {".md", ".py", ".json", ".gs", ".sh", ".txt", ".csv", ".yml", ".yaml", ".html", ".js", ".ts"}


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("使い方：check_neutral.py <フォルダ>\n")
        return 2
    root = Path(sys.argv[1])
    deny = [w.strip() for w in os.environ.get("NEUTRAL_DENYLIST", "").splitlines() if w.strip()]
    findings = []
    files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file() and p.suffix in TEXT_SUFFIXES and "__pycache__" not in p.parts]
    for f in sorted(files):
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in EMAIL.finditer(line):
                dom = m.group(1).lower()
                if dom not in ALLOWED_DOMAINS and not m.group(0).lower().startswith("noreply@"):
                    findings.append(f"{f}:{lineno} メールアドレス（{dom}）")
            if PHONE.search(line):
                findings.append(f"{f}:{lineno} 電話番号")
            m = COMPANY.search(line)
            if m:
                findings.append(f"{f}:{lineno} 会社の形「{m.group(1)}」")
            for i, w in enumerate(deny, 1):
                if w in line:
                    findings.append(f"{f}:{lineno} 秘密の語の一覧の {i} 番目")
    if findings:
        print("event-ops に特定の会社・人の情報があります：")
        for x in findings:
            print("  " + x)
        return 1
    print(f"中立です（{len(files)} ファイル）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
