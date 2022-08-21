from . import db
from .user import User
from sqlalchemy.sql import func

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey(User.id))
    time_created = db.Column(db.DateTime(
        timezone=True), server_default=func.now())
    text = db.Column(db.Text)