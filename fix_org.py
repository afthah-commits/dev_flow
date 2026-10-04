with open('backend/app/models/organization.py', 'r') as f:
    c = f.read()

c = c.replace('role = Column(Enum(OrganizationRole, native_enum=False), default=OrganizationRole.MEMBER, nullable=False)',
              'role = Column(Enum(OrganizationRole, native_enum=False), default=OrganizationRole.MEMBER, nullable=False)\n    custom_role_id = Column(Uuid, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)')

c = c.replace('user = relationship("User")',
              'user = relationship("User")\n    custom_role = relationship("Role")')

with open('backend/app/models/organization.py', 'w') as f:
    f.write(c)
