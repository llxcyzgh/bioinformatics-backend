import sys
from app.services import AuthService
from app.models import Base, User
from database import engine, SessionLocal


def seed_users():
    session = SessionLocal()
    try:
        if session.query(User).count() == 0:
            users = [
                User(
                    email="admin@bioflow.com",
                    username="admin",
                    hashed_password=AuthService.hash_password("admin123"),
                    full_name="Administrator"
                ),
                User(
                    email="researcher@bioflow.com",
                    username="researcher",
                    hashed_password=AuthService.hash_password("research123"),
                    full_name="Researcher"
                ),
                User(
                    email="student@bioflow.com",
                    username="student",
                    hashed_password=AuthService.hash_password("student123"),
                    full_name="Student User"
                ),
            ]
            session.add_all(users)
            session.commit()
            print("Seed data created successfully!")
        else:
            print("Users already exist, skipping seed.")
    finally:
        session.close()


def migrate():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def migrate_fresh():
    """Drop all tables and recreate them"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database tables recreated successfully!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fresh":
        migrate_fresh()
    else:
        migrate()
    seed_users()
