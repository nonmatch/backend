from ma import ma
from models.function import Function


class FunctionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Function
        load_instance = True
        load_only = ('locked_by',)
        exclude = ('deleted',)
        include_fk= True