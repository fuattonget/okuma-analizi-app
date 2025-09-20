#!/usr/bin/env python3
"""
Test runner script
"""
import os
import sys
import subprocess
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables
os.environ.setdefault("TEST_MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("TEST_DB_NAME", "okuma_analizi_test")
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB", "okuma_analizi_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("LOG_FORMAT", "text")
os.environ.setdefault("DEBUG", "false")

def run_tests():
    """Run all tests"""
    print("🧪 Running Okuma Analizi Tests")
    print("=" * 50)
    
    # Test files to run
    test_files = [
        "test_models_indexes.py",
        "test_migration_v2.py", 
        "test_analysis_pipeline_events.py",
        "test_api_sessions.py"
    ]
    
    # Run each test file
    for test_file in test_files:
        print(f"\n📋 Running {test_file}...")
        print("-" * 30)
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                f"tests/{test_file}",
                "-v",
                "--tb=short",
                "--asyncio-mode=auto"
            ], cwd=project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {test_file} passed")
            else:
                print(f"❌ {test_file} failed")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                
        except Exception as e:
            print(f"💥 Error running {test_file}: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test run completed")

if __name__ == "__main__":
    run_tests()

