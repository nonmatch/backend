from exceptions import ResourceExists
from models import db
from models.function import Function
from models.submission import Submission
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import desc
from typing import List
import logging

class SubmissionRepository:
    @staticmethod
    def create(function: int, owner: int, code: str, score: int, is_equivalent: bool, parent: int, compiled: str) -> dict:
        '''Create submission'''
        try:
            if parent is not None and int(parent) == 0:
                parent = None
            submission = Submission(
                function=function,
                owner=owner,
                code=code,
                score=score,
                is_equivalent=is_equivalent,
                parent=parent,
                compiled=compiled
            )
            db.session.add(submission)
            db.session.commit()
            return {'id': submission.id}
        except IntegrityError as e:
            logging.exception(e)
            db.session.rollback()
            raise ResourceExists('Submission already exists')

    @staticmethod
    def get_for_function(function: int) -> List[Submission]:
        '''Get all submissions for a function'''
        return Submission.query.with_entities(Submission.id, Submission.function, Submission.is_equivalent, Submission.score, Submission.owner, Submission.time_created).filter_by(function=function).order_by(Submission.score, desc(Submission.time_created)).all()

    @staticmethod
    def get_matched_for_function(function: int) -> List[Submission]:
        '''Get all submissions for a function with a score of 0'''
        return Submission.query.filter_by(score=0).with_entities(Submission.id, Submission.function, Submission.is_equivalent, Submission.score, Submission.owner, Submission.time_created).filter_by(function=function).order_by(Submission.score, desc(Submission.time_created)).all()

    @staticmethod
    def get_for_user(user: int) -> List[Submission]:
        '''Get all non submitted submissions for a user'''
        valid_functions = Function.query.with_entities(Function.id).filter_by(deleted=False, is_submitted=False)
        return Submission.query.with_entities(Submission.id, Submission.function, Submission.is_equivalent, Submission.score, Submission.owner, Submission.time_created).filter_by(owner=user).filter(Submission.function.in_(valid_functions)).order_by(desc(Submission.time_created)).all()


    @staticmethod
    def get(id: int) -> Submission:
        return Submission.query.get(id)