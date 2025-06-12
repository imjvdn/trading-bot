#!/usr/bin/env python3
"""
Run the hedge fund simulator example.
This script is a wrapper to run the example from the project root.
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now import and run the example
from hedgefund_simulator.example import main

if __name__ == "__main__":
    main()
