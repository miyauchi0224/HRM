#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
就業規則PDFを生成するスクリプト
- 1ページ目：就業規則の内容
- 2ページ目：改定版数と改定日
- ページ番号付与
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas as pdf_canvas
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter


def generate_pdf():
    """PDFを生成"""
    md_file = r"c:\Users\MiyauchiHitoshi\HRM\template\company_rule.md"
    temp_pdf = r"c:\Users\MiyauchiHitoshi\HRM\template\company_rule_temp.pdf"
    output_pdf = r"c:\Users\MiyauchiHitoshi\HRM\template\company_rule.pdf"

    # Markdownを読み込む
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # PDFドキュメントを作成
    doc = SimpleDocTemplate(temp_pdf, pagesize=A4, topMargin=15*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()

    # カスタムスタイル
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=12,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=11,
        spaceAfter=6,
        spaceBefore=6,
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=9,
        spaceAfter=4,
    )

    # コンテンツを構築
    story = []

    # Markdownの内容を行ごとに処理
    lines = md_content.split('\n')

    for line in lines:
        stripped = line.strip()

        if not stripped:
            story.append(Spacer(1, 2*mm))
        elif stripped.startswith('# ') and not stripped.startswith('## '):
            title_text = stripped[2:].strip()
            story.append(Paragraph(title_text, title_style))
        elif stripped.startswith('## ') and not stripped.startswith('### '):
            heading_text = stripped[3:].strip()
            story.append(Paragraph(heading_text, heading_style))
        elif stripped.startswith('### '):
            heading_text = stripped[4:].strip()
            story.append(Paragraph(heading_text, heading_style))
        elif stripped.startswith('- '):
            item_text = stripped[2:].strip()
            story.append(Paragraph(f"・ {item_text}", body_style))
        elif stripped == '---':
            story.append(Spacer(1, 3*mm))
        else:
            if stripped:
                story.append(Paragraph(stripped, body_style))

    # ページブレーク
    story.append(PageBreak())

    # 2ページ目：改定情報
    story.append(Spacer(1, 40*mm))
    story.append(Paragraph("改定情報", title_style))
    story.append(Spacer(1, 15*mm))

    # テーブルで改定情報を表示
    revision_data = [
        ['改定版数', 'Ver0.1'],
        ['改定日', '2026年4月24日']
    ]

    revision_table = Table(revision_data, colWidths=[40*mm, 80*mm])
    revision_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
    ]))

    story.append(revision_table)

    # PDFを構築
    doc.build(story)

    # ページ番号を追加
    add_page_numbers(temp_pdf, output_pdf)

    print(f"✓ PDF生成完了: {output_pdf}")


def add_page_numbers(input_pdf, output_pdf):
    """PDFにページ番号を追加"""
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    total_pages = len(reader.pages)

    for page_num, page in enumerate(reader.pages, 1):
        # ページ番号を追加するためのcanvasを作成
        packet = BytesIO()
        can = pdf_canvas.Canvas(packet, pagesize=A4)

        # 右下にページ番号を追加
        can.setFont("Helvetica", 9)
        page_text = f"{page_num} / {total_pages}"
        can.drawRightString(A4[0] - 1*cm, 1*cm, page_text)

        can.save()
        packet.seek(0)

        # ページに番号を追加
        overlay = PdfReader(packet).pages[0]
        page.merge_page(overlay)
        writer.add_page(page)

    # 出力
    with open(output_pdf, 'wb') as f:
        writer.write(f)


if __name__ == '__main__':
    try:
        generate_pdf()
    except ImportError as e:
        print(f"必要なライブラリがインストールされていません: {e}")
        print("以下をインストールしてください:")
        print("pip install reportlab PyPDF2")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
