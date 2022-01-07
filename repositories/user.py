from exceptions import ResourceExists
from flask_login import current_user
from models import User, db
from sqlalchemy.exc import IntegrityError
from typing import Optional

class UserRepository:

    @staticmethod
    def create(username: str, avatar_url: str) -> dict:
        ''' Create user '''
        result: dict = {}
        try:
            user = User(username=username, avatar_url=avatar_url)
            user.save()
            result = {
                'username': user.username,
                'avatar_url': user.avatar_url,
                'date_created': str(user.date_created),
            }
        except IntegrityError:
            User.rollback()
            raise ResourceExists('user already exists')

        return result

    @staticmethod
    def get(id: int) -> User:
        return User.query.with_entities(User.id, User.username, User.avatar).filter_by(id=id).first_or_404()

    @staticmethod
    def update(id: int, username: str, email: str) -> dict:
        if not current_user.is_authenticated or id != current_user.id:
            raise Exception('Not allowed ' + str(current_user.id) + ' != ' + str(id))
        try:
            user = User.query.get(id)
            if user is None:
                raise Exception('User record not found')
            user.username = username
            user.email = email
            db.session.commit()
            return user
        except IntegrityError:
            User.rollback()
            raise ResourceExists('user already exists')


    @staticmethod
    def get_by_name(username: str) -> dict:
        ''' Query a user by username '''
        user: dict = {}
        user = User.query.filter_by(username=username).first_or_404()
        user = {
          'username': user.username,
          'date_created': str(user.date_created),
        }
        return user

    @staticmethod
    def get_current_user() -> Optional[User]:
        if not current_user.is_authenticated:
            return None
        return current_user

    @staticmethod
    def get_by_name_and_email(username: str, email: str) -> Optional[User]:
        return User.query.filter_by(username=username, email=email).first()

    @staticmethod
    def create_anonymous(username: str, email: str) -> User:
        user = User(username=username, email=email)
        db.session.add(user)
        db.session.commit()