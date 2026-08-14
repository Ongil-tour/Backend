"""
로컬 개발용 mock 유저(app/deps.py의 MOCK_USER_ID) 시드.
실 인증(app/deps.py::get_current_user)이 이 유저의 access token으로 로그인한
것처럼 로컬/테스트에서 쓸 수 있도록 더미 유저 + 소셜 계정 + 즐겨찾기 목록 3개를 만든다.
실행: docker compose run --rm api python -m app.scripts.seed
"""
from app.core.database import SessionLocal
from app.deps import MOCK_USER_ID
from app.models.favorite import FavoriteList, ListType
from app.models.user import SocialAccount, User


def seed() -> None:
    db = SessionLocal()
    try:
        user = db.get(User, MOCK_USER_ID)
        if user is not None:
            print(f"mock user({MOCK_USER_ID}) already exists, skip")
            return

        user = User(id=MOCK_USER_ID, email="mock@ongil-tour.dev")
        db.add(user)
        db.flush()

        db.add(SocialAccount(user_id=user.id, provider="kakao", provider_user_id="mock-dev-user"))

        for list_type in ListType:
            db.add(FavoriteList(user_id=user.id, list_type=list_type.value))

        db.commit()
        print(f"seeded mock user({MOCK_USER_ID}) + 3 favorite_lists")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
