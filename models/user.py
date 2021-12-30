''' from . import db
from .abc import BaseModel

import datetime


class User(db.Model, BaseModel):
    username = db.Column(
        db.String, primary_key=True,
        unique=True, nullable=False)
    avatar_url = db.Column(db.String, nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, username: str, avatar_url: str = ''):
        self.username = username
        self.avatar_url = avatar_url '''

import os
from . import db
from flask_login import UserMixin, LoginManager
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin

from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True)
    avatar = db.Column(db.String(256))
    email = db.Column(db.String(256))

class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def generate_auth_token(user_id, expiration=604800):
    s = Serializer(os.getenv('SECRET_KEY'), expires_in=expiration)
    return s.dumps({'id': user_id})

def verify_auth_token(token):
    s = Serializer(os.getenv('SECRET_KEY'))
    try:
        data = s.loads(token)
    except SignatureExpired:
        print('signature expired')
        return None    # valid token, but expired
    except BadSignature:
        print('bad signature')
        return None    # invalid token
    user = User.query.get(data['id'])
    return user


@login_manager.request_loader
def load_user_from_request(request):
    print(request)
    # first, try to login using the token url arg
    token = request.args.get('token')
    if token:
        user = verify_auth_token(token)
        if user:
            return user

    # next, try to login using Basic Auth
    token = request.headers.get('Authorization')
    if token:
        token = token.replace('Basic ', '', 1)
        print(f'got token {token} via header')
        # try:
        #     token = base64.b64decode(token)
        # except TypeError:
        #     pass
        user = verify_auth_token(token)
        if user:
            return user

    # finally, return None if both methods did not login the user
    return None