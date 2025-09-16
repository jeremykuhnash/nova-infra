#!/usr/bin/env python3
"""Main Flask application entry point."""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.api import app  # noqa: E402

if __name__ == "__main__":
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))

    # Get debug mode from environment
    debug = os.environ.get("FLASK_ENV", "production") == "development"

    # Run the application
    app.run(host="0.0.0.0", port=port, debug=debug)
