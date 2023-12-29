from flask import request, jsonify
from flask_login import current_user
from flask_restful import Resource
from repositories.submission import SubmissionRepository
from repositories.user import UserRepository
from schemas.submission import SubmissionSchema
from schemas.user import UserSchema

user_schema = UserSchema()
submissions_schema = SubmissionSchema(many=True)


class User(Resource):
    def get(self, username: str):
        user = UserRepository.get(username)
        return user, 200


class UserResource(Resource):
    def get(self, id: str):
        return user_schema.dump(UserRepository.get(int(id)))

    def put(self, id: str):
        json = request.get_json(silent=True)
        username: str = json['username']
        email: str = json['email']
        return user_schema.dump(UserRepository.update(int(id), username, email))


class UserList(Resource):
    def post(self):
        '''
        Create user
        '''
        request_json = request.get_json(silent=True)
        username: str = request_json['username']
        avatar_url: str = request_json.get('avatar_url', '')
        try:
            user = UserRepository.create(username, avatar_url)
            return user, 200
        except Exception as e:
            response = jsonify(e.to_dict())
            response.status_code = e.status_code
            return response


class CurrentUserResource(Resource):
    def get(self):
        user = UserRepository.get_current_user()
        if user is None:
            return {
                'error': 'Not logged in'
            }, 404
        return user_schema.dump(user)


class DashboardResource(Resource):
    def get(self):
        if current_user is None or not current_user.is_authenticated:
            return []
        return submissions_schema.dump(SubmissionRepository.get_for_user(current_user.id))
