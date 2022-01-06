from flask_restful import Resource
from repositories.function import FunctionRepository
from repositories.submission import SubmissionRepository
from flask import request, jsonify
import os
from schemas.submission import SubmissionSchema
from flask_login import current_user
import json

from tools.find_nonmatching import calculate_score

submissions_schema = SubmissionSchema(many=True)
submission_schema = SubmissionSchema()

class SubmissionList(Resource):
    def get(self):
        return 'TODO', 404

    def post(self):
        '''Create a new submission'''
        json = request.get_json(silent=True)
        try:
            function: int = json['function']
            owner: int = json['int']
            code: str = json['code']
            score: int = json['score']
            is_equivalent: bool = json['is_equivalent']
            parent: int = json.get('parent', 0)
            compiled: str = json['compiled']
            SubmissionRepository.create(function, owner, code, score, is_equivalent, parent, compiled)
        except Exception as e:
            print(e)
            response = jsonify(e.to_dict())
            response.status_code = e.status_code
            return response


class SubmissionResource(Resource):
    def get(self, submission: int):
        return submission_schema.dump(SubmissionRepository.get(submission))

class FunctionSubmissions(Resource):
    def get(self, function: int):
        return submissions_schema.dump(SubmissionRepository.get_for_function(function)), 200

    def post(self, function: int):
        data = request.get_json(silent=True)
        try:
            if not current_user.is_authenticated:
                owner = None
            owner = current_user.id

            # Change the best_score of the function if this one is better
            func = FunctionRepository.get(int(function))

            compiled = json.loads(data['compiled'])
            compiled_asm = ''
            separator = ''
            for line in compiled['asm']:
                compiled_asm += separator + line['text']
                separator ='\n'

            # Calculate the score on the server
            score = calculate_score(func.asm, compiled_asm)

            if score < func.best_score:
                func.best_score = score
    
            submission = SubmissionRepository.create(function, owner, data['code'], score, data['is_equivalent'], data['parent'], data['compiled'])
            return submission, 200
        except Exception as e:
            print('GOT EXCEPTION')
            print(e)
            response = jsonify(e.to_dict())
            response.status_code = e.status_code
            return response