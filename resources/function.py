from flask_restful import Resource
from repositories.function import FunctionRepository
from schemas.function import FunctionSchema

functions_schema = FunctionSchema(many=True)
function_schema = FunctionSchema()


class FunctionList(Resource):
    def get(self):
        functions = FunctionRepository.get_all()
        return functions_schema.dump(functions), 200


class AsmFunctionList(Resource):
    def get(self):
        functions = FunctionRepository.get_all_asm()
        return functions_schema.dump(functions), 200


class FunctionResource(Resource):
    def get(self, function):
        return function_schema.dump(FunctionRepository.get(function))
