from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, users, facilities, map as map_router, favorites

app = FastAPI(title="Ongil-tour API", version="0.1.0")

# WebView(KakaoMapView.tsx)가 source={{ html: ..., baseUrl: ... }}로
# 지도 HTML을 로드하기 때문에, fetch() 요청의 Origin이 baseUrl 값으로 찍힌다.
# 프론트에서 baseUrl을 http://localhost -> https://localhost로 바꿔서 둘 다 허용해야 함.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "https://localhost"],
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