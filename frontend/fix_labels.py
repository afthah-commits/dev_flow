import re

def fix_labels(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    # Find label + Input pairs
    content = re.sub(
        r'<label className="block text-sm font-medium text-gray-300 mb-1">Email address</label>\s*<Input type="email"',
        r'<label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-1">Email address</label>\n        <Input id="email" type="email"',
        content
    )
    content = re.sub(
        r'<label className="block text-sm font-medium text-gray-300 mb-1">Password</label>\s*<Input type="password"',
        r'<label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1">Password</label>\n        <Input id="password" type="password"',
        content
    )
    content = re.sub(
        r'<label className="block text-sm font-medium text-gray-300 mb-1">Name</label>\s*<Input required',
        r'<label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">Name</label>\n        <Input id="name" required',
        content
    )
    
    with open(filepath, "w") as f:
        f.write(content)

fix_labels("c:/personal_projects/devflow/frontend/src/pages/Login.tsx")
fix_labels("c:/personal_projects/devflow/frontend/src/pages/Register.tsx")
print("Labels fixed.")
