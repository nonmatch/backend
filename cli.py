from models import db
from models.function import Function
from models.submission import Submission
from models.user import User
from repositories.function import FunctionRepository
from repositories.submission import SubmissionRepository
from sqlalchemy.sql.expression import desc
from subprocess import check_call
from tools.fakeness_score import calculate_fakeness_score
from tools.find_nonmatching import extract_USA_asm, get_code, get_symbols, update_nonmatching_functions
import click
import os
import requests
import sys
from flask import current_app

from tools.lock import GIT_LOCK, with_lock
from utils import get_env_variable

def create_cli(app):
    @app.cli.command('create-function')
    @click.argument('name')
    @click.argument('file')
    @click.argument('size')
    @click.argument('asm')
    def create_function(name, file, size, asm):
        # TODO move to FunctionRepository
        function = Function(name=name, file=file, size=size, asm=asm)
        db.session.add(function)
        db.session.commit()

    @app.cli.command('create-user')
    @click.argument('name')
    @click.argument('email')
    @click.argument('avatar')
    def create_user(name, email, avatar):
        user = User(username=name, avatar=avatar, email=email)
        db.session.add(user)
        db.session.commit()

    @app.cli.command('update-nonmatch')
    def update_nonmatch():
        update_nonmatching_functions()
        print('done')

    TMC_REPO = os.getenv('TMC_REPO')
    @app.cli.command('cron')
    def cron():
        with_lock(db.session, perform_cron, fail_cron, GIT_LOCK)

    def perform_cron():
        check_call(['git', 'checkout', 'master'], cwd=TMC_REPO)
        check_call(['git', 'reset', '--hard', 'HEAD'], cwd=TMC_REPO)
        check_call(['git', 'pull', 'upstream', 'master'], cwd=TMC_REPO)
        check_call(['git', 'checkout', 'nonmatch'], cwd=TMC_REPO)
        check_call(['git', 'rebase', 'master'], cwd=TMC_REPO)
        check_call(['make', '-j'], cwd=TMC_REPO)

        #update_nonmatching_functions()
        print('done')

    def fail_cron():
        print('Could not acquire git lock.')
        sys.exit(1)

    @app.cli.command('update-asm')
    @click.argument('func')
    def update_asm(func):
        function = FunctionRepository.get_by_name_internal(func)
        if function is None:
            print(f'Function {func} not found')
            sys.exit(1)
        update_asm_for_func(function)
        print('done')

    def update_asm_for_func(function: Function):
        symbols = get_symbols()
        (err, asm, src, signature) = get_code(function.name, True, symbols)
        if err:
            print(asm, file=sys.stderr)
            sys.exit(1)


        asm = extract_USA_asm(asm)
        # Run pycat.py on the asm code
        res = requests.post(current_app.config['PYCAT_URL'], asm)
        asm = res.text.rstrip()
        if asm.startswith('#'):
            # Remove Compiler Explorer comment
            asm = asm.split('\n', 1)[1]
        function.asm = asm
        db.session.commit()


    @app.cli.command('update-all-asm')
    def update_all_asm():
        functions = Function.query.filter_by(
            deleted=False, is_submitted=False
        ).all()

        for func in functions:
            print(f'{func.name}...')
            update_asm_for_func(func)
        print('all done')

    @app.cli.command('asm-errors')
    def find_asm_errors():
        print('\nFunctions with errors in asm:\n')
#        functions = Function.query.with_entities(Function.id, Function.name, Function.is_asm_func).filter(Function.asm.like('%error%')).all()
        functions = Function.query.filter(Function.asm.like('%Compiler Explorer%')).all()


        for func in functions:
            print(f'{func.id}\t{"a" if func.is_asm_func else "n"} {func.name}')
#            update_asm_for_func(func)

    @app.cli.command('decomp-me')
    def find_decomp_me_matched():
        functions = Function.query.filter_by(
            deleted=False, is_submitted=False, is_matched=False, decomp_me_matched=False
        ).filter(Function.decomp_me_scratch.isnot(None)).all()
        for func in functions:
            #DECOMP_ME_BACKEND = 'http://localhost:8000/api'
            DECOMP_ME_BACKEND = 'https://decomp.me/api'
            print(f'Check family of {func.decomp_me_scratch}')
            res = requests.get(DECOMP_ME_BACKEND + '/scratch/' + func.decomp_me_scratch + '/family')
            for scratch in res.json():
                if scratch['score'] == 0:
                    print('Matched')
                    func.decomp_me_matched = True
                    db.session.commit()
                    break
        print('done')

    @app.cli.command('add-decomp-me')
    @click.argument('func')
    @click.argument('slug')
    def add_decomp_me(func, slug):
        function = FunctionRepository.get_by_name_internal(func)
        if function is None:
            print(f'Function {func} not found')
            sys.exit(1)
        function.decomp_me_scratch = slug
        db.session.commit()
        print('done')
# Find functions with error in asm
# nonmatch=# SELECT id from function where asm like '%error%';
# nonmatch=# SELECT name,is_asm_func from "function" where asm like '%error%';


    @app.cli.command('add-interop')
    @click.argument('func')
    def add_interop(func):
        function = FunctionRepository.get_by_name_internal(func)
        if function is None:
            print(f'Function {func} not found')
            sys.exit(1)
        function.compile_flags = '-mthumb-interwork'
        db.session.commit()
        print('done')


    @app.cli.command('update-equivalent')
    def update_equivalent():
        functions = Function.query.filter_by(
            deleted=False, is_submitted=False
        ).all()

        for func in functions:
            func.has_equivalent_try = SubmissionRepository.has_equivalent_submission(func.id)
            print(f'{func.name}: {func.has_equivalent_try}')
        db.session.commit()
        print('done')

    @app.cli.command('remove-old-repo-submissions')
    def remove_old_repo_submissions():
        functions = Function.query.filter_by(
            deleted=False, is_submitted=False
        ).all()

        repo_user = int(get_env_variable('REPO_USER'))
        for func in functions:
            submissions = Submission.query.filter_by(owner=repo_user, is_equivalent=False, function=func.id).order_by(Submission.score, desc(Submission.time_created)).offset(1).all()
            for submission in submissions:
                # Cannot delete submission which has children.
                if db.session.query(Submission.id).filter_by(parent=submission.id).first() is None:
                    db.session.delete(submission)
        db.session.commit()
        print('done')

    @app.cli.command('set-fakematch')
    @click.argument('func')
    def set_fakematch(func):
        function = FunctionRepository.get_by_name_internal(func)
        if function is None:
            print(f'Function {func} not found')
            sys.exit(1)
        function.is_fakematch = True
        function.is_submitted = False
        function.deleted = False
        db.session.commit()
        print('calculating fakeness scores...')
        calc_fakeness_scores(function)
        print('done')
        
    @app.cli.command('calculate-fakeness-scores')
    @click.argument('func')
    def calculate_fakeness_scores(func):
        function = FunctionRepository.get_by_name_internal(func)
        if function is None:
            print(f'Function {func} not found')
            sys.exit(1)
        calc_fakeness_scores(function)
        print('done')
        
    def calc_fakeness_scores(function):
        best_fakeness_score = 999999
        submissions = SubmissionRepository.get_for_function(function.id)
        for submission_small in submissions:
            submission = SubmissionRepository.get(submission_small.id)
            submission.fakeness_score = calculate_fakeness_score(submission.code)
            if submission.score == 0 and submission.fakeness_score < best_fakeness_score:
                best_fakeness_score = submission.fakeness_score
            print(f'{submission.id}: {submission.fakeness_score}')
        function.best_fakeness_score = best_fakeness_score
        db.session.commit()

    @app.cli.command('add-fakematch')
    @click.argument('func')
    @click.argument('file')
    def add_fakematch(func, file):
        function = FunctionRepository.get_by_name_internal(func)
        if function is not None:
            print(f'Function {func} already exists')
            sys.exit(1)
        
        symbols = get_symbols()
        symbol = symbols.find_symbol_by_name(func)
        if symbol is None:
            print(f'No symbol found for {func}, maybe static?')
            sys.exit(1)
        
        print(f'Address: {hex(symbol.address)}')
        same_address_function = FunctionRepository.get_by_addr_internal(symbol.address)
        if same_address_function is not None:
            print(f'Function already exists as {same_address_function.name}')
            sys.exit(1)

        print('Enter asm (Stop with Ctrl+D):')
        asm = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            asm.append(line)
        res = requests.post(current_app.config['PYCAT_URL'], '\n'.join(asm))
        asm = res.text.rstrip()
        if asm.startswith('#'):
            # Remove Compiler Explorer comment
            asm = asm.split('\n', 1)[1]


        function = Function(name=func, file=file, size=symbol.length, addr=symbol.address, asm=asm, is_fakematch=True, deleted=False)
        db.session.add(function)
        db.session.commit()
        print('done')