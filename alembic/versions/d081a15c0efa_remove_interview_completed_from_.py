from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd081a15c0efa'
down_revision = '92722301a473'
branch_labels = None
depends_on = None


old_enum = sa.Enum(
    'PENDING', 'REVIEWED', 'INTERVIEW_SCHEDULED', 'INTERVIEW COMPLETED', 'REJECTED',
    name='applicationstatus'
)

new_enum = sa.Enum(
    'PENDING', 'REVIEWED', 'INTERVIEW_SCHEDULED', 'REJECTED',
    name='applicationstatus'
)


def upgrade():
    op.execute("ALTER TYPE applicationstatus RENAME TO applicationstatus_old")
    new_enum.create(op.get_bind(), checkfirst=False)

    op.execute("""
        ALTER TABLE job_applications
        ALTER COLUMN status TYPE applicationstatus
        USING status::text::applicationstatus
    """)

    op.execute("DROP TYPE applicationstatus_old")


def downgrade():
    old_enum.create(op.get_bind(), checkfirst=False)

    op.execute("""
        ALTER TABLE job_applications
        ALTER COLUMN status TYPE applicationstatus_old
        USING status::text::applicationstatus_old
    """)

    op.execute("DROP TYPE applicationstatus")
    op.execute("ALTER TYPE applicationstatus_old RENAME TO applicationstatus")
