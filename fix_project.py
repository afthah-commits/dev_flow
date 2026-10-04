with open('backend/app/models/project.py', 'r') as f:
    c = f.read()

c = c.replace('status = Column(Enum(ProjectStatus, native_enum=False), default=ProjectStatus.PLANNING, nullable=False)',
              'status = Column(Enum(ProjectStatus, native_enum=False), default=ProjectStatus.PLANNING, nullable=False, index=True)')
c = c.replace('priority = Column(Enum(ProjectPriority, native_enum=False), default=ProjectPriority.MEDIUM, nullable=False)',
              'priority = Column(Enum(ProjectPriority, native_enum=False), default=ProjectPriority.MEDIUM, nullable=False, index=True)')
c = c.replace('created_at = Column(DateTime(timezone=True), server_default=func.now())',
              'created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)')

with open('backend/app/models/project.py', 'w') as f:
    f.write(c)
