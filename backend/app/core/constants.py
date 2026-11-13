"""docs/tags.md의 코드 목록. 값을 바꿀 때는 tags.md를 먼저 고치고 팀에 공지한다.

- /api/meta/* 응답
- BE2 preferences 검증: `code in TAG_CODES` 처럼 사용
"""

TAGS = [
    {"code": "music", "name": "음악·공연"},
    {"code": "tradition", "name": "전통·역사"},
    {"code": "food", "name": "음식·먹거리"},
    {"code": "drink", "name": "술·음료"},
    {"code": "nature", "name": "꽃·자연"},
    {"code": "night", "name": "빛·야경"},
    {"code": "experience", "name": "체험"},
    {"code": "family", "name": "가족·어린이"},
    {"code": "art", "name": "예술·전시"},
    {"code": "local", "name": "특산물·장터"},
    {"code": "sports", "name": "스포츠·레저"},
    {"code": "winter", "name": "겨울·눈·얼음"},
]

REGIONS = [
    {"code": "1", "name": "서울"},
    {"code": "2", "name": "인천"},
    {"code": "3", "name": "대전"},
    {"code": "4", "name": "대구"},
    {"code": "5", "name": "광주"},
    {"code": "6", "name": "부산"},
    {"code": "7", "name": "울산"},
    {"code": "8", "name": "세종"},
    {"code": "31", "name": "경기"},
    {"code": "32", "name": "강원"},
    {"code": "33", "name": "충북"},
    {"code": "34", "name": "충남"},
    {"code": "35", "name": "경북"},
    {"code": "36", "name": "경남"},
    {"code": "37", "name": "전북"},
    {"code": "38", "name": "전남"},
    {"code": "39", "name": "제주"},
]

AGE_GROUPS = [
    {"code": "10s", "name": "10대"},
    {"code": "20s", "name": "20대"},
    {"code": "30s", "name": "30대"},
    {"code": "40s", "name": "40대"},
    {"code": "50s_plus", "name": "50대 이상"},
]

PLACE_CATEGORIES = ["attraction", "restaurant", "cafe"]

TAG_CODES = frozenset(t["code"] for t in TAGS)
REGION_CODES = frozenset(r["code"] for r in REGIONS)
AGE_GROUP_CODES = frozenset(a["code"] for a in AGE_GROUPS)
REGION_NAMES = {r["code"]: r["name"] for r in REGIONS}

# 사용자 선택 개수 제한 (api-spec.md 2장)
USER_REGIONS_MAX = 3
USER_TAGS_MIN, USER_TAGS_MAX = 1, 5
