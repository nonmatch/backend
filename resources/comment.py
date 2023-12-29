
from flask import request
from flask_login import current_user
from flask_restful import Resource
from repositories.audit import AuditRepository
from repositories.comment import CommentRepository
from repositories.function import FunctionRepository
from schemas.comment import CommentSchema
from utils import error_message_response, error_response


comments_schema = CommentSchema(many=True)
comment_schema = CommentSchema()


class CommentResource(Resource):
    def get(self, comment: id):
        return comment_schema.dump(CommentRepository.get(comment))

    def delete(self, comment: int):
        comm = CommentRepository.get(comment)
        if not comm or comm.is_deleted:
            return error_message_response('Comment not found.')
        if current_user is None or not current_user.is_authenticated:
            return error_message_response('Not logged in.')
        if comm.user != current_user.id:
            return error_message_response('This comment does not belong to you.')
        AuditRepository.create(current_user.id, f'Deleted comment {comment}')
        CommentRepository.delete(comm)
        return 'ok'

class FunctionCommentsResource(Resource):
    def get(self, function: int):
        return comments_schema.dump(CommentRepository.get_for_function(function)), 200

    def post(self, function: int):
        data = request.get_json()
        if data is None:
            return error_message_response('Invalid request')
        try:
            user = None
            if current_user is not None and current_user.is_authenticated:
                user = current_user.id
            else:
                return error_message_response('Not logged in')

            comment = CommentRepository.update(function, user, data['text'])

            return comment, 200
        except Exception as e:
            return error_response(e)

class ShortCommentsResource(Resource):
    def get(self):
        functions = FunctionRepository.get_all()

        comments = {}
        for function in functions:
            if function.best_fakeness_score > 0:
                comments[function.id] = []
                function_comments = CommentRepository.get_for_function(function.id)
                for comment in function_comments:
                    comments[function.id].append(comment.text.split('\n')[0])
        return comments, 200