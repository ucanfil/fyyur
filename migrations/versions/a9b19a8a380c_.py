"""empty message

Revision ID: a9b19a8a380c
Revises: 173eaa4fde84
Create Date: 2020-04-05 20:48:55.588144

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9b19a8a380c'
down_revision = '173eaa4fde84'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('name', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Artist', 'name')
    # ### end Alembic commands ###
