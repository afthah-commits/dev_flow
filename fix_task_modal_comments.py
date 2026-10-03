import re
with open('frontend/src/components/TaskDetailModal.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# We want to add <CommentThread entityType="TASK" entityId={task.id} /> just before <div className="col-span-1 space-y-6">
target = '<div className="col-span-1 space-y-6">'
new_text = '<div className="mt-8 pt-8 border-t border-gray-800"><CommentThread entityType="TASK" entityId={task.id} /></div>\n            ' + target

content = content.replace(target, new_text)

with open('frontend/src/components/TaskDetailModal.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
