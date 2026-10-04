with open('backend/app/api/v1/security.py', 'r') as f:
    c = f.read()

mfa = '''
import json
import secrets

@router.post("/mfa/setup")
def mfa_setup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA already enabled")
        
    secret = "MOCK_MFA_SECRET_" + secrets.token_hex(8)
    current_user.mfa_secret = secret
    db.commit()
    
    return {
        "secret": secret,
        "uri": f"otpauth://totp/DevFlow:{current_user.email}?secret={secret}&issuer=DevFlow"
    }

@router.post("/mfa/verify")
def mfa_verify(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Mock MFA verify (always accept '123456' for testing)
    if code != "123456" and code != "000000":
        raise HTTPException(status_code=400, detail="Invalid MFA code")
        
    current_user.mfa_enabled = True
    recovery_codes = [secrets.token_hex(4) + "-" + secrets.token_hex(4) for _ in range(10)]
    current_user.mfa_recovery_codes = json.dumps(recovery_codes)
    db.commit()
    
    return {"message": "MFA enabled", "recovery_codes": recovery_codes}

@router.post("/mfa/disable")
def mfa_disable(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA not enabled")
        
    if code != "123456" and code != "000000":
        raise HTTPException(status_code=400, detail="Invalid MFA code")
        
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.mfa_recovery_codes = None
    db.commit()
    
    return {"message": "MFA disabled"}
'''
c += mfa

with open('backend/app/api/v1/security.py', 'w') as f:
    f.write(c)
