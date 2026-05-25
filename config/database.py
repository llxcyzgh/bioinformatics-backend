import os

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bioflow.db")
DB_CONNECT_ARGS = {"check_same_thread": False}
