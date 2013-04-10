import os

DEBUG = True
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
STATIC_PATH = os.path.join(PROJECT_PATH, 'static')
MEDIA_PATH = os.path.join(PROJECT_PATH, 'static', 'media')

CELERY_IMPORTS = ("carpenter.tasks", )
