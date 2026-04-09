from app.database import engine, Base, init_db
from app import models

# Create all tables from models
print("Initializing database tables from SQLAlchemy models...")
Base.metadata.create_all(bind=engine)
print("✓ Database tables created successfully!")

# Verify tables exist
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\nTables in database: {tables}")

# Verify personnel table has all columns
if 'personnel' in tables:
    columns = [col['name'] for col in inspector.get_columns('personnel')]
    print(f"\nPersonnel table columns: {columns}")
    
    required_cols = ['status_custom', 'nup_rank', 'nup_entry_number', 'section', 'birthdate', 'religion']
    for col in required_cols:
        if col in columns:
            print(f"  ✓ {col}")
        else:
            print(f"  ✗ MISSING: {col}")
