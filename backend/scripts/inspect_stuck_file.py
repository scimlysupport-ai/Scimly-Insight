import os
from app.database.session import SessionLocal
from app.models.file import UploadedFile
from app.models.dataset import Dataset
from app.services.progress_service import get_progress

file_id = 46
print('QUERY file', file_id)

db = SessionLocal()
try:
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if file_record:
        print('file', file_record.id, file_record.status, file_record.stored_filename, file_record.size_bytes)
    else:
        print('file record not found')
    dataset = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if dataset:
        print('dataset', dataset.id, dataset.rows, dataset.columns)
    else:
        print('dataset record missing')
finally:
    db.close()

print('progress', get_progress(file_id))
