"""Add created_at to SupportTicket

Revision ID: b6d176ce16a0
Revises: 7c445bba9402
Create Date: 2025-07-21 09:08:36.538004

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6d176ce16a0'
down_revision = '7c445bba9402'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('support_ticket', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('support_ticket', schema=None) as batch_op:
        batch_op.drop_column('created_at')

    # ### end Alembic commands ###
