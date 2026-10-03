import sys
# Remove conflicting paths
sys.path = [p for p in sys.path if 'crmappclone' not in p]
sys.path.insert(0, 'C:\\personal_projects\\devflow\\backend')

from alembic.config import main
sys.exit(main())

import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))

bad_paths = [p for p in sys.path if "devflow" in p and "devflow\\backend" not in p]
for p in bad_paths:
    sys.path.remove(p)

sys.path.insert(0, backend_dir)

from alembic.config import main
sys.exit(main())

