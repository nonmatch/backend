from ma import ma
from models.audit import Audit

class AuditSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Audit
        load_instance = True
        include_fk = True