import os

# Application settings
APP_NAME = "BioFlow"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "True") == "True"

# Security
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
