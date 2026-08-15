"""模板路由"""
from fastapi import APIRouter, HTTPException

from api.models import TemplateSummary, TemplateDetail
from api.services.templates import TEMPLATES

router = APIRouter()


@router.get("/templates", response_model=list[TemplateSummary])
async def list_templates():
    """列出所有可用模板"""
    return [
        TemplateSummary(
            id=t["id"],
            name=t["name"],
            description=t["description"],
            preview_color=t["preview_color"],
        )
        for t in TEMPLATES.values()
    ]


@router.get("/templates/{template_id}", response_model=TemplateDetail)
async def get_template(template_id: str):
    """获取模板详情 (含完整 CDM)"""
    if template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    t = TEMPLATES[template_id]
    cdm = t["cdm"]() if callable(t["cdm"]) else t["cdm"]
    return TemplateDetail(
        id=t["id"],
        name=t["name"],
        description=t["description"],
        preview_color=t["preview_color"],
        cdm=cdm.model_dump(),
    )
