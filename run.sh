#!/bin/bash
#waitress-serve --port 5000 --call 'app:create_app'
venv/bin/gunicorn -b :5000 app:app  --timeout 500
