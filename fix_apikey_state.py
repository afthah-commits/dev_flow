with open('frontend/src/pages/settings/ApiKeys.tsx', 'r') as f:
    c = f.read()

c = c.replace('setNewKey(res.raw_key);', 'setNewKey(res.raw_key || null);')

with open('frontend/src/pages/settings/ApiKeys.tsx', 'w') as f:
    f.write(c)
