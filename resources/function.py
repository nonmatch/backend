from flask import request
from flask_login import current_user
from flask_restful import Resource
from repositories.function import FunctionRepository
from schemas.function import FunctionSchema
from tools.find_nonmatching import get_headers_code
from utils import error_message_response, error_response

functions_schema = FunctionSchema(many=True)
function_schema = FunctionSchema()


class FunctionList(Resource):
    def get(self):
        functions = FunctionRepository.get_nonmatch()
        return functions_schema.dump(functions), 200

class AllFunctionList(Resource):
    def get(self):
        functions = FunctionRepository.get_all()
        return functions_schema.dump(functions), 200


class AsmFunctionList(Resource):
    def get(self):
        functions = FunctionRepository.get_all_asm()
        return functions_schema.dump(functions), 200

class WithCodeFunctionList(Resource):
    def get(self):
        functions = FunctionRepository.get_all_with_code()
        return functions_schema.dump(functions), 200

class WithoutCodeFunctionList(Resource):
    def get(self):
        functions = FunctionRepository.get_all_without_code()
        return functions_schema.dump(functions), 200


class FunctionResource(Resource):
    def get(self, function):
        return function_schema.dump(FunctionRepository.get(function))

class FunctionHeadersResource(Resource):
    def get(self, function):
        try:
            return {
                'code': get_headers_code(FunctionRepository.get(function).name)
            }
        except Exception as e:
            return error_response(e)

class FunctionDecompMeResource(Resource):
    def post(self, function):
        func = FunctionRepository.get_internal(function)
        if func.decomp_me_scratch:
            return error_message_response('Function has already exported to decomp.me')
        json = request.get_json(silent=True)
        FunctionRepository.set_decomp_me_scratch(func, json['slug'])
        return 'ok'

class FunctionLockResource(Resource):
    def post(self, function):
        func = FunctionRepository.get_internal(function)
        if current_user is None or not current_user.is_authenticated:
            return error_message_response('Not logged in.')

        if func.locked_by or func.is_matched or func.deleted or func.is_submitted:
            return error_message_response(f'Function {func.name} is already locked.')

        FunctionRepository.lock(func, current_user.id)
        return 'ok'

class FunctionUnlockResource(Resource):
    def post(self, function):
        func = FunctionRepository.get_internal(function)
        if current_user is None or not current_user.is_authenticated:
            return error_message_response('Not logged in.')

        if not func.locked_by or func.is_matched or func.deleted or func.is_submitted:
            return error_message_response(f'Function {func.name} is not locked.')

        if func.locked_by != current_user.id:
            return error_message_response(f'Function {func.name} is not locked by you.')

        FunctionRepository.unlock(func)
        return 'ok'