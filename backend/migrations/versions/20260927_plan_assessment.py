from alembic import op
import sqlalchemy as sa

revision = "20260927_plan_assessment"
down_revision = "20260918_one_published"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "preparation_plans", sa.Column("assessment", sa.JSON(), nullable=True)
    )


def downgrade():
    op.drop_column("preparation_plans", "assessment")
