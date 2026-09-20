"""Only one published version per measure."""
from alembic import op
import sqlalchemy as sa

revision = '20260918_one_published'
down_revision = 'e3f44b13bbfa'
branch_labels = None
depends_on = None

def upgrade():
    op.create_index('uq_measure_published', 'measure_versions', ['measure_id'], unique=True,
                    postgresql_where=sa.text("state = 'published'"))

def downgrade():
    op.drop_index('uq_measure_published', table_name='measure_versions')
