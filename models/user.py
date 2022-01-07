from . import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin, LoginManager
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from sqlalchemy.sql import func
import logging
import os

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256))
    avatar = db.Column(db.String(256))
    email = db.Column(db.String(256))
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

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
        logging.warning('signature expired')
        return None    # valid token, but expired
    except BadSignature:
        logging.warning('bad signature')
        return None    # invalid token
    user = User.query.get(data['id'])
    return user


@login_manager.request_loader
def load_user_from_request(request):
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
        #logging.debug(f'got token {token} via header')
        # try:
        #     token = base64.b64decode(token)
        # except TypeError:
        #     pass
        user = verify_auth_token(token)
        if user:
            return user

    # finally, return None if both methods did not login the user
    return None