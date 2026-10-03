with open('frontend/src/pages/ProjectDetails.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "{ id: 'roadmap', label: 'Roadmap' },",
    "{ id: 'roadmap', label: 'Roadmap' },\n            { id: 'releases', label: 'Releases' },\n            { id: 'deployments', label: 'Deployments' },\n            { id: 'pipelines', label: 'Pipelines' },"
)

with open('frontend/src/pages/ProjectDetails.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
