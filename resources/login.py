from flask.helpers import url_for
from flask_login.utils import logout_user
from flask_restful import Resource


class LoginResource(Resource):
    def get(self):
        return {
             'redirect': url_for('github.login',_external=True)
         }

class LogoutResource(Resource):
    def post(self):
        logout_user()
        return 'ok'