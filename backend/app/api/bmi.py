from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text, extract
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

# Run migrations on module load
def run_migrations():
    """Add missing columns to existing tables for migration."""
    from sqlalchemy import create_engine, text
    from pathlib import Path
    import os
    
    # Get the database path
    base_dir = Path(__file__).resolve().parent.parent.parent  # api -> app -> backend
    db_path = base_dir / "cidg_dev.db"
    
    if not db_path.exists():
        return
    
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    
    with engine.connect() as conn:
        # Check if bmi_records table exists and add missing columns
        try:
            conn.execute(text("""
                ALTER TABLE bmi_records ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            conn.commit()
        except Exception:
            pass  # Column might already exist
        
        try:
            conn.execute(text("""
                ALTER TABLE bmi_records ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            conn.commit()
        except Exception:
            pass  # Column might already exist
        
        try:
            conn.execute(text("""
                ALTER TABLE bmi_records ADD COLUMN personnel_id INTEGER REFERENCES personnel(id)
            """))
            conn.commit()
        except Exception:
            pass  # Column might already exist
        
        # NEW: Add is_latest column for tracking latest BMI record per personnel
        try:
            conn.execute(text("""
                ALTER TABLE bmi_records ADD COLUMN is_latest BOOLEAN DEFAULT 1
            """))
            conn.commit()
        except Exception:
            pass  # Column might already exist
        
        # Ensure indexes exist for performance
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bmi_personnel_id ON bmi_records(personnel_id)
            """))
            conn.commit()
        except Exception:
            pass
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bmi_date_taken ON bmi_records(date_taken)
            """))
            conn.commit()
        except Exception:
            pass
        
        # NEW: Create index for is_latest flag
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bmi_is_latest ON bmi_records(is_latest)
            """))
            conn.commit()
        except Exception:
            pass
        
        # NEW: Initialize is_latest for existing records
        # For each unique name, mark only the latest record (by date_taken) as is_latest=True
        # and all others as is_latest=False
        try:
            # First, set all to False
            conn.execute(text("""
                UPDATE bmi_records SET is_latest = 0
            """))
            conn.commit()
            
            # Then, for each unique name, set the record with max date_taken to True
            # This subquery finds the max date per name
            conn.execute(text("""
                UPDATE bmi_records 
                SET is_latest = 1 
                WHERE id IN (
                    SELECT id FROM bmi_records b1
                    WHERE date_taken = (
                        SELECT MAX(date_taken) FROM bmi_records b2 
                        WHERE b2.name = b1.name
                    )
                )
            """))
            conn.commit()
        except Exception as e:
            print(f"Warning: Could not initialize is_latest: {e}")
            pass
        # NEW: Add status columns for BMI records
        try:
            conn.execute(text("""
                ALTER TABLE bmi_records ADD COLUMN status TEXT DEFAULT 'Active'
            """))
            conn.commit()
        except Exception:
            pass

        try:
            conn.execute(text("""
                ALTER TABLE bmi_records ADD COLUMN status_custom TEXT
            """))
            conn.commit()
        except Exception:
            pass
    
    engine.dispose()

try:
    run_migrations()
except Exception:
    pass  # Migration errors are handled gracefully

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


from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import Table, TableStyle, Paragraph, Image as RLImage, Spacer
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def draw_record_pdf_page(
    c: canvas.Canvas,
    rec: models.BMIRecord,
    db: Session,
    prepared_by: str = "",
    noted_by: str = "",
) -> None:
    """
    Rebuilt layout for Individual BMI Monitoring Form.
    Strict structured layout: header, photos (L), personnel details (R),
    classification + intervention, monthly monitoring table, signatures.
    """
    width, height = landscape(letter)
    M = 18
    content_x = M
    content_w = width - 2 * M

    # --- Title ---
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(width / 2, height - M - 6, "INDIVIDUAL BMI MONITORING FORM")

    # Compute core metrics
    bmi_value = compute_bmi(rec.weight_kg or 0, rec.height_cm or 0)
    pnp_classification = classify_pnp_bmi(bmi_value, rec.age or 0)
    who_classification = classify_who_bmi(bmi_value)
    metrics = compute_weight_metrics(rec.height_cm or 0, rec.weight_kg or 0, rec.age or 0)
    intervention = INTERVENTION_PACKAGE_MAP.get(pnp_classification, {"package": "", "duration": "", "recommendation": ""})

    # Starting Y below title
    y_top = height - M - 28

    # --- Upper section: Photos (left) and Personnel Details (right) ---
    photo_section_w = content_w * 0.48
    details_section_w = content_w - photo_section_w - 10
    photo_x = content_x
    details_x = content_x + photo_section_w + 10

    # Photos layout
    photo_h = 72
    photo_label_h = 10
    gap_between_photos = 6
    photo_w = (photo_section_w - (2 * gap_between_photos)) / 3
    photos_top = y_top
    photos_bottom = photos_top - photo_h - photo_label_h

    image_specs = [
        ("Right View", resolve_upload_path(rec.photo_right)),
        ("Front View", resolve_upload_path(rec.photo_front)),
        ("Left View", resolve_upload_path(rec.photo_left)),
    ]

    for i, (label, image_path) in enumerate(image_specs):
        ix = photo_x + i * (photo_w + gap_between_photos)
        iy = photos_bottom + photo_label_h
        # border
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.6)
        c.rect(ix, iy, photo_w, photo_h, stroke=1, fill=0)
        # image
        if image_path and os.path.exists(image_path):
            try:
                c.drawImage(image_path, ix + 1, iy + 1, width=photo_w - 2, height=photo_h - 2, preserveAspectRatio=True, anchor='c')
            except Exception:
                pass
        # label
        c.setFont("Helvetica", 7)
        c.drawCentredString(ix + photo_w / 2, iy - 8, label)

    # Personnel details table (right)
    details_fields = [
        ("RANK/NAME", f"{(rec.rank or '')} {(rec.name or '')}".strip()),
        ("UNIT", rec.unit or ""),
        ("AGE", f"{rec.age or ''}"),
        ("HEIGHT", f"{metrics.get('height_m', 0):.2f} m"),
        ("WEIGHT", f"{(rec.weight_kg or 0):.1f} kg"),
        ("WAIST", f"{(rec.waist_cm or 0):.1f} cm"),
        ("HIP", f"{(rec.hip_cm or 0):.1f} cm"),
        ("WRIST", f"{(rec.wrist_cm or 0):.1f} cm"),
        ("GENDER", rec.sex or ""),
        ("DATE TAKEN", rec.date_taken.strftime("%Y-%m-%d") if rec.date_taken else ""),
        ("BMI RESULT", f"{bmi_value:.2f}"),
        ("NORMAL WT RANGE", f"{metrics['normal_min_weight']:.1f} - {metrics['normal_max_weight']:.1f} kg"),
        ("WEIGHT TO LOSE", f"{metrics['weight_to_lose']:.1f} kg"),
    ]

    details_row_h = 13
    label_w = details_section_w * 0.45
    cur_y = y_top
    c.setFont("Helvetica-Bold", 9)
    c.drawString(details_x, cur_y, "PERSONNEL DETAILS")
    cur_y -= 14
    c.setFont("Helvetica", 8)
    for label, value in details_fields:
        # row rectangle
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.rect(details_x, cur_y - details_row_h, details_section_w, details_row_h, stroke=1, fill=0)
        # vertical separator
        c.line(details_x + label_w, cur_y - details_row_h, details_x + label_w, cur_y)
        # label (left), value (right-aligned)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(details_x + 4, cur_y - details_row_h + 3, label)
        c.setFont("Helvetica", 7)
        c.drawRightString(details_x + details_section_w - 6, cur_y - details_row_h + 3, value)
        cur_y -= details_row_h

    # Determine lower Y of upper section
    upper_bottom = min(photos_bottom, cur_y)

    # --- Middle section: Classification (left two columns) + Intervention (right) ---
    mid_gap = 10
    class_area_w = content_w * 0.62
    interv_area_w = content_w - class_area_w - mid_gap
    class_x = content_x
    class_y = upper_bottom - 12
    class_h = 60
    interv_x = class_x + class_area_w + mid_gap
    # classification box
    c.setStrokeColor(colors.black)
    c.rect(class_x, class_y - class_h, class_area_w, class_h, stroke=1, fill=0)
    # inside classification split into two columns: PNP (left) & WHO (right)
    sub_w = class_area_w / 2
    # headers
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(class_x + sub_w / 2, class_y - 10, "PNP BMI Acceptable Standard")
    c.drawCentredString(class_x + sub_w + sub_w / 2, class_y - 10, "WHO Standard")
    # classification values
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(class_x + sub_w / 2, class_y - 30, pnp_classification)
    c.drawCentredString(class_x + sub_w + sub_w / 2, class_y - 30, who_classification)

    # intervention box
    c.setStrokeColor(colors.black)
    c.rect(interv_x, class_y - class_h, interv_area_w, class_h, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(interv_x + interv_area_w / 2, class_y - 10, "INTERVENTION PACKAGE")
    c.setFont("Helvetica", 8)
    c.drawString(interv_x + 6, class_y - 28, f"Package: {intervention.get('package','')}")
    c.drawString(interv_x + 6, class_y - 40, f"Duration: {intervention.get('duration','')}")
    c.drawString(interv_x + 6, class_y - 52, f"Recommendation: {intervention.get('recommendation','')}")

    # --- Monthly weight monitoring table ---
    table_top = class_y - class_h - 14
    table_x = content_x
    table_w = content_w
    col_w = table_w / TOTAL_MONTH_COLUMNS
    year_row_h = 16
    month_row_h = 14
    weight_row_h = 14
    table_h = year_row_h + month_row_h + weight_row_h

    months = build_month_columns(rec.date_taken or datetime.utcnow())
    monthly_weight_map = load_monthly_weight_map(db, rec)

    # Draw YEAR row with grouped year spans
    # Group consecutive months by year
    groups = []
    if months:
        curr_year = months[0][0]
        start_idx = 0
        for idx, (yr, mo) in enumerate(months):
            if yr != curr_year:
                groups.append((curr_year, start_idx, idx - start_idx))
                curr_year = yr
                start_idx = idx
        groups.append((curr_year, start_idx, len(months) - start_idx))

    # Year row
    y_year = table_top
    c.setFont("Helvetica-Bold", 8)
    for year_val, start_col, span in groups:
        gx = table_x + start_col * col_w
        gw = span * col_w
        c.rect(gx, y_year - year_row_h, gw, year_row_h, stroke=1, fill=0)
        c.drawCentredString(gx + gw / 2, y_year - year_row_h + 4, str(year_val))

    # Month row
    y_month = y_year - year_row_h
    c.setFont("Helvetica", 8)
    for idx, (yr, mo) in enumerate(months):
        mx = table_x + idx * col_w
        c.rect(mx, y_month - month_row_h, col_w, month_row_h, stroke=1, fill=0)
        c.drawCentredString(mx + col_w / 2, y_month - month_row_h + 4, calendar.month_abbr[mo])

    # Weight row
    y_weight = y_month - month_row_h
    c.setFont("Helvetica", 8)
    for idx, (yr, mo) in enumerate(months):
        wx = table_x + idx * col_w
        c.rect(wx, y_weight - weight_row_h, col_w, weight_row_h, stroke=1, fill=0)
        wval = monthly_weight_map.get((yr, mo), None)
        display = f"{wval:.1f}" if (wval is not None and wval != "") else "-"
        c.drawCentredString(wx + col_w / 2, y_weight - weight_row_h + 4, display)

    # Label for table
    c.setFont("Helvetica-Bold", 9)
    c.drawString(table_x, y_year + 6, "MONTHLY WEIGHT MONITORING")

    # --- Signatures ---
    sig_y = M + 20
    sig_block_w = (content_w - 24) / 3
    left_x = content_x
    center_x = content_x + sig_block_w + 12
    right_x = content_x + (sig_block_w + 12) * 2
    line_w = 140

    # Certified Correct (left)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(left_x, sig_y + 30, "Certified Correct")
    c.line(left_x, sig_y + 12, left_x + line_w, sig_y + 12)
    c.setFont("Helvetica", 7)
    c.drawCentredString(left_x + line_w / 2, sig_y, "Signature over Printed Name")

    # Prepared by (center)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(center_x, sig_y + 30, "Prepared by")
    c.line(center_x, sig_y + 12, center_x + line_w, sig_y + 12)
    c.setFont("Helvetica", 7)
    if prepared_by:
        c.drawCentredString(center_x + line_w / 2, sig_y - 2, prepared_by)
    else:
        c.drawCentredString(center_x + line_w / 2, sig_y - 2, "")

    # Noted by (right)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(right_x, sig_y + 30, "Noted by")
    c.line(right_x, sig_y + 12, right_x + line_w, sig_y + 12)
    c.setFont("Helvetica", 7)
    if noted_by:
        c.drawCentredString(right_x + line_w / 2, sig_y - 2, noted_by)
    else:
        c.drawCentredString(right_x + line_w / 2, sig_y - 2, "")


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
    status: str = Form('Active'),
    status_custom: Optional[str] = Form(None),
    photo_front: UploadFile = File(...),
    photo_left: UploadFile = File(...),
    photo_right: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    ensure_upload_folders()
    # Normalize textual inputs to uppercase
    rank = rank.upper() if isinstance(rank, str) else rank
    name = name.upper() if isinstance(name, str) else name
    unit = unit.upper() if isinstance(unit, str) else unit
    sex = sex.upper() if isinstance(sex, str) else sex

    # parse name to first and last for file naming (First_Last)
    parts = name.strip().split() if name else []
    first_name = parts[0] if parts else ''
    last_name = parts[-1] if len(parts) > 1 else ''
    unit_folder = unit.upper()
    folder_abs = uploads_abs('bmi', unit_folder, bmi_folder_name(first_name, last_name))
    folder_rel = uploads_rel('bmi', unit_folder, bmi_folder_name(first_name, last_name))
    os.makedirs(folder_abs, exist_ok=True)
    base_name = f"{first_name}_{last_name}" if last_name else first_name
    front_name = f"BMI_{base_name}_front.jpg"
    left_name = f"BMI_{base_name}_left.jpg"
    right_name = f"BMI_{base_name}_right.jpg"
    front_path_abs = os.path.join(str(folder_abs), front_name)
    left_path_abs = os.path.join(str(folder_abs), left_name)
    right_path_abs = os.path.join(str(folder_abs), right_name)

    bmi_value = compute_bmi(weight_kg, height_cm)
    pnp_classification = classify_pnp_bmi(bmi_value, age)
    parsed_date_taken = parse_date_taken(date_taken)
    
    # Determine the effective date (today if not provided)
    effective_date = parsed_date_taken or datetime.utcnow()

    # VALIDATION: Do not allow duplicate BMI entries for the same person for the same month
    existing_same_month = db.query(models.BMIRecord).filter(
        models.BMIRecord.name.ilike(name),
        extract('month', models.BMIRecord.date_taken) == effective_date.month,
        extract('year', models.BMIRecord.date_taken) == effective_date.year
    ).first()
    if existing_same_month:
        raise HTTPException(status_code=400, detail="A BMI record already exists for this person for the selected month. You can edit the existing record instead.")

    # NEW: Find and mark existing latest records for this personnel as NOT latest
    # First try to find by name (case-insensitive match)
    existing_latest = db.query(models.BMIRecord).filter(
        models.BMIRecord.name.ilike(name)
    ).order_by(models.BMIRecord.date_taken.desc()).first()
    
    if existing_latest:
        existing_latest.is_latest = False
        db.commit()

    record = models.BMIRecord(
        rank=rank, name=name, unit=unit, age=age, sex=sex,
        height_cm=height_cm, weight_kg=weight_kg, waist_cm=waist_cm,
        hip_cm=hip_cm, wrist_cm=wrist_cm, bmi=bmi_value, classification=pnp_classification,
        result=f"{bmi_value:.2f}",
        date_taken=parsed_date_taken or datetime.utcnow(),
        photo_front=f"{folder_rel}/{front_name}".replace("\\","/"),
        photo_left=f"{folder_rel}/{left_name}".replace("\\","/"),
        photo_right=f"{folder_rel}/{right_name}".replace("\\","/"),
        status=status,
        status_custom=status_custom,
        is_latest=True,  # NEW: Mark as latest
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
    status: Optional[str] = Form(None),
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

    # Filter BMI records based on status parameters
    filtered_records = []
    for rec in records:
        # Apply BMI-record status filtering
        rec_status = (getattr(rec, 'status', None) or '').strip()
        if status:
            # If caller requested a specific BMI record status, enforce it
            if rec_status.upper() == status.upper():
                filtered_records.append(rec)
            else:
                # treat missing rec_status as 'Active' for comparison
                if not rec_status and status.upper() == 'ACTIVE':
                    filtered_records.append(rec)
        else:
            # Default behavior: include only records that are Active (or have no status set)
            if not rec_status or rec_status.upper() == 'ACTIVE':
                filtered_records.append(rec)

    records = filtered_records
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


# ==================== BMI LIST AND HISTORY ENDPOINTS ====================

@router.get('/', response_model=List[schemas.BMISchema])
def list_bmi(
    personnel_id: Optional[int] = None,
    unit: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    exact_date: Optional[str] = None,
    search: Optional[str] = None,
    latest_only: bool = False,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List BMI records with optional filtering.
    
    Query params:
    - personnel_id: Filter by personnel ID
    - unit: Filter by unit (RHQ, Cavite, etc.)
    - month: Filter by month (1-12)
    - year: Filter by year
    - exact_date: Filter by exact date (YYYY-MM-DD)
    - search: Search by name or rank
    - latest_only: If true, return only records where is_latest=True (one per personnel)
    """
    from sqlalchemy import extract, func, or_
    
    q = db.query(models.BMIRecord)
    
    # Apply filters
    if personnel_id:
        q = q.filter(models.BMIRecord.personnel_id == personnel_id)
    
    if unit and unit != 'All Units':
        q = q.filter(models.BMIRecord.unit == unit)
    
    if month and year:
        q = q.filter(
            extract('month', models.BMIRecord.date_taken) == month,
            extract('year', models.BMIRecord.date_taken) == year
        )
    
    if exact_date:
        parsed_date = parse_date_taken(exact_date)
        if parsed_date:
            q = q.filter(
                extract('year', models.BMIRecord.date_taken) == parsed_date.year,
                extract('month', models.BMIRecord.date_taken) == parsed_date.month,
                extract('day', models.BMIRecord.date_taken) == parsed_date.day
            )
    
    if search:
        search_term = f"%{search}%"
        q = q.filter(
            or_(
                models.BMIRecord.name.ilike(search_term),
                models.BMIRecord.rank.ilike(search_term)
            )
        )
    
    if latest_only:
        # NEW: Use is_latest flag for filtering - reliable one-per-personnel approach
        q = q.filter(models.BMIRecord.is_latest == True)

    # Apply status filtering: if provided, use it; otherwise default to Active or unspecified
    if status:
        q = q.filter(func.upper(models.BMIRecord.status) == status.upper())
    else:
        from sqlalchemy import or_
        q = q.filter(or_(models.BMIRecord.status == None, func.upper(models.BMIRecord.status) == 'ACTIVE'))
    
    return q.order_by(models.BMIRecord.date_taken.desc()).all()


@router.get('/history/{identifier}', response_model=schemas.BMIHistorySchema)
def get_bmi_history(
    identifier: str,
    db: Session = Depends(get_db)
):
    """
    Get all BMI history records for a specific personnel.
    
    The identifier can be:
    - A BMI record ID (numeric): Finds that record and returns all records with the same name
    - A personnel ID from Personnel table (numeric)
    - A name string: Finds all BMI records matching that name
    
    Returns the personnel info, latest record, and full history sorted newest first.
    """
    records = []
    personnel = None
    personnel_name = None
    personnel_rank = None
    personnel_unit = None
    
    # Check if it's a numeric ID or a name
    is_numeric = identifier.isdigit()
    
    if is_numeric:
        record_id = int(identifier)
        
        # First, try to find by BMI record ID and get its name
        bmi_record = db.query(models.BMIRecord).filter(models.BMIRecord.id == record_id).first()
        
        if bmi_record:
            # Get the personnel name from this BMI record
            personnel_name = bmi_record.name
            personnel_rank = bmi_record.rank
            personnel_unit = bmi_record.unit
            
            # Find all BMI records with the same name (case-insensitive)
            records = db.query(models.BMIRecord).filter(
                models.BMIRecord.name.ilike(bmi_record.name)
            ).order_by(models.BMIRecord.date_taken.desc()).all()
            
            # Also try to find Personnel by this name
            personnel = db.query(models.Personnel).filter(
                (models.Personnel.first_name + ' ' + models.Personnel.last_name).ilike(f"%{personnel_name}%") |
                (models.Personnel.last_name + ' ' + models.Personnel.first_name).ilike(f"%{personnel_name}%")
            ).first()
        else:
            # ID not found as BMI record, try it as a Personnel ID
            personnel = db.query(models.Personnel).filter(models.Personnel.id == record_id).first()
            if personnel:
                personnel_name = f"{personnel.first_name} {personnel.last_name}"
                personnel_rank = personnel.rank
                personnel_unit = personnel.unit
                # Get all BMI records for this personnel by personnel_id
                records = db.query(models.BMIRecord).filter(
                    models.BMIRecord.personnel_id == personnel.id
                ).order_by(models.BMIRecord.date_taken.desc()).all()
                
                # If no records by personnel_id, try by name
                if not records:
                    records = db.query(models.BMIRecord).filter(
                        models.BMIRecord.name.ilike(f"%{personnel_name}%")
                    ).order_by(models.BMIRecord.date_taken.desc()).all()
    else:
        # It's a name - find all matching BMI records
        personnel_name = identifier
        records = db.query(models.BMIRecord).filter(
            models.BMIRecord.name.ilike(f"%{identifier}%")
        ).order_by(models.BMIRecord.date_taken.desc()).all()
        
        if records:
            # Get info from the first (latest) record
            latest = records[0]
            personnel_rank = latest.rank
            personnel_unit = latest.unit
            
            # Try to find Personnel by name
            personnel = db.query(models.Personnel).filter(
                (models.Personnel.first_name + ' ' + models.Personnel.last_name).ilike(f"%{latest.name}%") |
                (models.Personnel.last_name + ' ' + models.Personnel.first_name).ilike(f"%{latest.name}%")
            ).first()
    
    # Get latest record
    latest = records[0] if records else None
    
    return {
        "personnel_id": personnel.id if personnel else (latest.personnel_id if latest else None),
        "personnel_name": personnel_name if personnel_name else (latest.name if latest else None),
        "personnel_rank": personnel_rank if personnel_rank else (latest.rank if latest else None),
        "personnel_unit": personnel_unit if personnel_unit else (latest.unit if latest else None),
        "latest_bmi": latest,
        "history": records
    }


@router.get('/history/by-name/{name}', response_model=schemas.BMIHistorySchema)
def get_bmi_history_by_name(
    name: str,
    db: Session = Depends(get_db)
):
    """
    Get BMI history by personnel name (for cases where personnel_id is not set).
    """
    # Get all BMI records matching this name
    records = db.query(models.BMIRecord).filter(
        models.BMIRecord.name.ilike(f"%{name}%")
    ).order_by(models.BMIRecord.date_taken.desc()).all()
    
    latest = records[0] if records else None
    
    return {
        "personnel_id": latest.personnel_id if latest else None,
        "personnel_name": name,
        "personnel_rank": latest.rank if latest else None,
        "personnel_unit": latest.unit if latest else None,
        "latest_bmi": latest,
        "history": records
    }


@router.get('/history/{personnel_id}/by-date', response_model=schemas.BMISchema)
def get_bmi_by_date(
    personnel_id: int,
    date: str,  # YYYY-MM-DD format
    db: Session = Depends(get_db)
):
    """
    Get the BMI record for a specific personnel on a specific date.
    If multiple records exist on that day, returns the most recent one.
    """
    from sqlalchemy import extract
    
    parsed_date = parse_date_taken(date)
    if not parsed_date:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get the personnel info
    personnel = db.query(models.Personnel).filter(models.Personnel.id == personnel_id).first()
    
    # Try to find records for this personnel on the specific date
    records = db.query(models.BMIRecord).filter(
        models.BMIRecord.personnel_id == personnel_id,
        extract('year', models.BMIRecord.date_taken) == parsed_date.year,
        extract('month', models.BMIRecord.date_taken) == parsed_date.month,
            extract('day', models.BMIRecord.date_taken) == parsed_date.day
        ).order_by(models.BMIRecord.date_taken.desc()).all()
    
    # If no records linked by personnel_id, try by name matching
    if not records and personnel:
        name_pattern = f"%{personnel.first_name}%{personnel.last_name}%"
        records = db.query(models.BMIRecord).filter(
            models.BMIRecord.name.ilike(name_pattern),
            extract('year', models.BMIRecord.date_taken) == parsed_date.year,
            extract('month', models.BMIRecord.date_taken) == parsed_date.month,
            extract('day', models.BMIRecord.date_taken) == parsed_date.day
        ).order_by(models.BMIRecord.date_taken.desc()).all()
    
    if not records:
        raise HTTPException(
            status_code=404,
            detail=f"No BMI record found for the selected date {date}"
        )
    
    # Return the most recent one
    return records[0]


@router.get('/latest/{personnel_id}', response_model=schemas.BMISchema)
def get_latest_bmi(
    personnel_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the latest BMI record for a specific personnel.
    """
    # Get the personnel info
    personnel = db.query(models.Personnel).filter(models.Personnel.id == personnel_id).first()
    
    # Try to find the latest record for this personnel
    record = db.query(models.BMIRecord).filter(
        models.BMIRecord.personnel_id == personnel_id
    ).order_by(models.BMIRecord.date_taken.desc()).first()
    
    # If no records linked by personnel_id, try by name matching
    if not record and personnel:
        name_pattern = f"%{personnel.first_name}%{personnel.last_name}%"
        record = db.query(models.BMIRecord).filter(
            models.BMIRecord.name.ilike(name_pattern)
        ).order_by(models.BMIRecord.date_taken.desc()).first()
    
    if not record:
        raise HTTPException(
            status_code=404,
            detail="No BMI records found for this personnel"
        )
    
    return record


@router.get('/timeline/{personnel_id}', response_model=List[schemas.BMITimelineSchema])
def get_bmi_timeline(
    personnel_id: int,
    db: Session = Depends(get_db)
):
    """
    Get simplified timeline data for BMI charts/cards.
    Returns date, BMI value, classification, and weight for each record.
    """
    # Get the personnel info
    personnel = db.query(models.Personnel).filter(models.Personnel.id == personnel_id).first()
    
    # Get all BMI records for timeline
    records = db.query(models.BMIRecord).filter(
        models.BMIRecord.personnel_id == personnel_id
    ).order_by(models.BMIRecord.date_taken.asc()).all()
    
    # If no records linked by personnel_id, try by name matching
    if not records and personnel:
        name_pattern = f"%{personnel.first_name}%{personnel.last_name}%"
        records = db.query(models.BMIRecord).filter(
            models.BMIRecord.name.ilike(name_pattern)
        ).order_by(models.BMIRecord.date_taken.asc()).all()
    
    timeline = []
    for rec in records:
        timeline.append({
            "date_taken": rec.date_taken,
            "bmi": rec.bmi,
            "classification": rec.classification,
            "weight_kg": rec.weight_kg
        })
    
    return timeline


@router.get('/personnel-list')
def get_personnel_with_bmi(db: Session = Depends(get_db)):
    """
    Get list of all personnel with their latest BMI status.
    Useful for dropdown selection in the BMI history view.
    """
    from sqlalchemy import func
    
    # Get all personnel
    all_personnel = db.query(models.Personnel).all()
    
    result = []
    for p in all_personnel:
        # Get latest BMI for this personnel
        latest_bmi = db.query(models.BMIRecord).filter(
            models.BMIRecord.personnel_id == p.id
        ).order_by(models.BMIRecord.date_taken.desc()).first()
        
        # Also check by name matching
        if not latest_bmi:
            name_pattern = f"%{p.first_name}%{p.last_name}%"
            latest_bmi = db.query(models.BMIRecord).filter(
                models.BMIRecord.name.ilike(name_pattern)
            ).order_by(models.BMIRecord.date_taken.desc()).first()
        
        # Count total BMI records for this personnel
        total_records = db.query(models.BMIRecord).filter(
            models.BMIRecord.personnel_id == p.id
        ).count()
        
        if not total_records:
            name_pattern = f"%{p.first_name}%{p.last_name}%"
            total_records = db.query(models.BMIRecord).filter(
                models.BMIRecord.name.ilike(name_pattern)
            ).count()
        
        result.append({
            "id": p.id,
            "name": f"{p.first_name} {p.last_name}",
            "rank": p.rank,
            "unit": p.unit,
            "status": p.status,
            "latest_bmi": latest_bmi.bmi if latest_bmi else None,
            "latest_classification": latest_bmi.classification if latest_bmi else None,
            "latest_date": latest_bmi.date_taken if latest_bmi else None,
            "total_records": total_records
        })
    
    return result


@router.get('/distinct-personnel')
def get_distinct_personnel_bmi(db: Session = Depends(get_db)):
    """
    Get list of all distinct personnel who have BMI records.
    Returns records where is_latest=True (one per personnel).
    """
    from sqlalchemy import func
    
    # NEW: Use is_latest flag - reliable approach
    # Get all records marked as latest
    latest_records = db.query(models.BMIRecord).filter(
        models.BMIRecord.is_latest == True
    ).all()
    
    result = []
    for rec in latest_records:
        # Count total BMI records for this personnel (by name)
        total_records = db.query(models.BMIRecord).filter(
            models.BMIRecord.name.ilike(rec.name)
        ).count()
        
        result.append({
            "id": rec.id,
            "name": rec.name,
            "rank": rec.rank,
            "unit": rec.unit,
            "personnel_id": rec.personnel_id,
            "latest_bmi": rec.bmi,
            "latest_classification": rec.classification,
            "latest_date": rec.date_taken,
            "total_records": total_records,
            "is_latest": rec.is_latest
        })
    
    return sorted(result, key=lambda x: (x['name'] or '').lower())


@router.get('/counts')
def bmi_counts(db: Session = Depends(get_db)):
    """
    Get BMI record counts per unit for the current month and total counts.
    """
    from sqlalchemy import extract, func
    from datetime import datetime
    
    now = datetime.utcnow()
    current_month = now.month
    current_year = now.year
    
    unit_map = {
        'RHQ': 'RHQ',
        'Cavite': 'CAVITE',
        'Laguna': 'LAGUNA',
        'Batangas': 'BATANGAS',
        'Rizal': 'RIZAL',
        'Quezon': 'QUEZON',
    }
    result = {}
    
    for display_name, db_unit in unit_map.items():
        # Count records for this unit in current month
        monthly_count = db.query(models.BMIRecord).filter(
            func.upper(models.BMIRecord.unit) == db_unit,
            extract('month', models.BMIRecord.date_taken) == current_month,
            extract('year', models.BMIRecord.date_taken) == current_year
        ).count()
        
        # Count total records for this unit
        total_count = db.query(models.BMIRecord).filter(
            func.upper(models.BMIRecord.unit) == db_unit
        ).count()
        
        result[display_name] = {
            'monthly': monthly_count,
            'total': total_count
        }
    
    # Get total monthly count across all units
    total_monthly = db.query(models.BMIRecord).filter(
        extract('month', models.BMIRecord.date_taken) == current_month,
        extract('year', models.BMIRecord.date_taken) == current_year
    ).count()
    
    result['total_monthly'] = total_monthly
    result['total'] = sum(v.get('total', 0) for v in result.values() if isinstance(v, dict))
    result['current_month'] = now.strftime('%B %Y')
    
    return result


# ==================== BMI UPDATE ENDPOINT (Version-Preserving) ====================

@router.put('/{record_id}', response_model=schemas.BMISchema)
async def update_bmi(
    record_id: int,
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
    status: str = Form('Active'),
    status_custom: Optional[str] = Form(None),
    photo_front: Optional[UploadFile] = File(None),
    photo_left: Optional[UploadFile] = File(None),
    photo_right: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Update an existing BMI record - VERSION PRESERVING.
    
    IMPORTANT: This does NOT overwrite the old record. Instead:
    1. The OLD record is kept unchanged as a historical snapshot (is_latest = False)
    2. A NEW BMI record is created with the updated values (is_latest = True)
    3. The new record becomes the latest/current version
    
    This preserves the complete history while allowing corrections/updates.
    """
    # Find the existing (old) record to verify it exists
    old_record = db.query(models.BMIRecord).filter(models.BMIRecord.id == record_id).first()
    if not old_record:
        raise HTTPException(status_code=404, detail="BMI record not found")
    
    # Preserve the old record's important fields before we do anything
    preserved_personnel_id = old_record.personnel_id
    preserved_old_front = old_record.photo_front
    preserved_old_left = old_record.photo_left
    preserved_old_right = old_record.photo_right
    
    # normalize incoming text fields for consistent matching
    rank = rank.upper() if isinstance(rank, str) else rank
    name = name.upper() if isinstance(name, str) else name
    unit = unit.upper() if isinstance(unit, str) else unit
    sex = sex.upper() if isinstance(sex, str) else sex

    # Parse date early to enforce monthly uniqueness
    parsed_date_check = parse_date_taken(date_taken) if date_taken else datetime.utcnow()

    # VALIDATION: Prevent duplicate BMI records for same person in the same month (excluding current record)
    dup = db.query(models.BMIRecord).filter(
        models.BMIRecord.name.ilike(name),
        extract('month', models.BMIRecord.date_taken) == parsed_date_check.month,
        extract('year', models.BMIRecord.date_taken) == parsed_date_check.year,
        models.BMIRecord.id != record_id
    ).first()
    if dup:
        raise HTTPException(status_code=400, detail='A BMI record already exists for this person for the selected month. You can edit the existing record instead.')

    # NEW: Mark the old record as NOT latest
    old_record.is_latest = False
    db.commit()
    
    # Parse name to first and last for file naming
    parts = name.strip().split()
    first_name = parts[0] if parts else ''
    last_name = parts[-1] if len(parts) > 1 else ''
    unit_folder = unit.upper()
    folder_abs = uploads_abs('bmi', unit_folder, bmi_folder_name(first_name, last_name))
    folder_rel = uploads_rel('bmi', unit_folder, bmi_folder_name(first_name, last_name))
    os.makedirs(folder_abs, exist_ok=True)
    base_name = f"{first_name}_{last_name}" if last_name else first_name
    
    # Determine photo paths for the NEW record
    # Use new photos if uploaded, otherwise reuse old photo paths
    front_photo_path = preserved_old_front
    left_photo_path = preserved_old_left
    right_photo_path = preserved_old_right
    
    # Handle new front photo
    if photo_front and photo_front.filename:
        front_name = f"BMI_{base_name}_front.jpg"
        front_path_abs = os.path.join(str(folder_abs), front_name)
        with open(front_path_abs, 'wb') as f:
            f.write(await photo_front.read())
        front_photo_path = f"{folder_rel}/{front_name}".replace("\\", "/")
    
    # Handle new left photo
    if photo_left and photo_left.filename:
        left_name = f"BMI_{base_name}_left.jpg"
        left_path_abs = os.path.join(str(folder_abs), left_name)
        with open(left_path_abs, 'wb') as f:
            f.write(await photo_left.read())
        left_photo_path = f"{folder_rel}/{left_name}".replace("\\", "/")
    
    # Handle new right photo
    if photo_right and photo_right.filename:
        right_name = f"BMI_{base_name}_right.jpg"
        right_path_abs = os.path.join(str(folder_abs), right_name)
        with open(right_path_abs, 'wb') as f:
            f.write(await photo_right.read())
        right_photo_path = f"{folder_rel}/{right_name}".replace("\\", "/")
    
    # Parse date
    parsed_date = parse_date_taken(date_taken) if date_taken else datetime.utcnow()
    
    # Calculate new BMI and classification
    bmi_value = compute_bmi(weight_kg, height_cm)
    pnp_classification = classify_pnp_bmi(bmi_value, age)
    
    # Use raw SQL INSERT to create the NEW record
    # This bypasses any ORM session issues that might cause overwriting
    from sqlalchemy import text
    
    # Insert new record with raw SQL, including is_latest=True
    insert_sql = text("""
        INSERT INTO bmi_records (
            personnel_id, rank, name, unit, age, sex, height_cm, weight_kg,
            waist_cm, hip_cm, wrist_cm, date_taken, bmi, classification, result,
            photo_front, photo_left, photo_right, status, status_custom, is_latest
        ) VALUES (
            :personnel_id, :rank, :name, :unit, :age, :sex, :height_cm, :weight_kg,
            :waist_cm, :hip_cm, :wrist_cm, :date_taken, :bmi, :classification, :result,
            :photo_front, :photo_left, :photo_right, :status, :status_custom, :is_latest
        )
    """)
    
    result = db.execute(insert_sql, {
        'personnel_id': preserved_personnel_id,
        'rank': rank,
        'name': name,
        'unit': unit,
        'age': age,
        'sex': sex,
        'height_cm': height_cm,
        'weight_kg': weight_kg,
        'waist_cm': waist_cm,
        'hip_cm': hip_cm,
        'wrist_cm': wrist_cm,
        'date_taken': parsed_date,
        'bmi': bmi_value,
        'classification': pnp_classification,
        'result': f"{bmi_value:.2f}",
        'photo_front': front_photo_path,
        'photo_left': left_photo_path,
        'photo_right': right_photo_path,
        'status': status,
        'status_custom': status_custom,
        'is_latest': True,  # NEW: Mark new record as latest
    })
    
    db.commit()
    
    # Get the ID of the newly inserted record
    new_record_id = result.lastrowid
    
    # Fetch the newly created record to return
    new_record = db.query(models.BMIRecord).filter(models.BMIRecord.id == new_record_id).first()
    
    # Return the NEW record (which is now the latest)
    return new_record


@router.delete('/{record_id}')
def delete_bmi_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.BMIRecord).filter(models.BMIRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail='BMI record not found')

    is_latest = bool(record.is_latest)
    personnel_id = record.personnel_id
    name = (record.name or '').strip()

    photo_paths = [
        resolve_upload_path(record.photo_front),
        resolve_upload_path(record.photo_left),
        resolve_upload_path(record.photo_right),
    ]

    db.delete(record)
    db.commit()

    if is_latest:
        candidate_query = db.query(models.BMIRecord)
        if personnel_id:
            candidate_query = candidate_query.filter(models.BMIRecord.personnel_id == personnel_id)
        elif name:
            candidate_query = candidate_query.filter(models.BMIRecord.name.ilike(name))

        latest_remaining = candidate_query.order_by(models.BMIRecord.date_taken.desc(), models.BMIRecord.id.desc()).first()
        if latest_remaining:
            latest_remaining.is_latest = True
            db.commit()

    for photo_path in photo_paths:
        try:
            if photo_path and os.path.exists(photo_path):
                os.remove(photo_path)
        except OSError:
            pass

    return {'message': 'BMI record deleted successfully'}


@router.get('/record/{record_id}', response_model=schemas.BMISchema)
def get_bmi_record(record_id: int, db: Session = Depends(get_db)):
    """
    Get a single BMI record by ID.
    Used to prefill the update form.
    """
    record = db.query(models.BMIRecord).filter(models.BMIRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="BMI record not found")
    return record
