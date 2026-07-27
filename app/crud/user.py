import uuid
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

# 3. 유저 UI 설정 업데이트 함수
def update_user_settings(db: Session, user_id: uuid.UUID, settings_update: UserSettingsUpdate):
    # 1. 먼저 해당 유저의 기존 설정 데이터를 찾습니다.
    db_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    
    # 2. 만약 설정 데이터가 텅 비어있다면? -> 새로 하나 만들어줍니다! (이 부분이 추가되었습니다)
    if not db_settings:
        db_settings = UserSettings(user_id=user_id)
        db.add(db_settings)
    
    # 3. 클라이언트(앱)가 고대비 설정을 보냈다면 업데이트
    if settings_update.high_contrast is not None:
        db_settings.high_contrast = settings_update.high_contrast
    
    # 4. 클라이언트가 폰트 사이즈 변경을 보냈다면 업데이트
    if settings_update.font_size is not None:
        db_settings.font_size = settings_update.font_size
        
    # 5. 변경되거나 새로 생성된 내용을 DB에 확정(commit)하고 최신 상태로 가져옵니다.
    db.commit()
    db.refresh(db_settings)
    
    return db_settings

# 4. 유저 탈퇴 (삭제) 함수
def delete_user(db: Session, user_id: uuid.UUID):
    # 1. 지울 유저 정보를 화면에 돌려주기 위해 미리 찾아만 둡니다.
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
        
    # 2. [강제 삭제 명령] 파이썬을 건너뛰고 DB에 설정 데이터를 날려버리라고 직접 명령합니다.
    db.query(UserSettings).filter(UserSettings.user_id == user_id).delete()
    
    # 3. [강제 삭제 명령] 설정이 날아갔으니, 안심하고 유저 본체도 다이렉트로 날려버립니다.
    db.query(User).filter(User.id == user_id).delete()
    
    # 4. 변경된 사항을 DB에 최종 확정 쾅!
    db.commit()
    
    return db_user