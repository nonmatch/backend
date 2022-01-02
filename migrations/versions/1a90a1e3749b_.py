"""Add created and updated timestamps

Revision ID: 1a90a1e3749b
Revises: b22b63d2637e
Create Date: 2022-01-03 16:00:25.064097

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a90a1e3749b'
down_revision = 'b22b63d2637e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'flask_dance_oauth', 'user', ['user_id'], ['id'])
    op.add_column('function', sa.Column('time_created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('function', sa.Column('time_updated', sa.DateTime(timezone=True), nullable=True))
    op.add_column('submission', sa.Column('time_created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('submission', sa.Column('time_updated', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user', sa.Column('time_created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('user', sa.Column('time_updated', sa.DateTime(timezone=True), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'time_updated')
    op.drop_column('user', 'time_created')
    op.drop_column('submission', 'time_updated')
    op.drop_column('submission', 'time_created')
    op.drop_column('function', 'time_updated')
    op.drop_column('function', 'time_created')
    op.drop_constraint(None, 'flask_dance_oauth', type_='foreignkey')
    # ### end Alembic commands ###
