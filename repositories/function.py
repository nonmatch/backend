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
    Function.locked_by,
    Function.is_asm_func,
    Function.has_equivalent_try
)

public_fields_single = (
    *public_fields,
    Function.asm,
    Function.compile_flags
)

stats_fields = (
    *public_fields,
    Function.is_asm_func,
    Function.is_matched,
    Function.is_submitted,
    Function.deleted
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
            deleted=False, is_matched=False, is_submitted=False
        ).with_entities(
            *public_fields,
            # Necessary for stats:
            Function.is_asm_func,
        ).order_by(Function.id).all()

    @staticmethod
    def get_stats() -> List[Function]:
        return Function.query.filter_by(
            deleted=False, is_submitted=False
        ).with_entities(
            Function.id,
            Function.name,
            Function.file,
            Function.size,
            Function.is_asm_func,
            Function.is_matched
        ).order_by(Function.id).all()

    @staticmethod
    def get_nonmatch() -> List[Function]:
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
    def get_all_equivalent() -> List[Function]:
        return Function.query.filter_by(
            deleted=False, is_matched=False, is_submitted=False, has_equivalent_try=True
        ).with_entities(
            *public_fields
        ).order_by(Function.id).all()

    @staticmethod
    def get_all_non_equivalent() -> List[Function]:
        return Function.query.filter_by(
            deleted=False, is_matched=False, is_submitted=False, has_equivalent_try=False
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
    def get_all_internal() -> List[Function]:
        return Function.query.with_entities(
            *stats_fields
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

    @staticmethod
    def set_has_equivalent_try(id: int, has_equivalent_try: bool) -> None:
        func = FunctionRepository.get_internal(id)
        func.has_equivalent_try = has_equivalent_try
        db.session.commit()

    @staticmethod
    def search(name: str) -> List[Function]:
        return Function.query.with_entities(
            *public_fields
        ).filter(Function.name.like(f'%{name}%')).limit(10).all()