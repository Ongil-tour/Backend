from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, users, facilities, map as map_router, favorites

app = FastAPI(title="Ongil-tour API", version="0.1.0")

# WebView(KakaoMapView.tsx)가 source={{ html: ..., baseUrl: 'http://localhost' }}로
# 지도 HTML을 로드하기 때문에, fetch() 요청의 Origin이 항상 http://localhost로 찍힌다.
# dev/prod 구분 없이 baseUrl이 코드에 고정값으로 박혀있어 origin도 하나로 고정.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(facilities.router)
app.include_router(map_router.router)
app.include_router(favorites.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}