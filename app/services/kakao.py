"""
카카오 로컬 카테고리 검색 클라이언트.

편의점(CS2)/병원(HP8)은 내부 DB에 배치 적재하지 않고 실시간으로 조회한다 (설계 근거:
무장애 상세 enrichment가 필요 없고, 편의점은 전국 단위로는 배치 대상으로 삼기엔 너무 큼).
대신 좌표를 격자로 스냅한 키로 Redis에 캐싱해 쿼터 소모와 레이턴시를 줄인다 (TTL 6~24h).
"""
import json

import httpx

from app.core.config import settings
from app.core.redis import get_redis

CATEGORY_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/category.json"

_GRID_PRECISION = 3  # 소수 3자리 ≈ 111m 격자
_CACHE_TTL_S = 12 * 60 * 60  # 6~24h 범위의 중간값
_PAGE_SIZE = 15
_MAX_PAGES = 3  # 카카오 API 자체 제한 (최대 45건)
_MAX_RADIUS_M = 20000  # 카카오 category search 반경 검색 상한


def _snap(value: float) -> float:
    return round(value, _GRID_PRECISION)


def _cache_key(category_group_code: str, **params) -> str:
    parts = ":".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"kakao:category:{category_group_code}:{parts}"


def _fetch_page(category_group_code: str, page: int, **geo_params) -> dict:
    resp = httpx.get(
        CATEGORY_SEARCH_URL,
        params={"category_group_code": category_group_code, "page": page, "size": _PAGE_SIZE, **geo_params},
        headers={"Authorization": f"KakaoAK {settings.KAKAO_REST_API_KEY}"},
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json()


def _fetch_all_documents(category_group_code: str, **geo_params) -> list[dict]:
    documents: list[dict] = []
    for page in range(1, _MAX_PAGES + 1):
        body = _fetch_page(category_group_code, page, **geo_params)
        documents.extend(body["documents"])
        if body["meta"]["is_end"]:
            break
    return documents


def _cached_or_fetch(cache_key: str, fetch) -> list[dict]:
    redis_client = get_redis()
    cached = redis_client.get(cache_key)
    if cached is not None:
        return json.loads(cached)

    documents = fetch()
    redis_client.setex(cache_key, _CACHE_TTL_S, json.dumps(documents))
    return documents


def search_by_radius(category_group_code: str, lat: float, lng: float, radius_m: int) -> list[dict]:
    """중심 좌표 반경(m) 내 카테고리 검색. 결과를 거리순으로 반환한다."""
    cache_key = _cache_key(category_group_code, lat=_snap(lat), lng=_snap(lng), radius_m=radius_m)
    return _cached_or_fetch(
        cache_key,
        lambda: _fetch_all_documents(
            category_group_code, x=lng, y=lat, radius=min(radius_m, _MAX_RADIUS_M), sort="distance"
        ),
    )


def search_by_bounds(
    category_group_code: str, sw_lat: float, sw_lng: float, ne_lat: float, ne_lng: float
) -> list[dict]:
    """bounding box 내 카테고리 검색."""
    cache_key = _cache_key(
        category_group_code,
        sw_lat=_snap(sw_lat),
        sw_lng=_snap(sw_lng),
        ne_lat=_snap(ne_lat),
        ne_lng=_snap(ne_lng),
    )
    rect = f"{sw_lng},{sw_lat},{ne_lng},{ne_lat}"
    return _cached_or_fetch(cache_key, lambda: _fetch_all_documents(category_group_code, rect=rect))
