import logging
import os

from flask.json import jsonify
import traceback

ENV = os.getenv('ENV')

def get_env_variable(name) -> str:
    try:
        return os.environ[name]
    except KeyError:
        message = 'Expected environment variable "{}" not set.'.format(name)
        raise Exception(message)


def error_response(e: Exception):
    logging.exception(e)
    traceback.print_tb(e.__traceback__)
    if ENV == 'production':
        response = jsonify(message= "Internal error")
    else:
        response = jsonify(message = f"{e.__class__.__name__}: {e}")
    response.status_code = 500
    return response

def error_message_response(message: str):
    logging.error(f'Error message: {message}')
    response = jsonify(message=message)
    response.status_code = 400
    return response