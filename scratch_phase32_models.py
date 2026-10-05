import re

with open('backend/app/models/delivery.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_enum = '''class ReleaseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PLANNED = "PLANNED"
    READY = "READY"
    RELEASED = "RELEASED"
    CANCELLED = "CANCELLED"'''

new_enum = '''class ReleaseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    APPROVED = "APPROVED"
    DEPLOYING = "DEPLOYING"
    DEPLOYED = "DEPLOYED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    CANCELLED = "CANCELLED"'''

text = text.replace(old_enum, new_enum)

old_release = '''    planned_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    
    created_by_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)'''

new_release = '''    planned_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    deployment_timestamp = Column(DateTime(timezone=True), nullable=True)
    rollback_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    created_by_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)'''

text = text.replace(old_release, new_release)

new_approval = '''
class ReleaseApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"

class ReleaseApproval(Base):
    __tablename__ = "release_approvals"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    release_id = Column(Uuid, ForeignKey("releases.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewer_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(ReleaseApprovalStatus, native_enum=False), default=ReleaseApprovalStatus.PENDING, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    release = relationship("Release")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
'''

text += new_approval

with open('backend/app/models/delivery.py', 'w', encoding='utf-8') as f:
    f.write(text)
