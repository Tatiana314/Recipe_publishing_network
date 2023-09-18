"""
Создание pdf-файла.
"""
from django.http import HttpResponse

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer
from reportlab.platypus.tables import TableStyle


def pdf_file_table(data, header_table):
    """Создаем таблицу в пдф-файле."""
    response = HttpResponse(headers={
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'attachment'
    })
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    elements = []

    styles = getSampleStyleSheet()
    styles_header_table = styles['Normal']
    styles_header_table.fontName = 'Arial'
    styles_header_table.fontSize = 22
    styles_header_table.alignment = 1

    doc = SimpleDocTemplate(response, pagesize=letter)
    table = Table(data, colWidths=175, rowHeights=30)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.brown),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Arial'),
        ('FONTSIZE', (0, 0), (-1, 0), 18),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Arial'),
        ('FONTSIZE', (0, 1), (-1, -1), 14),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('VALIGN', (-1, 0), (-2, 0), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))

    elements.append(Paragraph(header_table, styles_header_table))
    elements.append(Spacer(height=30, width=1))
    elements.append(table)
    doc.build(elements)
    return response
