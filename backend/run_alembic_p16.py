import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if 'crmappclone' not in p]
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

import alembic.config
alembicArgs = [
    'revision', '--autogenerate', '-m', 'add integration webhook apikey models'
]
alembic.config.main(argv=alembicArgs)
