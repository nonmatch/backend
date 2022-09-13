from celery import Celery

from utils import get_env_variable
def make_celery(app_name=__name__):
    redis_uri = get_env_variable('REDIS_URI')
    return Celery(app_name, backend=redis_uri, broker=redis_uri)

celery = make_celery()