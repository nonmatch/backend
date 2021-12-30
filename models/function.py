from . import db
from .user import User

class Function(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    file = db.Column(db.String(256))
    size = db.Column(db.Integer)
    asm = db.Column(db.Text)
    is_matched = db.Column(db.Boolean, default=False)
    locked_by = db.Column(db.Integer, db.ForeignKey(User.id))
