"""empty message

Revision ID: 487e5cfd1e1
Revises: 4a3af16ce5e
Create Date: 2015-07-02 16:18:18.479197

"""

# revision identifiers, used by Alembic.
revision = '487e5cfd1e1'
down_revision = '4a3af16ce5e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('results', sa.Column('return_code', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('results', 'return_code')
    ### end Alembic commands ###
