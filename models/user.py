from . import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin, LoginManager
from sqlalchemy.sql import func
import logging
import os
import jwt
import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256))
    avatar = db.Column(db.String(256))
    email = db.Column(db.String(256))
    time_created = db.Column(db.DateTime(
        timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())


class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)


login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def generate_auth_token(user_id, expiration=604800):
    reset_token = jwt.encode(
        {
            'id': user_id,
            'exp': datetime.datetime.now(tz=datetime.timezone.utc)
                    + datetime.timedelta(seconds=expiration)
        },
        os.getenv('SECRET_KEY'),
        algorithm='HS256'
    )
    return reset_token


def verify_auth_token(token):
    try:
        data = jwt.decode(
            token,
            os.getenv('SECRET_KEY'),
            leeway=datetime.timedelta(seconds=10),
            algorithms=["HS256"]
        )
    except Exception as e:
        print(e)
        logging.warning('signature expired')
        return None
    user = User.query.get(data.get('id'))
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
