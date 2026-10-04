import os

with open('backend/app/api/deps.py', 'r') as f:
    content = f.read()

dep_code = '''
from fastapi.security import APIKeyHeader
from app.models.api_key import APIKey
import hashlib
from datetime import datetime, timezone
import json

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def get_api_key_auth(
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_header)
) -> APIKey:
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key required")
    
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
        
    hashed = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
    
    db_key = db.query(APIKey).filter(APIKey.key_hash == hashed).first()
    if not db_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
        
    if db_key.revoked_at:
        raise HTTPException(status_code=401, detail="API Key revoked")
        
    if db_key.expires_at and db_key.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="API Key expired")
        
    db_key.last_used_at = datetime.now(timezone.utc)
    db.commit()
    
    return db_key
'''

if "def get_api_key_auth" not in content:
    content += dep_code
    with open('backend/app/api/deps.py', 'w') as f:
        f.write(content)
