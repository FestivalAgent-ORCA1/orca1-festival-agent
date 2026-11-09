"""모든 모델을 여기서 import 해야 Alembic이 테이블을 인식한다."""

from app.models.festival import Festival, FestivalTag, TravelTime  # noqa: F401  BE1

# BE2 (be2-MK 병합 후 추가)
# from app.models.user import User, UserRegion, UserTag
# from app.models.like import Like
# from app.models.schedule import Schedule, ScheduleItem
# from app.models.post import Comment, Post
# from app.models.notification import Notification
