FROM python:3.12-slim

WORKDIR /app

# psycopg2-binary라 별도 libpq-dev는 필요 없지만, 추후 빌드용 패키지 대비 최소한만 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]