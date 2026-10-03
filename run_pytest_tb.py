import sys, os, pytest
backend_dir = os.path.dirname(os.path.abspath('backend/run_pytest.py'))
bad_paths = [p for p in sys.path if "devflow" in p and "devflow\\\backend" not in p]
for p in bad_paths:
    sys.path.remove(p)
sys.path.insert(0, backend_dir)
sys.exit(pytest.main([os.path.join(backend_dir, "tests", "test_github.py"), "--tb=short"]))
