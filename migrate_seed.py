import json
import sys
import uuid
from app.services import AuthService
from app.models import Base, User, Project, Task, Message, Role, Permission, RolePermission, UserRole, Template, UploadedFile, ScriptFolder, Script
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
    seed_script_folders()
    seed_scripts()


def migrate():
    Base.metadata.create_all(bind=engine)
    migrate_messages_v2()
    print("Database tables created successfully!")


def migrate_messages_v2():
    """Add structured columns to messages table (v2 schema)."""
    import sqlite3
    from config.database import DATABASE_URL
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    new_columns = [
        ("images", "TEXT NOT NULL DEFAULT ''"),
        ("available_inputs", "TEXT NOT NULL DEFAULT ''"),
        ("goal_types", "TEXT NOT NULL DEFAULT ''"),
        ("workflow_candidates", "TEXT NOT NULL DEFAULT ''"),
        ("required_files", "TEXT NOT NULL DEFAULT ''"),
        ("result_content", "TEXT NOT NULL DEFAULT ''"),
        ("result_files", "TEXT NOT NULL DEFAULT ''"),
        ("next_steps", "TEXT NOT NULL DEFAULT ''"),
    ]

    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE messages ADD COLUMN {col_name} {col_type}")
            print(f"  Added column messages.{col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                pass  # already exists
            else:
                raise

    # Backfill existing rows
    EXTRACT_MAP = {
        "images": "images",
        "available_inputs": "available_inputs",
        "goal_types": "goal_types",
        "candidates": "workflow_candidates",
        "required_files": "required_files",
        "results": "result_content",
        "files": "result_files",
        "nextSteps": "next_steps",
    }

    cursor.execute("SELECT id, data FROM messages WHERE data IS NOT NULL AND data != ''")
    rows = cursor.fetchall()

    updated = 0
    for msg_id, data_str in rows:
        try:
            data = json.loads(data_str)
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(data, dict):
            continue

        col_values = {}
        for data_key, col_name in EXTRACT_MAP.items():
            if data_key in data:
                val = data.pop(data_key)
                col_values[col_name] = json.dumps(val, ensure_ascii=False) if val else ""

        if col_values:
            remaining = json.dumps(data, ensure_ascii=False) if data else ""
            sets = ", ".join(f"{col} = ?" for col in col_values)
            values = list(col_values.values()) + [remaining, msg_id]
            cursor.execute(
                f"UPDATE messages SET {sets}, data = ? WHERE id = ?",
                values,
            )
            updated += 1

    conn.commit()
    conn.close()
    if updated:
        print(f"  Backfilled {updated} messages with structured columns.")


def migrate_fresh():
    """Drop all tables and recreate them"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database tables recreated successfully!")


def seed_script_folders():
    session = SessionLocal()
    try:
        if session.query(ScriptFolder).count() == 0:
            folders = [
                ScriptFolder(name="数据预处理", parent_id=0, sort_order=1),
                ScriptFolder(name="质量控制", parent_id=0, sort_order=2),
                ScriptFolder(name="核心分析", parent_id=0, sort_order=3),
                ScriptFolder(name="多样性分析", parent_id=0, sort_order=4),
                ScriptFolder(name="统计检验", parent_id=0, sort_order=5),
                ScriptFolder(name="可视化", parent_id=0, sort_order=6),
                ScriptFolder(name="排序分析", parent_id=0, sort_order=7),
                ScriptFolder(name="功能预测", parent_id=0, sort_order=8),
            ]
            session.add_all(folders)
            session.commit()
            print("Seed script_folders created successfully!")
        else:
            print("Script folders already exist, skipping seed.")
    finally:
        session.close()


def seed_scripts():
    from pkg.amplicon.amplicon_tools import get_all_tools, DATA_TYPE_NAMES
    session = SessionLocal()
    try:
        if session.query(Script).count() == 0:
            tools = get_all_tools()
            category_folder = {
                "数据预处理": 1, "质量控制": 2, "核心分析": 3,
                "多样性分析": 4, "统计检验": 5, "可视化": 6,
                "排序分析": 7, "功能预测": 8,
            }
            tool_file_map = {
                "amp-import-fasta": "amplicon/01_import_fasta.sh",
                "amp-cutadapt": "amplicon/02_cutadapt.sh",
                "amp-flash": "amplicon/03_flash.sh",
                "amp-frags-qc": "amplicon/04_qc.sh",
                "amp-dada2": "amplicon/05_dada2.sh",
                "amp-taxonomy": "amplicon/06_taxonomy.sh",
                "amp-phylogeny": "amplicon/07_phylogeny.sh",
                "amp-feature-tables": "amplicon/08_feature_tables.sh",
                "amp-table-stats": "amplicon/09_table_stats.sh",
                "amp-alpha-data": "amplicon/10_alpha_data.R",
                "amp-beta-data": "amplicon/11_beta_data.R",
                "amp-upgma": "amplicon/12_upgma.R",
                "amp-alpha-div": "amplicon/13_alpha_div.R",
                "amp-alpha-rarefaction": "amplicon/14_alpha_rarefaction.R",
                "amp-beta-div": "amplicon/15_beta_div.R",
                "amp-catecomp": "amplicon/16_catecomp.R",
                "amp-lefse": "amplicon/17_lefse.R",
                "amp-metastat": "amplicon/18_metastat.R",
                "amp-randomforest": "amplicon/19_randomforest.R",
                "amp-simper": "amplicon/20_simper.R",
                "amp-ttest": "amplicon/21_ttest.R",
                "amp-top-species": "amplicon/22_top_species.R",
                "amp-genus-tree": "amplicon/23_genus_tree.R",
                "amp-krona": "amplicon/24_krona.R",
                "amp-network": "amplicon/25_network.R",
                "amp-network3d": "amplicon/26_network3d.R",
                "amp-otutree": "amplicon/27_otutree.R",
                "amp-taxasummary": "amplicon/28_taxa_heatmap.R",
                "amp-taxasummary-group": "amplicon/29_taxa_heatmap_group.R",
                "amp-ternary": "amplicon/30_ternary.R",
                "amp-venn": "amplicon/31_venn.R",
                "amp-pca": "amplicon/32_pca.R",
                "amp-pcoa": "amplicon/33_pcoa.R",
                "amp-nmds": "amplicon/34_nmds.R",
                "amp-dca": "amplicon/35_dca.R",
                "amp-funpre": "amplicon/36_picrust2.sh",
            }
            scripts = []
            for tool in tools:
                file_path = tool_file_map.get(tool.id, "")
                folder_id = category_folder.get(tool.category, 1)
                scripts.append(Script(
                    name=tool.name,
                    description=f"{tool.name} — 输入: {', '.join(DATA_TYPE_NAMES.get(i, i) for i in tool.inputs)}; 输出: {', '.join(DATA_TYPE_NAMES.get(o, o) for o in tool.outputs)}",
                    folder_id=folder_id,
                    tool_id=tool.id,
                    category=tool.category,
                    file_path=file_path,
                    inputs=json.dumps(tool.inputs),
                    outputs=json.dumps(tool.outputs),
                    runtime=5 + len(tool.outputs) * 3,
                    cost=round(1.0 + len(tool.outputs) * 0.8, 1),
                    weight=len(tool.outputs),
                    verified=1,
                    is_active=1,
                    uploaded_by=1,
                    verified_by=1,
                ))
            session.add_all(scripts)
            session.commit()
            print(f"Seed scripts created successfully! ({len(scripts)} scripts)")
        else:
            print("Scripts already exist, skipping seed.")
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fresh":
        migrate_fresh()
    else:
        migrate()
    seed()
