import os
import importlib.util
import datetime
import pathlib
from fastapi.testclient import TestClient

main_path = pathlib.Path(__file__).resolve().parents[1] / 'backend' / 'main.py'
spec = importlib.util.spec_from_file_location('backend_main', str(main_path))
mod = importlib.util.module_from_spec(spec)
# Ensure backend/app is importable as 'app' by adding backend folder to sys.path
import sys
backend_dir = str(main_path.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
# Disable auth for test client runs
os.environ['AUTH_DISABLED'] = '1'

spec.loader.exec_module(mod)
app = mod.app
# import app and DB utilities

# initialize DB and session
from app.database import init_db, SessionLocal
from app import models

init_db()

# seed minimal personnel and BMI record
db = SessionLocal()
try:
    # clear existing small set to avoid duplicates in repeated runs (safe for dev)
    # (Do not drop tables) remove persons with last_name TESTAUTO
    existing = db.query(models.Personnel).filter(models.Personnel.last_name == 'TESTAUTO').all()
    for e in existing:
        db.delete(e)
    db.commit()

    from datetime import datetime
    p = models.Personnel(
        rank='PMGEN',
        badge_number='TEST123',
        last_name='TESTAUTO',
        first_name='SEED',
        mi='',
        suffix='',
        unit='RHQ',
        qlf='',
        birthdate=datetime(1990,1,1),
        religion='NONE',
        status='Active'
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    # add BMI record
    dt = datetime.utcnow()
    rec = models.BMIRecord(
        personnel_id=p.id,
        rank=p.rank,
        name=f"{p.first_name} {p.last_name}",
        unit=p.unit,
        age=36,
        sex='Male',
        height_cm=170.0,
        weight_kg=85.0,
        waist_cm=90.0,
        hip_cm=95.0,
        wrist_cm=18.0,
        date_taken=dt,
        bmi=None,
        classification=None,
        result=None,
        status='Active',
        is_latest=True,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    print('Seeded personnel id', p.id, 'bmi id', rec.id)

finally:
    db.close()

client = TestClient(app)

# call personnel report
print('Requesting personnel report...')
resp = client.post('/api/personnel/report', data={'report_type':'excel','file_name':'test_form201'})
print('personnel report status', resp.status_code)
ct = resp.headers.get('content-disposition')
print('personnel disposition', ct)
if resp.status_code == 200:
    open('scripts/test_form201.xlsx','wb').write(resp.content)
    print('Saved scripts/test_form201.xlsx')

# call bmi report
print('Requesting bmi report...')
m = dt.month
y = dt.year
resp2 = client.post('/api/bmi/report', data={'month': str(m), 'year': str(y), 'report_type':'excel','file_name':'test_bmi','unit':'RHQ'})
print('bmi report status', resp2.status_code)
print('bmi disposition', resp2.headers.get('content-disposition'))
if resp2.status_code == 200:
    open('scripts/test_bmi.xlsx','wb').write(resp2.content)
    print('Saved scripts/test_bmi.xlsx')

print('Done')
