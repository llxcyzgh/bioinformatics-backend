import json
import logging
import os
import uuid
from typing import Optional

import httpx
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import Script
from app.services.domain_service import DomainService
from config.llm import DASHSCOPE_API_KEY, DASHSCOPE_API_BASE, DASHSCOPE_MODEL_NAME, LLM_PARSER_TIMEOUT

logger = logging.getLogger(__name__)

SCRIPTS_DIR = os.getenv("SCRIPTS_DIR", "scripts")


def _parse_script_io_llm(script_content: str) -> dict:
    """用 LLM 解析脚本代码，返回 inputs/outputs"""
    if not DASHSCOPE_API_KEY:
        return {"inputs": [], "outputs": []}

    system_prompt = """你是一个生物信息学脚本分析专家。分析用户给出的脚本代码，识别其输入和输出文件。

返回严格 JSON 格式（不要 markdown 代码块）：
{"inputs": ["input_file.fastq", "config.yaml"], "outputs": ["result.txt", "report.pdf"]}

规则：
- 提取文件名和文件类型，包括从命令行参数、变量赋值、函数调用中读取的文件路径
- 只返回文件名，不要描述
- 如果无法确定，返回空数组"""

    try:
        response = httpx.post(
            f"{DASHSCOPE_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
            json={
                "model": DASHSCOPE_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"分析以下脚本代码的输入输出文件：\n\n{script_content[:6000]}"},
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            },
            timeout=LLM_PARSER_TIMEOUT,
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
        result = json.loads(raw)
        logger.info(f"[ScriptService] LLM 解析脚本 IO: {raw[:300]}")
        return result
    except Exception as e:
        logger.warning(f"[ScriptService] LLM 解析脚本 IO 失败: {e}")
        return {"inputs": [], "outputs": []}


class ScriptService:

    @staticmethod
    def _invalidate_for(script: "Script") -> None:
        """脚本写操作后失效其所属领域的工具缓存，使建图/规划器读到最新数据。"""
        domain_id = getattr(script, "domain_id", None)
        if domain_id:
            DomainService.invalidate(domain_id)
        else:
            # 未归属领域的脚本：清空全部缓存兜底
            DomainService.invalidate(None)

    @staticmethod
    def list_scripts(
        db: Session,
        folder_id: Optional[int] = None,
        verified: Optional[int] = None,
        is_active: Optional[int] = None,
        tool_id: Optional[str] = None,
    ) -> list[Script]:
        query = Script.where(db)
        if folder_id is not None:
            query = query.filter(Script.folder_id == folder_id)
        if verified is not None:
            query = query.filter(Script.verified == verified)
        if is_active is not None:
            query = query.filter(Script.is_active == is_active)
        if tool_id:
            query = query.filter(Script.tool_id == tool_id)
        return query.order_by(Script.id.asc()).all()

    @staticmethod
    def get(db: Session, script_id: int) -> Script:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        return script

    @staticmethod
    def get_by_tool_id(db: Session, tool_id: str) -> Optional[Script]:
        results = Script.where(db, tool_id=tool_id, is_active=1, verified=1).all()
        return results[0] if results else None

    @staticmethod
    def create(
        db: Session,
        name: str,
        folder_id: int,
        tool_id: str,
        category: str,
        file_path: str,
        uploaded_by: int,
        description: str = "",
        md_content: str = "",
        inputs: str = "[]",
        outputs: str = "[]",
        version: str = "1.0.0",
        runtime: int = 0,
        cost: float = 0.0,
        weight: int = 0,
        valid_from: str = "",
        valid_until: str = "",
    ) -> Script:
        script = Script(
            name=name,
            description=description,
            folder_id=folder_id,
            tool_id=tool_id,
            category=category,
            version=version,
            file_path=file_path,
            md_content=md_content,
            inputs=inputs,
            outputs=outputs,
            runtime=runtime,
            cost=cost,
            weight=weight,
            uploaded_by=uploaded_by,
            valid_from=valid_from,
            valid_until=valid_until,
        )
        return script.save(db)

    @staticmethod
    def upload_script(
        db: Session,
        script_file: UploadFile,
        md_file: Optional[UploadFile],
        name: str,
        folder_id: int,
        tool_id: str,
        category: str,
        uploaded_by: int,
        version: str = "1.0.0",
        runtime: int = 0,
        cost: float = 0.0,
        weight: int = 0,
        inputs: str = "[]",
        outputs: str = "[]",
        valid_from: str = "",
        valid_until: str = "",
    ) -> Script:
        # 存储脚本文件
        ext = os.path.splitext(script_file.filename)[1] if script_file.filename else ".sh"
        stored_name = f"{uuid.uuid4().hex}{ext}"
        dest_dir = os.path.join(SCRIPTS_DIR, "uploaded")
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, stored_name)

        content = script_file.file.read()
        with open(dest_path, "wb") as f:
            f.write(content)

        rel_path = f"uploaded/{stored_name}"

        # 读取 MD 文件
        md_content = ""
        if md_file:
            md_content = md_file.file.read().decode("utf-8", errors="replace")

        # LLM 自动解析 inputs/outputs
        try:
            script_text = content.decode("utf-8", errors="replace")
            parsed_io = _parse_script_io_llm(script_text)
            if parsed_io.get("inputs") and inputs == "[]":
                inputs = json.dumps(parsed_io["inputs"], ensure_ascii=False)
            if parsed_io.get("outputs") and outputs == "[]":
                outputs = json.dumps(parsed_io["outputs"], ensure_ascii=False)
        except Exception as e:
            logger.warning(f"[ScriptService] 脚本 IO 解析异常: {e}")

        script = ScriptService.create(
            db=db,
            name=name,
            folder_id=folder_id,
            tool_id=tool_id,
            category=category,
            file_path=rel_path,
            uploaded_by=uploaded_by,
            md_content=md_content,
            version=version,
            runtime=runtime,
            cost=cost,
            weight=weight,
            inputs=inputs,
            outputs=outputs,
            valid_from=valid_from,
            valid_until=valid_until,
        )
        ScriptService._invalidate_for(script)
        return script

    @staticmethod
    def update(db: Session, script_id: int, **kwargs) -> Script:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        for key, value in kwargs.items():
            if hasattr(script, key) and value is not None:
                setattr(script, key, value)
        script = script.save(db)
        ScriptService._invalidate_for(script)
        return script

    @staticmethod
    def verify(db: Session, script_id: int, verified_by: int) -> Script:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        script.verified = 1
        script.verified_by = verified_by
        script = script.save(db)
        ScriptService._invalidate_for(script)
        return script

    @staticmethod
    def toggle_active(db: Session, script_id: int) -> Script:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        script.is_active = 0 if script.is_active else 1
        script = script.save(db)
        ScriptService._invalidate_for(script)
        return script

    @staticmethod
    def delete(db: Session, script_id: int) -> dict:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        domain_id = getattr(script, "domain_id", None)
        script.delete(db)
        if domain_id:
            DomainService.invalidate(domain_id)
        else:
            DomainService.invalidate(None)
        return {"detail": "Deleted"}

    @staticmethod
    def read_script_content(file_path: str) -> str:
        """读取脚本文件的完整内容"""
        full_path = os.path.join(SCRIPTS_DIR, file_path)
        if not os.path.exists(full_path):
            return ""
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    @staticmethod
    def upload_scripts_bulk(
        db: Session,
        script_files: list,
        folder_id: int,
        domain_id: int,
        uploaded_by: int,
        version: str = "1.0.0",
        runtime: int = 0,
        cost: float = 0.0,
        weight: int = 0,
        valid_from: str = "",
        valid_until: str = "",
    ) -> list:
        """批量上传多个脚本文件，各自成独立 Script 行；tool_id 由领域代码+文件名生成。"""
        import re
        from app.models import Domain, ScriptFolder
        from app.services.domain_service import DomainService

        folder = ScriptFolder.find(db, folder_id) if folder_id else None
        if not domain_id and folder:
            domain_id = folder.domain_id
        domain = Domain.find(db, domain_id) if domain_id else None
        domain_code = (domain.code if domain else "tool") or "tool"
        category = folder.name if folder else ""

        created = []
        seen = set()
        for i, sf in enumerate(script_files):
            base = os.path.splitext(sf.filename)[0] if sf.filename else f"script{i + 1}"
            slug = re.sub(r"[^a-zA-Z0-9]+", "-", base).strip("-").lower() or f"script{i + 1}"
            tool_id = f"{domain_code}-{slug}"
            if tool_id in seen:
                tool_id = f"{tool_id}-{i + 1}"
            seen.add(tool_id)

            script = ScriptService.upload_script(
                db=db,
                script_file=sf,
                md_file=None,
                name=base,
                folder_id=folder_id,
                tool_id=tool_id,
                category=category,
                uploaded_by=uploaded_by,
                version=version,
                runtime=runtime,
                cost=cost,
                weight=weight,
                inputs="[]",
                outputs="[]",
                valid_from=valid_from,
                valid_until=valid_until,
            )
            if domain_id:
                script.domain_id = domain_id
                script.save(db)
            created.append(script)

        if domain_id:
            DomainService.invalidate(domain_id)
        logger.info(f"[ScriptService] 批量上传 {len(created)} 个脚本 -> domain={domain_id} folder={folder_id}")
        return created

    @staticmethod
    def upload_library(
        db: Session,
        files: list,
        paths: list,
        domain_id: int,
        uploaded_by: int,
    ) -> dict:
        """
        文件夹上传：files 与 paths 同序，paths 为浏览器相对路径（含所选根目录）。
        配对 key = (分类路径, 文件名基名)；分类路径会剥掉所选根与「类型桶」目录
        （scripts/reference/代码/文档…），从而支持 .sh 与 .md 分置于不同子目录的结构
        （如 root/scripts/foo.sh + root/reference/foo.md）。
        从 .md 确定性解析元数据建图；.sh 落盘用于执行。新建脚本默认未校验/未启用。
        """
        import re
        from app.models import Domain, ScriptFolder
        from app.services.md_script_parser import parse_md

        domain = Domain.find(db, domain_id) if domain_id else None
        domain_code = (domain.code if domain else "tool") or "tool"

        # 1) 配对：key = (分类路径, 文件名基名)
        SH_EXTS = {".sh"}
        MD_EXTS = {".md", ".markdown"}
        # 「类型桶」目录名：配对时剥掉，使 .sh/.md 分目录也能配对
        _BUCKETS_EN = {"scripts", "reference", "sh", "md", "src", "source", "doc", "docs", "code", "bin", "shell", "mds", "shs"}
        _BUCKETS_CN = {"代码", "文档", "脚本", "说明", "源码", "描述"}

        def _is_bucket(seg: str) -> bool:
            return seg.lower() in _BUCKETS_EN or seg in _BUCKETS_CN

        def _rel_meta(rel: str):
            """返回 (基名key小写, ext小写, 分类, 显示基名)。"""
            parts = [p for p in rel.replace("\\", "/").split("/") if p]
            fname = parts[-1] if parts else rel
            name, ext = os.path.splitext(fname)
            # 目录：去掉首段（所选根）与文件名，再剥掉尾部「类型桶」目录
            dirs = parts[1:-1] if len(parts) >= 2 else []
            while dirs and _is_bucket(dirs[-1]):
                dirs = dirs[:-1]
            return name.lower(), ext.lower(), "/".join(dirs), name

        pairs: dict[str, dict] = {}  # pkey -> {"sh": [...], "md": [...], "cat": str, "rel": str}
        warnings = {"orphan_sh": [], "orphan_md": [], "conflict": [], "ignored": []}

        for f, raw_path in zip(files, paths):
            rel = (raw_path or f.filename or "").replace("\\", "/")
            base_key, ext, cat, _disp = _rel_meta(rel)
            if ext in SH_EXTS:
                kind = "sh"
            elif ext in MD_EXTS:
                kind = "md"
            else:
                warnings["ignored"].append(rel)
                continue
            pkey = f"{cat}\0{base_key}"
            bucket = pairs.setdefault(pkey, {"sh": [], "md": [], "cat": cat, "rel": rel})
            bucket[kind].append(f)

        folder_cache: dict[str, int] = {}

        def get_or_create_folder(cat: str) -> int:
            if not cat:
                return 0
            if cat in folder_cache:
                return folder_cache[cat]
            existing = ScriptFolder.where(db, name=cat, parent_id=0, domain_id=domain_id).first()
            if existing:
                folder_cache[cat] = existing.id
                return existing.id
            folder = ScriptFolder(name=cat, parent_id=0, domain_id=domain_id).save(db)
            folder_cache[cat] = folder.id
            return folder.id

        # 3) 逐对处理
        created = []
        seen_tool_ids = set()
        for pkey, bucket in pairs.items():
            shs, mds, cat = bucket["sh"], bucket["md"], bucket["cat"]
            # 同分类+同基名出现多个 .sh 或 .md：歧义，跳过并报告
            if len(shs) > 1 or len(mds) > 1:
                warnings["conflict"].append(bucket["rel"])
                continue
            if shs and not mds:
                warnings["orphan_sh"].append(bucket["rel"])
                continue
            if mds and not shs:
                warnings["orphan_md"].append(bucket["rel"])
                continue
            if not shs or not mds:
                continue
            sh_f, md_f = shs[0], mds[0]
            folder_id = get_or_create_folder(cat)

            # 解析 .md
            try:
                md_text = md_f.file.read().decode("utf-8", errors="replace")
            except Exception as e:
                logger.warning(f"[upload_library] 读取 .md 失败 {bucket['rel']}: {e}")
                md_text = ""
            meta = parse_md(md_text)

            # 存 .sh
            try:
                sh_bytes = sh_f.file.read()
            except Exception:
                sh_bytes = b""
            stored_name = f"{uuid.uuid4().hex}.sh"
            dest_dir = os.path.join(SCRIPTS_DIR, "uploaded")
            os.makedirs(dest_dir, exist_ok=True)
            with open(os.path.join(dest_dir, stored_name), "wb") as fp:
                fp.write(sh_bytes)
            rel_path = f"uploaded/{stored_name}"

            # tool_id：优先 .md 的 tool_name，否则基名 slug
            base = os.path.splitext(os.path.basename(sh_f.filename or key))[0]
            slug_src = meta.get("tool_name") or base
            slug = re.sub(r"[^a-zA-Z0-9]+", "-", slug_src).strip("-").lower() or "script"
            tool_id = f"{domain_code}-{slug}"
            if tool_id in seen_tool_ids:
                tool_id = f"{tool_id}-{len(seen_tool_ids) + 1}"
            seen_tool_ids.add(tool_id)

            script = Script(
                name=meta.get("name") or base,
                description=meta.get("description") or "",
                folder_id=folder_id,
                tool_id=tool_id,
                category=cat,
                file_path=rel_path,
                md_content=md_text,
                inputs=json.dumps(meta.get("inputs") or [], ensure_ascii=False),
                outputs=json.dumps(meta.get("outputs") or [], ensure_ascii=False),
                call_params=json.dumps(meta.get("call_params") or [], ensure_ascii=False),
                call_outputs=json.dumps(meta.get("call_outputs") or [], ensure_ascii=False),
                runtime=meta.get("runtime") or 0,
                cost=meta.get("cost") or 0.0,
                uploaded_by=uploaded_by,
                domain_id=domain_id or 0,
                verified=0,
                is_active=0,
            ).save(db)
            created.append(script)

        if domain_id:
            DomainService.invalidate(domain_id)
        logger.info(
            f"[upload_library] 领域={domain_id} 配对成功={len(created)} "
            f"孤立sh={len(warnings['orphan_sh'])} 孤立md={len(warnings['orphan_md'])} "
            f"歧义={len(warnings['conflict'])} 忽略={len(warnings['ignored'])}"
        )
        return {"created": created, "warnings": warnings}
