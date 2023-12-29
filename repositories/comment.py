from typing import List, Optional
from exceptions import ResourceExists
from models import db
from models.comment import Comment
from sqlalchemy.exc import IntegrityError
import logging

class CommentRepository:
    @staticmethod
    def create(function: int, user: int, text: str):
        '''Create comment'''
        try:
            comment = Comment(
                function=function,
                user=user,
                text=text
            )
            db.session.add(comment)
            db.session.commit()
            return {'id': comment.id}
        except IntegrityError as e:
            logging.exception(e)
            db.session.rollback()
            raise ResourceExists('Comment already exists')

    @staticmethod
    def get_for_function(function: int) -> List[Comment]:
        '''Get all comments for a function'''
        return Comment.query.with_entities(Comment.id, Comment.function, Comment.user, Comment.text).filter_by(function=function,is_deleted=False).all()

    @staticmethod
    def get_for_function_and_user(function: int, user: int) -> Optional[Comment]:
        '''Get comment for a function from a user'''
        return Comment.query.filter_by(function=function,user=user,is_deleted=False).first()

    @staticmethod
    def get(id: int) -> Comment:
        return Comment.query.filter_by(is_deleted=False,id=id).first_or_404('Comment not found.')

    @staticmethod
    def update(function: int, user: int, text: str):
        '''Create or update comment'''

        comment = CommentRepository.get_for_function_and_user(function, user)
        if comment is None:
            CommentRepository.create(function, user, text)
        else:
            comment.text = text
            db.session.commit()

    @staticmethod
    def delete(comment: Comment) -> None:
        comment.is_deleted = True
        db.session.commit()