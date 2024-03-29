"""Add best score for functions

Revision ID: f6b3a059659e
Revises: 7c3b6a63ffb0
Create Date: 2022-01-06 10:01:09.812350

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6b3a059659e'
down_revision = '7c3b6a63ffb0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('function', sa.Column('best_score', sa.Integer(), server_default=sa.text('99999'), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('function', 'best_score')
    # ### end Alembic commands ###
