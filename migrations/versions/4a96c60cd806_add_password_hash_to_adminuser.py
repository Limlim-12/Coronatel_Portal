"""Add password_hash to AdminUser

Revision ID: 4a96c60cd806
Revises: 
Create Date: 2025-07-08 10:14:51.883875

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a96c60cd806'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=150), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('password_hash', sa.String(length=256), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cx',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password', sa.String(length=200), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=True),
    sa.Column('avatar', sa.String(length=255), nullable=True),
    sa.Column('role', sa.String(length=10), nullable=False),
    sa.Column('contact', sa.String(length=50), nullable=True),
    sa.Column('account_number', sa.String(length=50), nullable=True),
    sa.Column('internet_plan', sa.String(length=50), nullable=True),
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
    sa.ForeignKeyConstraint(['cx_id'], ['cx.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notification',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cx_id', sa.Integer(), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
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
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('payment_proof')
    op.drop_table('notification')
    op.drop_table('cx_request')
    op.drop_table('cx')
    op.drop_table('admin_user')
    # ### end Alembic commands ###
