from flask import request, abort
from flask_dance.contrib.github import github
from flask_login import current_user
from flask_restful import Resource
from models import db
from models.function import Function
from models.pr import Pr
from models.user import User
from repositories.function import FunctionRepository
from repositories.submission import SubmissionRepository
from subprocess import check_call, check_output
from tools.find_nonmatching import split_code, store_code
from utils import error_message_response, error_response
import logging
import os

TMC_REPO = os.getenv('TMC_REPO')
PR_URL = os.getenv('PR_URL')


class PrResource(Resource):
    def get(self):
        if current_user is None or not current_user.is_authenticated or current_user.id != int(os.getenv('ADMIN_USER')):
            abort(404)
        return 'ok'

    def post(self):
        try:
            data = request.get_json()
            if data is None:
                return error_message_response('Invalid request')

            if current_user is None or not current_user.is_authenticated:
                return error_message_response('Need to be logged in to create PR')

            if not github.authorized:
                return error_message_response('Not correctly logged into GitHub')

            if data['title'] == '':
                return error_message_response('Need to enter a title')

            submissions = []
            functions = []
            # Check that all submissions have a score of zero and that they have not been submitted yet
            for id in data['selected']:
                submission = SubmissionRepository.get(id)
                if submission is None:
                    return error_message_response(f'Could not find submission with id {id}')
                submissions.append(submission)
                function = FunctionRepository.get(submission.function)
                if function is None:
                    return error_message_response(f'Could not find function with id {submission.function}')
                functions.append(function)
                if submission.score != 0:
                    return error_message_response(f'Submission for function {function.name} has a score of {submission.score}')
                if function.is_submitted:
                    return error_message_response(f'A Pull Request for function {function.name} was already submitted')

            pr = Pr(title=data['title'], text=data['text'], creator=current_user.id,
                    functions=', '.join(map(lambda x: str(x), data['selected'])))
            db.session.add(pr)
            db.session.commit()

            branch = f'patch-{pr.id}'
            # Set up the commit in the git repository
            check_call(['git', 'checkout', 'master'], cwd=TMC_REPO)
            check_call(['git', 'pull', 'upstream', 'master'], cwd=TMC_REPO)
            check_call(['git', 'checkout', '-b', branch], cwd=TMC_REPO)

            for i in range(len(submissions)):
                submission = submissions[i]
                function = functions[i]
                username = 'anonymous'
                email = ''
                if submission.owner is not None and submission.owner != 0:
                    user = User.query.with_entities(User.username, User.email).filter_by(
                        id=submission.owner).first_or_404()
                    if user is not None:
                        username = user.username
                        email = user.email
                    else:
                        logging.error(f'Could not find user {user}')

                # Write the code to the file
                (includes, header, src) = split_code(submission.code)
                (err, msg) = store_code(function.name,
                                        includes, header, src, submission.score == 0)
                if err:
                    return error_message_response(msg)

                check_call(['git', 'config', 'user.name',
                           username], cwd=TMC_REPO)
                check_call(
                    ['git', 'config', 'user.email', email], cwd=TMC_REPO)

                # Format to avoid
                check_call(['../format.sh'], cwd=TMC_REPO)

                check_call(['git', 'add', '.'], cwd=TMC_REPO)
                # TODO remove allow empty?
                check_call(
                    ['git', 'commit', '-m', f'Match {function.name}', '--allow-empty'], cwd=TMC_REPO)

            check_call(['git', 'push', '-u', 'origin',
                       branch, '-f'], cwd=TMC_REPO)

            arguments = {
                'title': data['title'],
                'head': f'nonmatch:{branch}',
                'base': 'master',
                # Only the nonmatch user can grant modifying, see https://github.com/backstrokeapp/server/issues/46#issuecomment-272597511
                'maintainer_can_modify': False,
            }

            if 'text' in data and data['text'] != '':
                arguments['body'] = data['text']
            res = github.post(PR_URL, json=arguments)

            data = res.json()
            if 'message' in data:
                logging.error(data)
                return error_message_response(data['message'])

            for function in functions:
                function.is_submitted = True

            pr.url = data['html_url']
            pr.functions = ', '.join(map(lambda f: f.name, functions))
            db.session.commit()

            return {'url': data['html_url']}
        except Exception as e:
            return error_response(e)
