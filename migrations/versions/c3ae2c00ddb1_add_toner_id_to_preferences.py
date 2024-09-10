"""Add toner_id to preferences

Revision ID: c3ae2c00ddb1
Revises: 
Create Date: 2023-07-14 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3ae2c00ddb1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('preferences', schema=None) as batch_op:
        batch_op.add_column(sa.Column('toner_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('proveedor_email', sa.String(length=100), nullable=True))
        batch_op.create_foreign_key('fk_preferences_toner_id', 'toner', ['toner_id'], ['id'])

    with op.batch_alter_table('movement', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reverted', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('explicacion_reversion', sa.String(length=200), nullable=True))


def downgrade():
    with op.batch_alter_table('movement', schema=None) as batch_op:
        batch_op.drop_column('explicacion_reversion')
        batch_op.drop_column('reverted')

    with op.batch_alter_table('preferences', schema=None) as batch_op:
        batch_op.drop_constraint('fk_preferences_toner_id', type_='foreignkey')
        batch_op.drop_column('proveedor_email')
        batch_op.drop_column('toner_id')
