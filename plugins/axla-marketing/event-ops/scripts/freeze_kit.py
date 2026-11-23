#!/usr/bin/env python3
"""送る版を凍結する（中間ループ）。spec 005。

送る資料の中身（手元のファイル）のハッシュを取り、events/<ID>/sent/<相手>_<版>.json に URL と一緒に書く。
- 同じ URL がすでに凍結されていて、中身のハッシュが違えば exit 1（送った版は変えない。新しい版は新しい URL で）
- 出したハッシュを approve.py new --sha256 に渡す。spec 002 の hook は、この記録と承認のハッシュを照合する
- 凍結した URL への上書きの公開は、spec 002 の hook が止める

使い方
  python3 freeze_kit.py --event <フォルダ> --partner PT-002 --url <資料の URL> --file <その版の中身のファイル> --version v1.0
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eventops_lib as lib  # noqa: E402


def main():
    p = argparse.ArgumentParser(description="送る版を凍結する")
    p.add_argument("--event", required=True)
    p.add_argument("--partner", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--version", required=True)
    a = p.parse_args()
    if not re.fullmatch(r"PT-\d{3,}", a.partner):
        sys.stderr.write("相手は番号（PT-001 の形）で書いてください\n")
        return 2
    if not re.fullmatch(r"v\d+\.\d+", a.version):
        sys.stderr.write("版は v1.0 の形で\n")
        return 2
    event = Path(a.event)
    src = Path(a.file)
    if not src.exists():
        sys.stderr.write(f"中身のファイルがありません：{src}\n")
        return 2
    sha = hashlib.sha256(src.read_bytes()).hexdigest()
    sent = event / "sent"
    sent.mkdir(exist_ok=True)
    for f in sent.glob("*.json"):
        rec = lib.load_json(f, {})
        if rec.get("url", "").rstrip("/") == a.url.rstrip("/") and rec.get("sha256") != sha:
            print(f"この URL はもう別の中身で凍結されています（{f.name}）。直したなら新しい版（_v1.1 など）を新しい URL で作ってください")
            lib.record_run(lib.base_of_event(event), "middle", "sandbox", "blocked", "refreeze_changed", partner=a.partner)
            return 1
    rec = {"url": a.url, "sha256": sha, "partner": a.partner, "version": a.version, "frozen_at": lib.now_iso()}
    lib.save_json(sent / f"{a.partner}_{a.version}.json", rec)
    lib.record_run(lib.base_of_event(event), "middle", "state_store", "frozen", None, partner=a.partner, version=a.version)
    print(f"{a.partner} 向けの {a.version} を凍結しました")
    print(f"sha256: {sha}")
    print(f"次：人が自分の端末で approve.py new --event {event} --kit {a.url} --sha256 {sha} --to {a.partner} --tools <送る道具>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
