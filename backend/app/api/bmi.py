from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import SessionLocal
from ..utils import ensure_upload_folders, bmi_folder_name, uploads_abs, uploads_rel
import os
from datetime import datetime
import calendar
import math
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

router = APIRouter()

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
    return round(weight_kg / (h * h), 1)

def classify_bmi(bmi: float) -> str:
    # Basic WHO classification as fallback
    if bmi < 16:
        return 'Severely Underweight'
    if bmi < 18.5:
        return 'Underweight'
    if bmi < 25:
        return 'Normal'
    if bmi < 30:
        return 'Overweight'
    if bmi < 35:
        return 'Obese Class 1'
    if bmi < 40:
        return 'Obese Class 2'
    return 'Obese Class 3'


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
    first_name = name.split()[0]
    last_name = '_'.join(name.split()[1:]) if len(name.split())>1 else ''
    folder_abs = uploads_abs('bmi', bmi_folder_name(first_name, last_name))
    folder_rel = uploads_rel('bmi', bmi_folder_name(first_name, last_name))
    os.makedirs(folder_abs, exist_ok=True)
    base_name = f"{first_name}_{last_name}" if last_name else first_name
    front_name = f"BMI_{base_name}_front.jpg"
    left_name = f"BMI_{base_name}_left.jpg"
    right_name = f"BMI_{base_name}_right.jpg"
    front_path_abs = os.path.join(str(folder_abs), front_name)
    left_path_abs = os.path.join(str(folder_abs), left_name)
    right_path_abs = os.path.join(str(folder_abs), right_name)

    bmi_value = compute_bmi(weight_kg, height_cm)
    classification = classify_bmi(bmi_value)
    result = f"{bmi_value}"

    record = models.BMIRecord(
        rank=rank, name=name, unit=unit, age=age, sex=sex,
        height_cm=height_cm, weight_kg=weight_kg, waist_cm=waist_cm,
        hip_cm=hip_cm, wrist_cm=wrist_cm, bmi=bmi_value, classification=classification,
        result=result,
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


@router.get('/', response_model=List[schemas.BMISchema])
def list_bmi(db: Session = Depends(get_db)):
    return db.query(models.BMIRecord).order_by(models.BMIRecord.date_taken.desc()).all()


@router.get('/{record_id}/pdf')
def generate_bmi_pdf(record_id: int, db: Session = Depends(get_db)):
    rec = db.query(models.BMIRecord).filter(models.BMIRecord.id==record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail='BMI record not found')

    buffer = BytesIO()
    # Use ReportLab canvas and explicit layout to match sample
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    # Title
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(width/2, height-40, 'INDIVIDUAL BMI MONITORING FORM')

    # Photos area (left)
    photos_x = 40
    photos_y_top = height - 120
    photo_w = 150
    photo_h = 110
    gap = 12
    # place three photos side-by-side
    try:
        # Right view (leftmost)
        if rec.photo_right and os.path.exists(rec.photo_right):
            c.drawImage(rec.photo_right, photos_x, photos_y_top - photo_h, width=photo_w, height=photo_h, preserveAspectRatio=True, anchor='nw')
        # Front view (middle)
        if rec.photo_front and os.path.exists(rec.photo_front):
            c.drawImage(rec.photo_front, photos_x + (photo_w + gap), photos_y_top - photo_h, width=photo_w, height=photo_h, preserveAspectRatio=True, anchor='nw')
        # Left view (rightmost)
        if rec.photo_left and os.path.exists(rec.photo_left):
            c.drawImage(rec.photo_left, photos_x + 2*(photo_w + gap), photos_y_top - photo_h, width=photo_w, height=photo_h, preserveAspectRatio=True, anchor='nw')
    except Exception:
        pass

    # Labels under photos
    c.setFont('Helvetica', 9)
    label_y = photos_y_top - photo_h - 14
    c.drawCentredString(photos_x + photo_w/2, label_y, 'Right View')
    c.drawCentredString(photos_x + (photo_w+gap) + photo_w/2, label_y, 'Front View')
    c.drawCentredString(photos_x + 2*(photo_w+gap) + photo_w/2, label_y, 'Left View')

    # Right side details table
    details_x = photos_x + 3*(photo_w + gap) + 20
    detail_y = height - 100
    c.setFont('Helvetica-Bold', 10)
    c.drawString(details_x, detail_y, 'Details')
    c.setFont('Helvetica', 10)
    detail_y -= 18
    info_pairs = [
        ('Rank / Name', f"{rec.rank} {rec.name}"),
        ('Unit', rec.unit),
        ('Age', str(rec.age)),
        ('Height', f"{rec.height_cm} cm"),
        ('Weight', f"{rec.weight_kg} kg"),
        ('Waist', f"{rec.waist_cm or ''}"),
        ('Hip', f"{rec.hip_cm or ''}"),
        ('Wrist', f"{rec.wrist_cm or ''}"),
        ('Gender', rec.sex),
        ('Date Taken', rec.date_taken.strftime('%Y-%m-%d') if rec.date_taken else ''),
    ]
    for label, val in info_pairs:
        c.drawString(details_x, detail_y, f"{label}:")
        c.drawString(details_x + 110, detail_y, str(val))
        detail_y -= 14

    # BMI Result box
    box_y = detail_y - 6
    c.setFont('Helvetica-Bold', 12)
    c.drawString(details_x, box_y, 'BMI Result:')
    c.setFont('Helvetica-Bold', 14)
    c.drawString(details_x + 90, box_y - 2, f"{rec.bmi}")
    detail_y = box_y - 30

    # Normal Weight range and Weight to Lose placeholders
    c.setFont('Helvetica', 10)
    c.drawString(details_x, detail_y, 'Normal Weight Range:')
    c.drawString(details_x + 130, detail_y, '')
    detail_y -= 16
    c.drawString(details_x, detail_y, 'Weight to Lose:')
    c.drawString(details_x + 130, detail_y, '')
    detail_y -= 24

    # Classification Section
    c.setFont('Helvetica-Bold', 11)
    c.drawString(40, label_y - 40, 'BMI Classification')
    c.setFont('Helvetica', 10)
    c.drawString(40, label_y - 58, 'PNP BMI Acceptable Standard:')
    c.drawString(240, label_y - 58, rec.classification or '')
    c.drawString(40, label_y - 76, 'WHO Standard:')
    # Use the same classification as WHO fallback
    c.drawString(240, label_y - 76, rec.classification or '')

    # Intervention Package
    intervention = ''
    # map classification to package per spec
    mapping = {
        'Severely Underweight':'A','Underweight':'A','Normal':'B','Acceptable BMI':'B',
        'Overweight':'C','Obese Class 1':'D','Obese Class 2':'E','Obese Class 3':'F'
    }
    intervention = mapping.get(rec.classification, '')
    c.drawString(40, label_y - 100, f'Intervention Package: PACKAGE "{intervention}"')

    # Signature area
    sig_y = label_y - 140
    c.drawString(40, sig_y, 'Certified Correct:')
    c.line(150, sig_y, 370, sig_y)
    c.drawString(150, sig_y - 12, 'Name / Signature')

    # Monthly Weight Monitoring Table (8 months before, current, 2 ahead)
    # Determine reference month
    ref_date = rec.date_taken or datetime.utcnow()
    ref_year = ref_date.year
    ref_month = ref_date.month
    months = []
    for offset in range(-8, 3):
        m = ref_month + offset
        y = ref_year
        # adjust year and month
        while m <= 0:
            m += 12; y -= 1
        while m > 12:
            m -= 12; y += 1
        months.append((y, m))

    # fetch monthly weights dict
    mw = { (w.year, w.month): w.weight for w in rec.monthly_weights }

    # Draw the table header and rows
    table_top = sig_y - 60
    col_x = 40
    col_w = (width - 80) / len(months)
    c.setFont('Helvetica-Bold', 9)
    # Year row
    for i, (y, m) in enumerate(months):
        x = col_x + i*col_w
        c.drawCentredString(x + col_w/2, table_top, str(y))
    # Month row
    for i, (y, m) in enumerate(months):
        x = col_x + i*col_w
        c.setFont('Helvetica', 9)
        c.drawCentredString(x + col_w/2, table_top - 14, calendar.month_abbr[m])
    # Weight row
    for i, (y, m) in enumerate(months):
        x = col_x + i*col_w
        val = mw.get((y,m), '')
        c.drawCentredString(x + col_w/2, table_top - 28, str(val) if val!='' else '')

    c.showPage()
    c.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type='application/pdf', headers={"Content-Disposition":f"attachment;filename=bmi_{record_id}.pdf"})


@router.post('/excel')
def generate_excel(records: List[int] = Form(...), prepared_by: str = Form(''), noted_by: str = Form(''), db: Session = Depends(get_db)):
    wb = Workbook()
    ws = wb.active
    ws.title = 'BMI Report'
    headers = ['Rank','Surname','First Name','Middle Name','QLR','Age','Height in CM','Weight for the month','Waist Size in CM','Hip Size in CM','Wrist Size in CM','BMI Result','BMI Classification','Weight to Lose']
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
        row = [rec.rank, surname, first, middle, '', rec.age, rec.height_cm, rec.weight_kg, rec.waist_cm, rec.hip_cm, rec.wrist_cm, rec.bmi, rec.classification, '']
        ws.append(row)
    ws.append([])
    ws.append(['Prepared by:', prepared_by])
    ws.append(['Noted by:', noted_by])
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return StreamingResponse(stream, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={"Content-Disposition":"attachment;filename=bmi_report.xlsx"})
