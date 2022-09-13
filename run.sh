#!/bin/bash
#waitress-serve --port 5000 --call 'app:create_app'
venv/bin/gunicorn -b :5000 app:app -w 1 --threads 100 --timeout 500
