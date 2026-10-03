import os
import glob

paths = [
    "c:/personal_projects/devflow/frontend/src/pages/*.tsx",
    "c:/personal_projects/devflow/frontend/src/components/*.tsx",
    "c:/personal_projects/devflow/frontend/src/components/**/*.tsx"
]

for p in paths:
    for filepath in glob.glob(p):
        with open(filepath, "r") as f:
            content = f.read()
        
        # Dashboard, Projects
        content = content.replace("filter(p: any) =>", "filter((p: any) =>")
        content = content.replace("map(p: any) =>", "map((p: any) =>")
        
        # ProjectCard, ProjectDetails
        content = content.replace("map(tech: string) =>", "map((tech: string) =>")
        
        # ProjectForm
        content = content.replace("map(s: any) =>", "map((s: any) =>")
        content = content.replace("filter(s: any) =>", "filter((s: any) =>")
        
        with open(filepath, "w") as f:
            f.write(content)

print("Fixed syntax errors")
