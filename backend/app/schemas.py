from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DocumentSchema(BaseModel):
    id: int
    doc_type: str
    file_path: str
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
    last_name: str
    first_name: str
    mi: Optional[str] = None
    suffix: Optional[str] = None
    unit: str
    status: str

class PersonnelSchema(BaseModel):
    id: int
    rank: str
    last_name: str
    first_name: str
    mi: Optional[str]
    suffix: Optional[str]
    unit: str
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
    class Config:
        orm_mode = True
