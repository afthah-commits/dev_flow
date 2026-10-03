import os

with open("c:/personal_projects/devflow/backend/.env", "r", encoding="utf-16", errors="ignore") as f:
    content = f.read()

# I will just write a new .env properly
env_content = """PROJECT_NAME="DevFlow API"
SECRET_KEY="your-super-secret-key-change-in-production"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL="sqlite:///./devflow.db"
FRONTEND_URL="http://localhost:5173"
BACKEND_URL="http://localhost:8000"

GITHUB_CLIENT_ID="dummy"
GITHUB_CLIENT_SECRET="dummy"
GITHUB_REDIRECT_URI="http://localhost:5173/settings/integrations/github/callback"
GITHUB_TOKEN_ENCRYPTION_KEY="mrUWABO0dyyamtbGr34IZ7CDPbDRgtVMrv7xJ4lFA7Q="
"""

with open("c:/personal_projects/devflow/backend/.env", "w", encoding="utf-8") as f:
    f.write(env_content)
    
print("Fixed .env")
