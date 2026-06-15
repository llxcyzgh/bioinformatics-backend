import json
import logging
import os
import uuid
from typing import Optional

import httpx
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import Script
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

        return ScriptService.create(
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

    @staticmethod
    def update(db: Session, script_id: int, **kwargs) -> Script:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        for key, value in kwargs.items():
            if hasattr(script, key) and value is not None:
                setattr(script, key, value)
        return script.save(db)

    @staticmethod
    def verify(db: Session, script_id: int, verified_by: int) -> Script:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        script.verified = 1
        script.verified_by = verified_by
        return script.save(db)

    @staticmethod
    def toggle_active(db: Session, script_id: int) -> Script:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        script.is_active = 0 if script.is_active else 1
        return script.save(db)

    @staticmethod
    def delete(db: Session, script_id: int) -> dict:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        script.delete(db)
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
