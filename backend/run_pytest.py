import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if 'crmappclone' not in p]
sys.path.insert(0, backend_dir)

import pytest
sys.exit(pytest.main([os.path.join(backend_dir, "tests", "test_delivery.py")]))
