"""Add avatar and email

Revision ID: 7b10a01330fa
Revises: 
Create Date: 2021-12-30 22:57:27.241725

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b10a01330fa'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('avatar', sa.String(length=256), nullable=True))
    op.add_column('user', sa.Column('email', sa.String(length=256), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'email')
    op.drop_column('user', 'avatar')
    # ### end Alembic commands ###
