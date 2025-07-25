"""Update SupportTicket fields

Revision ID: 83773aa6f5b9
Revises: b6d176ce16a0
Create Date: 2025-07-21 11:15:59.386959

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83773aa6f5b9'
down_revision = 'b6d176ce16a0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('support_ticket', schema=None) as batch_op:
        batch_op.add_column(sa.Column('form_type', sa.String(length=20), nullable=False))
        batch_op.add_column(sa.Column('account_type', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('other_issue_detail', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('request_service', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('repair_note', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('new_plan', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('account_note', sa.Text(), nullable=True))
        batch_op.drop_column('request_services')
        batch_op.drop_column('submitted_at')
        batch_op.drop_column('note')
        batch_op.drop_column('ticket_type')
        batch_op.drop_column('preferred_plan')
        batch_op.drop_column('reason')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('support_ticket', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reason', sa.VARCHAR(length=255), nullable=True))
        batch_op.add_column(sa.Column('preferred_plan', sa.VARCHAR(length=100), nullable=True))
        batch_op.add_column(sa.Column('ticket_type', sa.VARCHAR(length=50), nullable=False))
        batch_op.add_column(sa.Column('note', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('submitted_at', sa.DATETIME(), nullable=True))
        batch_op.add_column(sa.Column('request_services', sa.VARCHAR(length=50), nullable=True))
        batch_op.drop_column('account_note')
        batch_op.drop_column('new_plan')
        batch_op.drop_column('repair_note')
        batch_op.drop_column('request_service')
        batch_op.drop_column('other_issue_detail')
        batch_op.drop_column('account_type')
        batch_op.drop_column('form_type')

    # ### end Alembic commands ###
