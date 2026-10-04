with open('backend/app/api/public_v1/public.py', 'r') as f:
    c = f.read()

if 'import uuid' not in c:
    c = "import uuid\n" + c
    with open('backend/app/api/public_v1/public.py', 'w') as f:
        f.write(c)
