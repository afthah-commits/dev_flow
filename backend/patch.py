import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'CorrelationIdMiddleware' not in content:
    replacement = """openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

from app.core.exceptions import add_exception_handlers
from app.core.middleware import CorrelationIdMiddleware

add_exception_handlers(app)
app.add_middleware(CorrelationIdMiddleware)
"""
    content = re.sub(r'openapi_url=f"\{settings\.API_V1_STR\}/openapi\.json"\s*\)', replacement, content)
    with open('app/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
