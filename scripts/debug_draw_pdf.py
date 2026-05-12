import importlib.util, pathlib, sys
backend_dir = str(pathlib.Path(__file__).resolve().parents[1] / 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
from app.database import SessionLocal
from app.api.bmi import draw_record_pdf_page
from app import models
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, letter
from io import BytesIO
import traceback

print('Opening DB session')
db = SessionLocal()
try:
    rec = db.query(models.BMIRecord).order_by(models.BMIRecord.id.asc()).first()
    if not rec:
        print('No BMIRecord found in DB')
    else:
        print('Found BMIRecord id', rec.id)
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=landscape(letter))
        try:
            draw_record_pdf_page(c, rec, db=db)
            c.showPage()
            c.save()
            print('PDF draw completed without exception')
        except Exception as e:
            print('Exception while drawing PDF:')
            traceback.print_exc()
finally:
    db.close()
