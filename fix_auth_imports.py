import glob
files = glob.glob('backend/app/api/v1/*.py')
for f in files:
    with open(f, 'r') as file:
        content = file.read()
    if 'from app.models.auth import User' in content:
        content = content.replace('from app.models.auth import User', 'from app.models.user import User')
        with open(f, 'w') as file:
            file.write(content)
