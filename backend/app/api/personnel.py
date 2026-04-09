from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import SessionLocal, init_db
from ..utils import ensure_upload_folders, personnel_folder_name, uploads_abs, uploads_rel
import os
from datetime import datetime
from io import BytesIO
import hashlib
import json
import openpyxl.styles
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch

router = APIRouter()

def _upper_str(val):
    if val is None:
        return None
    if isinstance(val, str):
        return val.upper()
    return val

ALLOWED_FILE_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def abs_from_stored_path(stored_path: Optional[str]):
    if not stored_path:
        return None
    norm = str(stored_path).replace("\\", "/")
    idx = norm.find("uploads/")
    rel = norm[idx + len("uploads/"):] if idx >= 0 else norm.lstrip("/")
    return str(uploads_abs(*[p for p in rel.split("/") if p]))


async def read_and_validate_upload(file_obj: UploadFile):
    ext = (os.path.splitext(file_obj.filename or "")[1] or "").lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type for '{file_obj.filename}'. Allowed types: PDF, DOC, DOCX.",
        )
    content = await file_obj.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File '{file_obj.filename}' exceeds 10MB size limit.",
        )
    return ext, content


def file_sha256(path: Optional[str]):
    if not path or not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.on_event("startup")
def startup():
    ensure_upload_folders()
    init_db()


@router.post("/basic", response_model=schemas.PersonnelSchema)
def create_personnel_basic(
    rank: str = Form(...),
    badge_number: Optional[str] = Form(None),
    last_name: str = Form(...),
    first_name: str = Form(...),
    mi: Optional[str] = Form(None),
    suffix: Optional[str] = Form(None),
    unit: str = Form(...),
    status: str = Form(...),
    status_custom: Optional[str] = Form(None),
    qlf: Optional[str] = Form(None),
    nup_rank: Optional[str] = Form(None),
    nup_entry_number: Optional[int] = Form(None),
    date_of_reassignment: Optional[str] = Form(None),
    designation: Optional[str] = Form(None),
    date_of_designation: Optional[str] = Form(None),
    highest_eligibility: Optional[str] = Form(None),
    contact_number: Optional[str] = Form(None),
    birthdate: Optional[str] = Form(None),
    religion: Optional[str] = Form(None),
    section: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Create a personnel record without requiring any documents.
    Documents and trainings can be attached later via the update endpoint.
    """
    def _parse_date(s: Optional[str]):
        if not s:
            return None
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except Exception:
            try:
                return datetime.fromisoformat(s)
            except Exception:
                return None

    parsed_reassignment = _parse_date(date_of_reassignment)
    parsed_designation_date = _parse_date(date_of_designation)
    parsed_birthdate = _parse_date(birthdate)

    p = models.Personnel(
        rank=_upper_str(rank),
        badge_number=_upper_str(badge_number),
        last_name=_upper_str(last_name),
        first_name=_upper_str(first_name),
        mi=_upper_str(mi),
        suffix=_upper_str(suffix),
        unit=_upper_str(unit),
        status=_upper_str(status),
        status_custom=_upper_str(status_custom),
        qlf=_upper_str(qlf),
        nup_rank=_upper_str(nup_rank),
        nup_entry_number=nup_entry_number,
        date_of_reassignment=parsed_reassignment,
        designation=_upper_str(designation),
        date_of_designation=parsed_designation_date,
        highest_eligibility=_upper_str(highest_eligibility),
        contact_number=_upper_str(contact_number),
        birthdate=parsed_birthdate,
        religion=_upper_str(religion),
        section=_upper_str(section),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.post("/", response_model=schemas.PersonnelSchema)
async def create_personnel(
    rank: str = Form(...),
    badge_number: Optional[str] = Form(None),
    last_name: str = Form(...),
    first_name: str = Form(...),
    mi: Optional[str] = Form(None),
    suffix: Optional[str] = Form(None),
    unit: str = Form(...),
    status: str = Form(...),
    status_custom: Optional[str] = Form(None),
    qlf: Optional[str] = Form(None),
    nup_rank: Optional[str] = Form(None),
    nup_entry_number: Optional[int] = Form(None),
    date_of_reassignment: Optional[str] = Form(None),
    designation: Optional[str] = Form(None),
    date_of_designation: Optional[str] = Form(None),
    highest_eligibility: Optional[str] = Form(None),
    contact_number: Optional[str] = Form(None),
    birthdate: Optional[str] = Form(None),
    religion: Optional[str] = Form(None),
    section: Optional[str] = Form(None),
    # single-file documents (now optional so record can be saved even if incomplete)
    pds: Optional[UploadFile] = File(None),
    appointment: Optional[UploadFile] = File(None),
    promotion: Optional[UploadFile] = File(None),
    designation_file: Optional[UploadFile] = File(None),
    reassignment: Optional[UploadFile] = File(None),
    diploma: Optional[UploadFile] = File(None),
    eligibility: Optional[UploadFile] = File(None),
    iper: Optional[UploadFile] = File(None),
    saln: Optional[UploadFile] = File(None),
    pft: Optional[UploadFile] = File(None),
    rca: Optional[UploadFile] = File(None),
    # trainings: lists (optional)
    mandatory_files: Optional[List[UploadFile]] = File(None),
    mandatory_titles: Optional[List[str]] = Form(None),
    specialized_files: Optional[List[UploadFile]] = File(None),
    specialized_titles: Optional[List[str]] = Form(None),
    db: Session = Depends(get_db),
):

    # parse date strings into datetimes where provided
    def _parse_date(s: Optional[str]):
        if not s:
            return None
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except Exception:
            try:
                return datetime.fromisoformat(s)
            except Exception:
                return None

    parsed_reassignment = _parse_date(date_of_reassignment)
    parsed_designation_date = _parse_date(date_of_designation)
    parsed_birthdate = _parse_date(birthdate)

    # Normalize textual inputs to uppercase before saving and before using for filenames
    rank = _upper_str(rank)
    badge_number = _upper_str(badge_number)
    last_name = _upper_str(last_name)
    first_name = _upper_str(first_name)
    mi = _upper_str(mi)
    suffix = _upper_str(suffix)
    unit = _upper_str(unit)
    status = _upper_str(status)
    status_custom = _upper_str(status_custom)
    qlf = _upper_str(qlf)
    nup_rank = _upper_str(nup_rank)
    designation = _upper_str(designation)
    highest_eligibility = _upper_str(highest_eligibility)
    contact_number = _upper_str(contact_number)
    religion = _upper_str(religion)
    section = _upper_str(section)

    # create personnel entry (badge_number is optional)
    p = models.Personnel(
        rank=rank,
        badge_number=badge_number,
        last_name=last_name,
        first_name=first_name,
        mi=mi,
        suffix=suffix,
        unit=unit,
        status=status,
        status_custom=status_custom,
        qlf=qlf,
        nup_rank=nup_rank,
        nup_entry_number=nup_entry_number,
        designation=designation,
        highest_eligibility=highest_eligibility,
        contact_number=contact_number,
        birthdate=parsed_birthdate,
        religion=religion,
        section=section,
        date_of_reassignment=parsed_reassignment,
        date_of_designation=parsed_designation_date,
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    # save uploaded files into structured folder (by unit) and record them
    unit_folder = unit.upper()
    person_folder_abs = uploads_abs('form_201', unit_folder, personnel_folder_name(first_name, last_name))
    person_folder_rel = uploads_rel('form_201', unit_folder, personnel_folder_name(first_name, last_name))
    os.makedirs(person_folder_abs, exist_ok=True)

    async def save_single(file_obj: Optional[UploadFile], shortname: str):
        if not file_obj:
            return
        ext, content = await read_and_validate_upload(file_obj)
        # Use required file naming: FORM201_<First>_<Last>_<document>.pdf
        dest_name = f"FORM201_{first_name}_{last_name}_{shortname}{ext}"
        dest_path_abs = os.path.join(str(person_folder_abs), dest_name)
        with open(dest_path_abs, 'wb') as out:
            out.write(content)
        rel_path = f"{person_folder_rel}/{dest_name}".replace("\\", "/")
        doc = models.Document(personnel_id=p.id, doc_type=shortname, file_path=rel_path)
        db.add(doc)

    # map and save
    await save_single(pds, "pds")
    await save_single(appointment, "appointment")
    await save_single(promotion, "promotion")
    await save_single(designation_file, "designation")
    await save_single(reassignment, "reassignment")
    await save_single(diploma, "diploma")
    await save_single(eligibility, "eligibility")
    await save_single(iper, "iper")
    await save_single(saln, "saln")
    await save_single(pft, "pft")
    await save_single(rca, "rca")

    # trainings
    # save mandatory
    if mandatory_files:
        for idx, f in enumerate(mandatory_files):
            title = ""
            if mandatory_titles and idx < len(mandatory_titles):
                title = mandatory_titles[idx]
            safe_title = title.replace(" ", "_") if title else f"mandatory_{idx+1}"
            ext, content = await read_and_validate_upload(f)
            dest_name = f"FORM201_{first_name}_{last_name}_mandatory_{safe_title}{ext}"
            dest_path_abs = os.path.join(str(person_folder_abs), dest_name)
            with open(dest_path_abs, "wb") as out:
                out.write(content)
            norm_path = f"{person_folder_rel}/{dest_name}".replace("\\", "/")
            tc = models.TrainingCertificate(
                personnel_id=p.id,
                category="mandatory",
                title=(title.upper() if title else safe_title.upper()),
                file_path=norm_path,
            )
            db.add(tc)

    # save specialized
    if specialized_files:
        for idx, f in enumerate(specialized_files):
            title = ""
            if specialized_titles and idx < len(specialized_titles):
                title = specialized_titles[idx]
            safe_title = title.replace(" ", "_") if title else f"specialized_{idx+1}"
            ext, content = await read_and_validate_upload(f)
            dest_name = f"FORM201_{first_name}_{last_name}_specialized_{safe_title}{ext}"
            dest_path_abs = os.path.join(str(person_folder_abs), dest_name)
            with open(dest_path_abs, "wb") as out:
                out.write(content)
            norm_path = f"{person_folder_rel}/{dest_name}".replace("\\", "/")
            tc = models.TrainingCertificate(
                personnel_id=p.id,
                category="specialized",
                title=(title.upper() if title else safe_title.upper()),
                file_path=norm_path,
            )
            db.add(tc)

    db.commit()
    db.refresh(p)
    return p


@router.get("/", response_model=List[schemas.PersonnelSchema])
def list_personnel(db: Session = Depends(get_db)):
    return db.query(models.Personnel).order_by(models.Personnel.last_name).all()


@router.get("/counts")
def personnel_counts(db: Session = Depends(get_db)):
    units = ['RHQ','Cavite','Laguna','Batangas','Rizal','Quezon']
    counts = {u: db.query(models.Personnel).filter(models.Personnel.unit==u).count() for u in units}
    return counts


@router.get("/{person_id}/documents")
def get_documents(person_id: int, db: Session = Depends(get_db)):
    person = db.query(models.Personnel).filter(models.Personnel.id==person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail='Personnel not found')
    return person.documents


@router.get("/{person_id}", response_model=schemas.PersonnelSchema)
def get_person(person_id: int, db: Session = Depends(get_db)):
    person = db.query(models.Personnel).filter(models.Personnel.id==person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail='Personnel not found')
    return person


@router.put("/{person_id}", response_model=schemas.PersonnelSchema)
async def update_person(
    person_id: int,
    rank: str = Form(...),
    badge_number: Optional[str] = Form(None),
    last_name: str = Form(...),
    first_name: str = Form(...),
    mi: Optional[str] = Form(None),
    suffix: Optional[str] = Form(None),
    unit: str = Form(...),
    status: str = Form(...),
    status_custom: Optional[str] = Form(None),
    qlf: Optional[str] = Form(None),
    nup_rank: Optional[str] = Form(None),
    nup_entry_number: Optional[int] = Form(None),
    date_of_reassignment: Optional[str] = Form(None),
    designation: Optional[str] = Form(None),
    date_of_designation: Optional[str] = Form(None),
    highest_eligibility: Optional[str] = Form(None),
    contact_number: Optional[str] = Form(None),
    birthdate: Optional[str] = Form(None),
    religion: Optional[str] = Form(None),
    section: Optional[str] = Form(None),
    # optional replacement single files
    pds: Optional[UploadFile] = File(None),
    appointment: Optional[UploadFile] = File(None),
    promotion: Optional[UploadFile] = File(None),
    designation_file: Optional[UploadFile] = File(None),
    reassignment: Optional[UploadFile] = File(None),
    diploma: Optional[UploadFile] = File(None),
    eligibility: Optional[UploadFile] = File(None),
    iper: Optional[UploadFile] = File(None),
    saln: Optional[UploadFile] = File(None),
    pft: Optional[UploadFile] = File(None),
    rca: Optional[UploadFile] = File(None),
    # trainings/documents: deletions and additions
    delete_doc_types: Optional[str] = Form(None),
    delete_mandatory_ids: Optional[str] = Form(None),
    delete_specialized_ids: Optional[str] = Form(None),
    mandatory_files: Optional[List[UploadFile]] = File(None),
    mandatory_titles: Optional[List[str]] = Form(None),
    specialized_files: Optional[List[UploadFile]] = File(None),
    specialized_titles: Optional[List[str]] = Form(None),
    db: Session = Depends(get_db),
):
    person = db.query(models.Personnel).filter(models.Personnel.id==person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail='Personnel not found')

    # update basic fields
    # parse incoming date strings
    def _parse_date(s: Optional[str]):
        if not s:
            return None
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except Exception:
            try:
                return datetime.fromisoformat(s)
            except Exception:
                return None

    # Normalize incoming textual values to uppercase before saving
    person.rank = _upper_str(rank)
    person.badge_number = _upper_str(badge_number)
    person.last_name = _upper_str(last_name)
    person.first_name = _upper_str(first_name)
    person.mi = _upper_str(mi)
    person.suffix = _upper_str(suffix)
    person.unit = _upper_str(unit)
    person.status = _upper_str(status)
    person.status_custom = _upper_str(status_custom)
    person.qlf = _upper_str(qlf)
    person.nup_rank = _upper_str(nup_rank)
    person.nup_entry_number = nup_entry_number
    person.designation = _upper_str(designation)
    person.date_of_reassignment = _parse_date(date_of_reassignment)
    person.date_of_designation = _parse_date(date_of_designation)
    person.highest_eligibility = _upper_str(highest_eligibility)
    person.contact_number = _upper_str(contact_number)
    person.birthdate = _parse_date(birthdate)
    person.religion = _upper_str(religion)
    person.section = _upper_str(section)
    db.add(person)
    db.commit()

    # person folder (by unit)
    unit_folder = unit.upper()
    person_folder_abs = uploads_abs('form_201', unit_folder, personnel_folder_name(first_name, last_name))
    person_folder_rel = uploads_rel('form_201', unit_folder, personnel_folder_name(first_name, last_name))
    os.makedirs(person_folder_abs, exist_ok=True)

    # helper to replace or create document
    async def replace_single(file_obj: UploadFile, shortname: str):
        if not file_obj:
            return
        ext, content = await read_and_validate_upload(file_obj)
        dest_name = f"FORM201_{first_name}_{last_name}_{shortname}{ext}"
        dest_path_abs = os.path.join(str(person_folder_abs), dest_name)
        norm_path = f"{person_folder_rel}/{dest_name}".replace("\\", "/")
        # check existing doc
        doc = db.query(models.Document).filter(models.Document.personnel_id==person.id, models.Document.doc_type==shortname).first()
        existing_abs = abs_from_stored_path(doc.file_path) if doc else None
        if existing_abs and os.path.exists(existing_abs):
            old_hash = file_sha256(existing_abs)
            new_hash = hashlib.sha256(content).hexdigest()
            if old_hash == new_hash:
                return
        with open(dest_path_abs, 'wb') as out:
            out.write(content)
        if doc:
            if existing_abs and os.path.exists(existing_abs) and os.path.abspath(existing_abs) != os.path.abspath(dest_path_abs):
                try:
                    os.remove(existing_abs)
                except OSError:
                    pass
            doc.file_path = norm_path
            db.add(doc)
        else:
            doc = models.Document(personnel_id=person.id, doc_type=shortname, file_path=norm_path)
            db.add(doc)

    await replace_single(pds, 'pds')
    await replace_single(appointment, 'appointment')
    await replace_single(promotion, 'promotion')
    await replace_single(designation_file, 'designation')
    await replace_single(reassignment, 'reassignment')
    await replace_single(diploma, 'diploma')
    await replace_single(eligibility, 'eligibility')
    await replace_single(iper, 'iper')
    await replace_single(saln, 'saln')
    await replace_single(pft, 'pft')
    await replace_single(rca, 'rca')

    # handle deletion of existing single documents
    if delete_doc_types:
        try:
            doc_types = json.loads(delete_doc_types)
            for d_type in doc_types:
                doc = db.query(models.Document).filter(models.Document.personnel_id==person.id, models.Document.doc_type==d_type).first()
                if doc:
                    abs_path = abs_from_stored_path(doc.file_path)
                    if abs_path and os.path.exists(abs_path):
                        try:
                            os.remove(abs_path)
                        except OSError:
                            pass
                    db.delete(doc)
        except Exception:
            pass

    # handle deletions of trainings
    if delete_mandatory_ids:
        try:
            ids = json.loads(delete_mandatory_ids)
            for iid in ids:
                t = db.query(models.TrainingCertificate).filter(models.TrainingCertificate.id==iid, models.TrainingCertificate.personnel_id==person.id).first()
                if t:
                    # remove file
                    try:
                        abs_path = abs_from_stored_path(t.file_path)
                        if abs_path and os.path.exists(abs_path):
                            os.remove(abs_path)
                    except Exception:
                        pass
                    db.delete(t)
        except Exception:
            pass
    if delete_specialized_ids:
        try:
            ids = json.loads(delete_specialized_ids)
            for iid in ids:
                t = db.query(models.TrainingCertificate).filter(models.TrainingCertificate.id==iid, models.TrainingCertificate.personnel_id==person.id).first()
                if t:
                    try:
                        abs_path = abs_from_stored_path(t.file_path)
                        if abs_path and os.path.exists(abs_path):
                            os.remove(abs_path)
                    except Exception:
                        pass
                    db.delete(t)
        except Exception:
            pass

    # add new trainings if any
    if mandatory_files:
        for idx, f in enumerate(mandatory_files):
            title = ''
            if mandatory_titles and idx < len(mandatory_titles):
                title = mandatory_titles[idx]
            safe_title = title.replace(' ', '_') if title else f'mandatory_new_{idx+1}'
            ext, content = await read_and_validate_upload(f)
            dest_name = f"FORM201_{first_name}_{last_name}_mandatory_{safe_title}{ext}"
            dest_path_abs = os.path.join(str(person_folder_abs), dest_name)
            with open(dest_path_abs, 'wb') as out:
                out.write(content)
            norm_path = f"{person_folder_rel}/{dest_name}".replace("\\", "/")
            tc = models.TrainingCertificate(personnel_id=person.id, category='mandatory', title=(title.upper() if title else safe_title.upper()), file_path=norm_path)
            db.add(tc)

    if specialized_files:
        for idx, f in enumerate(specialized_files):
            title = ''
            if specialized_titles and idx < len(specialized_titles):
                title = specialized_titles[idx]
            safe_title = title.replace(' ', '_') if title else f'specialized_new_{idx+1}'
            ext, content = await read_and_validate_upload(f)
            dest_name = f"FORM201_{first_name}_{last_name}_specialized_{safe_title}{ext}"
            dest_path_abs = os.path.join(str(person_folder_abs), dest_name)
            with open(dest_path_abs, 'wb') as out:
                out.write(content)
            norm_path = f"{person_folder_rel}/{dest_name}".replace("\\", "/")
            tc = models.TrainingCertificate(personnel_id=person.id, category='specialized', title=(title.upper() if title else safe_title.upper()), file_path=norm_path)
            db.add(tc)

    db.commit()
    db.refresh(person)
    return person


@router.post('/form201-report')
def generate_form201_report(
    unit: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    prepared_by: str = Form(''),
    noted_by: str = Form(''),
    file_name: str = Form('form201_report'),
    db: Session = Depends(get_db),
):
    """
    Generate a Form 201 Personnel Report grouped by unit.
    
    Document Completion Logic:
    - 11 single document types + 1 mandatory training + 1 specialized training = 13 total
    - Completion: count_uploaded / 13
    - Status: "COMPLETE" if all 13, else "WITH DEFICIENCY"
    """
    from openpyxl.styles import Font, Border, Side, Alignment
    
    # Sanitize filename
    safe_name = (file_name or "form201_report").strip()
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in safe_name)
    safe_name = safe_name.strip("_") or "form201_report"
    
    # Query personnel with filters
    query = db.query(models.Personnel)
    if unit and unit != 'All Units':
        query = query.filter(models.Personnel.unit == unit)
    if status and status != 'All Status':
        query = query.filter(models.Personnel.status == status)
    
    all_personnel = query.all()
    
    # Group by unit and sort
    units = ['RHQ', 'CAVITE', 'LAGUNA', 'BATANGAS', 'RIZAL', 'QUEZON']
    grouped = {u: [] for u in units}
    for person in all_personnel:
        unit_key = person.unit.upper() if person.unit else 'RHQ'
        if unit_key in grouped:
            grouped[unit_key].append(person)
    
    # Sort each unit: by rank (if available), then by surname
    def rank_order(rank_str: str) -> int:
        rank_hierarchy = {
            'PGen': 1, 'MGen': 2, 'BGen': 3, 'Col': 4, 'LtCol': 5, 'Maj': 6,
            'Cpt': 7, '1st Lt': 8, '2nd Lt': 9, 'Spy': 10, 'PSP': 11, 'PFC': 12,
        }
        return rank_hierarchy.get(rank_str or '', 999)
    
    for unit_key in grouped:
        grouped[unit_key].sort(key=lambda p: (
            rank_order(p.rank),
            (p.last_name or '').lower(),
        ))
    
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = 'Form 201 Report'
    
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin'),
    )
    
    current_row = 1
    
    # Header
    ws.merge_cells(f'A{current_row}:I{current_row}')
    header = ws[f'A{current_row}']
    header.value = 'CRIMINAL INVESTIGATION AND DETECTION GROUP REGION 4A'
    header.font = Font(bold=True, size=12)
    header.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1
    
    ws.merge_cells(f'A{current_row}:I{current_row}')
    subheader = ws[f'A{current_row}']
    subheader.value = 'FORM 201 PERSONNEL REPORT'
    subheader.font = Font(bold=True, size=11)
    subheader.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1
    
    ws.merge_cells(f'A{current_row}:I{current_row}')
    date_cell = ws[f'A{current_row}']
    date_cell.value = f"(as of {datetime.utcnow().strftime('%B %d, %Y')})"
    date_cell.font = Font(italic=True, size=10)
    date_cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 2
    
    # Process each unit
    for unit_key in units:
        personnel_list = grouped[unit_key]
        if not personnel_list:
            continue
        
        # Unit header
        ws.merge_cells(f'A{current_row}:I{current_row}')
        unit_cell = ws[f'A{current_row}']
        unit_cell.value = f'UNIT: {unit_key}'
        unit_cell.font = Font(bold=True, size=11)
        unit_cell.fill = openpyxl.styles.PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
        unit_cell.alignment = Alignment(horizontal='left', vertical='center')
        current_row += 1
        
        # Table header
        headers = ['No.', 'Rank', 'Surname', 'First Name', 'Middle Name', 'Suffix', 'Status', 'Document Completion', 'Remarks']
        for col_idx, col_name in enumerate(headers, start=1):
            cell = ws.cell(row=current_row, column=col_idx)
            cell.value = col_name
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = openpyxl.styles.PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center', vertical='center')
        current_row += 1
        
        # Personnel rows
        for idx, person in enumerate(personnel_list, start=1):
            single_doc_count = len(person.documents or [])
            has_mandatory = any(t.category == 'mandatory' for t in (person.trainings or []))
            has_specialized = any(t.category == 'specialized' for t in (person.trainings or []))
            
            total_count = single_doc_count
            if has_mandatory:
                total_count += 1
            if has_specialized:
                total_count += 1
            
            completion_str = f"{total_count}/13"
            is_complete = total_count == 13
            remarks = "COMPLETE" if is_complete else "WITH DEFICIENCY"
            
            # Determine missing documents for remarks (optional)
            missing = []
            single_doc_types = ['pds', 'appointment', 'promotion', 'designation', 'reassignment', 'diploma', 'eligibility', 'iper', 'saln', 'pft', 'rca']
            existing_types = {d.doc_type for d in (person.documents or [])}
            for doc_type in single_doc_types:
                if doc_type not in existing_types:
                    missing.append(doc_type.upper())
            if not has_mandatory:
                missing.append('MANDATORY TRAINING')
            if not has_specialized:
                missing.append('SPECIALIZED TRAINING')
            
            row_data = [
                idx,
                person.rank or '',
                person.last_name or '',
                person.first_name or '',
                person.mi or '',
                person.suffix or '',
                person.status or '',
                completion_str,
                remarks,
            ]
            
            for col_idx, value in enumerate(row_data, start=1):
                cell = ws.cell(row=current_row, column=col_idx)
                cell.value = value
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='left', vertical='center')
                if col_idx == 1:
                    cell.alignment = Alignment(horizontal='center', vertical='center')
            
            current_row += 1
        
        current_row += 1
    
    # Footer section
    current_row += 1
    ws[f'A{current_row}'] = 'Prepared by: ________________________'
    ws[f'A{current_row}'].font = Font(name='Courier New', size=10)
    current_row += 1
    ws[f'D{current_row}'] = 'Noted by: ________________________'
    ws[f'D{current_row}'].font = Font(name='Courier New', size=10)
    
    # If prepared_by or noted_by provided, add them
    if prepared_by or noted_by:
        current_row += 3
        if prepared_by:
            ws[f'A{current_row}'] = prepared_by
        if noted_by:
            ws[f'D{current_row}'] = noted_by
    
    # Column widths
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 10
    ws.column_dimensions['G'].width = 12
    ws.column_dimensions['H'].width = 18
    ws.column_dimensions['I'].width = 20
    
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    
    return StreamingResponse(
        stream,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment;filename={safe_name}.xlsx"},
    )


@router.post('/report')
def personnel_report(
    unit: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    report_type: str = Form('excel'),
    file_name: str = Form('form201_report'),
    # New parameters from Generate Modal
    as_of_date: Optional[str] = Form(None),
    scope: Optional[str] = Form(None),
    specific_unit: Optional[str] = Form(None),
    # Signatories
    prepared_by_name: Optional[str] = Form(None),
    prepared_by_title: Optional[str] = Form(None),
    verified_by_name: Optional[str] = Form(None),
    verified_by_title: Optional[str] = Form(None),
    noted_by_name: Optional[str] = Form(None),
    noted_by_title: Optional[str] = Form(None),
    # Authorized values from modal
    authorized_values: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Generate comprehensive Form 201 Excel report with all tabs.
    Each tab has its own sorting and layout rules as specified.
    """
    from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
    from openpyxl.utils import get_column_letter
    import json

    # Parse authorized values from modal
    aut_values = {'PCO': {}, 'PNCO': {}, 'NUP': {}, 'Totals': {}}
    if authorized_values:
        try:
            aut_values = json.loads(authorized_values)
        except:
            pass

    # Default as of date
    report_date = as_of_date or datetime.utcnow().strftime('%Y-%m-%d')
    try:
        display_date = datetime.strptime(report_date, '%Y-%m-%d').strftime('%B %d, %Y')
    except:
        display_date = datetime.utcnow().strftime('%B %d, %Y')

    # Query personnel with filters
    q = db.query(models.Personnel)
    if scope == 'Specific Unit' and specific_unit:
        q = q.filter(models.Personnel.unit == specific_unit)
    elif unit and unit != 'All Units':
        q = q.filter(models.Personnel.unit == unit)
    if status and status != 'All Status':
        q = q.filter(models.Personnel.status == status)

    all_personnel = q.all()
    
    # Debug: Check the type and content of all_personnel
    print(f"DEBUG all_personnel type: {type(all_personnel)}, length: {len(all_personnel) if all_personnel else 0}")
    if all_personnel:
        print(f"DEBUG first item type: {type(all_personnel[0])}")
        print(f"DEBUG first item: {all_personnel[0]}")
        if hasattr(all_personnel[0], '__dict__'):
            print(f"DEBUG first item dict: {all_personnel[0].__dict__}")

    def safe(v):
        if v is None:
            return ''
        if isinstance(v, str) and not v.strip():
            return ''
        return v

    def fmt_date(v):
        if not v:
            return ''
        try:
            return v.strftime('%Y-%m-%d')
        except Exception:
            return str(v)

    # RANK ORDER for sorting uniformed personnel (highest to lowest)
    RANK_ORDER = {
        'PGEN': 1, 'PLTGEN': 2, 'PMGEN': 3, 'PBGEN': 4, 'PCOL': 5,
        'PLTCOL': 6, 'PMAJ': 7, 'PCPT': 8, 'PLT': 9,
        'PEMS': 10, 'PCMS': 11, 'PSMS': 12, 'PMSG': 13, 'PSSG': 14,
        'PCPL': 15, 'PAT': 16
    }

    def rank_sort_key(p):
        rank = (p.rank or '').upper()
        return (RANK_ORDER.get(rank, 999), p.last_name or '', p.first_name or '')

    def entry_number_sort_key(p):
        return (p.nup_entry_number or 999999, p.last_name or '', p.first_name or '')

    def alpha_sort_key(p):
        return (p.last_name or '', p.first_name or '')

    wb = Workbook()
    sheet_names = [
        'LIST OF NUP',
        'LIST OF U.P',
        'TERRITORIAL STRENGTH',
        'RANK STRUCTURE',
        'RANK PROFILE',
        'ALPHA LIST',
        'DISPOSITION OF TROOPS',
        'PERSONNEL FILL-UP',
        'KEY OFFICERS',
        'STATION LIST',
        'RANK INVENTORY',
        'CIDG RFU4A PCO CONTACT LIST',
    ]

    thin = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')

    # Helper to create titled header with as-of date
    def write_sheet_title(ws, title_text, cols=10):
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=cols)
        c = ws.cell(row=1, column=1)
        c.value = 'CRIMINAL INVESTIGATION AND DETECTION GROUP REGION 4A'
        c.font = Font(bold=True, size=12)
        c.alignment = Alignment(horizontal='center', vertical='center')
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=cols)
        c2 = ws.cell(row=2, column=1)
        c2.value = title_text
        c2.font = Font(bold=True, size=11)
        c2.alignment = Alignment(horizontal='center', vertical='center')
        ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=cols)
        c3 = ws.cell(row=3, column=1)
        c3.value = f"(as of {display_date})"
        c3.font = Font(italic=True, size=10)
        c3.alignment = Alignment(horizontal='center', vertical='center')

    # Helper to write signature blocks
    def write_signatures(ws, start_row, prepared_by_name, prepared_by_title, verified_by_name, verified_by_title, noted_by_name, noted_by_title):
        sig_row = start_row
        # Prepared by
        ws.cell(row=sig_row, column=1).value = 'Prepared by:'
        ws.cell(row=sig_row, column=1).font = Font(bold=True)
        ws.cell(row=sig_row+1, column=1).value = prepared_by_name or ''
        ws.cell(row=sig_row+2, column=1).value = prepared_by_title or ''
        
        # Verified by
        ws.cell(row=sig_row, column=4).value = 'Verified Correct by:'
        ws.cell(row=sig_row, column=4).font = Font(bold=True)
        ws.cell(row=sig_row+1, column=4).value = verified_by_name or ''
        ws.cell(row=sig_row+2, column=4).value = verified_by_title or ''
        
        # Noted by
        ws.cell(row=sig_row, column=7).value = 'Noted by:'
        ws.cell(row=sig_row, column=7).font = Font(bold=True)
        ws.cell(row=sig_row+1, column=7).value = noted_by_name or ''
        ws.cell(row=sig_row+2, column=7).value = noted_by_title or ''

    # ============================================================
    # TAB 1: LIST OF NUP - Sorted by Entry Number
    # ============================================================
    ws = wb.active
    ws.title = sheet_names[0]
    write_sheet_title(ws, sheet_names[0], 8)
    current_row = 5
    
    headers = ['Entry No.', 'Rank', 'Last', 'First', 'Middle', 'Q', 'Office']
    for col_idx, col_name in enumerate(headers, start=1):
        cell = ws.cell(row=current_row, column=col_idx)
        cell.value = col_name
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = header_fill
        cell.border = thin
        cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1
    
    # Filter NUP and sort by entry number
    nup_personnel = [p for p in all_personnel if (p.status or '').upper() == 'NUP']
    nup_personnel.sort(key=entry_number_sort_key)
    
    for idx, p in enumerate(nup_personnel, start=1):
        row = [
            p.nup_entry_number or idx,
            safe(p.nup_rank) or safe(p.rank),
            safe(p.last_name).upper(),
            safe(p.first_name).upper(),
            safe(p.mi).upper(),
            safe(p.suffix).upper(),
            safe(p.unit).upper(),
        ]
        for col_idx, val in enumerate(row, start=1):
            c = ws.cell(row=current_row, column=col_idx)
            c.value = val
            c.border = thin
            c.alignment = Alignment(horizontal='left', vertical='center')
        current_row += 1
    
    # Signatures
    current_row += 2
    write_signatures(ws, current_row, prepared_by_name, prepared_by_title, verified_by_name, verified_by_title, noted_by_name, noted_by_title)
    
    # Column widths
    for i, w in enumerate([10, 12, 18, 18, 12, 8, 18], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ============================================================
    # TAB 2: LIST OF U.P - Sorted by rank hierarchy
    # ============================================================
    ws = wb.create_sheet(title=sheet_names[1])
    write_sheet_title(ws, sheet_names[1], 10)
    current_row = 5
    
    headers = ['Entry No.', 'Rank', 'Last', 'First', 'Middle', 'Q', 'Badge No.', 'Office']
    for col_idx, col_name in enumerate(headers, start=1):
        cell = ws.cell(row=current_row, column=col_idx)
        cell.value = col_name
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = header_fill
        cell.border = thin
        cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1
    
    # Filter UP and sort by rank
    up_personnel = [p for p in all_personnel if (p.status or '').upper() == 'UP']
    up_personnel.sort(key=rank_sort_key)
    
    for idx, p in enumerate(up_personnel, start=1):
        row = [
            idx,
            safe(p.rank).upper(),
            safe(p.last_name).upper(),
            safe(p.first_name).upper(),
            safe(p.mi).upper(),
            safe(p.suffix).upper(),
            safe(p.badge_number).upper(),
            safe(p.unit).upper(),
        ]
        for col_idx, val in enumerate(row, start=1):
            c = ws.cell(row=current_row, column=col_idx)
            c.value = val
            c.border = thin
            c.alignment = Alignment(horizontal='left', vertical='center')
        current_row += 1
    
    # Signatures
    current_row += 2
    write_signatures(ws, current_row, prepared_by_name, prepared_by_title, verified_by_name, verified_by_title, noted_by_name, noted_by_title)
    
    for i, w in enumerate([10, 12, 18, 18, 12, 8, 14, 18], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ============================================================
    # TAB 3: TERRITORIAL STRENGTH
    # ============================================================
    ws = wb.create_sheet(title=sheet_names[2])
    write_sheet_title(ws, sheet_names[2], 5)
    current_row = 5
    
    headers = ['Office/Unit', 'PCOs', 'PNCOs', 'NUPs', 'Total']
    for col_idx, col_name in enumerate(headers, start=1):
        cell = ws.cell(row=current_row, column=col_idx)
        cell.value = col_name
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = header_fill
        cell.border = thin
        cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1
    
    # Fixed units order
    unit_order = ['RFU4A HQS', 'CAVITE PFU', 'LAGUNA PFU', 'BATANGAS PFU', 'RIZAL PFU', 'QUEZON PFU']
    
    # Map unit names
    unit_map = {
        'RHQ': 'RFU4A HQS', 'CAVITE': 'CAVITE PFU', 'LAGUNA': 'LAGUNA PFU',
        'BATANGAS': 'BATANGAS PFU', 'RIZAL': 'RIZAL PFU', 'QUEZON': 'QUEZON PFU'
    }
    
    totals = {'PCOs': 0, 'PNCOs': 0, 'NUPs': 0, 'Total': 0}
    
    for unit_name in unit_order:
        # Reverse map for query
        rev_map = {v: k for k, v in unit_map.items()}
        db_unit = rev_map.get(unit_name, unit_name)
        
        unit_personnel = [p for p in all_personnel if (p.unit or '').upper() == db_unit.upper()]
        
        pco_count = sum(1 for p in unit_personnel if p.status and p.status.upper() == 'UP' and p.rank in ['PCOL', 'PLTCOL', 'PMAJ', 'PCPT', 'PLT', 'PMGEN', 'PBGEN'])
        pnco_count = sum(1 for p in unit_personnel if p.status and p.status.upper() == 'UP' and p.rank in ['PEMS', 'PCMS', 'PSMS', 'PMSG', 'PSSG', 'PCPL', 'PAT'])
        nup_count = sum(1 for p in unit_personnel if p.status and p.status.upper() == 'NUP')
        
        total = pco_count + pnco_count + nup_count
        
        row = [unit_name, pco_count, pnco_count, nup_count, total]
        for col_idx, val in enumerate(row, start=1):
            c = ws.cell(row=current_row, column=col_idx)
            c.value = val
            c.border = thin
            c.alignment = Alignment(horizontal='center' if col_idx > 1 else 'left', vertical='center')
        
        totals['PCOs'] += pco_count
        totals['PNCOs'] += pnco_count
        totals['NUPs'] += nup_count
        totals['Total'] += total
        current_row += 1
    
    # Grand Total row
    ws.cell(row=current_row, column=1).value = 'GRAND TOTAL'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    for col in range(2, 6):
        ws.cell(row=current_row, column=col).value = totals[['PCOs', 'PNCOs', 'NUPs', 'Total'][col-2]]
        ws.cell(row=current_row, column=col).font = Font(bold=True)
        ws.cell(row=current_row, column=col).border = thin
    current_row += 2
    
    # Signatures
    write_signatures(ws, current_row, prepared_by_name, prepared_by_title, verified_by_name, verified_by_title, noted_by_name, noted_by_title)
    
    for i, w in enumerate([20, 10, 10, 10, 12], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ============================================================
    # TAB 4: RANK STRUCTURE (AUT vs ACT vs VAR)
    # ============================================================
    ws = wb.create_sheet(title=sheet_names[3])
    write_sheet_title(ws, sheet_names[3], 6)
    current_row = 5
    
    # Headers
    headers = ['Rank', 'AUT', 'ACT', 'VAR']
    for col_idx, col_name in enumerate(headers, start=1):
        cell = ws.cell(row=current_row, column=col_idx)
        cell.value = col_name
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = header_fill
        cell.border = thin
        cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1
    
    # Get AUT values - handle both object format and plain value format
    pco_aut = aut_values.get('PCO', {})
    if isinstance(pco_aut, str):
        pco_aut = {}
    pnco_aut = aut_values.get('PNCO', {})
    if isinstance(pnco_aut, str):
        pnco_aut = {}
    nup_aut = aut_values.get('NUP', 0)
    # Handle NUP - could be plain value or nested object
    if isinstance(nup_aut, dict):
        nup_aut = nup_aut.get('NUP', nup_aut.get('NUP', 0))
    if isinstance(nup_aut, str):
        nup_aut = int(nup_aut) if nup_aut else 0
    totals_aut = aut_values.get('Totals', {})
    if isinstance(totals_aut, str):
        totals_aut = {}
    
    # PCO ranks in order
    pco_ranks = ['PMGEN', 'PBGEN', 'PCOL', 'PLTCOL', 'PMAJ', 'PCPT', 'PLT']
    pco_actuals = {r: 0 for r in pco_ranks}
    
    for p in all_personnel:
        if p.status and p.status.upper() == 'UP':
            rank = (p.rank or '').upper()
            if rank in pco_ranks:
                pco_actuals[rank] = pco_actuals.get(rank, 0) + 1
    
    # Write PCO ranks
    for rank in pco_ranks:
        aut_val = int(pco_aut.get(rank, 0))
        act_val = pco_actuals.get(rank, 0)
        var_val = act_val - aut_val
        
        row = [rank, aut_val, act_val, var_val]
        for col_idx, val in enumerate(row, start=1):
            c = ws.cell(row=current_row, column=col_idx)
            c.value = val
            c.border = thin
            c.alignment = Alignment(horizontal='center', vertical='center')
        current_row += 1
    
    # PCO Subtotal
    pco_aut_sub = sum(int(pco_aut.get(r, 0)) for r in pco_ranks)
    pco_act_sub = sum(pco_actuals.values())
    ws.cell(row=current_row, column=1).value = 'Sub-Total (PCOs)'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=2).value = pco_aut_sub
    ws.cell(row=current_row, column=2).font = Font(bold=True)
    ws.cell(row=current_row, column=3).value = pco_act_sub
    ws.cell(row=current_row, column=3).font = Font(bold=True)
    ws.cell(row=current_row, column=4).value = pco_act_sub - pco_aut_sub
    ws.cell(row=current_row, column=4).font = Font(bold=True)
    for col in range(1, 5):
        ws.cell(row=current_row, column=col).border = thin
    current_row += 2
    
    # PNCO ranks in order
    pnco_ranks = ['PEMS', 'PCMS', 'PSMS', 'PMSG', 'PSSG', 'PCPL', 'PAT']
    pnco_actuals = {r: 0 for r in pnco_ranks}
    
    for p in all_personnel:
        if p.status and p.status.upper() == 'UP':
            rank = (p.rank or '').upper()
            if rank in pnco_ranks:
                pnco_actuals[rank] = pnco_actuals.get(rank, 0) + 1
    
    # Write PNCO ranks
    for rank in pnco_ranks:
        aut_val = int(pnco_aut.get(rank, 0))
        act_val = pnco_actuals.get(rank, 0)
        var_val = act_val - aut_val
        
        row = [rank, aut_val, act_val, var_val]
        for col_idx, val in enumerate(row, start=1):
            c = ws.cell(row=current_row, column=col_idx)
            c.value = val
            c.border = thin
            c.alignment = Alignment(horizontal='center', vertical='center')
        current_row += 1
    
    # PNCO Subtotal
    pnco_aut_sub = sum(int(pnco_aut.get(r, 0)) for r in pnco_ranks)
    pnco_act_sub = sum(pnco_actuals.values())
    ws.cell(row=current_row, column=1).value = 'Sub-Total (PNCOs)'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=2).value = pnco_aut_sub
    ws.cell(row=current_row, column=2).font = Font(bold=True)
    ws.cell(row=current_row, column=3).value = pnco_act_sub
    ws.cell(row=current_row, column=3).font = Font(bold=True)
    ws.cell(row=current_row, column=4).value = pnco_act_sub - pnco_aut_sub
    ws.cell(row=current_row, column=4).font = Font(bold=True)
    for col in range(1, 5):
        ws.cell(row=current_row, column=col).border = thin
    current_row += 2
    
    # NUP row
    nup_act = sum(1 for p in all_personnel if p.status and p.status.upper() == 'NUP')
    nup_aut_val = int(nup_aut) if nup_aut else 0
    ws.cell(row=current_row, column=1).value = 'NUP'
    ws.cell(row=current_row, column=2).value = nup_aut_val
    ws.cell(row=current_row, column=3).value = nup_act
    ws.cell(row=current_row, column=4).value = nup_act - nup_aut_val
    for col in range(1, 5):
        ws.cell(row=current_row, column=col).border = thin
    current_row += 2
    
    # Total Uniformed Personnel
    total_uniformed_act = pco_act_sub + pnco_act_sub
    total_uniformed_aut = totals_aut.get('TotalUniformed', total_uniformed_act)
    if isinstance(total_uniformed_aut, str):
        total_uniformed_aut = int(total_uniformed_aut) if total_uniformed_aut.isdigit() else total_uniformed_act
    ws.cell(row=current_row, column=1).value = 'Total Uniformed Personnel'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=2).value = total_uniformed_aut
    ws.cell(row=current_row, column=2).font = Font(bold=True)
    ws.cell(row=current_row, column=3).value = total_uniformed_act
    ws.cell(row=current_row, column=3).font = Font(bold=True)
    ws.cell(row=current_row, column=4).value = total_uniformed_act - total_uniformed_aut
    ws.cell(row=current_row, column=4).font = Font(bold=True)
    for col in range(1, 5):
        ws.cell(row=current_row, column=col).border = thin
    
    # Note: No signatories for Rank Structure
    for i, w in enumerate([20, 10, 10, 10], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # 5) RANK PROFILE (personnel distribution by rank per sub-unit)
    ws = wb.create_sheet(title=sheet_names[4])
    write_sheet_title(ws, sheet_names[4], 20)
    current_row = 5
    
    # Sub-units in order
    sub_units = ['RFU4A HQS', 'CAV PFU', 'LAG PFU', 'BATS PFU', 'RIZAL PFU', 'QZN PFU']
    unit_map = {'RHQ': 'RFU4A HQS', 'CAVITE': 'CAV PFU', 'LAGUNA': 'LAG PFU', 
                'BATANGAS': 'BATS PFU', 'RIZAL': 'RIZAL PFU', 'QUEZON': 'QZN PFU'}
    rev_map = {v: k for k, v in unit_map.items()}
    
    # Headers
    headers = ['Unit', 'PCOL', 'PLTCOL', 'PMAJ', 'PCPT', 'PLT', 'Actual PCO', 
               'PEMS', 'PCMS', 'PSMS', 'PMSG', 'PSSG', 'PCPL', 'PAT', 'Actual PNCO',
               'Sub-Total Uniformed', 'Actual NUP', 'Total']
    for col_idx, col_name in enumerate(headers, start=1):
        c = ws.cell(row=current_row, column=col_idx)
        c.value = col_name
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = header_fill
        c.border = thin
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    current_row += 1
    
    pco_ranks = ['PCOL', 'PLTCOL', 'PMAJ', 'PCPT', 'PLT']
    pnco_ranks = ['PEMS', 'PCMS', 'PSMS', 'PMSG', 'PSSG', 'PCPL', 'PAT']
    
    unit_totals = []
    for sub_unit in sub_units:
        db_unit = rev_map.get(sub_unit, sub_unit)
        unit_personnel = [p for p in all_personnel if (p.unit or '').upper() == db_unit.upper()]
        
        pco_counts = {r: sum(1 for p in unit_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == r) for r in pco_ranks}
        pnco_counts = {r: sum(1 for p in unit_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == r) for r in pnco_ranks}
        
        actual_pco = sum(pco_counts.values())
        actual_pnco = sum(pnco_counts.values())
        sub_total_uniformed = actual_pco + actual_pnco
        actual_nup = sum(1 for p in unit_personnel if p.status and p.status.upper() == 'NUP')
        total = sub_total_uniformed + actual_nup
        
        row = [sub_unit] + [pco_counts[r] for r in pco_ranks] + [actual_pco] + \
              [pnco_counts[r] for r in pnco_ranks] + [actual_pnco] + [sub_total_uniformed, actual_nup, total]
        
        for col_idx, val in enumerate(row, start=1):
            c = ws.cell(row=current_row, column=col_idx)
            c.value = val
            c.border = thin
            c.alignment = Alignment(horizontal='center', vertical='center')
        
        unit_totals.append({'pco': actual_pco, 'pnco': actual_pnco, 'uniformed': sub_total_uniformed, 'nup': actual_nup, 'total': total})
        current_row += 1
    
    # TOTAL row
    ws.cell(row=current_row, column=1).value = 'TOTAL'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    for col in range(2, 18):
        ws.cell(row=current_row, column=col).font = Font(bold=True)
        ws.cell(row=current_row, column=col).border = thin
    
    total_pco = sum(t['pco'] for t in unit_totals)
    total_pnco = sum(t['pnco'] for t in unit_totals)
    total_uniformed = sum(t['uniformed'] for t in unit_totals)
    total_nup = sum(t['nup'] for t in unit_totals)
    grand_total = sum(t['total'] for t in unit_totals)
    
    ws.cell(row=current_row, column=7).value = total_pco
    ws.cell(row=current_row, column=15).value = total_pnco
    ws.cell(row=current_row, column=16).value = total_uniformed
    ws.cell(row=current_row, column=17).value = total_nup
    ws.cell(row=current_row, column=18).value = grand_total
    
    # Signatures
    current_row += 2
    write_signatures(ws, current_row, prepared_by_name, prepared_by_title, verified_by_name, verified_by_title, noted_by_name, noted_by_title)
    
    for i, w in enumerate([15, 8, 8, 8, 8, 8, 10, 8, 8, 8, 8, 8, 8, 8, 10, 12, 10, 10], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ============================================================
    # TAB 6: ALPHA LIST - Alphabetical by last name
    # ============================================================
    ws = wb.create_sheet(title=sheet_names[5])
    write_sheet_title(ws, sheet_names[5], 12)
    current_row = 5
    
    headers = ['Entry Number', 'Account Number', 'Rank', 'Last', 'First', 'Middle', 'Q', 
               'Badge No.', 'Contact Number', 'Office', 'Date of Birth', 'Religion']
    for col_idx, col_name in enumerate(headers, start=1):
        c = ws.cell(row=current_row, column=col_idx)
        c.value = col_name
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = header_fill
        c.border = thin
        c.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1
    
    # Sort alphabetically by last name
    alpha_personnel = sorted(all_personnel, key=alpha_sort_key)
    
    for idx, p in enumerate(alpha_personnel, start=1):
        row = [
            idx,
            safe(p.badge_number),
            safe(p.rank).upper(),
            safe(p.last_name).upper(),
            safe(p.first_name).upper(),
            safe(p.mi).upper(),
            safe(p.suffix).upper(),
            safe(p.badge_number).upper(),
            safe(p.contact_number),
            safe(p.unit).upper(),
            fmt_date(p.birthdate),
            safe(p.religion).upper(),
        ]
        for col_idx, val in enumerate(row, start=1):
            c = ws.cell(row=current_row, column=col_idx)
            c.value = val
            c.border = thin
            c.alignment = Alignment(horizontal='left', vertical='center')
        current_row += 1
    
    # Signatures
    current_row += 2
    write_signatures(ws, current_row, prepared_by_name, prepared_by_title, verified_by_name, verified_by_title, noted_by_name, noted_by_title)
    
    for i, w in enumerate([12, 14, 10, 18, 18, 12, 8, 12, 14, 14, 14, 14], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ============================================================
    # TAB 7: DISPOSITION OF TROOPS
    # ============================================================
    ws = wb.create_sheet(title=sheet_names[6])
    write_sheet_title(ws, sheet_names[6], 18)
    current_row = 5
    
    # Headers
    dispo_headers = ['No.', 'Badge No.', 'Rank', 'Last', 'First', 'Middle', 'Qualifier', 
                      'Date of Reassignment', 'Designation', 'Date of Designation',
                      'Mandatory Training', 'Specialized Training', 'Highest Eligibility',
                      'Contact Number', 'Birthdate', 'Religion']
    
    # Sections in order
    sections = [
        'OFFICE OF THE REGIONAL CHIEF',
        'ADMIN AND HRDD SECTION',
        'INTELLIGENCE SECTION',
        'INVESTIGATION SECTION',
        'OPERATION & PCR SECTION',
        'CAVITE',
        'LAGUNA',
        'BATANGAS',
        'RIZAL',
        'QUEZON'
    ]
    
    section_map = {
        'OFFICE OF THE REGIONAL CHIEF': 'Regional Office',
        'ADMIN AND HRDD SECTION': 'Admin and HRDD Section',
        'INTELLIGENCE SECTION': 'Intelligence Section',
        'INVESTIGATION SECTION': 'Investigation Section',
        'OPERATION & PCR SECTION': 'Operation & PCR Section',
    }
    
    grand_pco_act = 0
    grand_pnco_act = 0
    grand_nup_act = 0
    
    for section in sections:
        db_unit = section_map.get(section, section)
        
        # Get personnel for this section/unit
        if section in section_map:
            section_personnel = [p for p in all_personnel if (p.section or '') == db_unit]
        else:
            section_personnel = [p for p in all_personnel if (p.unit or '').upper() == db_unit.upper()]
        
        if not section_personnel:
            continue
        
        # Sort by rank
        section_personnel.sort(key=rank_sort_key)
        
        # Section header
        ws.cell(row=current_row, column=1).value = section
        ws.cell(row=current_row, column=1).font = Font(bold=True, size=11)
        ws.cell(row=current_row, column=1).fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(dispo_headers))
        current_row += 1
        
        # Section table headers
        for col_idx, col_name in enumerate(dispo_headers, start=1):
            c = ws.cell(row=current_row, column=col_idx)
            c.value = col_name
            c.font = Font(bold=True, color='FFFFFF')
            c.fill = header_fill
            c.border = thin
            c.alignment = Alignment(horizontal='center', vertical='center')
        current_row += 1
        
        # Get mandatory and specialized training titles
        for idx, p in enumerate(section_personnel, start=1):
            mandatory_titles = '; '.join([t.title for t in (p.trainings or []) if t.category == 'mandatory']) or ''
            specialized_titles = '; '.join([t.title for t in (p.trainings or []) if t.category == 'specialized']) or ''
            
            row = [
                idx,
                safe(p.badge_number),
                safe(p.rank).upper(),
                safe(p.last_name).upper(),
                safe(p.first_name).upper(),
                safe(p.mi).upper(),
                safe(p.suffix).upper(),
                fmt_date(p.date_of_reassignment),
                safe(p.designation),
                fmt_date(p.date_of_designation),
                mandatory_titles,
                specialized_titles,
                safe(p.highest_eligibility),
                safe(p.contact_number),
                fmt_date(p.birthdate),
                safe(p.religion).upper(),
            ]
            for col_idx, val in enumerate(row, start=1):
                c = ws.cell(row=current_row, column=col_idx)
                c.value = val
                c.border = thin
                c.alignment = Alignment(horizontal='left', vertical='center')
            current_row += 1
        
        # Count for summary
        pco_count = sum(1 for p in section_personnel if p.status and p.status.upper() == 'UP' and 
                       (p.rank or '').upper() in ['PCOL', 'PLTCOL', 'PMAJ', 'PCPT', 'PLT', 'PMGEN', 'PBGEN'])
        pnco_count = sum(1 for p in section_personnel if p.status and p.status.upper() == 'UP' and 
                        (p.rank or '').upper() in ['PEMS', 'PCMS', 'PSMS', 'PMSG', 'PSSG', 'PCPL', 'PAT'])
        nup_count = sum(1 for p in section_personnel if p.status and p.status.upper() == 'NUP')
        
        grand_pco_act += pco_count
        grand_pnco_act += pnco_count
        grand_nup_act += nup_count
        
        current_row += 1
    
    # Summary section at bottom
    ws.cell(row=current_row, column=1).value = 'SUMMARY'
    ws.cell(row=current_row, column=1).font = Font(bold=True, size=11)
    ws.cell(row=current_row, column=1).fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=4)
    current_row += 1
    
    # Summary headers
    sum_headers = ['', 'ACT', 'AUT', 'VAR']
    for col_idx, col_name in enumerate(sum_headers, start=1):
        c = ws.cell(row=current_row, column=col_idx)
        c.value = col_name
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = header_fill
        c.border = thin
    current_row += 1
    
    # Summary rows
    summary_data = [
        ('PCO', grand_pco_act, pco_aut_sub, grand_pco_act - pco_aut_sub),
        ('PNCO', grand_pnco_act, pnco_aut_sub, grand_pnco_act - pnco_aut_sub),
        ('NUP', grand_nup_act, nup_aut_val, grand_nup_act - nup_aut_val),
        ('TOTAL', grand_pco_act + grand_pnco_act + grand_nup_act, pco_aut_sub + pnco_aut_sub + nup_aut_val, 
         (grand_pco_act + grand_pnco_act + grand_nup_act) - (pco_aut_sub + pnco_aut_sub + nup_aut_val))
    ]
    
    for label, act, aut, var in summary_data:
        ws.cell(row=current_row, column=1).value = label
        ws.cell(row=current_row, column=1).font = Font(bold=True)
        ws.cell(row=current_row, column=2).value = act
        ws.cell(row=current_row, column=3).value = aut
        ws.cell(row=current_row, column=4).value = var
        for col in range(1, 5):
            ws.cell(row=current_row, column=col).border = thin
        current_row += 1
    
    current_row += 1
    
    # Signatures (Checked by instead of Verified Correct by)
    sig_row = current_row
    ws.cell(row=sig_row, column=1).value = 'Prepared by:'
    ws.cell(row=sig_row, column=1).font = Font(bold=True)
    ws.cell(row=sig_row+1, column=1).value = prepared_by_name or ''
    ws.cell(row=sig_row+2, column=1).value = prepared_by_title or ''
    
    ws.cell(row=sig_row, column=4).value = 'Checked by:'
    ws.cell(row=sig_row, column=4).font = Font(bold=True)
    ws.cell(row=sig_row+1, column=4).value = verified_by_name or ''
    ws.cell(row=sig_row+2, column=4).value = verified_by_title or ''
    
    ws.cell(row=sig_row, column=7).value = 'Noted by:'
    ws.cell(row=sig_row, column=7).font = Font(bold=True)
    ws.cell(row=sig_row+1, column=7).value = noted_by_name or ''
    ws.cell(row=sig_row+2, column=7).value = noted_by_title or ''
    
    for i, w in enumerate([8, 12, 10, 18, 18, 12, 10, 14, 18, 14, 20, 20, 18, 14, 14, 14], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ============================================================
    # TAB 8: PERSONNEL FILL-UP
    # ============================================================
    ws = wb.create_sheet(title=sheet_names[7])
    write_sheet_title(ws, sheet_names[7], 20)
    current_row = 5
    
    fillup_headers = ['', 'PCOL', 'PLTCOL', 'PMAJ', 'PCPT', 'PLT', 'TOTAL', 
                      'PEMS', 'PCMS', 'PSMS', 'PMSG', 'PSSG', 'PCPL', 'PAT', 'TOTAL',
                      'NUP', 'GRAND TOTAL']
    
    for col_idx, col_name in enumerate(fillup_headers, start=1):
        c = ws.cell(row=current_row, column=col_idx)
        c.value = col_name
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = header_fill
        c.border = thin
        c.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1
    
    fillup_units = ['Regional Office', 'Cavite', 'Laguna', 'Batangas', 'Rizal', 'Quezon', 'TOTAL']
    
    for fu in fillup_units:
        if fu == 'TOTAL':
            ws.cell(row=current_row, column=1).value = 'TOTAL'
            ws.cell(row=current_row, column=1).font = Font(bold=True)
            for col in range(2, 18):
                ws.cell(row=current_row, column=col).font = Font(bold=True)
                ws.cell(row=current_row, column=col).border = thin
            ws.cell(row=current_row, column=7).value = 0
            ws.cell(row=current_row, column=15).value = 0
            ws.cell(row=current_row, column=16).value = 0
            ws.cell(row=current_row, column=17).value = 0
        else:
            db_unit = fu.upper() if fu != 'Regional Office' else 'RHQ'
            unit_personnel = [p for p in all_personnel if (p.unit or '').upper() == db_unit]
            
            pco_counts = {r: sum(1 for p in unit_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == r) 
                         for r in ['PCOL', 'PLTCOL', 'PMAJ', 'PCPT', 'PLT']}
            pnco_counts = {r: sum(1 for p in unit_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == r) 
                          for r in ['PEMS', 'PCMS', 'PSMS', 'PMSG', 'PSSG', 'PCPL', 'PAT']}
            
            pco_total = sum(pco_counts.values())
            pnco_total = sum(pnco_counts.values())
            nup_total = sum(1 for p in unit_personnel if p.status and p.status.upper() == 'NUP')
            
    # Comment out problematic row_data.append - just skip storing for now
            # row_data.append({
            #     'pco_total': int(pco_total) if pco_total else 0, 
            #     'pnco_total': int(pnco_total) if pnco_total else 0, 
            #     'nup_total': int(nup_total) if nup_total else 0
            # })
            
            row = [fu] + [pco_counts[r] for r in ['PCOL', 'PLTCOL', 'PMAJ', 'PCPT', 'PLT']] + [pco_total] + \
                  [pnco_counts[r] for r in ['PEMS', 'PCMS', 'PSMS', 'PMSG', 'PSSG', 'PCPL', 'PAT']] + [pnco_total] + [nup_total, pco_total + pnco_total + nup_total]
            
            for col_idx, val in enumerate(row, start=1):
                c = ws.cell(row=current_row, column=col_idx)
                c.value = val
                c.border = thin
                c.alignment = Alignment(horizontal='center', vertical='center')
        
        current_row += 1
    
    # Signatures
    current_row += 1
    write_signatures(ws, current_row, prepared_by_name, prepared_by_title, verified_by_name, verified_by_title, noted_by_name, noted_by_title)
    
    for i, w in enumerate([16, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 10, 12], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ============================================================
    # TAB 9: KEY OFFICERS (only those with designation)
    # ============================================================
    ws = wb.create_sheet(title=sheet_names[8])
    write_sheet_title(ws, sheet_names[8], 6)
    current_row = 5
    
    kheaders = ['Designation', 'Authorized Rank', 'Rank and Name', 'Date of Designation', 'Contact Number']
    for col_idx, col_name in enumerate(kheaders, start=1):
        c = ws.cell(row=current_row, column=col_idx)
        c.value = col_name
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = header_fill
        c.border = thin
        c.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1
    
    # Only personnel with designation
    key_officers = [p for p in all_personnel if p.designation and p.designation.strip()]
    key_officers.sort(key=lambda x: (x.designation or '', x.last_name or '', x.first_name or ''))
    
    for p in key_officers:
        fullname = f"{safe(p.rank)} {safe(p.last_name)}, {safe(p.first_name)}"
        row = [
            safe(p.designation).upper(),
            safe(p.rank).upper(),
            fullname.upper(),
            fmt_date(p.date_of_designation),
            safe(p.contact_number),
        ]
        for col_idx, val in enumerate(row, start=1):
            c = ws.cell(row=current_row, column=col_idx)
            c.value = val
            c.border = thin
            c.alignment = Alignment(horizontal='left', vertical='center')
        current_row += 1
    
    # Signatures
    current_row += 2
    write_signatures(ws, current_row, prepared_by_name, prepared_by_title, verified_by_name, verified_by_title, noted_by_name, noted_by_title)
    
    for i, w in enumerate([25, 15, 30, 16, 14], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ============================================================
    # TAB 10: STATION LIST (only those with designation, sorted by rank)
    # ============================================================
    ws = wb.create_sheet(title=sheet_names[9])
    write_sheet_title(ws, sheet_names[9], 8)
    current_row = 5
    
    sl_headers = ['Badge Number', 'SCOMM', 'Rank', 'Last', 'First', 'MI', 'Qualifier', 'Date of Designation', 'Designation']
    for col_idx, col_name in enumerate(sl_headers, start=1):
        c = ws.cell(row=current_row, column=col_idx)
        c.value = col_name
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = header_fill
        c.border = thin
        c.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1
    
    # Only personnel with designation, sorted by rank
    station_list = [p for p in all_personnel if p.designation and p.designation.strip()]
    station_list.sort(key=rank_sort_key)
    
    for p in station_list:
        row = [
            safe(p.badge_number).upper(),
            safe(p.badge_number).upper(),
            safe(p.rank).upper(),
            safe(p.last_name).upper(),
            safe(p.first_name).upper(),
            safe(p.mi).upper(),
            safe(p.suffix).upper(),
            fmt_date(p.date_of_designation),
            safe(p.designation).upper(),
        ]
        for col_idx, val in enumerate(row, start=1):
            c = ws.cell(row=current_row, column=col_idx)
            c.value = val
            c.border = thin
            c.alignment = Alignment(horizontal='left', vertical='center')
        current_row += 1
    
    current_row += 1
    
    # Recapitulation
    ws.cell(row=current_row, column=1).value = 'RECAPITULATION'
    ws.cell(row=current_row, column=1).font = Font(bold=True, size=11)
    current_row += 1
    
    recapitulation = [
        ('PCOL', sum(1 for p in station_list if (p.rank or '').upper() == 'PCOL')),
        ('PLTCOL', sum(1 for p in station_list if (p.rank or '').upper() == 'PLTCOL')),
        ('PMAJ', sum(1 for p in station_list if (p.rank or '').upper() == 'PMAJ')),
        ('PCPT', sum(1 for p in station_list if (p.rank or '').upper() == 'PCPT')),
        ('PLT', sum(1 for p in station_list if (p.rank or '').upper() == 'PLT')),
        ('TOTAL', sum(1 for p in station_list if (p.rank or '').upper() in ['PCOL', 'PLTCOL', 'PMAJ', 'PCPT', 'PLT']))
    ]
    
    for label, count in recapitulation:
        ws.cell(row=current_row, column=1).value = label
        ws.cell(row=current_row, column=2).value = count
        if label == 'TOTAL':
            ws.cell(row=current_row, column=1).font = Font(bold=True)
            ws.cell(row=current_row, column=2).font = Font(bold=True)
        current_row += 1
    
    # Signatures
    current_row += 2
    write_signatures(ws, current_row, prepared_by_name, prepared_by_title, verified_by_name, verified_by_title, noted_by_name, noted_by_title)
    
    for i, w in enumerate([14, 14, 10, 18, 18, 8, 10, 16, 25], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ============================================================
    # TAB 11: RANK INVENTORY (simple summary)
    # ============================================================
    ws = wb.create_sheet(title=sheet_names[10])
    write_sheet_title(ws, sheet_names[10], 5)
    current_row = 5
    
    ws.cell(row=current_row, column=1).value = 'RFU'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=2).value = 'CIDG REGION 4A'
    ws.cell(row=current_row, column=2).font = Font(bold=True)
    current_row += 1
    
    ws.cell(row=current_row, column=1).value = 'Date'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=2).value = display_date
    current_row += 2
    
    # PCO Section
    ws.cell(row=current_row, column=1).value = 'PCO'
    ws.cell(row=current_row, column=1).font = Font(bold=True, size=12)
    ws.cell(row=current_row, column=1).fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
    current_row += 1
    
    pco_inv = [
        ('PCOL', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PCOL')),
        ('PLTCOL', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PLTCOL')),
        ('PMAJ', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PMAJ')),
        ('PCPT', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PCPT')),
        ('PLT', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PLT')),
    ]
    
    for rank, count in pco_inv:
        ws.cell(row=current_row, column=1).value = rank
        ws.cell(row=current_row, column=2).value = count
        current_row += 1
    
    pco_total = sum(c for _, c in pco_inv)
    ws.cell(row=current_row, column=1).value = 'Total'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=2).value = pco_total
    ws.cell(row=current_row, column=2).font = Font(bold=True)
    current_row += 2
    
    # PNCO Section
    ws.cell(row=current_row, column=1).value = 'PNCO'
    ws.cell(row=current_row, column=1).font = Font(bold=True, size=12)
    ws.cell(row=current_row, column=1).fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
    current_row += 1
    
    pnco_inv = [
        ('PEMS', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PEMS')),
        ('PCMS', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PCMS')),
        ('PSMS', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PSMS')),
        ('PMSG', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PMSG')),
        ('PSSG', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PSSG')),
        ('PCPL', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PCPL')),
        ('PAT', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PAT')),
    ]
    
    for rank, count in pnco_inv:
        ws.cell(row=current_row, column=1).value = rank
        ws.cell(row=current_row, column=2).value = count
        current_row += 1
    
    pnco_total = sum(c for _, c in pnco_inv)
    ws.cell(row=current_row, column=1).value = 'Total'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=2).value = pnco_total
    ws.cell(row=current_row, column=2).font = Font(bold=True)
    current_row += 2
    
    # NUP Section
    ws.cell(row=current_row, column=1).value = 'NUP'
    ws.cell(row=current_row, column=1).font = Font(bold=True, size=12)
    ws.cell(row=current_row, column=1).fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
    current_row += 1
    
    nup_total = sum(1 for p in all_personnel if p.status and p.status.upper() == 'NUP')
    ws.cell(row=current_row, column=1).value = 'NUP'
    ws.cell(row=current_row, column=2).value = nup_total
    current_row += 1
    
    ws.cell(row=current_row, column=1).value = 'Total'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=2).value = nup_total
    ws.cell(row=current_row, column=2).font = Font(bold=True)
    current_row += 2
    
    # Total Strength
    ws.cell(row=current_row, column=1).value = 'TOTAL STRENGTH'
    ws.cell(row=current_row, column=1).font = Font(bold=True, size=12)
    ws.cell(row=current_row, column=1).fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
    current_row += 1
    
    ws.cell(row=current_row, column=1).value = 'PCO Total'
    ws.cell(row=current_row, column=2).value = pco_total
    current_row += 1
    ws.cell(row=current_row, column=1).value = 'PNCO Total'
    ws.cell(row=current_row, column=2).value = pnco_total
    current_row += 1
    ws.cell(row=current_row, column=1).value = 'NUP Total'
    ws.cell(row=current_row, column=2).value = nup_total
    current_row += 1
    
    grand_total = pco_total + pnco_total + nup_total
    ws.cell(row=current_row, column=1).value = 'Grand Total'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=2).value = grand_total
    ws.cell(row=current_row, column=2).font = Font(bold=True)
    
    # No signatures for Rank Inventory
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 15

    # ============================================================
    # TAB 12: CIDG RFU4A LIST OF PCOs AND CONTACT NUMBERS
    # ============================================================
    ws = wb.create_sheet(title=sheet_names[11])
    write_sheet_title(ws, sheet_names[11], 10)
    current_row = 5
    
    pco_headers = ['Badge No.', 'SCOMM', 'Rank', 'Last', 'First', 'MI', 'Qualifier', 'Designation', 'Contact Number']
    for col_idx, col_name in enumerate(pco_headers, start=1):
        c = ws.cell(row=current_row, column=col_idx)
        c.value = col_name
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = header_fill
        c.border = thin
        c.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1
    
    # Group by office, then by rank
    pco_offices = ['Regional Office', 'Cavite PFU', 'Laguna PFU', 'Batangas PFU', 'Rizal PFU', 'Quezon PFU']
    office_map = {'RHQ': 'Regional Office', 'CAVITE': 'Cavite PFU', 'LAGUNA': 'Laguna PFU', 
                  'BATANGAS': 'Batangas PFU', 'RIZAL': 'Rizal PFU', 'QUEZON': 'Quezon PFU'}
    rev_office = {v: k for k, v in office_map.items()}
    
    for pco_office in pco_offices:
        db_unit = rev_office.get(pco_office, pco_office)
        
        # Get PCO personnel for this office
        office_pcos = [p for p in all_personnel if 
                      p.status and p.status.upper() == 'UP' and 
                      (p.unit or '').upper() == db_unit.upper() and
                      (p.rank or '').upper() in ['PCOL', 'PLTCOL', 'PMAJ', 'PCPT', 'PLT', 'PMGEN', 'PBGEN']]
        
        if not office_pcos:
            continue
        
        # Sort by rank
        office_pcos.sort(key=rank_sort_key)
        
        # Office header
        ws.cell(row=current_row, column=1).value = pco_office
        ws.cell(row=current_row, column=1).font = Font(bold=True, size=11)
        ws.cell(row=current_row, column=1).fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(pco_headers))
        current_row += 1
        
        for p in office_pcos:
            row = [
                safe(p.badge_number).upper(),
                safe(p.badge_number).upper(),
                safe(p.rank).upper(),
                safe(p.last_name).upper(),
                safe(p.first_name).upper(),
                safe(p.mi).upper(),
                safe(p.suffix).upper(),
                safe(p.designation).upper(),
                safe(p.contact_number),
            ]
            for col_idx, val in enumerate(row, start=1):
                c = ws.cell(row=current_row, column=col_idx)
                c.value = val
                c.border = thin
                c.alignment = Alignment(horizontal='left', vertical='center')
            current_row += 1
    
    # Signatures
    current_row += 1
    write_signatures(ws, current_row, prepared_by_name, prepared_by_title, verified_by_name, verified_by_title, noted_by_name, noted_by_title)
    
    for i, w in enumerate([14, 14, 10, 18, 18, 8, 10, 25, 16], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ============================================================
    # Finalize and return the workbook
    # ============================================================
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    safe_base = (file_name or 'form201_report').strip() or 'form201_report'
    return StreamingResponse(
        stream,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment;filename={safe_base}.xlsx"}
    )
    current_row = 5
    r_headers = ['Rank', 'No.', 'Badge Number', 'Last Name', 'First Name', 'MI', 'Unit']
    for col_idx, col_name in enumerate(r_headers, start=1):
        c = ws.cell(row=current_row, column=col_idx)
        c.value = col_name
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = header_fill
        c.border = thin
    current_row += 1
    ranks_sorted = sorted({(p.rank or 'N/A') for p in all_personnel})
    for r in ranks_sorted:
        members = [p for p in all_personnel if (p.rank or '').upper() == (r or '').upper()]
        for idx, p in enumerate(members, start=1):
            row = [r, idx, safe(p.badge_number), safe(p.last_name), safe(p.first_name), safe(p.mi), safe(p.unit)]
            for col_idx, val in enumerate(row, start=1):
                c = ws.cell(row=current_row, column=col_idx)
                c.value = val
                c.border = thin
            current_row += 1
    for i, w in enumerate([18,6,14,18,18,10,16], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ============================================================
    # TAB 11: RANK INVENTORY (simple summary)
    # ============================================================
    ws = wb.create_sheet(title=sheet_names[10])
    write_sheet_title(ws, sheet_names[10], 5)
    current_row = 5
    
    ws.cell(row=current_row, column=1).value = 'RFU'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=2).value = 'CIDG REGION 4A'
    ws.cell(row=current_row, column=2).font = Font(bold=True)
    current_row += 1
    
    ws.cell(row=current_row, column=1).value = 'Date'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=2).value = display_date
    current_row += 2
    
    # PCO Section
    ws.cell(row=current_row, column=1).value = 'PCO'
    ws.cell(row=current_row, column=1).font = Font(bold=True, size=12)
    ws.cell(row=current_row, column=1).fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
    current_row += 1
    
    pco_inv = [
        ('PCOL', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PCOL')),
        ('PLTCOL', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PLTCOL')),
        ('PMAJ', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PMAJ')),
        ('PCPT', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PCPT')),
        ('PLT', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PLT')),
    ]
    
    for rank, count in pco_inv:
        ws.cell(row=current_row, column=1).value = rank
        ws.cell(row=current_row, column=2).value = count
        current_row += 1
    
    pco_total = sum(c for _, c in pco_inv)
    ws.cell(row=current_row, column=1).value = 'Total'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=2).value = pco_total
    ws.cell(row=current_row, column=2).font = Font(bold=True)
    current_row += 2
    
    # PNCO Section
    ws.cell(row=current_row, column=1).value = 'PNCO'
    ws.cell(row=current_row, column=1).font = Font(bold=True, size=12)
    ws.cell(row=current_row, column=1).fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
    current_row += 1
    
    pnco_inv = [
        ('PEMS', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PEMS')),
        ('PCMS', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PCMS')),
        ('PSMS', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PSMS')),
        ('PMSG', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PMSG')),
        ('PSSG', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PSSG')),
        ('PCPL', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PCPL')),
        ('PAT', sum(1 for p in all_personnel if p.status and p.status.upper() == 'UP' and (p.rank or '').upper() == 'PAT')),
    ]
    
    for rank, count in pnco_inv:
        ws.cell(row=current_row, column=1).value = rank
        ws.cell(row=current_row, column=2).value = count
        current_row += 1
    
    pnco_total = sum(c for _, c in pnco_inv)
    ws.cell(row=current_row, column=1).value = 'Total'
    ws.cell(row=current_row, column=1).font = Font(bold=True)
    ws.cell(row=current_row, column=2).value = pnco_total
    ws.cell(row=current_row, column=2).font = Font(bold=True)
    current_row += 2
    
    # NUP Section
    ws.cell(row=current_row, column=1).value = 'NUP'
    ws.cell(row=current_row, column=1).font = Font(bold=True, size=12)
    ws.cell(row=current_row, column=1).fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
    current_row += 1
    
    nup_count = sum(1 for p in all_personnel if p.status and p.status.upper() == 'NUP')
    ws.cell(row=current_row, column=1).value = 'NUP'
    ws.cell(row=current_row, column=2).value = nup_count
    current_row += 2
    
    # Grand Total
    ws.cell(row=current_row, column=1).value = 'GRAND TOTAL'
    ws.cell(row=current_row, column=1).font = Font(bold=True, size=12)
    ws.cell(row=current_row, column=2).value = pco_total + pnco_total + nup_count
    ws.cell(row=current_row, column=2).font = Font(bold=True, size=12)
    
    # Note: No signatories for Rank Inventory
    for i, w in enumerate([20, 15], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ============================================================
    # TAB 12: CIDG RFU4A LIST OF PCOs AND CONTACT NUMBERS
    # Only PCO records, grouped by office, sorted by rank hierarchy
    # ============================================================
    ws = wb.create_sheet(title=sheet_names[11])
    write_sheet_title(ws, sheet_names[11], 8)
    current_row = 5
    
    # Headers
    pco_headers = ['Badge No.', 'SCOMM', 'Rank', 'Last', 'First', 'MI', 'Qualifier', 'Designation', 'Contact Number']
    for col_idx, col_name in enumerate(pco_headers, start=1):
        c = ws.cell(row=current_row, column=col_idx)
        c.value = col_name
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = header_fill
        c.border = thin
        c.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1
    
    # Define office order and mapping
    office_order = ['RFU4A HQS', 'CAVITE PFU', 'LAGUNA PFU', 'BATANGAS PFU', 'RIZAL PFU', 'QUEZON PFU']
    unit_to_office = {
        'RHQ': 'RFU4A HQS', 'CAVITE': 'CAVITE PFU', 'LAGUNA': 'LAGUNA PFU',
        'BATANGAS': 'BATANGAS PFU', 'RIZAL': 'RIZAL PFU', 'QUEZON': 'QUEZON PFU'
    }
    
    # PCO ranks to include
    pco_ranks = ['PMGEN', 'PBGEN', 'PCOL', 'PLTCOL', 'PMAJ', 'PCPT', 'PLT']
    
    # Group personnel by office
    for office_name in office_order:
        # Find matching unit
        db_unit = None
        for k, v in unit_to_office.items():
            if v == office_name:
                db_unit = k
                break
        
        if not db_unit:
            continue
            
        # Filter PCOs for this unit
        office_personnel = [
            p for p in all_personnel 
            if (p.unit or '').upper() == db_unit.upper()
            and p.status and p.status.upper() == 'UP'
            and (p.rank or '').upper() in pco_ranks
        ]
        
        if not office_personnel:
            continue
        
        # Sort by rank hierarchy
        office_personnel.sort(key=rank_sort_key)
        
        # Office header
        ws.cell(row=current_row, column=1).value = office_name
        ws.cell(row=current_row, column=1).font = Font(bold=True, size=11)
        ws.cell(row=current_row, column=1).fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(pco_headers))
        current_row += 1
        
        # Write personnel rows
        for p in office_personnel:
            row = [
                safe(p.badge_number).upper(),
                safe(p.badge_number).upper(),  # SCOMM = Badge No
                safe(p.rank).upper(),
                safe(p.last_name).upper(),
                safe(p.first_name).upper(),
                safe(p.mi).upper(),
                safe(p.suffix).upper(),
                safe(p.designation).upper() if p.designation else '',
                safe(p.contact_number),
            ]
            for col_idx, val in enumerate(row, start=1):
                c = ws.cell(row=current_row, column=col_idx)
                c.value = val
                c.border = thin
                c.alignment = Alignment(horizontal='left', vertical='center')
            current_row += 1
        
        current_row += 1  # Blank row between offices
    
    # Signatures
    current_row += 1
    write_signatures(ws, current_row, prepared_by_name, prepared_by_title, verified_by_name, verified_by_title, noted_by_name, noted_by_title)
    
    for i, w in enumerate([12, 12, 10, 18, 18, 8, 10, 20, 14], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # Finalize stream
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    safe_base = (file_name or 'form201_report').strip() or 'form201_report'
    return StreamingResponse(stream, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={"Content-Disposition": f"attachment;filename={safe_base}.xlsx"})


@router.post('/form201-pdf')
def generate_form201_pdf(
    unit: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    prepared_by: str = Form(''),
    noted_by: str = Form(''),
    file_name: str = Form('form201_report'),
    mask_birthdate: bool = Form(False),
    db: Session = Depends(get_db),
):
    """
    Generate a PDF Form 201 personnel master list grouped by sections.
    Columns (exact order): No., Badge No., Rank, Last Name, First Name, Middle Name, QLF,
    Date of Reassignment, Designation, Date of Designation, Mandatory Training,
    Specialized Course, Highest Eligibility, Contact Number, Birthdate, Religion
    """
    # Query personnel with filters
    query = db.query(models.Personnel)
    if unit and unit != 'All Units':
        query = query.filter(models.Personnel.unit == unit)
    if status and status != 'All Status':
        query = query.filter(models.Personnel.status == status)

    all_personnel = query.all()

    # Group by section in required order
    sections = ['Regional Office', 'Admin and HRDD Section', 'Intelligence Section']
    grouped = {s: [] for s in sections}
    # Those without a valid section go to Regional Office
    for p in all_personnel:
        key = p.section if p.section in sections else 'Regional Office'
        grouped.setdefault(key, []).append(p)

    # Build PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), leftMargin=18, rightMargin=18, topMargin=18, bottomMargin=18)
    elements = []
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle('H', parent=styles['Heading2'], alignment=TA_CENTER, fontSize=12, leading=14)
    small_bold = ParagraphStyle('SB', parent=styles['Normal'], fontSize=8, leading=10)
    normal_small = ParagraphStyle('NS', parent=styles['Normal'], fontSize=7, leading=9)

    # Title
    elements.append(Paragraph('CRIMINAL INVESTIGATION AND DETECTION GROUP REGION 4A', header_style))
    elements.append(Paragraph('FORM 201 PERSONNEL MASTER LIST', ParagraphStyle('sub', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10)))
    elements.append(Paragraph(f"(as of {datetime.utcnow().strftime('%B %d, %Y')})", ParagraphStyle('sub2', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8)))
    elements.append(Spacer(1, 12))

    col_headers = ['No.', 'Badge No.', 'Rank', 'Last Name', 'First Name', 'Middle Name', 'QLF', 'Date of Reassignment', 'Designation', 'Date of Designation', 'Mandatory Training', 'Specialized Course', 'Highest Eligibility', 'Contact Number', 'Birthdate', 'Religion']

    # Column widths (points) - tuned to fit landscape letter with margins
    total_width = landscape(letter)[0] - 36  # left+right margins
    # distribute widths, favoring name columns
    col_widths = [28, 64, 48, 84, 84, 40, 44, 60, 64, 60, 80, 80, 64, 64, 56, 44]

    for section in sections:
        persons = grouped.get(section, [])
        if not persons:
            continue

        # Section header
        sect_para = Paragraph(f'<b>SECTION: {section}</b>', ParagraphStyle('sect', parent=styles['Normal'], fontSize=10))
        elements.append(sect_para)
        elements.append(Spacer(1, 6))

        # Table data
        data = [col_headers]
        for idx, p in enumerate(persons, start=1):
            # compile mandatory and specialized training titles
            mandatory_titles = [t.title for t in (p.trainings or []) if t.category == 'mandatory']
            specialized_titles = [t.title for t in (p.trainings or []) if t.category == 'specialized']

            def safe(val):
                if val is None or (isinstance(val, str) and not val.strip()):
                    return 'N/A'
                return val

            # format dates
            def fmt_date(val):
                if not val:
                    return 'N/A'
                try:
                    return val.strftime('%Y-%m-%d')
                except Exception:
                    return str(val)

            birth = '########' if mask_birthdate and p.birthdate else (fmt_date(p.birthdate) if p.birthdate else 'N/A')

            row = [
                idx,
                safe(p.badge_number),
                safe(p.rank),
                safe(p.last_name),
                safe(p.first_name),
                safe(p.mi),
                safe(p.qlf),
                fmt_date(p.date_of_reassignment) if getattr(p, 'date_of_reassignment', None) else 'N/A',
                safe(p.designation),
                fmt_date(p.date_of_designation) if getattr(p, 'date_of_designation', None) else 'N/A',
                '; '.join(mandatory_titles) if mandatory_titles else 'N/A',
                '; '.join(specialized_titles) if specialized_titles else 'N/A',
                safe(p.highest_eligibility),
                safe(p.contact_number),
                birth,
                safe(p.religion),
            ]
            data.append(row)

        t = Table(data, colWidths=col_widths, repeatRows=1)
        style = TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,1), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ])
        t.setStyle(style)
        elements.append(t)
        elements.append(Spacer(1, 12))

    # Footer prepared/noted
    if prepared_by or noted_by:
        elements.append(Paragraph(f'Prepared by: {prepared_by}', ParagraphStyle('foot', parent=styles['Normal'], fontSize=9)))
        elements.append(Paragraph(f'Noted by: {noted_by}', ParagraphStyle('foot', parent=styles['Normal'], fontSize=9)))

    doc.build(elements)
    buffer.seek(0)
    output_name = (file_name or 'form201_report').strip() or 'form201_report'
    return StreamingResponse(buffer, media_type='application/pdf', headers={"Content-Disposition": f"attachment;filename={output_name}.pdf"})
