import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.session import SessionLocal
from app.models.file import UploadedFile
from app.models.dataset import Dataset
from app.config import settings
import redis

session = SessionLocal()
file_record = session.query(UploadedFile).filter(UploadedFile.id == 37).first()
print('file_record:', None if not file_record else {
    'id': file_record.id,
    'status': file_record.status,
    'size_bytes': file_record.size_bytes,
    'stored_filename': file_record.stored_filename,
})
dataset = session.query(Dataset).filter(Dataset.file_id == 37).first()
print('dataset:', None if not dataset else {
    'file_id': dataset.file_id,
    'rows': dataset.rows,
    'columns': dataset.columns,
})

r = redis.Redis.from_url(settings.REDIS_URL)
val = r.get('scimly:progress:37')
print('redis_progress:', None if val is None else val.decode())
