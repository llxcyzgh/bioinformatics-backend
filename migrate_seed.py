import json
import sys
import uuid
from app.services import AuthService
from app.models import Base, User, Project, Task, Message, Role, Permission, RolePermission, UserRole, Template, UploadedFile, ScriptFolder, Script, Domain, DataType
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
    seed_domains()
    seed_data_types()
    backfill_domains()


def migrate():
    Base.metadata.create_all(bind=engine)
    migrate_messages_v2()
    migrate_tasks_v2()
    migrate_tasks_v3()
    migrate_domains_v1()
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


def migrate_tasks_v2():
    """Add qsub_id and script_path columns to tasks table."""
    import sqlite3
    from config.database import DATABASE_URL
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    new_columns = [
        ("qsub_id", "TEXT NOT NULL DEFAULT ''"),
        ("script_path", "TEXT NOT NULL DEFAULT ''"),
    ]

    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")
            print(f"  Added column tasks.{col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                pass
            else:
                raise

    conn.commit()
    conn.close()


def migrate_tasks_v3():
    """Add status column to tasks table."""
    import sqlite3
    from config.database import DATABASE_URL
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'")
        print("  Added column tasks.status")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            pass
        else:
            raise

    conn.commit()
    conn.close()


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
                "amp-import-fasta": "Amplicon/scripts/step0_import_fasta.sh",
                "amp-cutadapt": "Amplicon/scripts/step1_cutadapt.sh",
                "amp-flash": "Amplicon/scripts/step1_flash.sh",
                "amp-frags-qc": "Amplicon/scripts/step2_frags_qc.sh",
                "amp-dada2": "Amplicon/scripts/step3_dada2.sh",
                "amp-taxonomy": "Amplicon/scripts/step3_taxonomy.sh",
                "amp-phylogeny": "Amplicon/scripts/step3_phylogeny.sh",
                "amp-feature-tables": "Amplicon/scripts/step3_feature_tables.sh",
                "amp-table-stats": "Amplicon/scripts/step3_table_stats.sh",
                "amp-alpha-data": "Amplicon/scripts/step3_alpha_data.sh",
                "amp-beta-data": "Amplicon/scripts/step3_beta_data.sh",
                "amp-upgma": "Amplicon/scripts/step3_upgma.sh",
                "amp-top-species": "Amplicon/scripts/step3_top_species.sh",
                "amp-genus-tree": "Amplicon/scripts/step3_genus_tree.sh",
                "amp-catecomp": "Amplicon/scripts/step4_catecomp.sh",
                "amp-funpre": "Amplicon/scripts/step4_funpre.sh",
                "amp-krona": "Amplicon/scripts/step4_krona.sh",
                "amp-lefse": "Amplicon/scripts/step4_lefse.sh",
                "amp-metastat": "Amplicon/scripts/step4_metastat.sh",
                "amp-network": "Amplicon/scripts/step4_network.sh",
                "amp-network3d": "Amplicon/scripts/step4_network3d.sh",
                "amp-otutree": "Amplicon/scripts/step4_otutree.sh",
                "amp-randomforest": "Amplicon/scripts/step4_randomforest.sh",
                "amp-simper": "Amplicon/scripts/step4_simper.sh",
                "amp-taxasummary": "Amplicon/scripts/step4_taxasummary.sh",
                "amp-taxasummary-group": "Amplicon/scripts/step4_taxasummary_group.sh",
                "amp-ternary": "Amplicon/scripts/step4_ternary.sh",
                "amp-ttest": "Amplicon/scripts/step4_ttest.sh",
                "amp-venn": "Amplicon/scripts/step4_venn.sh",
                "amp-alpha-div": "Amplicon/scripts/step5_alpha_div.sh",
                "amp-alpha-rarefaction": "Amplicon/scripts/step5_alpha_rarefaction.sh",
                "amp-beta-div": "Amplicon/scripts/step5_beta_div.sh",
                "amp-dca": "Amplicon/scripts/step5_dca.sh",
                "amp-nmds": "Amplicon/scripts/step5_nmds.sh",
                "amp-pca": "Amplicon/scripts/step5_pca.sh",
                "amp-pcoa": "Amplicon/scripts/step5_pcoa.sh",
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


def migrate_domains_v1():
    """多领域改造 v1：给 script_folders/scripts 加 domain_id，给 scripts 加 call_params/call_outputs/per_sample。"""
    import sqlite3
    from config.database import DATABASE_URL
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    new_columns = [
        ("script_folders", "domain_id", "INTEGER NOT NULL DEFAULT 0"),
        ("scripts", "domain_id", "INTEGER NOT NULL DEFAULT 0"),
        ("scripts", "call_params", "TEXT NOT NULL DEFAULT ''"),
        ("scripts", "call_outputs", "TEXT NOT NULL DEFAULT ''"),
        ("scripts", "per_sample", "INTEGER NOT NULL DEFAULT 0"),
    ]
    for table, col, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            print(f"  Added column {table}.{col}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                pass
            else:
                raise

    conn.commit()
    conn.close()


def seed_domains():
    session = SessionLocal()
    try:
        if session.query(Domain).count() == 0:
            domain = Domain(
                name="扩增子分析",
                code="amplicon",
                description="基于 16S/ITS/18S 等扩增子测序的微生物群落分析：ASV 推断、物种分类、多样性分析、统计检验与可视化。",
                is_active=1,
                keywords="扩增子,16S,ITS,18S,ASV,OTU,微生物,群落,多样性,DADA2,QIIME",
                script_root="Amplicon",
                sort_order=1,
            )
            session.add(domain)
            session.commit()
            print("Seed domains created successfully!")
        else:
            print("Domains already exist, skipping seed.")
    finally:
        session.close()


def seed_data_types():
    from pkg.amplicon.amplicon_tools import DATA_TYPE_NAMES, DATA_TYPE_TO_FILE_REQUIREMENT
    session = SessionLocal()
    try:
        if session.query(DataType).count() == 0:
            domain = session.query(Domain).filter(Domain.code == "amplicon").first()
            if not domain:
                print("Amplicon domain not found, skipping data_types seed.")
                return
            rows = []
            for type_id, label in DATA_TYPE_NAMES.items():
                req = DATA_TYPE_TO_FILE_REQUIREMENT.get(type_id, {})
                rows.append(DataType(
                    domain_id=domain.id,
                    type_id=type_id,
                    label=req.get("label", label) if req else label,
                    description=req.get("description", "") if req else "",
                    extensions=json.dumps(req.get("extensions", []), ensure_ascii=False) if req else "[]",
                    required=int(req.get("required", 1)) if req else 1,
                    multiple=int(req.get("multiple", 0)) if req else 0,
                    is_uploadable=1 if req else 0,
                ))
            session.add_all(rows)
            session.commit()
            print(f"Seed data_types created successfully! ({len(rows)} types)")
        else:
            print("Data types already exist, skipping seed.")
    finally:
        session.close()


def backfill_domains():
    """把现有 folder/script 打上 amplicon 领域，并用 TOOL_SCRIPT_CALLS 回填脚本的调用参数。"""
    from pkg.amplicon.script_registry import TOOL_SCRIPT_CALLS
    session = SessionLocal()
    try:
        domain = session.query(Domain).filter(Domain.code == "amplicon").first()
        if not domain:
            print("Amplicon domain not found, skipping backfill.")
            return

        folders = session.query(ScriptFolder).filter(ScriptFolder.domain_id == 0).all()
        for f in folders:
            f.domain_id = domain.id

        scripts = session.query(Script).filter(Script.domain_id == 0).all()
        backfilled = 0
        for s in scripts:
            s.domain_id = domain.id
            if not s.call_params:
                call_def = TOOL_SCRIPT_CALLS.get(s.tool_id)
                if call_def:
                    s.call_params = json.dumps([
                        {"flag": p.flag, "data_type": p.data_type, "required": p.required, "default": p.default}
                        for p in call_def.params
                    ], ensure_ascii=False)
                    s.call_outputs = json.dumps([
                        {"data_type": o.data_type, "filename": o.filename}
                        for o in call_def.outputs
                    ], ensure_ascii=False)
                    s.per_sample = 1 if call_def.per_sample else 0
                    backfilled += 1

        session.commit()
        print(f"Backfilled domains: {len(folders)} folders, {len(scripts)} scripts tagged amplicon; {backfilled} scripts got call params.")
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fresh":
        migrate_fresh()
    else:
        migrate()
    seed()
