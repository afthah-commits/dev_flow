with open('frontend/src/pages/ProjectDetails.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

import_str = "import ProjectDiscussions from './ProjectDiscussions';\n"
content = import_str + content

content = content.replace(
    "{ id: 'activity', label: 'Activity' },",
    "{ id: 'activity', label: 'Activity' },\n            { id: 'discussions', label: 'Discussions' },"
)

content = content.replace(
    "{activeTab === 'pipelines' && <PipelineRuns />}",
    "{activeTab === 'pipelines' && <PipelineRuns />}\n        {activeTab === 'discussions' && <ProjectDiscussions projectId={project.id} />}"
)

# Also update the type
content = content.replace(
    ' | "deployments" | "pipelines">("overview");',
    ' | "deployments" | "pipelines" | "discussions">("overview");'
)

with open('frontend/src/pages/ProjectDetails.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
