
from flask_restful import Resource
from flask import Response, request
import requests

CEXPLORE_HOST='http://127.0.0.1:10240'

def proxy_forward(url: str) -> Response:
        resp=requests.request(
        method=request.method,
        url=url,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                if name.lower() not in excluded_headers]

        response = Response(resp.content, resp.status_code, headers)
        return response

class CompileResource(Resource):
    def post(self):
        return proxy_forward(CEXPLORE_HOST+'/api/compiler/agbpyccC/compile')

class PycatResource(Resource):
    def post(self):
        return proxy_forward(CEXPLORE_HOST+'/api/compiler/agbpycc/compile')