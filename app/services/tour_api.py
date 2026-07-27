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
import httpx

from app.core.config import settings

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


def _request_items(base_url: str, operation: str, **params):
    resp = httpx.get(
        f"{base_url}/{operation}",
        params={"serviceKey": settings.TOUR_API_KEY, **_COMMON_PARAMS, **params},
        timeout=10.0,
    )
    resp.raise_for_status()
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

    return data["response"]["body"]["items"]


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
