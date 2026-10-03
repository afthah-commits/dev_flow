with open('frontend/src/layouts/DashboardLayout.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

import_str = "import { GlobalSearch } from '../components/GlobalSearch';\n"
content = import_str + content

target = "<div className=\"flex-1 flex flex-col min-w-0 overflow-hidden\">"
new_text = "<GlobalSearch />\n        " + target

content = content.replace(target, new_text)

with open('frontend/src/layouts/DashboardLayout.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
