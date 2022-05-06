"""First Migration

Revision ID: 9ed6d50f1a52
Revises: 
Create Date: 2022-05-05 22:58:04.447353

"""
from alembic import op
import sqlalchemy as sa
import passlib.hash as _hash
import datetime as _dt

# revision identifiers, used by Alembic.
revision = '9ed6d50f1a52'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('arduinolist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('arduinoname', sa.String(), nullable=True),
    sa.Column('password_hash', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('arduinoname')
    )
    op.create_index(op.f('ix_arduinolist_id'), 'arduinolist', ['id'], unique=False)
    users_table = op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('date_created', sa.DateTime(), nullable=False),
    sa.Column('admin', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('freezer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('arduino_id', sa.Integer(), nullable=True),
    sa.Column('max_temp', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['arduino_id'], ['arduinolist.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_freezer_id'), 'freezer', ['id'], unique=False)
    op.create_table('temperature_readings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('freeze_id', sa.Integer(), nullable=True),
    sa.Column('temperature', sa.Integer(), nullable=True),
    sa.Column('reading_date', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['freeze_id'], ['freezer.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_temperature_readings_id'), 'temperature_readings', ['id'], unique=False)
    # ### end Alembic commands ###
    op.bulk_insert(
        users_table,
        [
            {'email':'admin@admin.com', 'hashed_password' : _hash.bcrypt.hash("admin"), 'admin': True,
            "date_created": _dt.date(2008, 8, 15)},
        ]
    )

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_temperature_readings_id'), table_name='temperature_readings')
    op.drop_table('temperature_readings')
    op.drop_index(op.f('ix_freezer_id'), table_name='freezer')
    op.drop_table('freezer')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_arduinolist_id'), table_name='arduinolist')
    op.drop_table('arduinolist')
    # ### end Alembic commands ###
