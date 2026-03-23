from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import SessionLocal
from ..utils import ensure_upload_folders, bmi_folder_name, uploads_abs, uploads_rel
import os
from datetime import datetime
import calendar
from io import BytesIO
from pathlib import Path
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

router = APIRouter()

PNP_BMI_AGE_TABLE = [
    {"group": "29 years old and below", "min_age": 0, "max_age": 29, "acceptable_min": 18.5, "acceptable_max": 24.9},
    {"group": "30-34 years old", "min_age": 30, "max_age": 34, "acceptable_min": 19.0, "acceptable_max": 25.4},
    {"group": "35-39 years old", "min_age": 35, "max_age": 39, "acceptable_min": 19.5, "acceptable_max": 25.9},
    {"group": "40-44 years old", "min_age": 40, "max_age": 44, "acceptable_min": 20.0, "acceptable_max": 26.4},
    {"group": "45-50 years old", "min_age": 45, "max_age": 50, "acceptable_min": 20.5, "acceptable_max": 26.9},
    {"group": "51 years old and above", "min_age": 51, "max_age": 200, "acceptable_min": 21.0, "acceptable_max": 27.4},
]

INTERVENTION_PACKAGE_MAP: Dict[str, Dict[str, str]] = {
    "Severely Underweight": {"package": "A", "duration": "48 weeks", "recommendation": "Gain 1-3 kg/month"},
    "Underweight": {"package": "A", "duration": "48 weeks", "recommendation": "Gain 1-3 kg/month"},
    "Normal": {"package": "B", "duration": "12 weeks", "recommendation": "Maintain"},
    "Acceptable BMI": {"package": "B", "duration": "12 weeks", "recommendation": "Maintain"},
    "Overweight": {"package": "C", "duration": "24 weeks", "recommendation": "Lose 2 kg/month"},
    "Obese Class 1": {"package": "D", "duration": "36 weeks", "recommendation": "Lose 2 kg/month"},
    "Obese Class 2": {"package": "E", "duration": "48 weeks", "recommendation": "Lose 2 kg/month"},
    "Obese Class 3": {"package": "F", "duration": "60 weeks", "recommendation": "Lose 2 kg/month"},
}

WHO_THRESHOLDS = {
    "underweight": 18.5,
    "normal_upper": 24.9,
    "overweight_upper": 29.9,
}

MONTHS_BEFORE = 8
MIN_MONTHS_AFTER = 2
TOTAL_MONTH_COLUMNS = 14

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def compute_bmi(weight_kg: float, height_cm: float) -> float:
    if height_cm <= 0:
        return 0.0
    h = height_cm / 100.0
    return round(weight_kg / (h * h), 2)


def get_pnp_age_row(age: int) -> Dict[str, float]:
    for row in PNP_BMI_AGE_TABLE:
        if row["min_age"] <= age <= row["max_age"]:
            return row
    return PNP_BMI_AGE_TABLE[-1]


def classify_who_bmi(bmi: float) -> str:
    if bmi < WHO_THRESHOLDS["underweight"]:
        return "Underweight"
    if bmi <= WHO_THRESHOLDS["normal_upper"]:
        return "Normal"
    if bmi <= WHO_THRESHOLDS["overweight_upper"]:
        return "Overweight"
    return "Obese"


def classify_pnp_bmi(bmi: float, age: int) -> str:
    age_row = get_pnp_age_row(age)
    acceptable_min = age_row["acceptable_min"]
    acceptable_max = age_row["acceptable_max"]

    if bmi < 16.0:
        return 'Severely Underweight'
    if bmi < 18.5:
        return 'Underweight'
    if 18.5 <= bmi <= 24.9:
        return 'Normal'
    if acceptable_min <= bmi <= acceptable_max:
        return 'Acceptable BMI'
    if bmi < 30:
        return 'Overweight'
    if bmi < 35:
        return 'Obese Class 1'
    if bmi < 40:
        return 'Obese Class 2'
    return 'Obese Class 3'


def compute_weight_metrics(height_cm: float, weight_kg: float, age: int) -> Dict[str, float]:
    h_m = height_cm / 100.0 if height_cm else 0
    h_sq = h_m * h_m
    age_row = get_pnp_age_row(age)

    normal_min_weight = round(18.5 * h_sq, 2) if h_sq else 0.0
    normal_max_weight = round(24.9 * h_sq, 2) if h_sq else 0.0
    acceptable_min_weight = round(age_row["acceptable_min"] * h_sq, 2) if h_sq else 0.0
    acceptable_max_weight = round(age_row["acceptable_max"] * h_sq, 2) if h_sq else 0.0

    target_weight = acceptable_max_weight if acceptable_max_weight else normal_max_weight
    weight_to_lose = round(weight_kg - target_weight, 2) if target_weight else 0.0
    if weight_to_lose < 0:
        weight_to_lose = 0.0

    return {
        "height_m": h_m,
        "normal_min_weight": normal_min_weight,
        "normal_max_weight": normal_max_weight,
        "acceptable_min_weight": acceptable_min_weight,
        "acceptable_max_weight": acceptable_max_weight,
        "target_weight": target_weight,
        "weight_to_lose": weight_to_lose,
        "age_group": age_row["group"],
        "acceptable_min_bmi": age_row["acceptable_min"],
        "acceptable_max_bmi": age_row["acceptable_max"],
    }


def parse_date_taken(date_taken: Optional[str]) -> Optional[datetime]:
    if not date_taken:
        return None
    try:
        return datetime.strptime(date_taken, "%Y-%m-%d")
    except ValueError:
        return None


def safe_filename(raw_name: str, fallback: str) -> str:
    candidate = (raw_name or "").strip()
    if not candidate:
        candidate = fallback
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in candidate)
    cleaned = cleaned.strip("_")
    return cleaned or fallback


def resolve_upload_path(stored_path: Optional[str]) -> Optional[str]:
    if not stored_path:
        return None
    normalized = str(stored_path).replace("\\", "/")
    candidate = Path(normalized)
    if candidate.exists():
        return str(candidate)
    idx = normalized.lower().find("uploads/")
    relative_from_uploads = normalized[idx + len("uploads/"):] if idx >= 0 else normalized.lstrip("/")
    return str(uploads_abs(*relative_from_uploads.split("/")))


def build_month_columns(reference_date: datetime) -> List[Tuple[int, int]]:
    months: List[Tuple[int, int]] = []

    for offset in range(-MONTHS_BEFORE, MIN_MONTHS_AFTER + 1):
        month = reference_date.month + offset
        year = reference_date.year
        while month <= 0:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        months.append((year, month))

    while len(months) < TOTAL_MONTH_COLUMNS:
        year, month = months[-1]
        month += 1
        if month > 12:
            month = 1
            year += 1
        months.append((year, month))

    return months[:TOTAL_MONTH_COLUMNS]


def load_monthly_weight_map(db: Session, rec: models.BMIRecord) -> Dict[Tuple[int, int], float]:
    weights = {(w.year, w.month): w.weight for w in rec.monthly_weights}

    try:
        rows = db.execute(
            text(
                """
                SELECT year, month, weight
                FROM monthly_weight_logs
                WHERE bmi_record_id = :record_id
                """
            ),
            {"record_id": rec.id},
        ).fetchall()
        for row in rows:
            weights[(int(row[0]), int(row[1]))] = float(row[2]) if row[2] is not None else None
    except Exception:
        # Keep compatibility with deployments that only have the legacy monthly_weights table.
        pass

    return weights


def draw_record_pdf_page(
    c: canvas.Canvas,
    rec: models.BMIRecord,
    db: Session,
    prepared_by: str = "",
    noted_by: str = "",
) -> None:
    width, height = landscape(letter)

    bmi_value = compute_bmi(rec.weight_kg or 0, rec.height_cm or 0)
    pnp_classification = classify_pnp_bmi(bmi_value, rec.age or 0)
    who_classification = classify_who_bmi(bmi_value)
    metrics = compute_weight_metrics(rec.height_cm or 0, rec.weight_kg or 0, rec.age or 0)
    intervention = INTERVENTION_PACKAGE_MAP.get(pnp_classification, {"package": "", "duration": "", "recommendation": ""})

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 30, "INDIVIDUAL BMI MONITORING FORM")

    left_x = 28
    top_y = height - 60
    image_w = 190
    image_h = 120
    image_gap = 14

    image_specs = [
        ("Right View", resolve_upload_path(rec.photo_right)),
        ("Front View", resolve_upload_path(rec.photo_front)),
        ("Left View", resolve_upload_path(rec.photo_left)),
    ]

    for idx, (label, image_path) in enumerate(image_specs):
        img_y = top_y - ((image_h + 26) * idx)
        c.setStrokeColor(colors.grey)
        c.rect(left_x, img_y - image_h, image_w, image_h, stroke=1, fill=0)
        if image_path and os.path.exists(image_path):
            try:
                c.drawImage(image_path, left_x + 2, img_y - image_h + 2, width=image_w - 4, height=image_h - 4, preserveAspectRatio=True, anchor="c")
            except Exception:
                pass
        c.setFont("Helvetica", 9)
        c.drawCentredString(left_x + (image_w / 2), img_y - image_h - 12, label)

    details_x = left_x + image_w + 28
    details_right = width - 24
    details_top = height - 60
    row_h = 20

    c.setFont("Helvetica-Bold", 10)
    c.drawString(details_x, details_top + 8, "PERSONNEL DETAILS")

    details = [
        ("Rank / Name", f"{rec.rank or ''} {rec.name or ''}".strip()),
        ("Unit", rec.unit or ""),
        ("Age", str(rec.age or "")),
        ("Height", f"{(rec.height_cm or 0):.2f} cm" if rec.height_cm is not None else ""),
        ("Weight", f"{(rec.weight_kg or 0):.2f} kg" if rec.weight_kg is not None else ""),
        ("Waist", f"{(rec.waist_cm or 0):.2f} cm" if rec.waist_cm is not None else ""),
        ("Hip", f"{(rec.hip_cm or 0):.2f} cm" if rec.hip_cm is not None else ""),
        ("Wrist", f"{(rec.wrist_cm or 0):.2f} cm" if rec.wrist_cm is not None else ""),
        ("Gender", rec.sex or ""),
        ("Date Taken", rec.date_taken.strftime("%Y-%m-%d") if rec.date_taken else ""),
        ("Age Group", metrics["age_group"]),
        ("BMI Result", f"{bmi_value:.2f}"),
        (
            "Normal Weight Range",
            f"{metrics['normal_min_weight']:.2f} kg - {metrics['normal_max_weight']:.2f} kg",
        ),
        (
            "Acceptable Weight Range",
            f"{metrics['acceptable_min_weight']:.2f} kg - {metrics['acceptable_max_weight']:.2f} kg",
        ),
        ("Weight to Lose", f"{metrics['weight_to_lose']:.2f} kg"),
    ]

    label_w = 170
    value_w = (details_right - details_x) - label_w
    current_y = details_top
    c.setFont("Helvetica", 9)
    for key, value in details:
        c.setStrokeColor(colors.lightgrey)
        c.rect(details_x, current_y - row_h, label_w, row_h, stroke=1, fill=0)
        c.rect(details_x + label_w, current_y - row_h, value_w, row_h, stroke=1, fill=0)
        c.drawString(details_x + 5, current_y - 14, key)
        c.drawString(details_x + label_w + 5, current_y - 14, str(value))
        current_y -= row_h

    section_y = current_y - 18
    c.setFont("Helvetica-Bold", 10)
    c.drawString(details_x, section_y, "BMI CLASSIFICATION")
    section_y -= 18
    c.setFont("Helvetica", 9)
    c.drawString(details_x, section_y, "PNP BMI Acceptable Standard:")
    c.drawString(details_x + 180, section_y, pnp_classification)
    section_y -= 14
    c.drawString(details_x, section_y, "WHO Standard:")
    c.drawString(details_x + 180, section_y, who_classification)

    section_y -= 22
    c.setFont("Helvetica-Bold", 10)
    c.drawString(details_x, section_y, "INTERVENTION")
    section_y -= 18
    c.setFont("Helvetica", 9)
    c.drawString(details_x, section_y, f"Intervention Package: {intervention['package']}")
    section_y -= 14
    c.drawString(details_x, section_y, f"Duration: {intervention['duration']}")
    section_y -= 14
    c.drawString(details_x, section_y, f"Recommendation: {intervention['recommendation']}")

    table_x = 28
    table_y = 140
    table_w = width - 56
    col_w = table_w / TOTAL_MONTH_COLUMNS

    months = build_month_columns(rec.date_taken or datetime.utcnow())
    monthly_weight_map = load_monthly_weight_map(db, rec)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(table_x, table_y + 52, "MONTHLY WEIGHT MONITORING")
    c.setFont("Helvetica-Bold", 8)

    for idx, (year, month) in enumerate(months):
        x = table_x + (idx * col_w)
        c.setStrokeColor(colors.black)
        c.rect(x, table_y + 30, col_w, 18, stroke=1, fill=0)
        c.rect(x, table_y + 12, col_w, 18, stroke=1, fill=0)
        c.rect(x, table_y - 6, col_w, 18, stroke=1, fill=0)
        c.drawCentredString(x + col_w / 2, table_y + 35, str(year))
        c.drawCentredString(x + col_w / 2, table_y + 17, calendar.month_abbr[month])
        weight_value = monthly_weight_map.get((year, month), "")
        c.setFont("Helvetica", 8)
        if weight_value in ("", None):
            display_weight = ""
        else:
            display_weight = f"{weight_value:.2f}"
        c.drawCentredString(x + col_w / 2, table_y - 1, display_weight)
        c.setFont("Helvetica-Bold", 8)

    c.setFont("Helvetica-Bold", 8)
    c.drawString(table_x - 22, table_y + 35, "Year")
    c.drawString(table_x - 26, table_y + 17, "Month")
    c.drawString(table_x - 28, table_y - 1, "Weight")

    signature_y = 72
    c.setFont("Helvetica", 9)
    c.drawString(34, signature_y, "Certified Correct:")
    c.line(124, signature_y, 320, signature_y)
    c.drawString(130, signature_y - 12, "Name / Signature")

    if prepared_by:
        c.drawString(360, signature_y, f"Prepared by: {prepared_by}")
    if noted_by:
        c.drawString(360, signature_y - 14, f"Noted by: {noted_by}")


@router.post('/', response_model=schemas.BMISchema)
async def create_bmi(
    rank: str = Form(...),
    name: str = Form(...),
    unit: str = Form(...),
    age: int = Form(...),
    sex: str = Form(...),
    height_cm: float = Form(...),
    weight_kg: float = Form(...),
    waist_cm: Optional[float] = Form(None),
    hip_cm: Optional[float] = Form(None),
    wrist_cm: Optional[float] = Form(None),
    date_taken: Optional[str] = Form(None),
    photo_front: UploadFile = File(...),
    photo_left: UploadFile = File(...),
    photo_right: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    ensure_upload_folders()

    # parse name to first and last for file naming (Last_First)
    parts = name.strip().split()
    first_name = parts[0] if parts else ''
    last_name = parts[-1] if len(parts) > 1 else ''
    unit_folder = unit.upper()
    folder_abs = uploads_abs('bmi', unit_folder, bmi_folder_name(first_name, last_name))
    folder_rel = uploads_rel('bmi', unit_folder, bmi_folder_name(first_name, last_name))
    os.makedirs(folder_abs, exist_ok=True)
    base_name = f"{last_name}_{first_name}" if last_name else first_name
    front_name = f"BMI_{base_name}_front.jpg"
    left_name = f"BMI_{base_name}_left.jpg"
    right_name = f"BMI_{base_name}_right.jpg"
    front_path_abs = os.path.join(str(folder_abs), front_name)
    left_path_abs = os.path.join(str(folder_abs), left_name)
    right_path_abs = os.path.join(str(folder_abs), right_name)

    bmi_value = compute_bmi(weight_kg, height_cm)
    pnp_classification = classify_pnp_bmi(bmi_value, age)
    parsed_date_taken = parse_date_taken(date_taken)

    record = models.BMIRecord(
        rank=rank, name=name, unit=unit, age=age, sex=sex,
        height_cm=height_cm, weight_kg=weight_kg, waist_cm=waist_cm,
        hip_cm=hip_cm, wrist_cm=wrist_cm, bmi=bmi_value, classification=pnp_classification,
        result=f"{bmi_value:.2f}",
        date_taken=parsed_date_taken or datetime.utcnow(),
        photo_front=f"{folder_rel}/{front_name}".replace("\\","/"),
        photo_left=f"{folder_rel}/{left_name}".replace("\\","/"),
        photo_right=f"{folder_rel}/{right_name}".replace("\\","/"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # save photos after record exists
    with open(front_path_abs,'wb') as f:
        f.write(await photo_front.read())
    with open(left_path_abs,'wb') as f:
        f.write(await photo_left.read())
    with open(right_path_abs,'wb') as f:
        f.write(await photo_right.read())

    return record


@router.post('/report')
def bmi_report(
    month: Optional[int] = Form(None),
    year: Optional[int] = Form(None),
    unit: Optional[str] = Form(None),
    prepared_by: str = Form(''),
    noted_by: str = Form(''),
    report_type: str = Form('pdf'),
    file_name: str = Form('bmi_report'),
    db: Session = Depends(get_db),
):
    # fetch records matching filters
    q = db.query(models.BMIRecord)
    if unit and unit != 'All Units':
        q = q.filter(models.BMIRecord.unit == unit)
    if month and year:
        # filter by date_taken month/year
        from sqlalchemy import extract
        q = q.filter(extract('month', models.BMIRecord.date_taken) == month, extract('year', models.BMIRecord.date_taken) == year)
    records = q.order_by(models.BMIRecord.date_taken.desc()).all()
    safe_base_name = safe_filename(file_name, 'bmi_report')

    if report_type.lower() == 'excel':
        # reuse existing excel generator logic
        ids = [r.id for r in records]
        return generate_excel(records=ids, prepared_by=prepared_by, noted_by=noted_by, file_name=safe_base_name, db=db)

    # For PDF: create combined multi-page PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    for rec in records:
        draw_record_pdf_page(c, rec, db=db, prepared_by=prepared_by, noted_by=noted_by)
        c.showPage()

    c.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type='application/pdf',
        headers={"Content-Disposition": f"attachment;filename={safe_base_name}.pdf"},
    )


@router.get('/', response_model=List[schemas.BMISchema])
def list_bmi(db: Session = Depends(get_db)):
    return db.query(models.BMIRecord).order_by(models.BMIRecord.date_taken.desc()).all()


@router.get('/{record_id}/pdf')
def generate_bmi_pdf(record_id: int, file_name: Optional[str] = None, db: Session = Depends(get_db)):
    rec = db.query(models.BMIRecord).filter(models.BMIRecord.id==record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail='BMI record not found')

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    draw_record_pdf_page(c, rec, db=db)
    c.showPage()
    c.save()
    buffer.seek(0)
    output_name = safe_filename(file_name or f"bmi_{record_id}", f"bmi_{record_id}")
    return StreamingResponse(
        buffer,
        media_type='application/pdf',
        headers={"Content-Disposition": f"attachment;filename={output_name}.pdf"},
    )


@router.post('/excel')
def generate_excel(
    records: List[int] = Form(...),
    prepared_by: str = Form(''),
    noted_by: str = Form(''),
    file_name: str = Form('bmi_report'),
    db: Session = Depends(get_db),
):
    wb = Workbook()
    ws = wb.active
    ws.title = 'BMI Report'
    headers = [
        'Rank',
        'Surname',
        'First Name',
        'Middle Name',
        'QLR',
        'Age',
        'Height in CM',
        'Weight for the month',
        'Waist Size in CM',
        'Hip Size in CM',
        'Wrist Size in CM',
        'BMI Result',
        'PNP BMI Classification',
        'WHO BMI Classification',
        'Weight to Lose',
    ]
    ws.append(headers)
    for rid in records:
        rec = db.query(models.BMIRecord).filter(models.BMIRecord.id==rid).first()
        if not rec:
            continue
        # split name
        parts = rec.name.split()
        surname = parts[-1] if len(parts)>1 else ''
        first = parts[0]
        middle = ' '.join(parts[1:-1]) if len(parts)>2 else ''
        bmi_value = compute_bmi(rec.weight_kg or 0, rec.height_cm or 0)
        pnp_classification = classify_pnp_bmi(bmi_value, rec.age or 0)
        who_classification = classify_who_bmi(bmi_value)
        metrics = compute_weight_metrics(rec.height_cm or 0, rec.weight_kg or 0, rec.age or 0)
        row = [
            rec.rank,
            surname,
            first,
            middle,
            '',
            rec.age,
            rec.height_cm,
            rec.weight_kg,
            rec.waist_cm,
            rec.hip_cm,
            rec.wrist_cm,
            bmi_value,
            pnp_classification,
            who_classification,
            metrics['weight_to_lose'],
        ]
        ws.append(row)
    ws.append([])
    ws.append(['Prepared by:', prepared_by])
    ws.append(['Noted by:', noted_by])
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    safe_base_name = safe_filename(file_name, 'bmi_report')
    return StreamingResponse(
        stream,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment;filename={safe_base_name}.xlsx"},
    )
