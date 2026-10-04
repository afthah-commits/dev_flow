import os
import sys

sys.path = [p for p in sys.path if 'crmappclone' not in p]
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    from alembic.config import main
    sys.exit(main())
