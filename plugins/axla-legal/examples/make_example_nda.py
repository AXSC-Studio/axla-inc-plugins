"""お試し用のダミーの NDA（.docx）を作る。架空の会社どうしの契約で、本物の契約ではない。

使い方:
    python3 -I make_example_nda.py <出力の .docx>

同じ出力になる（日時を固定している）。examples/example-nda.docx はこれで作ったもの。
相手の雛形によくある形（空欄の「●●」、前項・前条の参照、署名欄）を入れてある。
"""
import sys
import zipfile
from xml.sax.saxutils import escape

PARAS = [
    '秘密保持契約書',
    '架空商事株式会社（以下「甲」という。）と見本スタジオ合同会社（以下「乙」という。）は、相互に開示する情報の取扱いについて、次のとおり合意する。',
    '第1条（目的）',
    '甲および乙は、●●（以下「本目的」という。）のために、相手方に秘密情報を開示する。',
    '第2条（秘密情報の定義）',
    '本契約において「秘密情報」とは、開示者が受領者に開示した技術上または営業上の一切の情報をいう。',
    '前項の規定にかかわらず、次の情報は秘密情報に含まれない。（1）開示の時点で公知の情報（2）受領者がすでに保有していた情報',
    '第3条（秘密保持）',
    '受領者は、秘密情報を第三者に開示または漏えいしてはならない。',
    '前項の規定にかかわらず、受領者は、本目的のために必要な範囲で、自己の役員および従業員に秘密情報を開示することができる。',
    '第4条（返還）',
    '受領者は、開示者から求められたときは、秘密情報を含む資料を返還し、または破棄する。',
    '第5条（有効期間）',
    '本契約の有効期間は、締結日から1年間とする。第2条から第4条の規定は、本契約の終了後も2年間効力を有する。',
    '第6条（合意管轄）',
    '本契約に関する紛争は、東京地方裁判所を第一審の専属的合意管轄裁判所とする。',
    '本契約の成立を証するため、本書2通を作成し、甲乙記名押印のうえ、各1通を保有する。',
    '2099年1月1日',
    '甲：架空商事株式会社　代表取締役　架空 太郎',
    '乙：見本スタジオ合同会社　代表社員　見本 花子',
]

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
      'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" mc:Ignorable="w14"')


def para(i, text):
    bold = '<w:rPr><w:b/></w:rPr>' if text.startswith('第') and text.endswith('）') or i == 0 else ''
    jc = '<w:pPr><w:jc w:val="center"/></w:pPr>' if i == 0 else ''
    return (f'<w:p w14:paraId="{i + 1:08X}" w14:textId="77777777">{jc}<w:r>{bold}'
            f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>')


FILES = {
    '[Content_Types].xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
    '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
    '</Types>',
    '_rels/.rels': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
    '</Relationships>',
    'word/_rels/document.xml.rels': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
    '</Relationships>',
    'word/settings.xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:defaultTabStop w:val="720"/></w:settings>',
    'docProps/core.xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>秘密保持契約書（見本）</dc:title>'
    '<dc:creator>架空商事 法務部</dc:creator><cp:lastModifiedBy>架空商事 法務部</cp:lastModifiedBy>'
    '<dcterms:created xsi:type="dcterms:W3CDTF">2099-01-01T00:00:00Z</dcterms:created>'
    '<dcterms:modified xsi:type="dcterms:W3CDTF">2099-01-01T00:00:00Z</dcterms:modified></cp:coreProperties>',
    'word/document.xml': f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>'
    + ''.join(para(i, t) for i, t in enumerate(PARAS))
    + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1701" w:right="1701" w:bottom="1701" w:left="1701" '
      'w:header="851" w:footer="992" w:gutter="0"/></w:sectPr></w:body></w:document>',
}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with zipfile.ZipFile(sys.argv[1], 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted(FILES, key=lambda n: (n != '[Content_Types].xml', n)):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, FILES[name].encode('utf-8'))
    print(f'ok: {sys.argv[1]}（段落 {len(PARAS)}）')


if __name__ == '__main__':
    main()
