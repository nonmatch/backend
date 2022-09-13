import logging
import os
from subprocess import check_call
from models.pr import Pr
from repositories.function import FunctionRepository
from tools.lock import GIT_LOCK, obtain_lock, release_lock
from . import celery
from repositories.submission import SubmissionRepository
from time import sleep
from models import db
from models.user import OAuth, User
from tools.find_nonmatching import split_code, store_code
from flask_dance.contrib.github import github
from flask import current_app
from flask_socketio import SocketIO
import requests

GITHUB_API = 'https://api.github.com'

# Prevents the created branch from being pushed and the PR from being created.
# Instead a mock url is returned.
MOCK_PR_CREATION = False

@celery.task(name='pr', bind=True)
def pr_task(self, pr_id):
    TMC_REPO = os.getenv('TMC_REPO')
    PR_URL = os.getenv('PR_URL')



    socketio = SocketIO(message_queue=current_app.config['REDIS_URI'])

    pr = Pr.query.get(pr_id)
    if pr is None:
        raise Exception(f'PR with id {pr_id} not found.')

    status = []
    submissions = []
    functions = []
    for id in pr.functions.split(','):
        submission = SubmissionRepository.get(id)
        if submission is None:
            raise Exception(f'Submission {id} not found')
        submissions.append(submission)
        function = FunctionRepository.get_internal(submission.function)
        if function is None:
            raise Exception(f'Could not find function with id {submission.function}.')
        functions.append(function)
        status.append({
            'id': submission.id,
            'name': function.name,
            'edited': False,
            'formatted': False,
            'commited': False
        })
        print(submission)

    def emit_status(message: str, process: float):
        socketio.emit('status', {
            'pr': pr_id,
            'message': message,
            'progress': process,
            'submissions': status
        })

    emit_status('Starting task to generate pull request...', 0.1)
    obtained_lock = False
    try:
        while not obtained_lock:
            obtained_lock = obtain_lock(db.session, GIT_LOCK , 1)
            if not obtained_lock:
                emit_status('Waiting for git repo lock...', 0.1)
                print(f'Another git operation is in progress. Waiting for a minute.')
                sleep(60)

        emit_status('Checking out current state of the repo...', 0.1)

        branch = f'patch-{pr.id}'
        # Set up the commit in the git repository
        check_call(['git', 'checkout', 'master'], cwd=TMC_REPO)
        check_call(['git', 'reset', '--hard', 'HEAD'], cwd=TMC_REPO)
        check_call(['git', 'pull', 'upstream', 'master'], cwd=TMC_REPO)
        check_call(['git', 'checkout', '-b', branch], cwd=TMC_REPO)

        submission_count = len(submissions)
        def calculate_progress(i: int, offset: int) -> float:
            # Progress from 0.2 to 0.8
            # With three steps for each submission
            step = i * 3 + offset
            percentage = step / (3 * submission_count)
            return 0.6 * percentage + 0.2

        for i in range(submission_count):
            submission = submissions[i]
            function = functions[i]
            step_name = f'Creating commit for {function.name}...'

            emit_status(step_name, calculate_progress(i, 0))

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
                raise Exception(msg)

            status[i]['edited'] = True
            emit_status(step_name, calculate_progress(i, 1))

            check_call(['git', 'config', 'user.name',
                    username], cwd=TMC_REPO)
            check_call(
                ['git', 'config', 'user.email', email], cwd=TMC_REPO)

            # Format to avoid
            check_call(['../format.sh'], cwd=TMC_REPO)

            status[i]['formatted'] = True
            emit_status(step_name, calculate_progress(i, 2))

            check_call(['git', 'add', '.'], cwd=TMC_REPO)
            # TODO remove allow empty?
            check_call(
                ['git', 'commit', '-m', f'Match {function.name}', '--allow-empty'], cwd=TMC_REPO)

            status[i]['commited'] = True


        emit_status('Pushing code...', 0.8)

        if MOCK_PR_CREATION:
            url = 'https://MOCK_DONE_URL'
            pr.url = url
            pr.is_submitted = True
            db.session.commit()

            emit_status('Submitted pull request.', 1)
            socketio.emit('finish', {
                'pr': pr_id,
                'url': url
            })

            return {'url': url}

        check_call(['git', 'push', '-u', 'origin',
                branch, '-f'], cwd=TMC_REPO)

        emit_status('Submitting pull request...', 0.9)

        arguments = {
            'title': pr.title,
            'head': f'nonmatch:{branch}',
            'base': 'master',
            # Only the nonmatch user can grant modifying, see https://github.com/backstrokeapp/server/issues/46#issuecomment-272597511
            'maintainer_can_modify': False,
        }

        if pr.text and pr.text != '':
            arguments['body'] = pr.text


        # Manually get the token for the creator of the PR.
        token = OAuth.query.filter_by(user_id=pr.creator).one().token['access_token']

        res = requests.post(GITHUB_API + PR_URL, json=arguments, headers={'Authorization': 'Bearer ' + token})

        data = res.json()
        if 'message' in data:
            logging.error(data)
            raise Exception('GitHub Pull Request creation failed: ' + data['message'])

        emit_status('Submitted pull request.', 1)

        for function in functions:
            function.is_submitted = True

        url = data['html_url']
        pr.url = url
        pr.is_submitted = True
        db.session.commit()

        socketio.emit('finish', {
            'pr': pr_id,
            'url': url
        })
        return {'url': url}
    except Exception as e:
        socketio.emit('error', {
            'pr': pr_id,
            'message': str(e),
        })
        pr.is_error = True
        pr.error = str(e)
        db.session.commit()
        raise e
    finally:
        if obtained_lock:
            release_lock(db.session, GIT_LOCK, 1)