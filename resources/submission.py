from flask import request, jsonify
from flask_login import current_user
from flask_migrate import current
from flask_restful import Resource
from models.user import User
from repositories.audit import AuditRepository
from repositories.function import FunctionRepository
from repositories.submission import SubmissionRepository
from repositories.user import UserRepository
from schemas.submission import SubmissionSchema
from tools.fakeness_score import calculate_fakeness_score
from tools.find_nonmatching import calculate_score
from utils import error_message_response, error_response
import json
import logging

submissions_schema = SubmissionSchema(many=True)
submission_schema = SubmissionSchema()




class SubmissionResource(Resource):
    def get(self, submission: int):
        return submission_schema.dump(SubmissionRepository.get(submission))

    def delete(self, submission: int):
        subm = SubmissionRepository.get(submission)
        if not subm or subm.is_deleted:
            return error_message_response('Submission not found.')
        if current_user is None or not current_user.is_authenticated:
            return error_message_response('Not logged in.')
        if subm.owner != current_user.id:
            return error_message_response('This submission does not belong to you.')
        AuditRepository.create(current_user.id, f'Deleted submission {submission}')
        SubmissionRepository.delete(subm)
        return 'ok'

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

            fakeness_score = calculate_fakeness_score(data['code'])
            if score == 0 and fakeness_score < func.best_fakeness_score:
                func.best_fakeness_score = fakeness_score

            submission = SubmissionRepository.create(
                function, owner, data['code'], score, data['is_equivalent'], data['parent'], data['compiled'], data['comments'], fakeness_score)
            FunctionRepository.set_has_equivalent_try(function, SubmissionRepository.has_equivalent_submission(function))
            return submission, 200
        except Exception as e:
            return error_response(e)

class LatestSubmissionsResource(Resource):
    def get(self):
        return submissions_schema.dump(SubmissionRepository.get_latest())

class EquivalentResource(Resource):
    def post(self, submission: int):
        data = request.get_json()
        if data is None:
            return error_message_response('Invalid request')
        try:
            if current_user is None or not current_user.is_authenticated:
                return error_message_response('Not logged in.')
            subm = SubmissionRepository.get(submission)
            if not subm:
                return error_message_response('Submission does not exist.')
            is_equivalent = data['is_equivalent'] == 'true'
            AuditRepository.create(current_user.id, f'Set submission {submission} to equivalent: {is_equivalent}')
            SubmissionRepository.set_equivalent(subm, is_equivalent)
            FunctionRepository.set_has_equivalent_try(subm.function, SubmissionRepository.has_equivalent_submission(subm.function))
            return 'ok'
        except Exception as e:
            return error_response(e)