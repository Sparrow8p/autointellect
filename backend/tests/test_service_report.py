from datetime import date
from io import BytesIO

from pypdf import PdfReader

from app.services.service_report import ReportCar, ReportRecord, ReportWork, build_service_report

CAR = ReportCar(brand="Hyundai", model="Solaris", year=2018, mileage=85_000, region="Татарстан")


def make_pdf(records):
    return build_service_report(CAR, records, generated_on=date(2026, 11, 18))


def text_of(pdf: bytes) -> str:
    return "\n".join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)


def record(day, works, **extra):
    return ReportRecord(
        service_date=day,
        mileage=extra.get("mileage"),
        sto_name=extra.get("sto_name"),
        note=extra.get("note"),
        works=works,
        has_receipt=extra.get("has_receipt", False),
    )


def test_report_is_a_pdf_with_cyrillic_text():
    pdf = make_pdf([record(date(2026, 5, 3), [ReportWork("Замена масла", 3_500)], mileage=92_000)])
    assert pdf.startswith(b"%PDF")
    text = text_of(pdf)
    assert "История обслуживания" in text
    assert "Hyundai Solaris" in text
    assert "Замена масла" in text
    assert "03.05.2026" in text
    assert "3 500 ₽" in text


def test_records_are_in_date_order_and_total_is_summed():
    pdf = make_pdf(
        [
            record(date(2026, 5, 3), [ReportWork("Вторая", 2_000)]),
            record(date(2025, 1, 10), [ReportWork("Первая", 1_000), ReportWork("Ещё", 500)]),
        ]
    )
    text = text_of(pdf)
    assert text.index("Первая") < text.index("Вторая")
    assert "Записей: 2" in text
    assert "3 500 ₽" in text  # 1000 + 500 + 2000


def test_user_text_is_not_treated_as_markup():
    pdf = make_pdf(
        [
            record(
                date(2026, 5, 3),
                [ReportWork("<b>Масло</b> & фильтр", 100)],
                sto_name="СТО <Тест>",
                note="<i>важно</i>",
            )
        ]
    )
    text = text_of(pdf)
    assert "<b>Масло</b> & фильтр" in text
    assert "СТО <Тест>" in text
    assert "<i>важно</i>" in text


def test_receipt_marker():
    with_receipt = text_of(
        make_pdf([record(date(2026, 1, 1), [ReportWork("А", 1)], has_receipt=True)])
    )
    without = text_of(make_pdf([record(date(2026, 1, 1), [ReportWork("А", 1)])]))
    assert "Чек приложен" in with_receipt
    assert "Чека нет" in without


def test_many_records_make_several_pages():
    records = [record(date(2026, 1, 1), [ReportWork(f"Работа {i}", 100)]) for i in range(60)]
    assert len(PdfReader(BytesIO(make_pdf(records))).pages) > 1
