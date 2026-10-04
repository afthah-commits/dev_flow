content = open('backend/app/main.py', encoding='utf-8').read()
content = content.replace('prefix="/governance"', 'prefix=f"{settings.API_V1_STR}/governance"')
content = content.replace('prefix="/privacy"', 'prefix=f"{settings.API_V1_STR}/privacy"')
open('backend/app/main.py', 'w', encoding='utf-8').write(content)
