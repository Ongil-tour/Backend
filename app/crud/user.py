import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.user import User, UserSettings
from app.schemas.user import UserSettingsUpdate

# 1. 이메일로 유저 찾기 함수
def get_user_by_email(db: Session, email: str):
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

    # (2) 기존 설정 데이터 찾기
    db_settings = get_user_settings(db, user_id)
    
    # (3) 클라이언트가 '실제로 값을 넣어서 보낸 필드'만 딕셔너리로 추출 (exclude_unset=True)
    update_dict = update_data.model_dump(exclude_unset=True) 

    if db_settings:
        # (4) [Upsert: 갱신] 데이터가 이미 있으면 뽑아낸 값을 덮어씌우기
        for key, value in update_dict.items():
            setattr(db_settings, key, value)
    else:
        # (5) [Upsert: 생성] 데이터가 없으면 추출한 값으로 새로 생성하기
        db_settings = UserSettings(user_id=user_id, **update_dict)
        db.add(db_settings)
        
    db.commit()
    db.refresh(db_settings)
    
    return db_settings

# 5. 유저 탈퇴 (삭제) 함수
def delete_user(db: Session, user_id: uuid.UUID):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()

    return None