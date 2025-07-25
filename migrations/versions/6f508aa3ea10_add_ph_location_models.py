"""Add PH location models

Revision ID: 6f508aa3ea10
Revises: d7c63a0a9e56
Create Date: 2025-07-23 07:57:22.700361

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6f508aa3ea10'
down_revision = 'd7c63a0a9e56'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('region',
    sa.Column('reg_code', sa.String(length=10), nullable=False),
    sa.Column('reg_desc', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('reg_code')
    )
    op.create_table('province',
    sa.Column('prov_code', sa.String(length=10), nullable=False),
    sa.Column('prov_desc', sa.String(length=100), nullable=False),
    sa.Column('reg_code', sa.String(length=10), nullable=False),
    sa.ForeignKeyConstraint(['reg_code'], ['region.reg_code'], ),
    sa.PrimaryKeyConstraint('prov_code')
    )
    op.create_table('city_mun',
    sa.Column('citymun_code', sa.String(length=10), nullable=False),
    sa.Column('citymun_desc', sa.String(length=100), nullable=False),
    sa.Column('prov_code', sa.String(length=10), nullable=False),
    sa.ForeignKeyConstraint(['prov_code'], ['province.prov_code'], ),
    sa.PrimaryKeyConstraint('citymun_code')
    )
    op.create_table('barangay',
    sa.Column('brgy_code', sa.String(length=10), nullable=False),
    sa.Column('brgy_desc', sa.String(length=100), nullable=False),
    sa.Column('citymun_code', sa.String(length=10), nullable=False),
    sa.ForeignKeyConstraint(['citymun_code'], ['city_mun.citymun_code'], ),
    sa.PrimaryKeyConstraint('brgy_code')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('barangay')
    op.drop_table('city_mun')
    op.drop_table('province')
    op.drop_table('region')
    # ### end Alembic commands ###
