with open('frontend/src/pages/ProjectDetails.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "{activeTab === 'roadmap' && <Roadmap project={project} />}",
    "{activeTab === 'roadmap' && <Roadmap project={project} />}\n        {activeTab === 'releases' && <Releases />}\n        {activeTab === 'deployments' && <Deployments />}\n        {activeTab === 'pipelines' && <PipelineRuns />}"
)

with open('frontend/src/pages/ProjectDetails.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
