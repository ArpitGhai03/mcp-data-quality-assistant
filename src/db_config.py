"""
PostgreSQL database configuration
"""

import os
from dotenv import load_dotenv
import sys

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

# PostgreSQL connection settings
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", 5432))
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")

# Database names
PROD_DB_NAME = os.getenv("PROD_DB_NAME", "prod")
STAGING_DB_NAME = os.getenv("STAGING_DB_NAME", "staging")


def get_prod_config():
    """Get production database configuration"""
    return {
        "host": PG_HOST,
        "port": PG_PORT,
        "database": PROD_DB_NAME,
        "user": PG_USER,
        "password": PG_PASSWORD,
    }


def get_staging_config():
    """Get staging database configuration"""
    return {
        "host": PG_HOST,
        "port": PG_PORT,
        "database": STAGING_DB_NAME,
        "user": PG_USER,
        "password": PG_PASSWORD,
    }
