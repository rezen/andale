import os
import time
from random import randrange
from celery import Celery, group, chain
from celery.result import AsyncResult, GroupResult
from celery.events import EventReceiver
from celery.events.state import State
import backend

# https://github.com/celery/celery/blob/e2031688284484d5b5a57ba29cd9cae2d9a81e39/celery/app/base.py#L141
# https://stackoverflow.com/questions/15159394/how-to-monitor-events-from-workers-in-a-celery-django-application
# event - task-succeeded
Celery.backend_cls = "backend.Backend"
app = Celery(
    broker=os.environ["CELERY_BROKER_URL"],
    include=("tasks",),
    backend="backend.Backend",
)


def my_monitor(app):
    state = app.events.State()

    def announce_failed_tasks(event):
        if event["type"] != "things":
            return

        print(event)
        """
    nonlocal state
    state.event(event)
    task = state.tasks.get(event['uuid'])
    print(task)
    """

        # print('task-progress: %s[%s] %s' % (
        #    task.name, task.uuid, task.info(),))

    with app.connection() as connection:
        print("CAPTURE")
        recv = EventReceiver(connection, handlers={"*": announce_failed_tasks}, app=app)
        recv.capture(limit=None, timeout=None, wakeup=True)


my_monitor(app)
