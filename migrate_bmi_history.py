from sqlalchemy import create_engine, text
from pathlib import Path

# Use absolute path to the database (backend directory)
db_path = Path("backend/cidg_dev.db")
print(f"Database path: {db_path.absolute()}")

engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})

with engine.connect() as conn:
    # Create bmi_history table
    try:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS bmi_history (
                id INTEGER PRIMARY KEY,
                personnel_id INTEGER,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                weight REAL NOT NULL,
                bmi_result REAL NOT NULL,
                bmi_classification TEXT NOT NULL,
                waist REAL,
                hip REAL,
                wrist REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (personnel_id) REFERENCES personnel(id)
            )
        '''))
        conn.commit()
        print('SUCCESS: Created bmi_history table')
    except Exception as e:
        print(f'  bmi_history table creation error: {e}')

    # Add personnel_id to existing bmi_records if not exists
    try:
        conn.execute(text('ALTER TABLE bmi_records ADD COLUMN personnel_id INTEGER REFERENCES personnel(id)'))
        conn.commit()
        print('SUCCESS: Added personnel_id column to bmi_records')
    except Exception as e:
        print(f'  personnel_id column: {e}')

    # Migrate existing BMI data to history table
    try:
        # Insert existing BMI records into history table
        conn.execute(text('''
            INSERT INTO bmi_history (personnel_id, month, year, weight, bmi_result, bmi_classification, waist, hip, wrist, created_at)
            SELECT
                br.personnel_id,
                CAST(strftime('%m', br.date_taken) AS INTEGER) as month,
                CAST(strftime('%Y', br.date_taken) AS INTEGER) as year,
                br.weight_kg,
                br.bmi,
                br.classification,
                br.waist_cm,
                br.hip_cm,
                br.wrist_cm,
                br.date_taken
            FROM bmi_records br
            WHERE br.date_taken IS NOT NULL
        '''))
        conn.commit()
        print('SUCCESS: Migrated existing BMI data to history table')
    except Exception as e:
        print(f'  Migration error: {e}')

    # Update personnel_id in bmi_records based on name matching
    try:
        conn.execute(text('''
            UPDATE bmi_records
            SET personnel_id = (
                SELECT p.id
                FROM personnel p
                WHERE UPPER(TRIM(p.first_name || ' ' || p.last_name)) = UPPER(TRIM(bmi_records.name))
                LIMIT 1
            )
            WHERE personnel_id IS NULL
        '''))
        conn.commit()
        print('SUCCESS: Updated personnel_id in bmi_records based on name matching')
    except Exception as e:
        print(f'  personnel_id update error: {e}')

print('\nBMI history migration complete!')