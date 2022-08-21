from flask_restful import Resource
from flask import request, abort
from repositories.audit import AuditRepository
from schemas.audit import AuditSchema
from utils import error_message_response, error_response, get_env_variable
from flask_login import current_user

audits_schema = AuditSchema(many=True)

class AuditResource(Resource):
    def post(self):
        data = request.json()
        if data is None:
            return error_message_response('Invalid request')
        try:
            user = None
            if current_user is not None and current_user.is_authenticated:
                user = current_user.id
            AuditRepository.create(user, data['text'])
            return 'ok'
        except Exception as e:
            return error_response(e)

    def get(self):
        if current_user is None or not current_user.is_authenticated or current_user.id != int(get_env_variable('ADMIN_USER')):
            abort(404)
        return audits_schema.dump(AuditRepository.get_latest())