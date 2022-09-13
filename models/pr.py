from . import db
from .user import User
from sqlalchemy.sql import func, expression


class Pr(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    text = db.Column(db.Text)
    functions = db.Column(db.Text)
    creator = db.Column(db.Integer, db.ForeignKey(User.id))
    time_created = db.Column(db.DateTime(
        timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    url = db.Column(db.Text)
    is_submitted = db.Column(
        db.Boolean, server_default=expression.false(), nullable=False)
    is_error = db.Column(
        db.Boolean, server_default=expression.false(), nullable=False)
    error = db.Column(db.Text)