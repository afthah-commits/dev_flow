import codecs

with open('backend/app/db/base.py', 'rb') as f:
    content = f.read()

# Replace null bytes (if any)
clean = content.replace(b'\x00', b'')

with open('backend/app/db/base.py', 'wb') as f:
    f.write(clean)
