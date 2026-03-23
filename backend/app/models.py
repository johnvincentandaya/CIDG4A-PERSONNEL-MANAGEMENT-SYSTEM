from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import os
from pathlib import Path
from .database import Base

class Personnel(Base):
    __tablename__ = 'personnel'
    id = Column(Integer, primary_key=True, index=True)
    rank = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    mi = Column(String, nullable=True)
    suffix = Column(String, nullable=True)
    unit = Column(String, nullable=False)
    status = Column(String, nullable=False)
    date_added = Column(DateTime, default=datetime.utcnow)
    documents = relationship('Document', back_populates='personnel', cascade='all, delete')
    trainings = relationship('TrainingCertificate', back_populates='personnel', cascade='all, delete')
    bmi_records = relationship('BMIRecord', back_populates='personnel', cascade='all, delete')

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey('personnel.id'))
    doc_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    personnel = relationship('Personnel', back_populates='documents')

    @property
    def file_name(self):
        return os.path.basename(self.file_path or "") or None

    @property
    def file_type(self):
        _, ext = os.path.splitext(self.file_path or "")
        return ext.lstrip('.').upper() if ext else None

    @property
    def upload_date(self):
        if not self.file_path:
            return None
        abs_path = Path(self.file_path)
        if not abs_path.is_absolute():
            abs_path = Path(__file__).resolve().parents[2] / self.file_path
        if abs_path.exists():
            return datetime.fromtimestamp(abs_path.stat().st_mtime)
        return None

    @property
    def file_url(self):
        return self.file_path

class TrainingCertificate(Base):
    __tablename__ = 'training_certificates'
    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey('personnel.id'))
    category = Column(String, nullable=False)  # mandatory or specialized
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    personnel = relationship('Personnel', back_populates='trainings')

class BMIRecord(Base):
    __tablename__ = 'bmi_records'
    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey('personnel.id'))
    rank = Column(String)
    name = Column(String)
    unit = Column(String)
    age = Column(Integer)
    sex = Column(String)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    waist_cm = Column(Float)
    hip_cm = Column(Float)
    wrist_cm = Column(Float)
    date_taken = Column(DateTime, default=datetime.utcnow)
    bmi = Column(Float)
    classification = Column(String)
    result = Column(String)
    photo_front = Column(String)
    photo_left = Column(String)
    photo_right = Column(String)
    monthly_weights = relationship('MonthlyWeight', back_populates='bmi_record', cascade='all, delete')
    personnel = relationship('Personnel', back_populates='bmi_records')

class MonthlyWeight(Base):
    __tablename__ = 'monthly_weights'
    id = Column(Integer, primary_key=True, index=True)
    bmi_record_id = Column(Integer, ForeignKey('bmi_records.id'))
    year = Column(Integer)
    month = Column(Integer)
    weight = Column(Float)
    bmi_record = relationship('BMIRecord', back_populates='monthly_weights')
