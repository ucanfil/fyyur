"""empty message

Revision ID: 173eaa4fde84
Revises: efcaaf55d111
Create Date: 2020-04-05 20:48:40.513218

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '173eaa4fde84'
down_revision = 'efcaaf55d111'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Artist', 'name')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###