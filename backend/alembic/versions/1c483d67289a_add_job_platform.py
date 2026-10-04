
"""Add Job platform

Revision ID: 1c483d67289a
Revises: ec2b93e3c3a3
Create Date: 2026-10-04 14:55:36.568478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c483d67289a'
down_revision: Union[str, None] = 'ec2b93e3c3a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('job_schedules',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('job_type', sa.String(), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=True),
    sa.Column('cron_expression', sa.String(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_job_schedules_org_id', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('job_schedules', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_schedules_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_schedules_organization_id'), ['organization_id'], unique=False)

    with op.batch_alter_table('job_executions', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_job_executions_job_id', 'jobs', ['job_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organization_id', sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column('job_type', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('priority', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('attempts', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('max_attempts', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True))
        batch_op.drop_index('ix_jobs_name')
        batch_op.drop_index('ix_jobs_next_run_at')
        batch_op.create_index(batch_op.f('ix_jobs_job_type'), ['job_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_jobs_organization_id'), ['organization_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_jobs_scheduled_at'), ['scheduled_at'], unique=False)
        batch_op.create_foreign_key('fk_jobs_org_id', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
        batch_op.drop_column('next_run_at')
        batch_op.drop_column('retry_count')
        batch_op.drop_column('task_name')
        batch_op.drop_column('name')


def downgrade() -> None:
    pass
