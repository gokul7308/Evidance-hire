import os
from pathlib import Path

class Config:
    # Base directory of the project
    BASE_DIR = Path(__file__).resolve().parent.parent

    # Database configuration
    DB_NAME = "evidence_hire.db"
    DB_PATH = os.path.join(BASE_DIR, DB_NAME)

    # Add other configurations here as needed
