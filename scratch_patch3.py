import re

with open('backend/app/services/automation_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'except Exception as e:\s+action_exec\.status = "FAILED"'
replacement = '''except Exception as e:
        action_exec.status = "FAILED"
        action_exec.output_data = {"error": str(e)}'''

text = re.sub(pattern, replacement, text)

with open('backend/app/services/automation_engine.py', 'w', encoding='utf-8') as f:
    f.write(text)
