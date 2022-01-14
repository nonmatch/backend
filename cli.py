from models import db
from models.function import Function
from models.user import User
from repositories.function import FunctionRepository
from tools.find_nonmatching import PYCAT_URL, get_code, update_nonmatching_functions
import click
import requests
import sys


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

    @app.cli.command('update-asm')
    @click.argument('func')
    def update_asm(func):
        function = FunctionRepository.get_by_name(func)
        if function is None:
            print(f'Function {func} not found')
            sys.exit(1)
        (err, asm, src, signature) = get_code(func, True)
        if err:
            print(asm, file=sys.stderr)
            sys.exit(1)

        # Run pycat.py on the asm code
        res = requests.post(PYCAT_URL, asm)
        asm = res.text.rstrip()
        function.asm = asm
        db.session.commit()
        print('done')


# Find functions with error in asm
# nonmatch=# SELECT id from function where asm like '%error%';
