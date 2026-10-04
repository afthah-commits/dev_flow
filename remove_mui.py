import re

file_path = 'frontend/src/pages/jobs/JobCenter.tsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'import\s+{(.*?)}\s+from\s+[\'\"]@mui/material[\'\"];', '', content, flags=re.DOTALL)
content = content.replace('<Box', '<div').replace('</Box>', '</div>')
content = content.replace('<Typography', '<div').replace('</Typography>', '</div>')
content = content.replace('<Grid', '<div').replace('</Grid>', '</div>')
content = content.replace('<Paper', '<div').replace('</Paper>', '</div>')
content = content.replace('<FormControl', '<div').replace('</FormControl>', '</div>')
content = content.replace('<InputLabel', '<label').replace('</InputLabel>', '</label>')
content = content.replace('<Select', '<select').replace('</Select>', '</select>')
content = content.replace('<MenuItem', '<option').replace('</MenuItem>', '</option>')
content = content.replace('<Button', '<button').replace('</Button>', '</button>')
content = content.replace('<CircularProgress />', '<div>Loading...</div>')
content = content.replace('<TableContainer', '<div').replace('</TableContainer>', '</div>')
content = content.replace('<Table', '<table').replace('</Table>', '</table>')
content = content.replace('<TableHead', '<thead').replace('</TableHead>', '</thead>')
content = content.replace('<TableBody', '<tbody').replace('</TableBody>', '</tbody>')
content = content.replace('<TableRow', '<tr').replace('</TableRow>', '</tr>')
content = content.replace('<TableCell', '<td').replace('</TableCell>', '</td>')
content = content.replace('<Chip', '<span').replace('</Chip>', '</span>')
content = content.replace('<Dialog', '<dialog').replace('</Dialog>', '</dialog>')
content = content.replace('<DialogTitle', '<h2').replace('</DialogTitle>', '</h2>')
content = content.replace('<DialogContent', '<div').replace('</DialogContent>', '</div>')
content = content.replace('<DialogActions', '<div').replace('</DialogActions>', '</div>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
