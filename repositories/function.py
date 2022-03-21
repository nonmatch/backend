from exceptions import ResourceExists
from models import db
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from models.function import Function

public_fields = (
    Function.id,
    Function.name,
    Function.file,
    Function.size,
    Function.best_score,
    Function.time_created,
    Function.decomp_me_scratch,
    Function.decomp_me_matched,
    Function.locked_by)

public_fields_single = (
    *public_fields,
    Function.asm
)


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

    # TODO also exclude fields like deleted, is_submitted and time_changed?
    # TODO Rename deleted to is_deleted

    @staticmethod
    def get_all() -> List[Function]:
        return Function.query.filter_by(
            deleted=False, is_matched=False, is_submitted=False, is_asm_func=False
        ).with_entities(
            *public_fields
        ).order_by(Function.id).all()

    @staticmethod
    def get_all_asm() -> List[Function]:
        return Function.query.filter_by(
            deleted=False, is_matched=False, is_submitted=False, is_asm_func=True
        ).with_entities(
            *public_fields
        ).order_by(Function.id).all()

    @staticmethod
    def get_all_with_code() -> List[Function]:
        return Function.query.filter_by(
            deleted=False, is_matched=False, is_submitted=False, has_code_try=True
        ).with_entities(
            *public_fields
        ).order_by(Function.id).all()

    @staticmethod
    def get_all_without_code() -> List[Function]:
        return Function.query.filter_by(
            deleted=False, is_matched=False, is_submitted=False, has_code_try=False
        ).with_entities(
            *public_fields
        ).order_by(Function.id).all()

    @staticmethod
    def get_all_matched() -> List[Function]:
        return Function.query.filter_by(
            deleted=False, is_matched=True, is_submitted=False
        ).with_entities(
            *public_fields
        ).order_by(Function.id).all()

    @staticmethod
    def get(id: int) -> Function:
        return Function.query.with_entities(*public_fields_single).filter_by(id=id).first_or_404()

    @staticmethod
    def get_internal(id: int) -> Function:
        return Function.query.get(id)

    @staticmethod
    def get_by_name_internal(name: str) -> Optional[Function]:
        return Function.query.filter_by(name=name).first()

    @staticmethod
    def set_decomp_me_scratch(function: Function, decomp_me_slug: str):
        function.decomp_me_scratch = decomp_me_slug
        db.session.commit()

    @staticmethod
    def lock(function: Function, user: id):
        function.locked_by = user
        db.session.commit()

    @staticmethod
    def unlock(function: Function):
        function.locked_by = None
        db.session.commit()