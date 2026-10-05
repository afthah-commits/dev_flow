import re

with open('backend/app/api/v1/delivery.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Make sure ReleaseEngine is imported
if "from app.services.release_engine import ReleaseEngine" not in text:
    text = text.replace("from app.services.delivery import DeliveryService", "from app.services.delivery import DeliveryService\nfrom app.services.release_engine import ReleaseEngine")

# Find the get_readiness function and replace it
pattern = r"@releases_router\.get\(\"/\{release_id\}/readiness\", response_model=ReleaseReadiness\)\ndef get_readiness.*?return ReleaseReadiness\(.*?\)"

new_func = '''@releases_router.get("/{release_id}/readiness", response_model=ReleaseReadiness)
def get_readiness(release_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    
    result = ReleaseEngine.evaluate_readiness(db, release)
    return ReleaseReadiness(**result)'''

text = re.sub(pattern, new_func, text, flags=re.DOTALL)

with open('backend/app/api/v1/delivery.py', 'w', encoding='utf-8') as f:
    f.write(text)
