from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_user_car
from app.models import ServiceRecord, ServiceWork, User
from app.schemas.service_record import (
    ServiceRecordCreate,
    ServiceRecordRead,
    ServiceWorkRead,
)
from app.services.receipts import (
    MAX_RECEIPT_BYTES,
    delete_receipt,
    detect_type,
    receipt_path,
    save_receipt,
)
from app.services.service_report import (
    ReportCar,
    ReportRecord,
    ReportWork,
    build_service_report,
)

router = APIRouter(prefix="/service-records", tags=["service-records"])


def _get_user_record(db: DbSession, user: User, record_id: int) -> ServiceRecord:
    """Запись журнала пользователя; для чужой и несуществующей — 404."""
    record = db.scalar(
        select(ServiceRecord).where(ServiceRecord.id == record_id, ServiceRecord.user_id == user.id)
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service record not found"
        )
    return record


def _to_read(record: ServiceRecord) -> ServiceRecordRead:
    works = [ServiceWorkRead(name=w.name, price=int(w.price)) for w in record.works]
    return ServiceRecordRead(
        id=record.id,
        car_id=record.car_id,
        service_date=record.service_date,
        mileage=record.mileage,
        sto_name=record.sto_name,
        note=record.note,
        works=works,
        total=sum(w.price for w in works),
        has_receipt=record.receipt_file is not None,
        created_at=record.created_at,
    )


@router.post("", response_model=ServiceRecordRead, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: ServiceRecordCreate, current_user: CurrentUser, db: DbSession
) -> ServiceRecordRead:
    """Новая запись журнала. Файл чека добавляется отдельно: PUT /{id}/receipt."""
    car = get_user_car(db, current_user, payload.car_id)
    record = ServiceRecord(
        user_id=current_user.id,
        car_id=car.id,
        service_date=payload.service_date,
        mileage=payload.mileage,
        sto_name=payload.sto_name,
        note=payload.note,
        works=[ServiceWork(name=w.name, price=Decimal(w.price)) for w in payload.works],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _to_read(record)


@router.get("", response_model=list[ServiceRecordRead])
def list_records(
    car_id: int,
    current_user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ServiceRecordRead]:
    """Журнал обслуживания одного авто, новые записи сверху."""
    car = get_user_car(db, current_user, car_id)
    records = db.scalars(
        select(ServiceRecord)
        .where(ServiceRecord.car_id == car.id)
        .order_by(ServiceRecord.service_date.desc(), ServiceRecord.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return [_to_read(r) for r in records]


# Важно: /report объявлен раньше /{record_id}, иначе «report» принимался бы за id.
@router.get("/report")
def service_report(car_id: int, current_user: CurrentUser, db: DbSession) -> Response:
    """PDF «История обслуживания» для покупателя: все записи авто по порядку дат."""
    car = get_user_car(db, current_user, car_id)
    records = db.scalars(
        select(ServiceRecord)
        .where(ServiceRecord.car_id == car.id)
        .order_by(ServiceRecord.service_date, ServiceRecord.id)
    ).all()
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No service records for this car"
        )
    pdf = build_service_report(
        ReportCar(
            brand=car.brand, model=car.model, year=car.year, mileage=car.mileage, region=car.region
        ),
        [
            ReportRecord(
                service_date=r.service_date,
                mileage=r.mileage,
                sto_name=r.sto_name,
                note=r.note,
                works=[ReportWork(name=w.name, price=int(w.price)) for w in r.works],
                has_receipt=r.receipt_file is not None,
            )
            for r in records
        ],
        generated_on=date.today(),
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="service-report-{car.id}.pdf"'},
    )


@router.get("/{record_id}", response_model=ServiceRecordRead)
def get_record(record_id: int, current_user: CurrentUser, db: DbSession) -> ServiceRecordRead:
    return _to_read(_get_user_record(db, current_user, record_id))


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(record_id: int, current_user: CurrentUser, db: DbSession) -> None:
    record = _get_user_record(db, current_user, record_id)
    receipt_file = record.receipt_file
    db.delete(record)
    db.commit()
    delete_receipt(receipt_file)  # файл удаляем после того, как запись из базы ушла


@router.put("/{record_id}/receipt", response_model=ServiceRecordRead)
def upload_receipt(
    record_id: int, file: UploadFile, current_user: CurrentUser, db: DbSession
) -> ServiceRecordRead:
    """Загрузить (или заменить) чек: JPEG, PNG или PDF, до 5 МБ. Поле формы — `file`."""
    record = _get_user_record(db, current_user, record_id)
    data = file.file.read(MAX_RECEIPT_BYTES + 1)
    if len(data) > MAX_RECEIPT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is larger than 5 MB"
        )
    detected = detect_type(data)
    if detected is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG or PDF files are allowed",
        )
    mime, extension = detected
    old_file = record.receipt_file
    record.receipt_file = save_receipt(data, extension)
    record.receipt_type = mime
    db.commit()
    db.refresh(record)
    delete_receipt(old_file)
    return _to_read(record)


@router.get("/{record_id}/receipt")
def download_receipt(record_id: int, current_user: CurrentUser, db: DbSession) -> FileResponse:
    record = _get_user_record(db, current_user, record_id)
    if record.receipt_file is None or record.receipt_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
    path = receipt_path(record.receipt_file)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
    return FileResponse(
        path,
        media_type=record.receipt_type,
        filename=f"receipt-{record.id}{path.suffix}",
        content_disposition_type="inline",
        headers={"X-Content-Type-Options": "nosniff"},
    )
