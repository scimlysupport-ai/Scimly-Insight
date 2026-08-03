from app.workers.tasks import process_large_file

print('task name', process_large_file.name)
print('task app broker', process_large_file.app.conf.broker_url)
print('task app result_backend', process_large_file.app.conf.result_backend)
print('task app default queue', process_large_file.app.conf.task_default_queue)
print('task app registered?', process_large_file.name in process_large_file.app.tasks)
print('app tasks sample', [k for k in process_large_file.app.tasks.keys() if 'process_large_file' in k])
