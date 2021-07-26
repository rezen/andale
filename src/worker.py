import os
import time 
from random import randrange
from celery import Celery, group, chain
from celery.result import AsyncResult, GroupResult
import backend

# https://github.com/celery/celery/blob/e2031688284484d5b5a57ba29cd9cae2d9a81e39/celery/app/base.py#L141
# https://stackoverflow.com/questions/15159394/how-to-monitor-events-from-workers-in-a-celery-django-application
# event - task-succeeded
Celery.backend_cls = 'backend.Backend'
app = Celery(
  broker=os.environ['CELERY_BROKER_URL'], 
  include=('tasks',),
  backend='backend.Backend',
)


@app.task(bind=True, name='test')  
def test(self, val): 
    length = randrange(12)
    print("STart", length) 
    time.sleep(length)
    print("End", length)
    return val



@app.task(bind=True, name='refresh', send_events=True)  
def refresh(self, urls):
    print("STARTTTTt......")
    job = group([test.s(u) for u in urls])
    result = job.apply_async()
    print(f"==== Before join ... {result.id}")
    last_count = 0
    while result.waiting():
        if result.completed_count() == last_count:
            time.sleep(0.1)
            continue

        last_count = result.completed_count()
        print(f" ==== > completed {last_count}")
        self.update_state(state='PROGRESS', meta={'completed': last_count})
        self.send_event('things', retry=True, retry_policy=None, progress={'completed': last_count})

    print(f"==== After join... {result.id}")
    return result.join()


app.conf.beat_schedule = {
  'refresh': {
    'task': 'refresh',
    'schedule': float(os.environ['NEWSPAPER_SCHEDULE']),
    'args': (os.environ['NEWSPAPER_URLS'].split(','),)
  },
}

# my_monitor(app)
