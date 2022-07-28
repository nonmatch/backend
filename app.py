from flask import Flask, jsonify, redirect, url_for, request
from flask_dance.contrib.github import github
from flask_login import current_user
from flask_restful import Api
from flask_cors import CORS
from flask_migrate import Migrate

from dotenv import load_dotenv
from cli import create_cli

from models import db
from models.user import generate_auth_token, login_manager
from oauth import github_blueprint
from resources.cexplore import CompileResource, PycatResource
from resources.function import AllFunctionList, AsmFunctionList, FunctionDecompMeResource, FunctionHeadersResource, FunctionList, FunctionLockResource, FunctionResource, FunctionUnlockResource, WithCodeFunctionList, WithoutCodeFunctionList
from resources.login import LoginResource, LogoutResource
from resources.match import MatchResource
from resources.pr import PrResource
from resources.stats import StatsResource
from resources.submission import FunctionSubmissions, LatestSubmissionsResource, SubmissionResource
from resources.user import CurrentUserResource, DashboardResource, UserResource


# Load .env file manually, so the POSTGRESQL variables are available for get_config
load_dotenv()
from config import get_config

import logging

logging.basicConfig(filename='error.log', level=logging.DEBUG)
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
# app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


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

    if request.args.get('mock') and app.config['ENV'] == 'development':
        # Generate mock token for user with id 2.
        token = generate_auth_token(2)
        return redirect(app.config['FRONTEND_URL'] + '?token=' + token.decode('ascii'))

    if not current_user.is_authenticated:
        return 'Authentication failed'
    token = generate_auth_token(current_user.id)
    return redirect(app.config['FRONTEND_URL'] + '?token=' + token.decode('ascii'))


api = Api(app)
api.add_resource(FunctionList, '/functions')
api.add_resource(AllFunctionList, '/all_functions')
api.add_resource(AsmFunctionList, '/asm_functions')
api.add_resource(WithCodeFunctionList, '/with_code')
api.add_resource(WithoutCodeFunctionList, '/without_code')
api.add_resource(FunctionResource, '/functions/<function>')
api.add_resource(FunctionHeadersResource, '/functions/<function>/headers')
api.add_resource(FunctionDecompMeResource, '/functions/<function>/decompMe')
api.add_resource(FunctionLockResource, '/functions/<function>/lock')
api.add_resource(FunctionUnlockResource, '/functions/<function>/unlock')
api.add_resource(LatestSubmissionsResource, '/submissions')
api.add_resource(SubmissionResource, '/submissions/<submission>')
api.add_resource(UserResource, '/users/<id>')
api.add_resource(CurrentUserResource, '/user')
api.add_resource(DashboardResource, '/user/functions')
api.add_resource(LoginResource, '/oauth/login')
api.add_resource(LogoutResource, '/oauth/logout')
api.add_resource(FunctionSubmissions, '/functions/<function>/submissions')
api.add_resource(MatchResource, '/matches')
api.add_resource(PrResource, '/pr')
api.add_resource(StatsResource, '/stats')
api.add_resource(CompileResource, '/api/compiler/agbcc/compile')
api.add_resource(PycatResource, '/api/compiler/cat/compile')

create_cli(app)

if __name__ == '__main__':

    app.run(debug=True)
