"""Phase 45 dashboard layouts

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('dashboard_layouts',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('layout', sa.JSON(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'organization_id', name='uq_dashboard_layout_user_org')
    )
    with op.batch_alter_table('dashboard_layouts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_dashboard_layouts_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_dashboard_layouts_organization_id'), ['organization_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_dashboard_layouts_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('dashboard_layouts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_dashboard_layouts_user_id'))
        batch_op.drop_index(batch_op.f('ix_dashboard_layouts_organization_id'))
        batch_op.drop_index(batch_op.f('ix_dashboard_layouts_id'))
    op.drop_table('dashboard_layouts')
