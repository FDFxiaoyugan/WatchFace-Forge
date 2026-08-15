"""api.models — API 请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from schema.cdm.models import WatchFaceCDM


class CompileRequest(BaseModel):
    """CDM → WFF XML 请求"""
    cdm: WatchFaceCDM


class CompileResponse(BaseModel):
    """编译结果"""
    wff_xml: str
    validation_passed: bool
    validation_errors: list = []


class BuildRequest(BaseModel):
    """CDM → APK 构建请求"""
    cdm: WatchFaceCDM
    template_id: Optional[str] = None


class BuildResponse(BaseModel):
    """构建结果"""
    task_id: str
    status: str  # "success" | "failed"
    apk_filename: Optional[str] = None
    apk_size: Optional[int] = None
    download_url: Optional[str] = None
    error: Optional[str] = None


class TemplateSummary(BaseModel):
    """模板摘要"""
    id: str
    name: str
    description: str
    preview_color: str


class TemplateDetail(BaseModel):
    """模板详情 (含 CDM)"""
    id: str
    name: str
    description: str
    preview_color: str
    cdm: dict
