from . import db
from .function import Function
from .user import User
from sqlalchemy.sql import expression, func


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text)
    owner = db.Column(db.Integer, db.ForeignKey(User.id))
    function = db.Column(db.Integer, db.ForeignKey(Function.id))
    score = db.Column(db.Integer)
    is_equivalent = db.Column(db.Boolean, default=False)
    parent = db.Column(db.ForeignKey('submission.id'))
    time_created = db.Column(db.DateTime(
        timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    compiled = db.Column(db.Text)
    comments = db.Column(db.Text)
    is_deleted = db.Column(
        db.Boolean, server_default=expression.false(), nullable=False)
    fakeness_score = db.Column(db.Integer, server_default=expression.text('-1'))