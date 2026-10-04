with open('backend/app/main.py', 'r') as f:
    lines = f.readlines()

new_lines = []
middleware_buffer = []
in_middleware = False
for line in lines:
    if '@app.middleware("http")' in line or 'import time' in line or 'import uuid' in line or 'from fastapi import Request' in line:
        if 'import time' in line and not in_middleware:
            in_middleware = True
    if in_middleware:
        middleware_buffer.append(line)
        if 'return response' in line:
            in_middleware = False
    else:
        new_lines.append(line)

final_c = "".join(new_lines)
final_c = final_c.replace('openapi_url=f"{settings.API_V1_STR}/openapi.json"\n)', 'openapi_url=f"{settings.API_V1_STR}/openapi.json"\n)\n\n' + "".join(middleware_buffer))

with open('backend/app/main.py', 'w') as f:
    f.write(final_c)
