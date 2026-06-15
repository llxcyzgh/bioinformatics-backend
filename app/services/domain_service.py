"""
领域服务（多领域改造）

把 DB 数据转成 pkg/amplicon 纯算法需要的 DTO（ToolDef / ScriptCallDef），
并按领域缓存。pkg/amplicon 保持无 DB 依赖。
"""

import json
import logging

from sqlalchemy.orm import Session

from app.models import Domain, DataType, Script
from pkg.amplicon.amplicon_tools import ToolDef
from pkg.amplicon.script_registry import ScriptCallDef, ParamDef, OutputFileDef

logger = logging.getLogger(__name__)


class DomainService:
    """按领域提供工具图、脚本调用定义、根输入需求。"""

    # domain_id -> list[ToolDef]；脚本写操作（期三）后调 invalidate 清理
    _tools_cache: dict[int, list[ToolDef]] = {}

    # Phase 2 过桥：期三接入 DomainClassifier 后由分流结果替代
    AMPLICON_CODE = "amplicon"

    # ─── 领域查询 ──────────────────────────────────────────────
    @staticmethod
    def get_domain_by_code(db: Session, code: str) -> Domain | None:
        return Domain.where(db, code=code).first()

    @staticmethod
    def get_amplicon_domain(db: Session) -> Domain:
        d = DomainService.get_domain_by_code(db, DomainService.AMPLICON_CODE)
        if not d:
            raise ValueError("amplicon 领域未初始化，请先运行 migrate_seed.py")
        return d

    # ─── 工具图（ToolDef）────────────────────────────────────
    @classmethod
    def get_domain_tools(cls, db: Session, domain_id: int) -> list[ToolDef]:
        if domain_id not in cls._tools_cache:
            rows = Script.where(db, domain_id=domain_id, verified=1, is_active=1).all()
            cls._tools_cache[domain_id] = [
                ToolDef(
                    id=s.tool_id,
                    name=s.name,
                    inputs=json.loads(s.inputs or "[]"),
                    outputs=json.loads(s.outputs or "[]"),
                    category=s.category,
                )
                for s in rows
            ]
            logger.info(f"[DomainService] 加载领域 {domain_id} 工具图: {len(cls._tools_cache[domain_id])} 个工具")
        return cls._tools_cache[domain_id]

    # ─── 脚本调用定义（ScriptCallDef）────────────────────────
    @classmethod
    def get_call_defs(cls, db: Session, domain_id: int, tool_ids: list[str]) -> dict[str, ScriptCallDef]:
        rows = (
            Script.where(db, domain_id=domain_id, verified=1, is_active=1)
            .filter(Script.tool_id.in_(tool_ids))
            .all()
        )
        return {s.tool_id: DomainService._build_call_def(s) for s in rows}

    @staticmethod
    def _build_call_def(s: Script) -> ScriptCallDef:
        params = [
            ParamDef(
                flag=p["flag"],
                data_type=p["data_type"],
                required=p.get("required", True),
                default=p.get("default"),
            )
            for p in json.loads(s.call_params or "[]")
        ]
        outputs = [
            OutputFileDef(data_type=o["data_type"], filename=o["filename"])
            for o in json.loads(s.call_outputs or "[]")
        ]
        return ScriptCallDef(
            tool_id=s.tool_id,
            script_path=s.file_path,
            params=params,
            outputs=outputs,
            per_sample=bool(s.per_sample),
        )

    @staticmethod
    def get_tool_names(db: Session, domain_id: int) -> dict[str, str]:
        rows = Script.where(db, domain_id=domain_id, verified=1, is_active=1).all()
        return {s.tool_id: s.name for s in rows}

    # ─── 根输入文件需求（替代 resolve_root_inputs）────────────
    @classmethod
    def resolve_required_files(cls, db: Session, domain_id: int, tool_chain_ids: list[str]) -> list[dict]:
        """
        从工具链推导用户必须上传的根输入文件。
        逻辑与 amplicon_tools.resolve_root_inputs 等价，但数据取自该领域的 DataType 词表。
        """
        tools = {t.id: t for t in cls.get_domain_tools(db, domain_id)}
        type_meta = {t.type_id: t for t in DataType.where(db, domain_id=domain_id).all()}

        produced: set[str] = set()
        required_types: list[str] = []
        for tid in tool_chain_ids:
            tool = tools.get(tid)
            if not tool:
                continue
            for inp in tool.inputs:
                if inp not in produced:
                    required_types.append(inp)
            produced.update(tool.outputs)

        # 去重保序
        seen: set[str] = set()
        unique: list[str] = []
        for t in required_types:
            if t not in seen:
                seen.add(t)
                unique.append(t)

        result: list[dict] = []
        for type_id in unique:
            meta = type_meta.get(type_id)
            if meta and meta.is_uploadable:
                # 可上传根输入：带扩展名；multiple 仅在为真时给出（与原 DATA_TYPE_TO_FILE_REQUIREMENT 一致）
                entry = {
                    "typeId": type_id,
                    "label": meta.label,
                    "description": meta.description,
                    "extensions": json.loads(meta.extensions or "[]"),
                    "required": bool(meta.required),
                }
                if meta.multiple:
                    entry["multiple"] = True
                result.append(entry)
            elif meta:
                # 链中出现的中间类型（非根输入）—— 与原 resolve_root_inputs 兜底一致
                result.append({
                    "typeId": type_id,
                    "label": meta.label,
                    "description": type_id,
                    "extensions": [],
                    "required": True,
                })
            else:
                result.append({
                    "typeId": type_id,
                    "label": type_id,
                    "description": type_id,
                    "extensions": [],
                    "required": True,
                })
        return result

    # ─── 缓存失效（期三脚本写操作时调用）──────────────────────
    @classmethod
    def invalidate(cls, domain_id: int | None = None) -> None:
        if domain_id is None:
            cls._tools_cache.clear()
        else:
            cls._tools_cache.pop(domain_id, None)
