#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
就業規則HTMLを生成するスクリプト
"""

def generate_html():
    """HTMLを生成"""
    md_file = r"c:\Users\MiyauchiHitoshi\HRM\template\company_rule.md"
    output_html = r"c:\Users\MiyauchiHitoshi\HRM\template\company_rule.html"

    # Markdownを読み込む
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Markdownの内容をHTMLに変換
    html_parts = []
    html_parts.append('''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>就業規則</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }

        .page {
            background-color: white;
            width: 210mm;
            height: 297mm;
            margin: 10mm auto;
            padding: 15mm;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            position: relative;
            page-break-after: always;
        }

        .page:last-child {
            page-break-after: avoid;
        }

        .page-number {
            position: absolute;
            bottom: 10mm;
            right: 15mm;
            font-size: 9pt;
            color: #666;
        }

        h1 {
            font-size: 18pt;
            text-align: center;
            margin-bottom: 15mm;
            margin-top: 0;
            border-bottom: 2px solid #333;
            padding-bottom: 5mm;
        }

        h2 {
            font-size: 12pt;
            font-weight: bold;
            margin-top: 10mm;
            margin-bottom: 6mm;
            border-left: 3px solid #333;
            padding-left: 5mm;
        }

        h3 {
            font-size: 11pt;
            font-weight: bold;
            margin-top: 8mm;
            margin-bottom: 4mm;
            padding-left: 10mm;
        }

        p {
            font-size: 10pt;
            margin-bottom: 4mm;
            padding-left: 10mm;
            text-align: justify;
        }

        ul {
            margin-left: 15mm;
            margin-bottom: 4mm;
            list-style: none;
        }

        li {
            font-size: 10pt;
            margin-bottom: 2mm;
        }

        li:before {
            content: "・ ";
            margin-right: 5mm;
        }

        hr {
            border: none;
            border-top: 1px solid #ccc;
            margin: 5mm 0;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10mm auto;
        }

        th, td {
            border: 1px solid #333;
            padding: 8mm;
            text-align: center;
            font-size: 10pt;
        }

        th {
            background-color: #f0f0f0;
            font-weight: bold;
        }

        .revision-page {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100%;
        }

        .revision-title {
            font-size: 18pt;
            font-weight: bold;
            margin-bottom: 30mm;
            text-align: center;
        }

        .revision-table {
            width: 60%;
            margin: 0 auto;
        }

        @media print {
            body {
                background-color: white;
            }
            .page {
                box-shadow: none;
                margin: 0;
                width: 100%;
                height: auto;
                page-break-after: always;
            }
        }
    </style>
</head>
<body>
''')

    # ページ1：就業規則の内容
    html_parts.append('<div class="page">')

    lines = md_content.split('\n')
    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue
        elif stripped.startswith('# ') and not stripped.startswith('## '):
            title = stripped[2:].strip()
            html_parts.append(f'<h1>{title}</h1>')
        elif stripped.startswith('## ') and not stripped.startswith('### '):
            heading = stripped[3:].strip()
            html_parts.append(f'<h2>{heading}</h2>')
        elif stripped.startswith('### '):
            subheading = stripped[4:].strip()
            html_parts.append(f'<h3>{subheading}</h3>')
        elif stripped.startswith('- '):
            item = stripped[2:].strip()
            html_parts.append(f'<li>{item}</li>')
        elif stripped == '---':
            html_parts.append('<hr>')
        else:
            if stripped and not stripped.startswith('-'):
                html_parts.append(f'<p>{stripped}</p>')

    html_parts.append('<div class="page-number">1 / 2</div>')
    html_parts.append('</div>')

    # ページ2：改定情報
    html_parts.append('''<div class="page revision-page">
        <div class="revision-title">改定情報</div>
        <table class="revision-table">
            <tr>
                <th style="width: 40%;">改定版数</th>
                <td style="width: 60%;">Ver0.1</td>
            </tr>
            <tr>
                <th>改定日</th>
                <td>2026年4月24日</td>
            </tr>
        </table>
        <div class="page-number">2 / 2</div>
    </div>
</body>
</html>
''')

    # HTMLをファイルに書き込む
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))

    print(f"✓ HTML生成完了: {output_html}")
    print("\n【次のステップ】")
    print("1. ブラウザでHTMLファイルを開く")
    print("2. Ctrl+P で印刷ダイアログを開く")
    print("3. 「PDFに保存」を選択")
    print("4. ファイル名を company_rule.pdf に設定")
    print("5. 「保存」をクリック")


if __name__ == '__main__':
    generate_html()
