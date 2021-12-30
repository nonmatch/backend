from . import db
from .user import User
from .function import Function

# TODO created timestamp?
class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text)
    owner = db.Column(db.Integer, db.ForeignKey(User.id))
    function = db.Column(db.Integer, db.ForeignKey(Function.id))
    score = db.Column(db.Integer)
    is_equivalent = db.Column(db.Boolean, default=False)
    parent = db.Column(db.ForeignKey('submission.id'))