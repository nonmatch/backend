from ma import ma
from models.pr import Pr


class PrSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Pr
        load_instance = True
        include_fk = True
