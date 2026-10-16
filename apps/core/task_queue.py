"""Django-Q2 task dispatch helpers.

Tasks are addressed by import path so the queue worker can execute them in a
separate process. Redis remains available for Channels, but is no longer a
Celery broker.
"""

from django_q.tasks import async_task


def enqueue_task(task, *args, **kwargs):
    """Queue a callable through Django-Q2 and return its task id."""
    task_path = f"{task.__module__}.{task.__name__}"
    return async_task(task_path, *args, **kwargs)
