"""
run.py
"""

import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host=os.environ.get("HOST", "0.0.0.0"), debug=debug, port=int(os.environ.get("PORT", 5000)))
