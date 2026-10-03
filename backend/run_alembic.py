import sys
# Remove conflicting paths
sys.path = [p for p in sys.path if 'crmappclone' not in p]
sys.path.insert(0, 'C:\\personal_projects\\devflow\\backend')

from alembic.config import main
sys.exit(main())
