# Ongil-tour Backend

무장애(Barrier-Free) 관광 정보 서비스 Ongil-tour의 백엔드. FastAPI + PostgreSQL(PostGIS) + Redis, Docker Compose로 로컬 개발, Render로 배포.

## 담당

| 도메인 | 담당 | 라우터 |
|---|---|---|
| 인증 · 유저 | 이다영 | `app/routers/auth.py`, `app/routers/users.py` |
| 시설 · 지도 · 외부 API 연동 | 이가희 | `app/routers/facilities.py`, `app/routers/map.py` |
| 즐겨찾기 | 신지민 | `app/routers/favorites.py` |

## 로컬 개발 환경 세팅

### 0. 사전 요구사항
- Docker Desktop

### 1. 환경변수
```
cp .env.example .env
```
`JWT_SECRET_KEY`, `KAKAO_REST_API_KEY`, `TOUR_API_KEY` 등은 실제 값 발급 전까지 예제값/빈 값 그대로 두어도 무방 (JWT 완성 전까지는 mock auth로 개발).

### 2. 컨테이너 기동
```
docker compose up -d db redis
docker compose build api
```

### 3. DB 마이그레이션
```
docker compose run --rm api alembic upgrade head
```
모델을 수정했다면:
```
docker compose run --rm api alembic revision --autogenerate -m "설명"
docker compose run --rm api alembic upgrade head
```
PostGIS의 `spatial_ref_sys` 시스템 테이블은 `alembic/env.py`의 `include_object` 필터로 diff에서 제외되어 있음. 새 모델 추가 시 이 필터를 건드릴 필요는 없음.

### 4. Mock 유저 시드
JWT가 아직 없으므로 `app/deps.py`의 `get_current_user_mock()`이 항상 `id=1` 유저를 반환한다. 로컬 DB에 해당 유저가 없으면 인증이 필요한 라우터 호출 시 에러가 나므로 최초 1회 시드 필요:
```
docker compose run --rm api python -m app.scripts.seed
```
재실행해도 안전(이미 있으면 skip).

### 5. 서버 기동
```
docker compose up -d api
curl http://localhost:8000/health
```

## Mock Auth (JWT 완성 전)

이다영의 실 JWT 인증이 나오기 전까지, 인증이 필요한 라우터는 `Depends(get_current_user_mock)`을 사용해 항상 시드된 `id=1` 유저로 동작한다. 실 인증 연동 시 `get_current_user_mock` → `get_current_user`로 교체하고 `app/deps.py`의 mock 함수는 삭제할 것.

## 브랜치 시작하는 법 (팀원 공통)

`main`에는 이번에 올라간 스캐폴딩(라우터 스텁, 모델, mock auth, 초기 마이그레이션, 시드 스크립트)이 이미 들어있다. 팀원은 이 저장소의 Collaborator가 아니라 **각자 fork한 저장소에서 작업 → `Ongil-tour/Backend`의 `main`으로 PR**을 올리는 방식으로 진행한다. `main`으로의 merge는 PR 리뷰를 거쳐서만 이루어짐(직접 push 없음).

```
# 1. GitHub에서 Ongil-tour/Backend를 본인 계정으로 Fork

# 2. 본인 fork를 clone
git clone https://github.com/<본인-계정>/Backend.git
cd Backend

# 3. 원본 저장소를 upstream으로 등록 (나중에 main 최신화용)
git remote add upstream https://github.com/Ongil-tour/Backend.git

# 4. 본인 담당 브랜치로 분기 (브랜치명은 담당 구분과 동일하게)
git checkout -b auth-users        # 이다영
git checkout -b facilities-map    # 이가희
git checkout -b favorites         # 신지민

# 5. 작업 후 본인 fork로 push
git push -u origin auth-users     # (또는 본인 브랜치명)

# 6. GitHub에서 본인 fork의 브랜치 -> Ongil-tour/Backend main 으로 PR 생성
```

그 다음 위 "로컬 개발 환경 세팅" 1~5단계(.env 생성 → 컨테이너 기동 → 마이그레이션 → 시드 → 서버 기동)를 각자 브랜치에서 그대로 수행하면 동일한 스캐폴딩 위에서 바로 개발 시작 가능. 각자 손댈 파일은 대략 다음과 같다.

- **auth-users (이다영)**: `app/routers/auth.py`, `app/routers/users.py`, `app/models/user.py`(필요시 필드 보정), `app/deps.py`(실 JWT 완성되면 `get_current_user` 추가), `app/schemas/user.py`.
- **facilities-map (이가희)**: `app/routers/facilities.py`, `app/routers/map.py`, `app/models/facility.py`, `app/schemas/facility.py`, TourAPI 연동 클라이언트(신규 파일, 예: `app/services/tour_api.py`).
- **favorites (신지민)**: `app/routers/favorites.py`, `app/models/favorite.py`, `app/schemas/favorite.py`.

각 라우터의 `TODO: 구현` / `raise NotImplementedError`가 본인이 채울 부분이다. CRUD 로직은 `app/crud/`에 도메인별 파일(`facility.py`, `favorite.py`, `user.py`)로 나눠서 추가하는 걸 권장 (현재 `app/crud/__init__.py`만 있고 빈 상태).

### 시작 전에 확인할 것

- **PR로만 merge됨**: 저장소가 public이라 Collaborator로 추가되지 않아도 fork + PR은 누구나 가능. `main`에 대한 직접 push는 하지 않고, PR을 올리면 리포 관리자가 리뷰 후 merge한다.
- **`.env`는 각자 로컬에서 새로 생성**: `.gitignore` 대상이라 저장소에는 없음. 클론 후 반드시 `cp .env.example .env`부터.
- **외부 API 키 없이도 개발은 가능**: `KAKAO_REST_API_KEY`, `TOUR_API_KEY`는 이가희 파트 실연동 테스트에만 필요. 나머지는 mock 데이터로 라우터/CRUD 로직 작성 가능하고, 키 발급 후 `.env`에 채워 넣으면 됨.

## 브랜치 / merge 전략

- 도메인별 라우터가 분리되어 있어 3인이 각자 파트에서 독립적으로 작업 가능 (mock auth 덕분에 인증 라우터를 기다릴 필요 없음).
- merge 순서: `auth-users` → `facilities-map` → `favorites` (`favorites`/`facilities`가 `users.id` FK에 의존하므로 인증/유저 파트가 먼저 들어가야 함).
- 각자 작업 완료되면 fork에서 `Ongil-tour/Backend`의 `main`으로 PR 생성 → 위 순서대로 리뷰/머지(리포 관리자가 처리). 뒤 순서 담당자는 앞 PR이 머지된 뒤 `git fetch upstream && git merge upstream/main`으로 최신 `main`을 받아 이어가는 걸 권장 (모델 변경으로 인한 마이그레이션 충돌 방지).
- 모델을 수정한 PR은 반드시 `alembic revision --autogenerate`로 생성한 마이그레이션 파일을 함께 커밋할 것.

## 스키마 개요

- `facilities`: 시설 마스터. 접근성 필드 7종(휠체어 접근성/경사로/장애인 화장실/장애인 주차장/엘리베이터/반려동물 동반/수유실) + `geom`(PostGIS Point, 공간쿼리용) + `latitude`/`longitude`(응답용).
- `favorite_lists`: 유저당 고정 3개 리스트(`list_type` enum). 실제 명칭(want_to_go/visited/custom)은 확정 문서 나오면 `app/models/favorite.py`의 `ListType`과 함께 교체.
- `favorites`: `facility_id` FK로 정규화, TourAPI raw 필드 없음.
- `users` / `refresh_tokens`: OAuth(카카오/구글/네이버) 기반.

## 자주 쓰는 명령어

```
docker compose logs -f api          # 로그 확인
docker compose down                 # 전체 종료 (볼륨 유지)
docker compose down -v              # 전체 종료 + DB 볼륨 삭제 (스키마 초기화하고 싶을 때)
```
