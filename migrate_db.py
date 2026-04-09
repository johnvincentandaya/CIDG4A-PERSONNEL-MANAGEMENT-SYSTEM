from sqlalchemy import create_engine, text
from pathlib import Path

# Use absolute path to the database
db_path = Path("c:/Users/John Vincent Andaya/Desktop/CIDG DMS/CIDG4A-PERSONNEL-MANAGEMENT-SYSTEM/cidg_dev.db")
print(f"Database path: {db_path}")

engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})

with engine.connect() as conn:
    # Add missing columns
    try:
        conn.execute(text('ALTER TABLE personnel ADD COLUMN status_custom STRING'))
        conn.commit()
        print('✓ Added status_custom column')
    except Exception as e:
        print(f'  status_custom: {e}')
    
    try:
        conn.execute(text('ALTER TABLE personnel ADD COLUMN nup_rank STRING'))
        conn.commit()
        print('✓ Added nup_rank column')
    except Exception as e:
        print(f'  nup_rank: {e}')
    
    try:
        conn.execute(text('ALTER TABLE personnel ADD COLUMN nup_entry_number INTEGER'))
        conn.commit()
        print('✓ Added nup_entry_number column')
    except Exception as e:
        print(f'  nup_entry_number: {e}')
    
    try:
        conn.execute(text('ALTER TABLE personnel ADD COLUMN section STRING'))
        conn.commit()
        print('✓ Added section column')
    except Exception as e:
        print(f'  section: {e}')
        
print('\nMigration complete!')
