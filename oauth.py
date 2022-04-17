from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_dance.contrib.github import github, make_github_blueprint
from flask_login import current_user, login_user
from models import db
from models.user import OAuth, User
from sqlalchemy.orm.exc import NoResultFound
import logging
import os

github_blueprint = make_github_blueprint(
    client_id=os.getenv('GITHUB_ID'),
    client_secret=os.getenv('GITHUB_SECRET'),
    scope='public_repo',#,user:email'
    storage=SQLAlchemyStorage(
        OAuth,
        db.session,
        user=current_user,
        user_required=False,
    ),
    redirect_to='generate_token',
    authorized_url='/github/authorized'
)


@oauth_authorized.connect_via(github_blueprint)
def github_logged_in(blueprint, token):
    info = github.get('/user')
    if info.ok:
        account_info = info.json()
        logging.debug(account_info)
        username = account_info['login']

        query = User.query.filter_by(username=username,email=entry['email'])
        try:
            user = query.one()
        except NoResultFound:
            avatar = account_info['avatar_url']
            email = ''
            res = github.get('/user/public_emails')
            if res.ok:
                json = res.json()
                for entry in json:
                    if entry['visibility'] == 'private':
                        continue
                    email = entry['email']
                    break
                logging.debug(json)
            user = User(username=username,avatar=avatar,email=email)
            db.session.add(user)
            db.session.commit()
        login_user(user)
