#!/bin/bash
#waitress-serve --port 5000 --call 'app:create_app'
gunicorn -b :5000 app:app 