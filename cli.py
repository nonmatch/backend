from models import db
from models.function import Function
from models.user import User
from repositories.function import FunctionRepository
from tools.find_nonmatching import PYCAT_URL, extract_USA_asm, get_code, get_symbols, update_nonmatching_functions
import click
import requests
import sys
from subprocess import check_call
import os

from tools.lock import GIT_LOCK, with_lock

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

        update_nonmatching_functions()
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
        res = requests.post(PYCAT_URL, asm)
        asm = res.text.rstrip()
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
        functions = Function.query.with_entities(Function.id, Function.name, Function.is_asm_func).filter(Function.asm.like('%error%')).all()
        for func in functions:
            print(f'{func.id}\t{"a" if func.is_asm_func else "n"} {func.name}')

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