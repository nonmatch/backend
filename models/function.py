from . import db
from .user import User
from sqlalchemy.sql import expression
from sqlalchemy.sql import func


class Function(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    file = db.Column(db.String(256))
    size = db.Column(db.Integer)
    asm = db.Column(db.Text)
    addr = db.Column(db.Integer)
    is_matched = db.Column(
        db.Boolean, server_default=expression.false(), nullable=False)
    is_submitted = db.Column(
        db.Boolean, server_default=expression.false(), nullable=False)
    locked_by = db.Column(db.Integer, db.ForeignKey(User.id))
    time_created = db.Column(db.DateTime(
        timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    deleted = db.Column(
        db.Boolean, server_default=expression.false(), nullable=False)
    best_score = db.Column(db.Integer, server_default=expression.text('99999'))
    is_asm_func = db.Column(
        db.Boolean, server_default=expression.false(), nullable=False)
    # Has a submission associated that contains at least some code
    has_code_try = db.Column(
        db.Boolean, server_default=expression.false(), nullable=False)