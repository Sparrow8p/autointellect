"""PDF-отчёт «История обслуживания» для покупателя (чистая логика, без базы)."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.scenarios import format_rubles

FONTS_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"
FONT = "DejaVuSans"
FONT_BOLD = "DejaVuSans-Bold"


@dataclass(frozen=True)
class ReportWork:
    name: str
    price: int


@dataclass(frozen=True)
class ReportRecord:
    service_date: date
    mileage: int | None
    sto_name: str | None
    note: str | None
    works: Sequence[ReportWork]
    has_receipt: bool


@dataclass(frozen=True)
class ReportCar:
    brand: str
    model: str
    year: int
    mileage: int
    region: str


def _register_fonts() -> None:
    # DejaVu содержит кириллицу и знак ₽; стандартные шрифты PDF их не умеют.
    if FONT not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT, str(FONTS_DIR / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont(FONT_BOLD, str(FONTS_DIR / "DejaVuSans-Bold.ttf")))


def _text(value: str) -> str:
    # Paragraph понимает мини-HTML, поэтому пользовательский текст нужно экранировать.
    return escape(value)


def _date(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def build_service_report(
    car: ReportCar, records: Sequence[ReportRecord], generated_on: date
) -> bytes:
    """Возвращает PDF: данные авто, записи по порядку дат, итоговая сумма."""
    _register_fonts()

    normal = ParagraphStyle("normal", fontName=FONT, fontSize=10, leading=14)
    small = ParagraphStyle("small", parent=normal, fontSize=8.5, leading=12, textColor="#555555")
    title = ParagraphStyle("title", parent=normal, fontName=FONT_BOLD, fontSize=18, leading=22)
    heading = ParagraphStyle("heading", parent=normal, fontName=FONT_BOLD, fontSize=11)

    ordered = sorted(records, key=lambda r: r.service_date)
    total = sum(work.price for record in ordered for work in record.works)

    story: list = [
        Paragraph("История обслуживания", title),
        Spacer(1, 4 * mm),
        Paragraph(
            f"<b>{_text(car.brand)} {_text(car.model)}</b>, {car.year} г. · "
            f"пробег {format_rubles(car.mileage)} км · регион: {_text(car.region)}",
            normal,
        ),
        Spacer(1, 2 * mm),
        Paragraph(
            f"Записей: {len(ordered)} · Потрачено на обслуживание: {format_rubles(total)} ₽", normal
        ),
        Spacer(1, 6 * mm),
    ]

    for record in ordered:
        parts = [_date(record.service_date)]
        if record.mileage is not None:
            parts.append(f"{format_rubles(record.mileage)} км")
        if record.sto_name:
            parts.append(_text(record.sto_name))
        story.append(Paragraph(" · ".join(parts), heading))
        story.append(Spacer(1, 1.5 * mm))

        rows = [
            [Paragraph(_text(w.name), normal), f"{format_rubles(w.price)} ₽"] for w in record.works
        ]
        subtotal = sum(w.price for w in record.works)
        rows.append([Paragraph("<b>Итого</b>", normal), f"{format_rubles(subtotal)} ₽"])
        table = Table(rows, colWidths=[130 * mm, 40 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), FONT),
                    ("FONTNAME", (0, -1), (-1, -1), FONT_BOLD),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.lightgrey),
                    ("LINEABOVE", (0, -1), (-1, -1), 0.75, colors.grey),
                ]
            )
        )
        story.append(table)
        if record.note:
            story.append(Spacer(1, 1.5 * mm))
            story.append(Paragraph(f"Примечание: {_text(record.note)}", small))
        story.append(Spacer(1, 1.5 * mm))
        story.append(Paragraph("Чек приложен" if record.has_receipt else "Чека нет", small))
        story.append(Spacer(1, 6 * mm))

    story.append(Paragraph(f"Сформировано в «Авто-Интеллект» {_date(generated_on)}", small))

    buffer = BytesIO()
    SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="История обслуживания",
    ).build(story)
    return buffer.getvalue()
