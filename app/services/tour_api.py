"""
TourAPI(한국관광공사) 클라이언트.

두 개의 별도 서비스로 나뉘어 있고, data.go.kr 활용신청도 각각 따로 필요하다.
- KorService2      : detailCommon2(이름/주소/좌표/연락처), detailIntro2(타입별 부가정보)
- KorWithService2  : detailWithTour2(무장애 정보)

실제 호출로 확인한 사항(Postman 대신 curl로 검증, 2026-07-18):
- detailCommon2, detailWithTour2는 contentTypeId 파라미터를 받지 않는다 (넣으면
  INVALID_REQUEST_PARAMETER_ERROR). detailIntro2는 contentTypeId가 필수다.
- detailIntro2 응답 필드는 contentTypeId별로 완전히 다르다 (OPERATING_HOURS_FIELD_BY_TYPE 참고).
- detailWithTour2 필드는 contentTypeId와 무관하게 항상 동일한 필드셋이며, 전부
  boolean이 아니라 자유서술 텍스트다(값 있으면 문자열, 없으면 ""). wheelchair_accessible은
  전용 필드가 없고 route/exit 텍스트 서술 여부로 판단한다(app/services/facility_sync.py 참고).
"""
import time

import httpx

from app.core.config import settings

_MAX_RETRIES = 3
_RETRY_BACKOFF_S = 2.0

KOR_SERVICE_BASE = "https://apis.data.go.kr/B551011/KorService2"
KOR_WITH_SERVICE_BASE = "https://apis.data.go.kr/B551011/KorWithService2"

_COMMON_PARAMS = {
    "MobileOS": "ETC",
    "MobileApp": "ongil",
    "_type": "json",
}

# detailIntro2에서 "운영시간"에 해당하는 필드는 contentTypeId마다 이름이 다르다.
# 실제 호출로 확인된 것만 채운다 (미확인 타입은 조립 시 operating_hours=None으로 빠진다).
OPERATING_HOURS_FIELD_BY_TYPE: dict[str, str] = {
    "12": "usetime",         # 관광지
    "14": "usetimeculture",  # 문화시설
    "32": "checkintime",     # 숙박
    "39": "opentimefood",    # 음식점
}


class TourApiError(RuntimeError):
    pass


class TourApiQuotaExceededError(TourApiError):
    """일일/트래픽 쿼터 초과로 API가 더 이상 정상 응답하지 않는 상태."""


# data.go.kr 공통 에러코드 중 쿼터/트래픽 관련. 22 = LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR.
_QUOTA_EXCEEDED_RESULT_CODES = {"22"}


def _get_with_retry(url: str, params: dict) -> httpx.Response:
    """TourAPI가 가끔 응답을 10초 넘게 끌거나(단순 지연), 컨테이너 네트워크가 일시적으로
    DNS/연결 오류를 내는 경우가 있어 - 쿼터 초과와 무관한 전송 레벨 오류 전반에 대해
    지수 백오프로 재시도한다. httpx.TransportError가 TimeoutException/ConnectError 등을
    전부 포괄하는 상위 클래스."""
    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            return httpx.get(url, params=params, timeout=20.0)
        except httpx.TransportError as e:
            last_error = e
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_BACKOFF_S * (2**attempt))
    raise last_error


def _request_body(base_url: str, operation: str, **params) -> dict:
    """공통 응답 검증 후 body 전체(items뿐 아니라 totalCount 등)를 반환한다."""
    resp = _get_with_retry(
        f"{base_url}/{operation}",
        params={"serviceKey": settings.TOUR_API_KEY, **_COMMON_PARAMS, **params},
    )
    if resp.status_code == 429:
        # 게이트웨이 레벨 트래픽 제한(초당/일일 호출 한도 초과)도 쿼터 초과로 취급한다.
        # raise_for_status()에 맡기면 일반 Exception(HTTPStatusError)이 되어 배치가
        # 이걸 "이 항목만 실패"로 오인하고 남은 수천 건에 계속 429를 날리며 헛돈다.
        raise TourApiQuotaExceededError(f"{operation}: 429 Too Many Requests (트래픽/쿼터 초과)")
    if resp.status_code >= 400:
        # httpx의 기본 메시지는 serviceKey가 담긴 전체 URL을 그대로 노출하므로
        # (배치 실패 로그에 API 키가 평문으로 수천 줄 남는다), 직접 sanitize해서 던진다.
        raise TourApiError(f"{operation}: HTTP {resp.status_code} {resp.reason_phrase}")
    try:
        data = resp.json()
    except ValueError:
        # 쿼터를 넘기면 게이트웨이가 _type=json을 무시하고 XML 에러 페이지를 내려준다.
        raise TourApiQuotaExceededError(
            f"{operation}: 쿼터 초과로 추정되는 비-JSON 응답: {resp.text[:200]!r}"
        )

    header = data["response"]["header"]
    if header["resultCode"] in _QUOTA_EXCEEDED_RESULT_CODES:
        raise TourApiQuotaExceededError(f"{operation}({params}): {header['resultMsg']}")
    if header["resultCode"] not in ("0000", "03"):  # 03 = NODATA_ERROR (해당 데이터 없음)
        raise TourApiError(f"{operation}({params}) failed: {header['resultMsg']}")

    return data["response"]["body"]


def _request_items(base_url: str, operation: str, **params):
    return _request_body(base_url, operation, **params)["items"]


def _get(base_url: str, operation: str, **params) -> dict:
    """단건 조회용. item이 여러 개면 첫 번째만 반환한다."""
    items = _request_items(base_url, operation, **params)
    if items == "":
        return {}
    item = items["item"]
    return item[0] if isinstance(item, list) else item


def _get_list(base_url: str, operation: str, **params) -> list[dict]:
    items = _request_items(base_url, operation, **params)
    if items == "":
        return []
    item = items["item"]
    return item if isinstance(item, list) else [item]


def get_detail_common(content_id: str) -> dict:
    """이름/주소/좌표/연락처(title, addr1, addr2, mapx, mapy, tel, overview 등)."""
    return _get(KOR_SERVICE_BASE, "detailCommon2", contentId=content_id)


def get_detail_intro(content_id: str, content_type_id: str) -> dict:
    """운영시간 등 타입별 부가정보. 필드명은 contentTypeId에 따라 다르다."""
    return _get(KOR_SERVICE_BASE, "detailIntro2", contentId=content_id, contentTypeId=content_type_id)


def get_detail_with_tour(content_id: str) -> dict:
    """무장애 정보(parking, restroom, elevator, lactationroom, helpdog, route, exit 등, 전부 텍스트)."""
    return _get(KOR_WITH_SERVICE_BASE, "detailWithTour2", contentId=content_id)


def get_area_based_list(content_type_id: str, area_code: str, num_of_rows: int = 20, page_no: int = 1) -> list[dict]:
    """지역+타입 기준 콘텐츠 목록. 배치에서 contentId 리스트를 뽑을 때 사용 (item에 contentid, title 포함)."""
    return _get_list(
        KOR_SERVICE_BASE,
        "areaBasedList2",
        arrange="A",
        numOfRows=num_of_rows,
        pageNo=page_no,
        contentTypeId=content_type_id,
        areaCode=area_code,
    )


def get_area_based_count(content_type_id: str, area_code: str) -> int:
    """지역+타입 기준 전체 건수만 저비용으로 조회한다 (numOfRows=1, list 콜 1건).
    배치 실행 전 규모 산정용 - 상세 콜(시설당 2~3콜)을 전혀 쓰지 않는다."""
    body = _request_body(
        KOR_SERVICE_BASE,
        "areaBasedList2",
        arrange="A",
        numOfRows=1,
        pageNo=1,
        contentTypeId=content_type_id,
        areaCode=area_code,
    )
    return int(body.get("totalCount", 0))
