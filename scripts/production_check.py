import os
import sys
import requests
import sqlite3
import subprocess

def check_env():
    print("Checking environment variables...")
    required_backend = ['DATABASE_URL', 'SECRET_KEY']
    for req in required_backend:
        # Don't print the actual value!
        if req in os.environ:
            print(f" [PASS] {req} is set")
        else:
            print(f" [WARN] {req} is NOT set in current environment")

def check_frontend_build():
    print("Checking frontend build...")
    if os.path.exists("frontend/dist/index.html"):
        print(" [PASS] Frontend build directory exists.")
    else:
        print(" [FAIL] Frontend build directory not found. Did you run 'npm run build'?")
        return False
    return True

def main():
    print("=== DevFlow Production Check ===")
    check_env()
    frontend_ok = check_frontend_build()
    
    if not frontend_ok:
        sys.exit(1)
        
    print("\nNote: Please ensure the backend is running and healthy by checking /health endpoint.")
    print("Production check completed.")

if __name__ == "__main__":
    main()
