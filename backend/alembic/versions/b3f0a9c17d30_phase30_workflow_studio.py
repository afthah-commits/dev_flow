"""phase30_workflow_studio

Revision ID: b3f0a9c17d30
Revises: 70994c719dcd
Create Date: 2026-10-04 22:10:00.000000

Phase 30 — Visual Workflow Studio & Advanced Form Builder.

Additive-only migration:
- New tables: workflow_versions, workflow_state_layouts
- New columns: workflow_states.state_type / approval_config,
  workflow_transitions.description / approval_config,
  workflow_executions.workflow_version_id / trigger_source / error_message

Never deletes existing data. Uses batch_alter_table so it works on SQLite
and PostgreSQL alike.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f0a9c17d30'
down_revision: Union[str, Sequence[str], None] = '70994c719dcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('workflow_versions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('workflow_id', sa.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'PUBLISHED', 'ARCHIVED', name='workflowversionstatus', native_enum=False), nullable=False),
        sa.Column('snapshot', sa.JSON(), nullable=True),
        sa.Column('change_note', sa.Text(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', 'version_number', name='uq_workflow_version_number')
    )
    with op.batch_alter_table('workflow_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_workflow_versions_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_workflow_versions_organization_id'), ['organization_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_workflow_versions_workflow_id'), ['workflow_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_workflow_versions_status'), ['status'], unique=False)

    op.create_table('workflow_state_layouts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workflow_id', sa.UUID(), nullable=False),
        sa.Column('state_id', sa.UUID(), nullable=False),
        sa.Column('x', sa.Float(), nullable=False),
        sa.Column('y', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['state_id'], ['workflow_states.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', 'state_id', name='uq_workflow_state_layout')
    )
    with op.batch_alter_table('workflow_state_layouts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_workflow_state_layouts_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_workflow_state_layouts_workflow_id'), ['workflow_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_workflow_state_layouts_state_id'), ['state_id'], unique=False)

    with op.batch_alter_table('workflow_states', schema=None) as batch_op:
        batch_op.add_column(sa.Column('state_type', sa.String(), nullable=False, server_default='NORMAL'))
        batch_op.add_column(sa.Column('approval_config', sa.JSON(), nullable=True))

    with op.batch_alter_table('workflow_transitions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('approval_config', sa.JSON(), nullable=True))

    with op.batch_alter_table('workflow_executions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('workflow_version_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('trigger_source', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('error_message', sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            'fk_workflow_executions_version',
            'workflow_versions',
            ['workflow_version_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('workflow_executions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_workflow_executions_version', type_='foreignkey')
        batch_op.drop_column('error_message')
        batch_op.drop_column('trigger_source')
        batch_op.drop_column('workflow_version_id')

    with op.batch_alter_table('workflow_transitions', schema=None) as batch_op:
        batch_op.drop_column('approval_config')
        batch_op.drop_column('description')

    with op.batch_alter_table('workflow_states', schema=None) as batch_op:
        batch_op.drop_column('approval_config')
        batch_op.drop_column('state_type')

    with op.batch_alter_table('workflow_state_layouts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_workflow_state_layouts_state_id'))
        batch_op.drop_index(batch_op.f('ix_workflow_state_layouts_workflow_id'))
        batch_op.drop_index(batch_op.f('ix_workflow_state_layouts_id'))

    op.drop_table('workflow_state_layouts')

    with op.batch_alter_table('workflow_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_workflow_versions_status'))
        batch_op.drop_index(batch_op.f('ix_workflow_versions_workflow_id'))
        batch_op.drop_index(batch_op.f('ix_workflow_versions_organization_id'))
        batch_op.drop_index(batch_op.f('ix_workflow_versions_id'))

    op.drop_table('workflow_versions')
