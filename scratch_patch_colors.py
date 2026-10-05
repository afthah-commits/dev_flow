with open('frontend/src/pages/Releases.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("r.status === 'RELEASED'", "r.status === 'DEPLOYED'")
text = text.replace("r.status === 'PLANNED'", "r.status === 'APPROVED'")
text = text.replace("handleAction('plan')", "handleAction('ready')")
text = text.replace("handleAction('ready')", "handleAction('approve')") // this line might be messed up if I just replace

with open('frontend/src/pages/Releases.tsx', 'w', encoding='utf-8') as f:
    f.write(text)
