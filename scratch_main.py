with open('backend/app/main.py', 'r') as f:
    content = f.read()

# Add imports
content = content.replace(
    'from app.api.v1 import knowledge',
    'from app.api.v1 import knowledge, clients, client_portal'
)

# Mount routers
mounts = '''
app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
app.include_router(client_portal.router, prefix="/api/v1/client-portal", tags=["client-portal"])
'''

content = content.replace('app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])', 'app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])' + mounts)

with open('backend/app/main.py', 'w') as f:
    f.write(content)
