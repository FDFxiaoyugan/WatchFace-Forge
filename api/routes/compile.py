"""编译路由 — CDM → WFF XML"""
import sys
from pathlib import Path
from fastapi import APIRouter

from api.models import CompileRequest, CompileResponse

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "wff-builder"))

from compiler.wff.compiler import WFFCompiler
from wff_builder import validate_watchface_xml

router = APIRouter()


@router.post("/compile", response_model=CompileResponse)
async def compile_cdm(req: CompileRequest):
    """将 CDM 编译为 WFF XML"""
    compiler = WFFCompiler()
    wff_xml = compiler.compile(req.cdm)

    failures = validate_watchface_xml(wff_xml)
    errors = [f for f in failures if f["severity"] == "error"]

    return CompileResponse(
        wff_xml=wff_xml,
        validation_passed=len(errors) == 0,
        validation_errors=errors,
    )
