"""
로컬 개발용 mock 유저(id=1) 시드.
app/deps.py의 get_current_user_mock()이 참조하는 더미 유저를 만든다.
실행: docker compose run --rm api python -m app.scripts.seed
"""
from app.core.database import SessionLocal
from app.models.favorite import FavoriteList, ListType
from app.models.user import OAuthProvider, User


def seed() -> None:
    db = SessionLocal()
    try:
        user = db.get(User, 1)
        if user is not None:
            print("mock user(id=1) already exists, skip")
            return

        user = User(
            id=1,
            provider=OAuthProvider.KAKAO,
            provider_id="mock-dev-user",
            email="mock@ongil-tour.dev",
            nickname="mock유저",
        )
        db.add(user)
        db.flush()

        for list_type in ListType:
            db.add(FavoriteList(user_id=user.id, list_type=list_type))

        db.commit()
        print("seeded mock user(id=1) + 3 favorite_lists")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
