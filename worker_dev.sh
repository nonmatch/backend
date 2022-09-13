#!/bin/bash
watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A app.celery worker --concurrency=1 --loglevel=INFO