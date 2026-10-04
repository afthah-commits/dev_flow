with open('frontend/src/pages/AutomationDetails.tsx', 'r') as f:
    c = f.read()

c = c.replace(r'navigate(\/automations/\\);', 'navigate(`/automations/${res.id}`);')

with open('frontend/src/pages/AutomationDetails.tsx', 'w') as f:
    f.write(c)
