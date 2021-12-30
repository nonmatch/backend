from flask_restful import Resource
from repositories.submission import SubmissionRepository
from flask import request, jsonify
import os
from schemas.submission import SubmissionSchema
from flask_login import current_user

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
            SubmissionRepository.create(function, owner, code, score, is_equivalent, parent)
        except Exception as e:
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
        json = request.get_json(silent=True)
        print(json)
        try:
            if not current_user.is_authenticated:
                owner = None
            owner = current_user.id
            submission = SubmissionRepository.create(function, owner, json['code'], json['score'], json['is_equivalent'], json['parent'])
            return submission, 200
        except Exception as e:
            print('GOT EXCEPTION')
            print(e)
            response = jsonify(e.to_dict())
            response.status_code = e.status_code
            return response