"""Repository checks run by CI (Issue #19). / CI が回すリポジトリの検査（Issue #19）。

    python3 -I .github/scripts/check_repo.py <base ref>

1. Version bump: if anything under plugins/<p>/ changed against the base, plugins/<p>/.claude-plugin/plugin.json
   must have a different "version". / プラグインのフォルダが変わったのに版が上がっていなければ落とす。
2. No "version" in marketplace.json plugin entries (the version lives only in plugin.json).
   / marketplace.json のプラグインの項目に version があれば落とす。
   If the plugin has a CHANGELOG.md, the new version must have a "## X.Y.Z" entry. / 変更履歴があるプラグインは、新しい版の見出しが要る。
3. No contract files: *.docx, *.pdf, *.zip, "Redline Data.json" or a contracts/ folder anywhere in the repository,
   except the fictional samples under plugins/*/examples/ or plugins/*/<feature>/examples/. / 契約ファイルが混ざっていたら落とす（見本の置き場所は除く）。
"""
import json
import re
import subprocess
import sys


def git(*args):
    return subprocess.run(['git', *args], capture_output=True, text=True, check=True).stdout


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else 'origin/main'
    errors = []

    changed = [f for f in git('diff', '--name-only', f'{base}...HEAD').split('\n') if f]
    plugins = sorted({f.split('/')[1] for f in changed if f.startswith('plugins/') and f.count('/') >= 2})
    for p in plugins:
        path = f'plugins/{p}/.claude-plugin/plugin.json'
        try:
            new = json.loads(git('show', f'HEAD:{path}')).get('version')
        except subprocess.CalledProcessError:
            continue  # removed plugin
        try:
            old = json.loads(git('show', f'{base}:{path}')).get('version')
        except subprocess.CalledProcessError:
            old = None  # new plugin
        if old is not None and old == new:
            errors.append(f'{p}: files changed but version is still {new} (bump it in {path}) / 版が上がっていない')
        changelog = f'plugins/{p}/CHANGELOG.md'
        try:
            log = git('show', f'HEAD:{changelog}')
        except subprocess.CalledProcessError:
            log = None  # 変更履歴をまだ持たないプラグインは見ない
        if log is not None and old != new and not re.search(r'^## ' + re.escape(str(new)) + r'\s*$', log, re.M):
            errors.append(f'{p}: version {new} has no "## {new}" entry in {changelog} / 変更履歴に書いていない')

    market = json.loads(git('show', 'HEAD:.claude-plugin/marketplace.json'))
    for e in market.get('plugins', []):
        if 'version' in e:
            errors.append(f'marketplace.json: "{e.get("name")}" has a version; keep it only in plugin.json / version は plugin.json だけ')

    for f in git('ls-files').split('\n'):
        if not f or re.match(r'^plugins/[^/]+/([^/]+/)?examples/', f):
            continue
        if re.search(r'\.(docx|pdf|zip)$', f, re.I) or f.endswith('Redline Data.json') or re.search(r'(^|/)contracts/', f):
            errors.append(f'{f}: looks like a contract file / 契約ファイルらしい')

    for e in errors:
        print('ERROR:', e)
    print('ok' if not errors else f'{len(errors)} problem(s)')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
