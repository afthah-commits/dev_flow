"""Phase 44 project templates

Revision ID: a1b2c3d4e5f6
Revises: 86f704f37613
Create Date: 2026-10-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '86f704f37613'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('project_templates',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('created_by_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('project_templates', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_project_templates_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_project_templates_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_project_templates_organization_id'), ['organization_id'], unique=False)

    op.create_table('project_template_tasks',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('template_id', sa.Uuid(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='taskpriority', native_enum=False), nullable=False),
    sa.Column('label_names', sa.JSON(), nullable=True),
    sa.Column('checklist_items', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['template_id'], ['project_templates.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('project_template_tasks', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_project_template_tasks_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_project_template_tasks_template_id'), ['template_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('project_template_tasks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_project_template_tasks_template_id'))
        batch_op.drop_index(batch_op.f('ix_project_template_tasks_id'))
    op.drop_table('project_template_tasks')

    with op.batch_alter_table('project_templates', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_project_templates_organization_id'))
        batch_op.drop_index(batch_op.f('ix_project_templates_name'))
        batch_op.drop_index(batch_op.f('ix_project_templates_id'))
    op.drop_table('project_templates')
