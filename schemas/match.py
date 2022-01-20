from ma import ma
from marshmallow import fields


class MatchSchema(ma.Schema):
    name = fields.Str()
    function = fields.Int()
    owner = fields.Int()
    submission = fields.Int()
    time_created = fields.DateTime()
    size = fields.Int()
    file = fields.Str()
