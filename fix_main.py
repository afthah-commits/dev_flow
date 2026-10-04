with open('backend/app/main.py', 'r') as f:
    c = f.read()

import textwrap

middlewares = textwrap.dedent('''\
    import time
    import uuid
    from fastapi import Request

    @app.middleware("http")
    async def add_security_and_observability_headers(request: Request, call_next):
        start_time = time.time()
        
        # Extract or generate Request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
            
        # Attach request_id to state
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Add Observability Headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Add Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
''')

c = c.replace('app = FastAPI(', middlewares + '\napp = FastAPI(')

health_endpoints = textwrap.dedent('''\
    from app.db.session import SessionLocal
    from sqlalchemy import text

    @app.get("/health")
    def health_check():
        return {"status": "ok"}
        
    @app.get("/health/database")
    def health_database():
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
        finally:
            db.close()

    @app.get("/health/workers")
    def health_workers():
        return {"status": "healthy", "message": "In-memory jobs processor active"}
''')

import re
c = re.sub(r'@app\.get\("/health"\)\s*def health_check\(\):\s*return \{"status": "ok"\}', health_endpoints, c)

with open('backend/app/main.py', 'w') as f:
    f.write(c)
