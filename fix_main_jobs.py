with open('backend/app/main.py', 'r') as f:
    c = f.read()

import re
if 'job_engine.start()' not in c:
    c = c.replace('app = FastAPI(', 'from app.core.jobs import job_engine\napp = FastAPI(')
    
    events = '''
@app.on_event("startup")
async def startup_event():
    job_engine.start()

@app.on_event("shutdown")
async def shutdown_event():
    job_engine.stop()
'''
    c = c.replace('app = FastAPI(', events + '\napp = FastAPI(')

with open('backend/app/main.py', 'w') as f:
    f.write(c)
