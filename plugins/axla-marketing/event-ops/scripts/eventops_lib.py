"""event-ops の道具が共有する小さな部品（Python 3 の標準だけ）。

- 置き場：使う側のリポの loop/marketing/event-ops/
- 状態ストア（State Store）：events/<ID>/checklist.json・state.json・event-log.md
- 観測記録（Observability）：loop/marketing/event-ops/runs.jsonl に1周1行（実名なし）
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("loop") / "marketing" / "event-ops"
EVENT_ID = re.compile(r"^\d{6}_[a-z0-9][a-z0-9-]{0,60}$")
CRITICAL = re.compile(r"致命的\s*[:：]\s*(\d+)")


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def find_base(start):
    """start から上へたどって loop/marketing/event-ops/ を探す。無ければ None。"""
    p = Path(start).resolve()
    for d in [p, *p.parents]:
        if (d / DATA_DIR).is_dir():
            return d / DATA_DIR
        if d.name == "event-ops" and d.parent.name == "marketing" and d.parent.parent.name == "loop":
            return d
    return None


def base_of_event(event_dir):
    """events/<ID>/ から loop/marketing/event-ops/ を返す。"""
    return Path(event_dir).resolve().parent.parent


def load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record_run(base, layer, primitive, result, fail_code=None, **extra):
    """runs.jsonl に1行。実名・宛先は渡さないこと。"""
    if base is None:
        return
    line = {"ts": now_iso(), "layer": layer, "primitive": primitive, "result": result, "fail_code": fail_code}
    line.update(extra)
    try:
        with open(Path(base) / "runs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError:
        pass


# --- checklist（検証器の台帳） ----------------------------------------------

def checklist_path(event_dir):
    return Path(event_dir) / "checklist.json"


def load_checklist(event_dir):
    return load_json(checklist_path(event_dir), {"items": []})


def evidence_problem(event_dir, item):
    """証拠に問題があれば理由を返す。無ければ None。"""
    ev = item.get("evidence")
    if not ev:
        return "証拠が無い"
    if re.match(r"^https?://", ev):
        return None
    p = (Path(event_dir) / ev).resolve()
    if not str(p).startswith(str(Path(event_dir).resolve())):
        return "証拠がイベントのフォルダの外にある"
    if not p.exists():
        return f"証拠のファイルが無い（{ev}）"
    if item.get("kind") == "review":
        m = CRITICAL.search(p.read_text(encoding="utf-8"))
        if not m:
            return "検証役の記録に「致命的: N」が無い"
        if int(m.group(1)) != 0:
            return f"致命的が {m.group(1)} 件残っている"
    return None


def unmet_items(event_dir):
    """未達の項目（達成でない、または証拠が崩れている）を返す。"""
    out = []
    for item in load_checklist(event_dir).get("items", []):
        if not item.get("passes"):
            out.append((item["id"], "未達"))
            continue
        why = evidence_problem(event_dir, item)
        if why:
            out.append((item["id"], why))
    return out


def append_to_section(log_path, heading, line):
    """event-log.md の見出しのすぐ下に1行足す。見出しが無ければ末尾に作る。"""
    p = Path(log_path)
    text = p.read_text(encoding="utf-8") if p.exists() else ""
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if l.strip().startswith("## ") and heading in l:
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            # 「（まだない）」のような置き文字は消す
            if j < len(lines) and lines[j].strip() in ("（まだない）", "(none)"):
                lines.pop(j)
            lines.insert(i + 1, line)
            p.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    p.write_text(text.rstrip("\n") + f"\n\n## {heading}\n{line}\n", encoding="utf-8")
