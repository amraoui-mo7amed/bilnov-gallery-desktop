#!/usr/bin/env python3
"""
Bilnov Gallery Desktop Application Entrypoint
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from desktop.main import main

if __name__ == "__main__":
    main()
