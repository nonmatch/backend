from ma import ma
from models.comment import Comment


class CommentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Comment
        load_instance = True
        include_fk = True
