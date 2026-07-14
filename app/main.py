from fastapi import FastAPI

from app.routers import auth, users, facilities, map as map_router, favorites

app = FastAPI(title="Ongil-tour API", version="0.1.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(facilities.router)
app.include_router(map_router.router)
app.include_router(favorites.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}