"""모든 모델을 여기서 import 해야 Alembic이 테이블을 인식한다."""

from app.models.festival import Festival, FestivalTag, TravelTime  # noqa: F401  BE1
from app.models.user import User, UserRegion, UserTag  # noqa: F401  BE2
from app.models.like import Like  # noqa: F401
from app.models.schedule import Schedule, ScheduleItem  # noqa: F401
from app.models.post import Comment, Post  # noqa: F401
from app.models.notification import Notification  # noqa: F401
