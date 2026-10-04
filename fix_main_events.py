with open('backend/app/main.py', 'r') as f:
    lines = f.readlines()

new_lines = []
events_buffer = []
in_events = False
for line in lines:
    if '@app.on_event("startup")' in line:
        in_events = True
    if in_events:
        events_buffer.append(line)
        if 'job_engine.stop()' in line:
            in_events = False
    else:
        new_lines.append(line)

final_c = "".join(new_lines)
final_c = final_c.replace('openapi_url=f"{settings.API_V1_STR}/openapi.json"\n)', 'openapi_url=f"{settings.API_V1_STR}/openapi.json"\n)\n\n' + "".join(events_buffer))

with open('backend/app/main.py', 'w') as f:
    f.write(final_c)
