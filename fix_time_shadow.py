with open('backend/app/main.py', 'r') as f:
    c = f.read()

c = c.replace('import time\nimport uuid', 'import time as _time\nimport uuid')
c = c.replace('start_time = time.time()', 'start_time = _time.time()')
c = c.replace('process_time = time.time() - start_time', 'process_time = _time.time() - start_time')

with open('backend/app/main.py', 'w') as f:
    f.write(c)
