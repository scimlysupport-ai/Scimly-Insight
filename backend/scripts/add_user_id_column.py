from sqlalchemy import text
from app.database.session import engine

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS user_id integer"))
    conn.commit()
print('ALTER TABLE executed')
