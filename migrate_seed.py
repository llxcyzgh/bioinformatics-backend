import sys
import uuid
from app.services import AuthService
from app.models import Base, User, Project, Task, Message
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
                    email="user@bioflow.com",
                    username="user",
                    hashed_password=AuthService.hash_password("user123"),
                    full_name="User"
                ),
            ]
            session.add_all(users)
            session.commit()
            print("Seed users created successfully!")
        else:
            print("Users already exist, skipping seed.")
    finally:
        session.close()


def seed_projects():
    session = SessionLocal()
    try:
        if session.query(Project).count() == 0:
            projects = [
                Project(
                    name="Demo Project",
                    description="A demo project for testing",
                    user_id=1
                ),
                Project(
                    name="RNA-Seq Analysis",
                    description="RNA sequencing data analysis",
                    user_id=1
                ),
            ]
            session.add_all(projects)
            session.commit()
            print("Seed projects created successfully!")
        else:
            print("Projects already exist, skipping seed.")
    finally:
        session.close()


def seed_tasks():
    session = SessionLocal()
    try:
        if session.query(Task).count() == 0:
            tasks = [
                Task(
                    uuid=str(uuid.uuid4()),
                    name="Quality Control",
                    project_id=1,
                    user_id=1
                ),
                Task(
                    uuid=str(uuid.uuid4()),
                    name="Differential Expression",
                    project_id=2,
                    user_id=1
                ),
            ]
            session.add_all(tasks)
            session.commit()
            print("Seed tasks created successfully!")
        else:
            print("Tasks already exist, skipping seed.")
    finally:
        session.close()


def seed_messages():
    session = SessionLocal()
    try:
        if session.query(Message).count() == 0:
            messages = [
                Message(
                    task_id=1,
                    role="user",
                    type="text",
                    content="Please run quality control on the raw FASTQ files."
                ),
                Message(
                    task_id=1,
                    role="assistant",
                    type="text",
                    content="Quality control completed. All samples passed QC checks."
                ),
                Message(
                    task_id=2,
                    role="user",
                    type="text",
                    content="Find differentially expressed genes between control and treatment groups."
                ),
            ]
            session.add_all(messages)
            session.commit()
            print("Seed messages created successfully!")
        else:
            print("Messages already exist, skipping seed.")
    finally:
        session.close()


def seed():
    seed_users()
    seed_projects()
    seed_tasks()
    seed_messages()


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
    seed()
