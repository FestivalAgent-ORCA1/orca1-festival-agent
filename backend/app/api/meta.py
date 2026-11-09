"""/api/meta — 태그·지역·연령대 목록 (docs/tags.md)"""

from fastapi import APIRouter

from app.core.constants import AGE_GROUPS, REGIONS, TAGS
from app.schemas.festival import CodeName

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/tags", response_model=list[CodeName])
def list_tags():
    return TAGS


@router.get("/regions", response_model=list[CodeName])
def list_regions():
    return REGIONS


@router.get("/age-groups", response_model=list[CodeName])
def list_age_groups():
    return AGE_GROUPS
