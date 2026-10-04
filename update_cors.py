import sys
content = open('backend/app/main.py').read()
old_code = """# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)"""
new_code = """# Set all CORS enabled origins
allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()] if hasattr(settings, 'ALLOWED_ORIGINS') else [settings.FRONTEND_URL]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)"""
open('backend/app/main.py', 'w').write(content.replace(old_code, new_code))
