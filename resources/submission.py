from flask import request, jsonify
from flask_login import current_user
from flask_migrate import current
from flask_restful import Resource
from models.user import User
from repositories.function import FunctionRepository
from repositories.submission import SubmissionRepository
from repositories.user import UserRepository
from schemas.submission import SubmissionSchema
from tools.find_nonmatching import calculate_score
from utils import error_message_response, error_response
import json
import logging

submissions_schema = SubmissionSchema(many=True)
submission_schema = SubmissionSchema()




class SubmissionResource(Resource):
    def get(self, submission: int):
        return submission_schema.dump(SubmissionRepository.get(submission))


class FunctionSubmissions(Resource):
    def get(self, function: int):
        return submissions_schema.dump(SubmissionRepository.get_for_function(function)), 200

    def post(self, function: int):
        data = request.get_json()
        if data is None:
            return error_message_response('Invalid request')

        try:
            owner = None
            if current_user is not None and current_user.is_authenticated:
                # If this are the details of the current user, use them
                if current_user.username == data['username'] and current_user.email == data['email']:
                    owner = current_user.id

            if owner is None and data['username'] is not None and data['username'] != '':
                user = UserRepository.get_by_name_and_email(
                    username=data['username'], email=data['email'])
                if user is None:
                    # Need to create this user
                    user = UserRepository.create_anonymous(
                        username=data['username'], email=data['email'])

                owner = user.id

            # Change the best_score of the function if this one is better
            func = FunctionRepository.get_internal(int(function))

            compiled = json.loads(data['compiled'])
            compiled_asm = ''
            separator = ''
            for line in compiled['asm']:
                compiled_asm += separator + line['text']
                separator = '\n'

            # Calculate the score on the server
            score = calculate_score(func.asm, compiled_asm)

            if score < func.best_score:
                func.best_score = score
            if score == 0:
                func.is_matched = True
            if not func.has_code_try:
                func.has_code_try = True

            submission = SubmissionRepository.create(
                function, owner, data['code'], score, data['is_equivalent'], data['parent'], data['compiled'], data['comments'])
            return submission, 200
        except Exception as e:
            return error_response(e)

class LatestSubmissionsResource(Resource):
    def get(self):
        return submissions_schema.dump(SubmissionRepository.get_latest())