"""
alembic autogenerate가 모든 테이블을 인식하려면 각 모델 모듈이 import되어
Base.metadata에 클래스가 등록되어 있어야 한다. env.py의 `import app.models`가
이 파일을 거쳐 아래 임포트들을 실행시키는 진입점.
"""
from app.models.user import User, SocialAccount, UserSettings, RefreshToken
from app.models.facility import Facility
from app.models.favorite import FavoriteList, Favorite, ListType

__all__ = [
    "User",
    "SocialAccount",
    "UserSettings",
    "RefreshToken",
    "Facility",
    "FavoriteList",
    "Favorite",
    "ListType",
]
