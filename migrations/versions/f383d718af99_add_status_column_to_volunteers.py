"""Add status column to volunteers

Revision ID: f383d718af99
Revises: 
Create Date: 2025-02-19 20:41:33.927011

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f383d718af99'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('volunteers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('volunteers', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###
