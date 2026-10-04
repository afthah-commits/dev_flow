import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)

sys.path = [p for p in sys.path if 'crmappclone' not in p]
sys.path.insert(0, backend_dir)

import pytest
sys.exit(pytest.main(["tests/test_automations.py", "tests/test_p16.py", "tests/test_webhooks_integrations.py", "-v", "--tb=short"]))
