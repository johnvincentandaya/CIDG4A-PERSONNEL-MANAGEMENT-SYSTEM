from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import SessionLocal, init_db
from ..utils import ensure_upload_folders, personnel_folder_name
import os
from datetime import datetime

router = APIRouter()

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

    # save uploaded files into structured folder and record them
    person_folder = os.path.join('uploads', 'form_201', personnel_folder_name(first_name, last_name))
    os.makedirs(person_folder, exist_ok=True)

    async def save_single(file_obj: Optional[UploadFile], shortname: str):
        if not file_obj:
            return
        ext = os.path.splitext(file_obj.filename)[1] or '.pdf'
        dest_name = f"FORM201_{first_name}_{last_name}_{shortname}{ext}"
        dest_path = os.path.join(person_folder, dest_name)
        content = await file_obj.read()
        with open(dest_path, 'wb') as out:
            out.write(content)
        norm_path = dest_path.replace('\\','/')
        doc = models.Document(personnel_id=p.id, doc_type=shortname, file_path=norm_path)
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
            ext = os.path.splitext(f.filename)[1] or ".pdf"
            dest_name = f"FORM201_{first_name}_{last_name}_mandatory_{safe_title}{ext}"
            dest_path = os.path.join(person_folder, dest_name)
            content = await f.read()
            with open(dest_path, "wb") as out:
                out.write(content)
            norm_path = dest_path.replace("\\", "/")
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
            ext = os.path.splitext(f.filename)[1] or ".pdf"
            dest_name = f"FORM201_{first_name}_{last_name}_specialized_{safe_title}{ext}"
            dest_path = os.path.join(person_folder, dest_name)
            content = await f.read()
            with open(dest_path, "wb") as out:
                out.write(content)
            norm_path = dest_path.replace("\\", "/")
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
    # trainings: deletions and additions
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

    # person folder
    person_folder = os.path.join('uploads', 'form_201', personnel_folder_name(first_name, last_name))
    os.makedirs(person_folder, exist_ok=True)

    # helper to replace or create document
    async def replace_single(file_obj: UploadFile, shortname: str):
        if not file_obj:
            return
        ext = os.path.splitext(file_obj.filename)[1] or '.pdf'
        dest_name = f"FORM201_{first_name}_{last_name}_{shortname}{ext}"
        dest_path = os.path.join(person_folder, dest_name)
        content = await file_obj.read()
        with open(dest_path, 'wb') as out:
            out.write(content)
        norm_path = dest_path.replace('\\','/')
        # check existing doc
        doc = db.query(models.Document).filter(models.Document.personnel_id==person.id, models.Document.doc_type==shortname).first()
        if doc:
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

    # handle deletions of trainings
    import json
    if delete_mandatory_ids:
        try:
            ids = json.loads(delete_mandatory_ids)
            for iid in ids:
                t = db.query(models.TrainingCertificate).filter(models.TrainingCertificate.id==iid, models.TrainingCertificate.personnel_id==person.id).first()
                if t:
                    # remove file
                    try:
                        if t.file_path and os.path.exists(t.file_path):
                            os.remove(t.file_path)
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
                        if t.file_path and os.path.exists(t.file_path):
                            os.remove(t.file_path)
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
            ext = os.path.splitext(f.filename)[1] or '.pdf'
            dest_name = f"FORM201_{first_name}_{last_name}_mandatory_{safe_title}{ext}"
            dest_path = os.path.join(person_folder, dest_name)
            content = await f.read()
            with open(dest_path, 'wb') as out:
                out.write(content)
            norm_path = dest_path.replace('\\','/')
            tc = models.TrainingCertificate(personnel_id=person.id, category='mandatory', title=title or safe_title, file_path=norm_path)
            db.add(tc)

    if specialized_files:
        for idx, f in enumerate(specialized_files):
            title = ''
            if specialized_titles and idx < len(specialized_titles):
                title = specialized_titles[idx]
            safe_title = title.replace(' ', '_') if title else f'specialized_new_{idx+1}'
            ext = os.path.splitext(f.filename)[1] or '.pdf'
            dest_name = f"FORM201_{first_name}_{last_name}_specialized_{safe_title}{ext}"
            dest_path = os.path.join(person_folder, dest_name)
            content = await f.read()
            with open(dest_path, 'wb') as out:
                out.write(content)
            norm_path = dest_path.replace('\\','/')
            tc = models.TrainingCertificate(personnel_id=person.id, category='specialized', title=title or safe_title, file_path=norm_path)
            db.add(tc)

    db.commit()
    db.refresh(person)
    return person
