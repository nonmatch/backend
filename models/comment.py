from . import db
from .function import Function
from .user import User
from sqlalchemy.sql import expression, func

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey(User.id))
    function = db.Column(db.Integer, db.ForeignKey(Function.id))
    time_created = db.Column(db.DateTime(
        timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    is_deleted = db.Column(
        db.Boolean, server_default=expression.false(), nullable=False)
    text = db.Column(db.Text)