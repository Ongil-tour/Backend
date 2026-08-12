import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.user import User, UserSettings
from app.schemas.user import UserSettingsUpdate

# 1. 이메일로 유저 찾기 함수
def get_user_by_email(db: Session, email: str):
    # DB의 User 테이블에서 email 필드가 전달받은 email과 같은 첫 번째 데이터를 가져옴
    return db.query(User).filter(User.email == email).first()

# 2. 고유 ID(UUID)로 유저 찾기 함수
def get_user_by_id(db: Session, user_id: uuid.UUID):
    return db.query(User).filter(User.id == user_id).first()

# 3. 유저 설정 조회 함수
def get_user_settings(db: Session, user_id: uuid.UUID):
    return db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

# 4. 이름 변경 및 422 에러 검증 + Upsert 로직 고도화
def upsert_user_settings(db: Session, user_id: uuid.UUID, update_data: UserSettingsUpdate):
    # (1) [방어 로직] 폰트 사이즈가 들어왔는데 허용된 값('sm', 'md', 'lg')이 아니면 422 에러 발생
    if update_data.font_size is not None and update_data.font_size not in ['sm', 'md', 'lg']:
        raise HTTPException(status_code=422, detail="font_size는 'sm', 'md', 'lg' 중 하나여야 합니다.")

    # (2) [방어 로직] 프로필 사진 검증 - 4개 중 하나여야 함
    if update_data.profile_image is not None and update_data.profile_image not in ['avatar_1', 'avatar_2', 'avatar_3', 'avatar_4']:
        raise HTTPException(status_code=422, detail="profile_image는 정해진 4개 중 하나여야 합니다.")

    # (3) 기존 설정 데이터 찾기
    db_settings = get_user_settings(db, user_id)

    # (4) 클라이언트가 '실제로 값을 넣어서 보낸 필드'만 딕셔너리로 추출 (exclude_unset=True)
    update_dict = update_data.model_dump(exclude_unset=True)

    if db_settings:
        # (5) [Upsert: 갱신] 데이터가 이미 있으면 뽑아낸 값을 덮어씌우기
        for key, value in update_dict.items():
            setattr(db_settings, key, value)
    else:
        # (6) [Upsert: 생성] 데이터가 없으면 추출한 값으로 새로 생성하기
        db_settings = UserSettings(user_id=user_id, **update_dict)
        db.add(db_settings)

    db.commit()
    db.refresh(db_settings)

    return db_settings

# 5. 유저 탈퇴 (삭제) 함수
def delete_user(db: Session, user_id: uuid.UUID) -> bool:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False

    # ondelete="CASCADE" 설정 덕분에 user_settings, social_accounts,
    # favorite_lists, refresh_tokens는 DB가 알아서 같이 지워줌
    db.delete(db_user)
    db.commit()

    return True