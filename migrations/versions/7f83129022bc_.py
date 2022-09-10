"""Add deleted to function

Revision ID: 7f83129022bc
Revises: 8716917910ab
Create Date: 2022-01-03 22:53:55.123619

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f83129022bc'
down_revision = '8716917910ab'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('function', sa.Column('deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('function', 'deleted')
    # ### end Alembic commands ###
