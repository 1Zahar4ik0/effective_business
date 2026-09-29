from alembic import op
import sqlalchemy as sa

revision = "20260927_round_acceptance"
down_revision = "20260927_plan_assessment"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "selection_rounds",
        sa.Column(
            "acceptance_status",
            sa.String(20),
            nullable=False,
            server_default="unconfirmed",
        ),
    )
    op.add_column(
        "selection_rounds",
        sa.Column("acceptance_checked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("selection_rounds", "acceptance_checked_at")
    op.drop_column("selection_rounds", "acceptance_status")
