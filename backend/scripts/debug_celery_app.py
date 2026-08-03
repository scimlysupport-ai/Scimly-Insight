from app.workers.celery_app import app

print('broker_url=', app.conf.broker_url)
print('result_backend=', app.conf.result_backend)
print('task_default_queue=', app.conf.task_default_queue)
print('task_acks_late=', app.conf.task_acks_late)
print('task_serializer=', app.conf.task_serializer)
print('accept_content=', app.conf.accept_content)
print('include=', app.conf.include)
print('queues=', app.conf.task_queues)
print('registered=', app.tasks.keys())
