from typing import List

from sqlalchemy.orm import defer
from models import Function, db
from sqlalchemy.exc import IntegrityError
from exceptions import ResourceExists

class FunctionRepository:

    @staticmethod
    def create() -> dict:
        '''Create function'''
        result: dict = {}
        try:
            function = Function()
            db.session.add(function)
            db.session.commit()
            result = {
                'id': function.id
            }
        except IntegrityError:
            db.session.rollback()
            raise ResourceExists('Function already exists')
        return result

    @staticmethod
    def get_all() -> List[Function]:
        functions: list = []
        functions = Function.query.filter_by(deleted=False).options(defer(Function.asm)).all()

        # Need to do this so the defer of code is not triggered.
        return [x.__dict__ for x in functions]

    @staticmethod
    def get(id: int) -> Function:
        return Function.query.get(id)