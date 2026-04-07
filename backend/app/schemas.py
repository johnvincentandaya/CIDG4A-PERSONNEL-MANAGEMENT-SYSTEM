from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DocumentSchema(BaseModel):
    id: int
    doc_type: str
    file_path: str
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    upload_date: Optional[datetime] = None
    file_url: Optional[str] = None
    class Config:
        orm_mode = True

class TrainingCertificateSchema(BaseModel):
    id: int
    category: str
    title: str
    file_path: str
    class Config:
        orm_mode = True

class PersonnelCreate(BaseModel):
    rank: str
    badge_number: str
    last_name: str
    first_name: str
    mi: Optional[str] = None
    suffix: Optional[str] = None
    unit: str
    status: str

    # Optional Form201 fields
    qlf: Optional[str] = None
    date_of_reassignment: Optional[datetime] = None
    designation: Optional[str] = None
    date_of_designation: Optional[datetime] = None
    highest_eligibility: Optional[str] = None
    contact_number: Optional[str] = None
    birthdate: Optional[datetime] = None
    religion: Optional[str] = None
    section: Optional[str] = None

class PersonnelSchema(BaseModel):
    id: int
    rank: str
    badge_number: Optional[str]
    last_name: str
    first_name: str
    mi: Optional[str]
    suffix: Optional[str]
    unit: str
    qlf: Optional[str]
    date_of_reassignment: Optional[datetime]
    designation: Optional[str]
    date_of_designation: Optional[datetime]
    highest_eligibility: Optional[str]
    contact_number: Optional[str]
    birthdate: Optional[datetime]
    religion: Optional[str]
    section: Optional[str]
    status: str
    date_added: datetime
    documents: List[DocumentSchema] = []
    trainings: List[TrainingCertificateSchema] = []
    class Config:
        orm_mode = True

class BMICreate(BaseModel):
    rank: str
    name: str
    unit: str
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    waist_cm: Optional[float] = None
    hip_cm: Optional[float] = None
    wrist_cm: Optional[float] = None
    date_taken: Optional[datetime] = None

class BMISchema(BaseModel):
    id: int
    personnel_id: Optional[int] = None
    rank: str
    name: str
    unit: str
    age: int
    sex: Optional[str]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    waist_cm: Optional[float]
    hip_cm: Optional[float]
    wrist_cm: Optional[float]
    date_taken: Optional[datetime]
    bmi: Optional[float]
    classification: Optional[str]
    result: Optional[str]
    photo_front: Optional[str]
    photo_left: Optional[str]
    photo_right: Optional[str]
    is_latest: Optional[bool] = True
    class Config:
        from_attributes = True


class BMIHistorySchema(BaseModel):
    """Schema for BMI history response with personnel info"""
    personnel_id: Optional[int] = None
    personnel_name: Optional[str] = None
    personnel_rank: Optional[str] = None
    personnel_unit: Optional[str] = None
    latest_bmi: Optional[BMISchema] = None
    history: List[BMISchema] = []


class BMITimelineSchema(BaseModel):
    """Schema for BMI timeline data for charts"""
    date_taken: Optional[datetime]
    bmi: Optional[float]
    classification: Optional[str]
    weight_kg: Optional[float]
    class Config:
        from_attributes = True
