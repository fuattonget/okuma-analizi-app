#!/usr/bin/env python3
"""
Worker main entry point for RQ
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the job function so RQ can find it
from jobs import analyze_audio

# Make the function available at module level for RQ
# This allows RQ to call it as "main.analyze_audio" or "jobs.analyze_audio"
analyze_audio = analyze_audio

if __name__ == "__main__":
    # This file is imported by RQ worker
    # The analyze_audio function is now available for RQ to call
    print("Worker main.py loaded successfully")
    print(f"analyze_audio function available: {analyze_audio}")
    pass