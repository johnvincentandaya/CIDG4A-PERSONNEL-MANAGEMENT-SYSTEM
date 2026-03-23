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

router = APIRouter()

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
    last_name: str = Form(...),
    first_name: str = Form(...),
    mi: Optional[str] = Form(None),
    suffix: Optional[str] = Form(None),
    unit: str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Create a personnel record without requiring any documents.
    Documents and trainings can be attached later via the update endpoint.
    """
    p = models.Personnel(
        rank=rank,
        last_name=last_name,
        first_name=first_name,
        mi=mi,
        suffix=suffix,
        unit=unit,
        status=status,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.post("/", response_model=schemas.PersonnelSchema)
async def create_personnel(
    rank: str = Form(...),
    last_name: str = Form(...),
    first_name: str = Form(...),
    mi: Optional[str] = Form(None),
    suffix: Optional[str] = Form(None),
    unit: str = Form(...),
    status: str = Form(...),
    # single-file documents (now optional so record can be saved even if incomplete)
    pds: Optional[UploadFile] = File(None),
    appointment: Optional[UploadFile] = File(None),
    promotion: Optional[UploadFile] = File(None),
    designation: Optional[UploadFile] = File(None),
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

    # create personnel entry
    p = models.Personnel(
        rank=rank,
        last_name=last_name,
        first_name=first_name,
        mi=mi,
        suffix=suffix,
        unit=unit,
        status=status,
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
        dest_name = f"FORM201_{last_name}_{first_name}_{shortname}{ext}"
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
    await save_single(designation, "designation")
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
            dest_name = f"FORM201_{last_name}_{first_name}_mandatory_{safe_title}{ext}"
            dest_path_abs = os.path.join(str(person_folder_abs), dest_name)
            with open(dest_path_abs, "wb") as out:
                out.write(content)
            norm_path = f"{person_folder_rel}/{dest_name}".replace("\\", "/")
            tc = models.TrainingCertificate(
                personnel_id=p.id,
                category="mandatory",
                title=title or safe_title,
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
            dest_name = f"FORM201_{last_name}_{first_name}_specialized_{safe_title}{ext}"
            dest_path_abs = os.path.join(str(person_folder_abs), dest_name)
            with open(dest_path_abs, "wb") as out:
                out.write(content)
            norm_path = f"{person_folder_rel}/{dest_name}".replace("\\", "/")
            tc = models.TrainingCertificate(
                personnel_id=p.id,
                category="specialized",
                title=title or safe_title,
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
    last_name: str = Form(...),
    first_name: str = Form(...),
    mi: Optional[str] = Form(None),
    suffix: Optional[str] = Form(None),
    unit: str = Form(...),
    status: str = Form(...),
    # optional replacement single files
    pds: Optional[UploadFile] = File(None),
    appointment: Optional[UploadFile] = File(None),
    promotion: Optional[UploadFile] = File(None),
    designation: Optional[UploadFile] = File(None),
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
    person.rank = rank
    person.last_name = last_name
    person.first_name = first_name
    person.mi = mi
    person.suffix = suffix
    person.unit = unit
    person.status = status
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
        dest_name = f"FORM201_{last_name}_{first_name}_{shortname}{ext}"
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
    await replace_single(designation, 'designation')
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
            dest_name = f"FORM201_{last_name}_{first_name}_mandatory_{safe_title}{ext}"
            dest_path_abs = os.path.join(str(person_folder_abs), dest_name)
            with open(dest_path_abs, 'wb') as out:
                out.write(content)
            norm_path = f"{person_folder_rel}/{dest_name}".replace("\\", "/")
            tc = models.TrainingCertificate(personnel_id=person.id, category='mandatory', title=title or safe_title, file_path=norm_path)
            db.add(tc)

    if specialized_files:
        for idx, f in enumerate(specialized_files):
            title = ''
            if specialized_titles and idx < len(specialized_titles):
                title = specialized_titles[idx]
            safe_title = title.replace(' ', '_') if title else f'specialized_new_{idx+1}'
            ext, content = await read_and_validate_upload(f)
            dest_name = f"FORM201_{last_name}_{first_name}_specialized_{safe_title}{ext}"
            dest_path_abs = os.path.join(str(person_folder_abs), dest_name)
            with open(dest_path_abs, 'wb') as out:
                out.write(content)
            norm_path = f"{person_folder_rel}/{dest_name}".replace("\\", "/")
            tc = models.TrainingCertificate(personnel_id=person.id, category='specialized', title=title or safe_title, file_path=norm_path)
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
def personnel_report(unit: Optional[str] = Form(None), status: Optional[str] = Form(None), report_type: str = Form('excel'), db: Session = Depends(get_db)):
    q = db.query(models.Personnel)
    if unit and unit != 'All Units':
        q = q.filter(models.Personnel.unit == unit)
    if status and status != 'All Status':
        q = q.filter(models.Personnel.status == status)
    records = q.order_by(models.Personnel.last_name).all()
    # generate excel
    wb = Workbook()
    ws = wb.active
    ws.title = 'Form201 Report'
    headers = ['Rank','Last Name','First Name','Middle Initial','Suffix','Unit','Status','Document Completion Status','Date Added']
    ws.append(headers)
    expected_docs = 13
    for p in records:
        doc_count = len(p.documents or [])
        completion = f"{doc_count}/{expected_docs}"
        row = [p.rank, p.last_name, p.first_name, p.mi or '', p.suffix or '', p.unit, p.status, completion, p.date_added.strftime('%Y-%m-%d') if p.date_added else '']
        ws.append(row)
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return StreamingResponse(stream, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={"Content-Disposition":"attachment;filename=form201_report.xlsx"})
