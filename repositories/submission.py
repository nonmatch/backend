from typing import List

from sqlalchemy.orm import defer
from models.submission import Submission
from models import db
from sqlalchemy.exc import IntegrityError
from exceptions import ResourceExists

class SubmissionRepository:
    @staticmethod
    def create(function: int, owner: int, code: str, score: int, is_equivalent: bool, parent: int) -> dict:
        '''Create submission'''
        try:
            if int(parent) == 0:
                parent = None
            submission = Submission(
                function=function,
                owner=owner,
                code=code,
                score=score,
                is_equivalent=is_equivalent,
                parent=parent
            )
            db.session.add(submission)
            db.session.commit()
            return {'id': submission.id}
        except IntegrityError as e:
            print(e)
            db.session.rollback()
            raise ResourceExists('Submission already exists')

    @staticmethod
    def get_for_function(function: int) -> List[Submission]:
        '''Get all submissions for a function'''
        return Submission.query.with_entities(Submission.id, Submission.function, Submission.is_equivalent, Submission.score, Submission.owner).filter_by(function=function).all()


    @staticmethod
    def get(id: int) -> Submission:
        return Submission.query.get(id)