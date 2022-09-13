from flask import request, abort
from flask_dance.contrib.github import github
from flask_login import current_user
from flask_restful import Resource
from models import db
from models.function import Function
from models.pr import Pr
from models.user import User
from repositories.function import FunctionRepository
from repositories.pr import PrRepository
from repositories.submission import SubmissionRepository
from subprocess import check_call, check_output
from schemas.pr import PrSchema
from tasks.pr_task import pr_task
from tools.find_nonmatching import split_code, store_code
from tools.lock import GIT_LOCK, obtain_lock, release_lock
from utils import error_message_response, error_response
import logging
import os

TMC_REPO = os.getenv('TMC_REPO')
PR_URL = os.getenv('PR_URL')

pr_schema = PrSchema()

class PrResource(Resource):
    def get(self):
        if current_user is None or not current_user.is_authenticated or current_user.id != int(os.getenv('ADMIN_USER')):
            abort(404)
        return 'ok'

    def post(self):
        try:
            data = request.get_json()
            if data is None:
                return error_message_response('Invalid request.')

            if current_user is None or not current_user.is_authenticated:
                return error_message_response('Need to be logged in to create PR.')

            if not github.authorized:
                return error_message_response('Not correctly logged into GitHub.')

            if data['title'] == '':
                return error_message_response('Need to enter a title.')

            if len(data['selected']) == 0:
                return error_message_response('Need to submit at least one submission.')

            submissions = []
            functions = []
            # Check that all submissions have a score of zero and that they have not been submitted yet
            for id in data['selected']:
                submission = SubmissionRepository.get(id)
                if submission is None:
                    return error_message_response(f'Could not find submission with id {id}.')
                submissions.append(submission)
                function = FunctionRepository.get_internal(submission.function)
                if function is None:
                    return error_message_response(f'Could not find function with id {submission.function}.')
                functions.append(function)
                if submission.score != 0:
                    return error_message_response(f'Submission for function {function.name} has a score of {submission.score}.')
                if function.is_submitted:
                    return error_message_response(f'A Pull Request for function {function.name} was already submitted.')

            pr = Pr(title=data['title'], text=data['text'], creator=current_user.id,
                    functions=', '.join(map(lambda x: str(x), data['selected'])))
            db.session.add(pr)
            db.session.commit()

            pr_task.delay(pr.id)
            return {'id': pr.id}
        except Exception as e:
            return error_response(e)

class PrStatusResource(Resource):
    def get(self, id: int):
        return pr_schema.dump(PrRepository.get(id))