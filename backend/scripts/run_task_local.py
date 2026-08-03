from app.workers.tasks import process_large_file

print('running process_large_file synchronously for id=37')
res = process_large_file.__wrapped__(None, 37)
print('result:', res)
