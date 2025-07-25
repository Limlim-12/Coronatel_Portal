"""Initial migration

Revision ID: 7860773c7f3a
Revises: 
Create Date: 2025-07-18 08:02:12.150106

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7860773c7f3a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=150), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('avatar', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cx',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password', sa.String(length=200), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=True),
    sa.Column('avatar', sa.String(length=255), nullable=True),
    sa.Column('role', sa.String(length=10), nullable=False),
    sa.Column('account_status', sa.String(length=20), nullable=True),
    sa.Column('contact', sa.String(length=50), nullable=True),
    sa.Column('account_number', sa.String(length=50), nullable=True),
    sa.Column('internet_plan', sa.String(length=50), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.Column('first_name', sa.String(length=50), nullable=True),
    sa.Column('middle_name', sa.String(length=50), nullable=True),
    sa.Column('middle_initial', sa.String(length=50), nullable=True),
    sa.Column('surname', sa.String(length=50), nullable=True),
    sa.Column('extension_name', sa.String(length=50), nullable=True),
    sa.Column('birthdate', sa.Date(), nullable=True),
    sa.Column('gender', sa.String(length=20), nullable=True),
    sa.Column('location_country', sa.String(length=50), nullable=True),
    sa.Column('location_region', sa.String(length=50), nullable=True),
    sa.Column('location_province', sa.String(length=50), nullable=True),
    sa.Column('location_city', sa.String(length=50), nullable=True),
    sa.Column('location_barangay', sa.String(length=50), nullable=True),
    sa.Column('location_zip', sa.String(length=20), nullable=True),
    sa.Column('location_street', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('admin_message',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cx_id', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('subject', sa.String(length=150), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('sent_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['cx_id'], ['cx.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['admin_user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cx_login_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cx_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['cx_id'], ['cx.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cx_request',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cx_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('billing_from', sa.Date(), nullable=True),
    sa.Column('billing_to', sa.Date(), nullable=True),
    sa.Column('amount', sa.Float(), nullable=True),
    sa.Column('soa_filename', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('admin_note', sa.Text(), nullable=True),
    sa.Column('response_note', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['cx_id'], ['cx.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notification',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cx_id', sa.Integer(), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('notif_type', sa.String(length=50), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('amount', sa.Float(), nullable=True),
    sa.Column('reference_id', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['cx_id'], ['cx.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('payment_proof',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=True),
    sa.Column('cx_id', sa.Integer(), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(), nullable=True),
    sa.Column('reference_number', sa.String(length=100), nullable=True),
    sa.Column('payment_date', sa.Date(), nullable=True),
    sa.Column('amount', sa.Float(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['cx_id'], ['cx.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('private_message',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('recipient_id', sa.Integer(), nullable=False),
    sa.Column('subject', sa.String(length=200), nullable=True),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('sent_at', sa.DateTime(), nullable=True),
    sa.Column('is_read', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['recipient_id'], ['cx.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['admin_user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reactivation_request',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('account_number', sa.String(length=100), nullable=True),
    sa.Column('email', sa.String(length=150), nullable=True),
    sa.Column('cx_id', sa.Integer(), nullable=False),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('requested_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['account_number'], ['cx.account_number'], ),
    sa.ForeignKeyConstraint(['cx_id'], ['cx.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('soa',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cx_id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(), nullable=True),
    sa.Column('billing_from', sa.Date(), nullable=True),
    sa.Column('billing_to', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['cx_id'], ['cx.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('soa')
    op.drop_table('reactivation_request')
    op.drop_table('private_message')
    op.drop_table('payment_proof')
    op.drop_table('notification')
    op.drop_table('cx_request')
    op.drop_table('cx_login_log')
    op.drop_table('admin_message')
    op.drop_table('cx')
    op.drop_table('admin_user')
    # ### end Alembic commands ###
