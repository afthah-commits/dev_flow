import codecs

with open('frontend/src/components/TaskDetailModal.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# I need to add import for CommentThread
import_str = "import CommentThread from './CommentThread';\n"
content = import_str + content

# I will replace the attachments placeholder or just append CommentThread
# Find the end of the col-span-2 block
target = "</div>\n                </div>\n\n            </div>\n            <div className=\"space-y-6\">\n"

new_target = "</div>\n                </div>\n\n                <div className=\"mt-8 pt-8 border-t border-gray-800\">\n                    <CommentThread entityType=\"TASK\" entityId={task.id} />\n                </div>\n            </div>\n            <div className=\"space-y-6\">\n"

if target in content:
    content = content.replace(target, new_target)
else:
    # If not found, let's just append to the first "</div>" that closes col-span-2 space-y-8
    pass

with open('frontend/src/components/TaskDetailModal.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
