import sys
import uuid
from app.services import AuthService
from app.models import Base, User, Project, Task, Message, Role, Permission, RolePermission, UserRole, Template
from database import engine, SessionLocal


def seed_roles():
    session = SessionLocal()
    try:
        if session.query(Role).count() == 0:
            roles = [
                Role(name="admin", description="系统管理员"),
                Role(name="user", description="普通用户"),
            ]
            session.add_all(roles)
            session.commit()
            print("Seed roles created successfully!")
        else:
            print("Roles already exist, skipping seed.")
    finally:
        session.close()


def seed_permissions():
    session = SessionLocal()
    try:
        if session.query(Permission).count() == 0:
            permissions = [
                Permission(name="project.create", description="创建项目"),
                Permission(name="project.read", description="查看项目"),
                Permission(name="project.update", description="更新项目"),
                Permission(name="project.delete", description="删除项目"),
                Permission(name="task.create", description="创建任务"),
                Permission(name="task.read", description="查看任务"),
                Permission(name="task.update", description="更新任务"),
                Permission(name="task.delete", description="删除任务"),
                Permission(name="message.create", description="创建消息"),
                Permission(name="message.read", description="查看消息"),
            ]
            session.add_all(permissions)
            session.commit()
            print("Seed permissions created successfully!")
        else:
            print("Permissions already exist, skipping seed.")
    finally:
        session.close()


def seed_role_permissions():
    session = SessionLocal()
    try:
        if session.query(RolePermission).count() == 0:
            # admin (id=1) 拥有全部权限 (1-10)
            admin_perms = [RolePermission(role_id=1, permission_id=i) for i in range(1, 11)]
            # user (id=2) 拥有部分权限
            user_perms = [
                RolePermission(role_id=2, permission_id=1),   # project.create
                RolePermission(role_id=2, permission_id=2),   # project.read
                RolePermission(role_id=2, permission_id=5),   # task.create
                RolePermission(role_id=2, permission_id=6),   # task.read
                RolePermission(role_id=2, permission_id=9),   # message.create
                RolePermission(role_id=2, permission_id=10),  # message.read
            ]
            session.add_all(admin_perms + user_perms)
            session.commit()
            print("Seed role_permissions created successfully!")
        else:
            print("Role permissions already exist, skipping seed.")
    finally:
        session.close()


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


def seed_user_roles():
    session = SessionLocal()
    try:
        if session.query(UserRole).count() == 0:
            user_roles = [
                UserRole(user_id=1, role_id=1),  # admin -> admin role
                UserRole(user_id=2, role_id=2),  # user -> user role
            ]
            session.add_all(user_roles)
            session.commit()
            print("Seed user_roles created successfully!")
        else:
            print("User roles already exist, skipping seed.")
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


def seed_templates():
    session = SessionLocal()
    try:
        if session.query(Template).count() == 0:
            templates = [
                Template(
                    name="FastQC Quality Report",
                    description="Run FastQC on FASTQ files and generate quality report",
                    is_public=True,
                    user_id=1,
                    scripts="fastqc -t 4 -o ./results/fastqc *.fastq.gz"
                ),
                Template(
                    name="HISAT2 Alignment",
                    description="Align RNA-Seq reads to reference genome using HISAT2",
                    is_public=True,
                    user_id=1,
                    scripts="hisat2 -x genome_index -1 R1.fastq.gz -2 R2.fastq.gz -S aligned.sam"
                ),
                Template(
                    name="Custom Analysis",
                    description="Private custom analysis template",
                    is_public=False,
                    user_id=2,
                    scripts=""
                ),
            ]
            session.add_all(templates)
            session.commit()
            print("Seed templates created successfully!")
        else:
            print("Templates already exist, skipping seed.")
    finally:
        session.close()


def seed():
    seed_roles()
    seed_permissions()
    seed_role_permissions()
    seed_users()
    seed_user_roles()
    seed_projects()
    seed_tasks()
    seed_messages()
    seed_templates()


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
