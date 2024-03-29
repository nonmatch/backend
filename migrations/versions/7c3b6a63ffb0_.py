"""Boolean default on server

Revision ID: 7c3b6a63ffb0
Revises: 7f83129022bc
Create Date: 2022-01-03 23:12:14.221136

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c3b6a63ffb0'
down_revision = '7f83129022bc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('function', 'is_matched',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.alter_column('function', 'deleted',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('function', 'deleted',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column('function', 'is_matched',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    # ### end Alembic commands ###
