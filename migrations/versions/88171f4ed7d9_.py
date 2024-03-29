"""Add is_asm_func field

Revision ID: 88171f4ed7d9
Revises: b84bb0dc5139
Create Date: 2022-01-14 14:39:18.572225

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88171f4ed7d9'
down_revision = 'b84bb0dc5139'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('function', sa.Column('is_asm_func', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('function', 'is_asm_func')
    # ### end Alembic commands ###
