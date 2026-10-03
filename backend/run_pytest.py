import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)

# Remove conflicting paths
sys.path = [p for p in sys.path if 'crmappclone' not in p]
bad_paths = [p for p in sys.path if "devflow" in p and "devflow\\backend" not in p]
for p in bad_paths:
    sys.path.remove(p)

sys.path.insert(0, backend_dir)

import pytest
sys.exit(pytest.main(["tests"]))
