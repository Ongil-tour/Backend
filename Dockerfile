FROM python:3.12-slim

WORKDIR /app

# psycopg2-binary라 별도 libpq-dev는 필요 없지만, 추후 빌드용 패키지 대비 최소한만 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render는 컨테이너가 리슨해야 할 포트를 $PORT로 주입한다(고정 8000이 아님).
# alembic upgrade head를 먼저 돌려서 배포마다 스키마를 최신으로 맞춘다(멱등).
# docker-compose.yml의 api 서비스는 자체 command:로 이 CMD를 덮어써서 로컬 개발엔 영향 없음.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]