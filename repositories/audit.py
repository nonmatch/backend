from typing import List
from models import db
from models.audit import Audit
from sqlalchemy.sql.expression import desc

class AuditRepository:
    @staticmethod
    def create(user: int, text: str) -> Audit:
        '''Create an audit log.'''
        audit = Audit(user=user, text=text)
        db.session.add(audit)
        db.session.commit()
        return audit

    @staticmethod
    def get_latest() -> List[Audit]:
        '''Returns the latest 20 audit logs.'''
        return Audit.query.order_by(desc(Audit.time_created)).limit(20).all()