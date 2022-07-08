
from flask_restful import Resource
from flask import Response, request
import requests

from utils import get_env_variable

#CEXPLORE_HOST='http://192.168.0.178:10240'
#CEXPLORE_HOST='https://cexplore.henny022.eu.ngrok.io'

def proxy_forward(url: str) -> Response:

    json = request.get_json()
    if get_env_variable('PROXY_NEW_FORMAT') == 'true':
        json['options']['libraries'].append(
            {
                'id': 'tmc',
                'version': 'master'
            }
        )

    resp=requests.request(
    method=request.method,
    url=url,
    headers={key: value for (key, value) in request.headers if key != 'Host'},
    json=json,
    cookies=request.cookies,
    allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
            if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response

class CompileResource(Resource):
    def post(self):
        return proxy_forward(get_env_variable('PROXY_COMPILE_URL'))

class PycatResource(Resource):
    def post(self):
        return proxy_forward(get_env_variable('PROXY_CAT_URL'))
