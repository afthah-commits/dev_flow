import sys
sys.path = [p for p in sys.path if 'crmappclone' not in p]
sys.path.insert(0, 'C:\\personal_projects\\devflow\\backend')

import pytest
sys.exit(pytest.main(["tests/test_time.py"]))
