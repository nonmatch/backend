from flask import Flask, jsonify, redirect, render_template, url_for, request
from flask_dance.contrib.github import github
from flask_login import logout_user, login_required, current_user
from flask_restful import Api
from flask_cors import CORS
from flask_migrate import Migrate

from dotenv import load_dotenv
import click

from models.function import Function
from models import db, login_manager
from models.user import User, generate_auth_token
from oauth import github_blueprint
from repositories.function import FunctionRepository
from repositories.submission import SubmissionRepository
from resources.function import FunctionList, FunctionResource
from resources.login import LoginResource, LogoutResource
from resources.match import MatchResource
from resources.pr import PrResource
from resources.submission import FunctionSubmissions, SubmissionList, SubmissionResource
from resources.user import CurrentUserResource, DashboardResource, UserResource
from tools.find_nonmatching import update_nonmatching_functions
from werkzeug.middleware.proxy_fix import ProxyFix


# Load .env file manually, so the POSTGRESQL variables are available for get_config
load_dotenv()
from config import get_config

import logging
logging.basicConfig(filename='error.log',level=logging.DEBUG)
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config.from_object(get_config(None))
app.register_blueprint(github_blueprint, url_prefix='/login')

db.init_app(app)
migrate = Migrate(app, db)
login_manager.init_app(app)

with app.app_context():
    db.create_all()

# Fix so that https is still correctly identified when passing through ngrok proxy tunnel
#app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

@app.route('/')
def homepage():
    return redirect(app.config['FRONTEND_URL'])

@app.route('/ping')
def ping():
    return jsonify(ping='pong')

@app.route('/github')
def login():
    if not github.authorized:
        return redirect(url_for('github.login'))
    res = github.get('/user/public_emails')
    logging.debug(res.json())

    res = github.get('/user')
    data = res.json()
    logging.debug(data)
    if 'message' in data:
        return {'error': data['message']}

    return f'You are @{res.json()["login"]} on GitHub'

@app.route('/generate_token')
def generate_token():
    '''After successful OAuth dance, generate the token that is send to the frontend, so the GitHub access token is not exposed'''
    if not current_user.is_authenticated:
        return 'Authentication failed'
    token = generate_auth_token(current_user.id)
    return redirect(app.config['FRONTEND_URL']+'?token='+token.decode('ascii'))

api = Api(app)
api.add_resource(FunctionList, '/functions')
api.add_resource(FunctionResource, '/functions/<function>')
api.add_resource(SubmissionList, '/submissions')
api.add_resource(SubmissionResource, '/submissions/<submission>')
api.add_resource(UserResource, '/users/<id>')
api.add_resource(CurrentUserResource, '/user')
api.add_resource(DashboardResource, '/user/functions')
api.add_resource(LoginResource, '/oauth/login')
api.add_resource(LogoutResource, '/oauth/logout')
api.add_resource(FunctionSubmissions, '/functions/<function>/submissions')
api.add_resource(MatchResource, '/matches')
api.add_resource(PrResource, '/pr')


##### CLI commands
@app.cli.command('create-function')
@click.argument('name')
@click.argument('file')
@click.argument('size')
@click.argument('asm')
def create_function(name, file, size, asm):
    # TODO move to FunctionRepository
    function = Function(name=name, file=file, size=size,asm=asm)
    db.session.add(function)
    db.session.commit()

@app.cli.command('create-user')
@click.argument('name')
@click.argument('email')
@click.argument('avatar')
def create_user(name, email, avatar):
    user = User(username=name,avatar=avatar,email=email)
    db.session.add(user)
    db.session.commit()

@app.cli.command('update-nonmatch')
def update_nonmatch():
    update_nonmatching_functions()

if __name__ == '__main__':

    app.run(debug=True)
