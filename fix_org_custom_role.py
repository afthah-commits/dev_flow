with open('backend/app/models/organization.py', 'r') as f:
    c = f.read()

c = c.replace('''    team = relationship("Team", back_populates="members")
    user = relationship("User")
    custom_role = relationship("Role")''',
'''    team = relationship("Team", back_populates="members")
    user = relationship("User")''')

with open('backend/app/models/organization.py', 'w') as f:
    f.write(c)
